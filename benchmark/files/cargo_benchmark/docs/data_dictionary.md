# Data Dictionary (schema version 2: 20 tables, 300 columns)

Conventions: timestamps are UTC text `YYYY-MM-DD HH:MM:SS`; dates are `YYYY-MM-DD`; money is USD unless a column says otherwise. The dataset's "now" is **2025-12-20 00:00:00** (`benchmark_meta.as_of_timestamp`). All airlines, aircraft registrations, customers, consignees, crew, brokers, insurers and suppliers are fictional; airports and aircraft models are public facts with approximate, illustrative figures.

Names below are the **normal** schema. The **mixed** and **cryptic** schemas rename every table and column one to one (see [schema_variants.md](schema_variants.md)) and hold identical rows.

## Tables

| Table | Rows | Meaning | Key columns / rules |
|---|---:|---|---|
| `benchmark_meta` | 5 | Dataset constants | as-of timestamp, seed, engine, schema version |
| `airports` | 18 | Airports served | `iata_code` (3) / `icao_code` (4) unique; `region` north_america / europe / middle_east / asia_pacific; `is_cargo_hub`, `has_24h_customs`, `night_curfew` 0/1 |
| `airlines` | 5 | Cargo carriers | `iata_code` (2), `icao_code` (3), `callsign`, `aoc_number` unique; `home_hub_airport_id` → airports; `alliance` nullable |
| `aircraft_types` | 5 | Freighter models | payload, volume, range, MTOW, empty weight, fuel capacity, burn per hour, `main_deck_positions`; empty weight + payload ≤ MTOW |
| `aircraft` | 22 | Individual aircraft | `tail_number`, `serial_number` unique; `home_airport_id`; `ownership` owned/leased (lessor and lease end only when leased); `status` active / maintenance / retired, only active aircraft fly |
| `customers` | 63 | Shippers and forwarders | `account_code` unique; (`name`,`country`) unique, one name exists in two countries; `loyalty_tier` follows shipment volume; 3 customers never ship |
| `warehouses` | 54 | Cargo terminals at airports | `warehouse_type` general / cold_chain / dangerous_goods / express; `is_bonded` (every airport has at least one bonded warehouse); `min_temperature_c` NULL iff no cold rooms |
| `crew_members` | 235 | Pilots and loadmasters | `crew_rank` captain / first_officer / loadmaster; pilots have `type_rating_id`, licence and medical dates, loadmasters have none; `seniority_number` unique per airline; `is_active` |
| `flights` | 2,252 | Individual flights | `flight_number` = airline code + 3 digits; `status` scheduled / completed / cancelled; `actual_*` and `takeoff_weight_kg` only for completed; `cancellation_reason` only for cancelled; `weather_at_departure` NULL only for future flights; `delay_code` only for completed flights departing > 15 min late |
| `crew_assignments` | 5,630 | Crew rostered on a flight | `duty_role` captain / first_officer / relief_pilot / loadmaster; exactly one pilot flying; `report_time` = scheduled departure − 90 min, `release_time` = arrival + 30 min; `rest_minutes_before` since the member's previous release; `block_minutes_credited` only when completed |
| `maintenance_records` | 450 | Checks and repairs | `check_type` line / A_check / B_check / C_check / unscheduled; `ata_chapter` only for unscheduled; `status` planned / in_progress / completed (costs and labour only when completed, `end_time` NULL while in progress); `is_aog` = unplanned grounding |
| `fuel_uplifts` | 2,092 | Fuel loaded before a completed flight | one per completed flight, at its origin; kg = litres × density; cost = litres × price; CO2 = 3.16 × burned kg (tank to wake); `fuel_type` Jet A in the US, Jet A-1 elsewhere |
| `shipments` | 3,110 | A consignment booked by a customer | `awb_number` unique (last digit = serial mod 7); `chargeable_weight_kg` = max(weight, volume × 167); DG class only for dangerous goods; temperature range only for pharmaceuticals and perishables; `status` booked / in_transit / delivered / cancelled |
| `flight_cargo` | 3,818 | Shipment legs on flights | `leg_number` 1..n; each leg carries the whole shipment in one ULD; PMC/PAG pallets on the main deck, AKE/RKN containers and BULK in the lower hold; `load_sequence` unique per flight; `loaded_at` only for flown legs |
| `invoices` | 2,909 | One invoice per departed shipment | `invoice_number` unique; freight + fuel + security + handling + DG surcharges − discount = `amount_usd`; terms copied from the customer; discounts only for gold/platinum customers |
| `payments` | 2,544 | Money received against invoices | `customer_id` repeats the invoice owner; paid in `original_currency`, `original_amount` × `exchange_rate_to_usd` = `amount_usd` |
| `incidents` | 160 | Problems on a flown leg | `airport_id` = destination of that leg; `warehouse_id` nullable; `root_cause`, `reported_by`; `delay_minutes` only for delays; `resolved_at` and `corrective_action` only when resolved |
| `insurance_claims` | 78 | Claims filed for incidents with a claim amount | one per incident; customer = shipment owner; `status` filed / under_review / approved / rejected / paid with matching decision, rejection and settlement dates |
| `customs_declarations` | 4,181 | Export and import declarations | only when origin and destination are in different customs territories (Germany and the Netherlands form one EU territory); lodged at a bonded warehouse; `status` pending / cleared / held; duty = value × rate; exports carry no duty or VAT |
| `tracking_events` | 22,104 | Shipment status scans | `event_code` BKD booked, RCS received from shipper, DEP / ARR flight departure / arrival, RCF received from flight, NFD consignee notified, DLV delivered to consignee, CAN cancelled; `temperature_c` only for temperature-controlled shipments |

