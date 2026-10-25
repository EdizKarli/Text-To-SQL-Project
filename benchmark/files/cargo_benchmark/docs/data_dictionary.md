# Data Dictionary

Conventions: timestamps are UTC text `YYYY-MM-DD HH:MM:SS`; dates are `YYYY-MM-DD`; money is USD. The dataset's "now" is **2025-12-20** (`benchmark_meta.as_of_timestamp`). All airlines, aircraft registrations and customers are fictional.

| Table | Meaning | Key columns / rules |
|---|---|---|
| `airlines` | Cargo carriers (5) | `iata_code` 2 letters, unique |
| `airports` | Airports served (18) | `iata_code` 3 letters, unique; `is_cargo_hub` 0/1; lat/long in range |
| `aircraft_types` | Freighter models (5) | `max_payload_kg`, `max_volume_m3`, `max_range_km` (approximate illustrative values) |
| `aircraft` | Individual aircraft (22) | `tail_number` unique; `status` ∈ active / maintenance / retired; only `active` aircraft fly |
| `customers` | Shippers and forwarders (63) | `payment_terms_days` ∈ 15/30/45/60; (`name`,`country`) unique — one name occurs in two countries; 3 customers never ship |
| `flights` | Individual flights | `flight_number` = airline code + 3 digits; `status` ∈ scheduled / completed / cancelled; `actual_*` filled **only** for completed flights; `distance_km` great-circle |
| `shipments` | A consignment booked by a customer | `origin/destination_airport_id`, `total_weight_kg`, `total_volume_m3`, `declared_value_usd`; `status` ∈ booked / in_transit / delivered / cancelled |
| `flight_cargo` | Links shipments to the flights (legs) carrying them | `leg_number` 1..n; `leg_status` planned / flown; each leg carries the whole shipment; cancelled shipments have no rows |
| `invoices` | One invoice per departed shipment | issued on date leg 1 actually departed; `due_date` = issue + customer terms; `status` unpaid / partially_paid / paid |
| `payments` | Money received against invoices | `customer_id` repeats the invoice owner (cross-table rule); an invoice may have several payments |
| `incidents` | Problems on a flown leg | `incident_type`, `severity`, `claim_amount_usd` (nullable), `resolved` 0/1 |
| `benchmark_meta` | Dataset constants | as-of timestamp, seed |

## Business rules (enforced by `validation/validation_checks.sql`)
* Flight-number prefix = operating airline; distance ≤ aircraft range; no overlapping flights per aircraft; each flight departs where the aircraft's previous non-cancelled flight landed.
* Loaded weight and volume per flight never exceed the aircraft type's limits; no cargo on cancelled flights.
* Leg 1 starts at the shipment origin, the last leg ends at its destination, consecutive legs connect with ≥ 12 h on the ground, and nothing departs before the booking date.
* Shipment status is derived from its legs: no legs → cancelled; all flown → delivered; some flown → in_transit; none → booked.
* Invoice status is derived from payments; due date from customer terms; payments are never dated before issue or after the as-of day and never exceed the invoice.
* Temperature-excursion incidents occur only for pharmaceuticals/perishables; claims never exceed declared value.

## Deliberate edge cases
Customers with no shipments (3) · customers with only cancelled shipments · duplicate customer name in two countries · aircraft with no flights (maintenance/retired) · multi-leg shipments (~27 %) · multi-payment invoices · partially paid and unpaid invoices · empty flights with no cargo · departure delays up to 8 h.