## Business rules (enforced by `validation/validation_checks.sql`)
* Flight-number prefix = operating airline; distance ≤ aircraft range; no overlapping flights per aircraft; each flight departs where the aircraft's previous non-cancelled flight landed.
* Loaded weight and volume never exceed the aircraft type's limits; main-deck ULDs never exceed the main-deck positions; take-off weight = empty weight + cargo + fuel ≤ MTOW.
* Leg 1 starts at the shipment origin, the last leg ends at its destination, consecutive legs connect with ≥ 12 h on the ground, and nothing departs before the booking date.
* Shipment status follows its legs: no legs → cancelled; all flown → delivered (landed at the destination); some flown → in_transit; none → booked.
* Crew belong to the operating airline, pilots are type-rated on the aircraft, licences are valid on the day of the flight, nobody works two duties at once and rest between duties is ≥ 12 h.
* Maintenance never overlaps the aircraft's flights and happens where the aircraft is; the grounded aircraft has an in-progress check.
* Customs: exports are cleared before leg 1 departs; imports are lodged after the final arrival; a consignee is only notified (NFD) and handed the goods (DLV) after a cleared import.
* Invoice and payment arithmetic, claim amounts and claim dates, and FX conversions are consistent; temperature excursion incidents and out-of-range probe readings occur only for temperature-controlled cargo.

## Deliberate edge cases
Customers with no shipments (3) · customers with only cancelled shipments · duplicate customer name in two countries · aircraft with no flights (maintenance/retired) · multi-leg shipments (~27 %) · multi-payment invoices · partially paid and unpaid invoices · empty flights with no cargo · departure delays up to 8 h · crew who were never rostered (inactive or on the grounded fleet) · pilots whose licence expired during 2025 · airports without a cold-chain warehouse · domestic and intra-EU shipments without customs · delivered shipments still held by import customs (no DLV scan) · incidents without insurance claims and root causes without any claim · rejected claims (no approved amount).

## Simplifications
* A shipment travels as one ULD and is never split; each leg carries the whole shipment.
* Crew are not tracked geographically between duties (only rest, airline, type rating and licence validity are enforced).
* Fuel burn uses a simple per-hour model by aircraft type; fuel prices and FX rates follow a smooth monthly pattern.
* Customs duty rates and VAT rates are illustrative, not legal tariffs.
