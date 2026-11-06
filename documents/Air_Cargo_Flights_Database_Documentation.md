# Air Cargo Flights Database: Documentation

This guide explains our benchmark database. It covers every table and column, the rules the data follows, the edge cases, the simplifications and the questions.

## 1. Overview

The Air Cargo Flights database is a synthetic (computer-generated) SQLite database. It is a text-to-SQL benchmark: a test for systems that turn English questions into SQL.

It models five fictional cargo airlines. They fly 22 freighter aircraft between 18 real airports during 2025. The dataset's "today" is **2025-12-20 00:00:00**. Flights before it have been flown or cancelled. Flights after it are still scheduled.

### 1.1 Key facts

| Item | Value |
|---|---|
| Engine | SQLite 3.25 or newer |
| Size | 20 tables, 300 columns, 49,735 rows |
| Time covered | Flights from 1 January to 31 December 2025 |
| "Today" | 2025-12-20 00:00:00 UTC (stored in `benchmark_meta`) |
| Questions | 480: 120 base questions (40 easy, 40 moderate, 40 hard), each in 4 styles |
| Real or fictional | Real: airports and aircraft models (approximate figures). Fictional: airlines, companies, people, registrations and amounts. |

### 1.2 Airlines, aircraft and airports

**Airlines (5)**

| Code | Airline | Country | Main hub | Alliance | Aircraft |
|---|---|---|---|---|---:|
| MC | Meridian Air Cargo | United States | MEM | SkyFreight Alliance | 7 |
| BF | Bosphorus Freight | Turkey | IST | none | 4 |
| SK | Silkline Cargo | Hong Kong | HKG | SkyFreight Alliance | 4 |
| EA | Eurasia Air Freight | Germany | LEJ | CargoLink | 4 |
| GC | Gulf Crescent Cargo | United Arab Emirates | DXB | CargoLink | 3 |

**Aircraft models (5)**

| Model | Maker | Max cargo weight | Max cargo volume | Range | Aircraft |
|---|---|---:|---:|---:|---:|
| 747-8F | Boeing | 134,000 kg | 854 m³ | 8,000 km | 3 |
| 777F | Boeing | 102,000 kg | 653 m³ | 9,000 km | 5 |
| 767-300F | Boeing | 52,700 kg | 438 m³ | 6,000 km | 6 |
| A330-200F | Airbus | 65,000 kg | 475 m³ | 7,400 km | 5 |
| 737-800BCF | Boeing | 23,000 kg | 140 m³ | 3,700 km | 3 |

20 of the 22 aircraft are active. One Gulf Crescent A330-200F is grounded for a long check. One Meridian 767-300F is retired. These two have no flights.

**Airports (18; \* = cargo hub)**

| Region | Airports |
|---|---|
| North America (7) | MEM Memphis\*, SDF Louisville\*, ANC Anchorage\*, LAX Los Angeles, ORD Chicago, MIA Miami, JFK New York |
| Europe (4) | FRA Frankfurt\*, LEJ Leipzig\*, AMS Amsterdam, IST Istanbul\* |
| Middle East (2) | DXB Dubai\*, DOH Doha\* |
| Asia Pacific (5) | HKG Hong Kong\*, PVG Shanghai, ICN Incheon (Seoul)\*, NRT Tokyo Narita, SIN Singapore |

### 1.3 Files

All paths are inside `benchmark/files/cargo_benchmark/`.

| What | Where |
|---|---|
| Database | `databases/cargo_normal.db` |
| Table definitions, with comments | `schema/schema.sql` |
| Questions | `questions/questions_normal.json` |
| Reasoning hints | `hints/hints_normal.jsonl` |
| Data checks and answer tests | `validation/` |
| Running and scoring a model | `evaluation/run_ollama.py`, `evaluation/evaluate.py` |

The same data also exists with German-style names (mixed) and meaningless names (cryptic). See `docs/schema_variants.md`.

## 2. How to read this document

- **"Today"** is 2025-12-20 00:00:00. Everything recorded happened before it: flights, scans, payments, incidents. Only plans and deadlines come after it: scheduled flights, planned maintenance, rostered crew, due dates and expiry dates.
- **Times** are UTC text `YYYY-MM-DD HH:MM:SS`. **Dates** are `YYYY-MM-DD`. SQLite has no date type, so date maths uses `julianday()` and `substr()`.
- **Money** is in US dollars (USD) unless the column says otherwise.
- **Flags** are 0/1 columns: 1 = yes, 0 = no.
- **Codes** are columns with a fixed list of allowed values. This document lists them all.
- **IDs:** every table has a number key (e.g. `airport_id`). A column that holds another table's key is a link, shown as "→ table".
- **Empty** means NULL. "Empty?" says when and why a value is missing. "No" means it is always filled.

## 3. How the data fits together

### 3.1 The life of a shipment

1. A customer books a shipment (`shipments`). Scan **BKD** (booked).
2. The goods arrive at a warehouse at the origin airport and are weighed. Scan **RCS** (received from shipper).
3. If the goods cross a customs border, an export declaration is lodged (`customs_declarations`).
4. The shipment flies on one flight, or two with a connection. Each flight it takes is one row in `flight_cargo`, called a "leg". Every flown leg has a **DEP** (departed) and an **ARR** (arrived) scan.
5. On the day the first flight departs, an invoice is issued (`invoices`). The customer pays it (`payments`).
6. When the last flight lands, the status becomes `delivered`. If needed, an import declaration is lodged at the destination.
7. The goods reach the destination warehouse (**RCF**), the receiver is notified (**NFD**) and the goods are handed over (**DLV**). Handover happens only after import customs releases the goods.
8. If something goes wrong on a leg (damage, delay, loss…), an incident is recorded (`incidents`). If the customer asks for money, an insurance claim follows (`insurance_claims`).

### 3.2 The operations side

- Each airline (`airlines`) operates aircraft (`aircraft`) of a model (`aircraft_types`). One aircraft flies each flight (`flights`).
- Pilots and loadmasters (`crew_members`) are put on flights through `crew_assignments`.
- Every completed flight has exactly one fuelling record (`fuel_uplifts`).
- Checks and repairs between flights are in `maintenance_records`.
- Each airport has 2 to 4 cargo warehouses (`warehouses`).

### 3.3 Tables at a glance

| Area | Table | One row is … | Rows |
|---|---|---|---:|
| Reference | `airports` | an airport | 18 |
| Reference | `airlines` | a cargo airline | 5 |
| Reference | `aircraft_types` | a freighter model | 5 |
| Reference | `aircraft` | one aircraft | 22 |
| Reference | `customers` | a customer company | 63 |
| Reference | `warehouses` | a warehouse at an airport | 54 |
| Crew | `crew_members` | a pilot or loadmaster | 235 |
| Crew | `crew_assignments` | one person on one flight | 5,630 |
| Operations | `flights` | one flight | 2,252 |
| Operations | `maintenance_records` | a check or repair | 450 |
| Operations | `fuel_uplifts` | the fuel for one flight | 2,092 |
| Sales | `shipments` | a consignment booked by a customer | 3,110 |
| Sales | `flight_cargo` | one leg of a shipment on one flight | 3,818 |
| Money | `invoices` | the bill for one shipment | 2,909 |
| Money | `payments` | one payment for an invoice | 2,544 |
| Problems | `incidents` | a problem on a shipment leg | 160 |
| Problems | `insurance_claims` | an insurance claim for an incident | 78 |
| Border | `customs_declarations` | an export or import declaration | 4,181 |
| Tracking | `tracking_events` | one status scan of a shipment | 22,104 |
| Helper | `benchmark_meta` | a dataset setting | 5 |

### 3.4 Common join paths

| From | To | Path |
|---|---|---|
| a flight | its airline | `flights.aircraft_id` → `aircraft.airline_id` → `airlines` |
| a shipment | its flights | `shipments` → `flight_cargo` (by `shipment_id`) → `flights` (by `flight_id`) |
| an invoice | its customer | `invoices.shipment_id` → `shipments.customer_id` → `customers` (payments also store `customer_id`) |
| an incident | its shipment and customer | `incidents.flight_cargo_id` → `flight_cargo.shipment_id` → `shipments.customer_id` |
| a claim | its shipment | `insurance_claims.incident_id` → `incidents` → `flight_cargo` → `shipments` |
| fuel or crew | the aircraft | `fuel_uplifts.flight_id` or `crew_assignments.flight_id` → `flights.aircraft_id` → `aircraft` |
| a flight | both its airports | `origin_airport_id` and `destination_airport_id` → `airports` (join `airports` twice) |

## 4. Tables and columns

Each table starts with what one row is, the number of rows, the key and the links.

### 4.1 airports

**One row:** an airport (real, approximate figures). **Rows:** 18. **Key:** `airport_id`. **Used by:** most other tables.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `airport_id` | Airport number (1–18). | ID | No |
| `iata_code` | 3-letter airline code, e.g. FRA. Unique. | text | No |
| `icao_code` | 4-letter air traffic code, e.g. EDDF. Unique. | text | No |
| `name` | Full airport name. | text | No |
| `city` | City it serves. | text | No |
| `country` | Country (11 values; Hong Kong is its own value). | text | No |
| `region` | `north_america`, `europe`, `middle_east` or `asia_pacific`. Istanbul is `europe`. | code | No |
| `timezone` | Local time zone, e.g. Europe/Berlin. Information only: all times are UTC. | text | No |
| `latitude`, `longitude` | Position. North/east are +, south/west are −. | degrees | No |
| `elevation_m` | Height above sea level (Amsterdam is −3). | metres | No |
| `runway_count` | Number of runways. | count | No |
| `longest_runway_m` | Longest runway. | metres | No |
| `is_cargo_hub` | 1 = major cargo hub (10 airports). | flag | No |
| `annual_cargo_capacity_t` | Cargo it can handle per year. | tonnes/year | No |
| `has_24h_customs` | 1 = customs open 24 hours (15 airports). | flag | No |
| `night_curfew` | 1 = night flight limits (FRA, NRT). Information only: the schedule ignores it. | flag | No |

### 4.2 airlines

**One row:** a cargo airline (fictional). **Rows:** 5. **Key:** `airline_id`. **Links:** `home_hub_airport_id` → airports. **Used by:** `aircraft`, `crew_members`. A flight belongs to an airline through its aircraft.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `airline_id` | Airline number (1–5). | ID | No |
| `iata_code` | 2-letter code: MC, BF, SK, EA, GC. Every flight number starts with it. | text | No |
| `icao_code` | 3-letter code: MDC, BSF, SLK, EAF, GCC. | text | No |
| `name` | Airline name, e.g. Meridian Air Cargo. | text | No |
| `callsign` | Radio name, e.g. MERIDIAN. | text | No |
| `country` | Home country. | text | No |
| `headquarters_city` | City of the head office. | text | No |
| `founded_year` | Year founded (1994–2009). | year | No |
| `home_hub_airport_id` | Main hub → airports. | ID | No |
| `alliance` | `CargoLink` or `SkyFreight Alliance` (fictional). | code | Yes: no alliance (Bosphorus Freight) |
| `is_cargo_only` | 1 = cargo only. 0 = also flies passengers (Bosphorus, Gulf Crescent); only cargo flights are in the data. | flag | No |
| `aoc_number` | Air operator certificate: the licence to run an airline. | text | No |
| `website`, `contact_email` | Fictional addresses (.example). | text | No |

### 4.3 aircraft_types

**One row:** a freighter model (real, approximate figures). **Rows:** 5. **Key:** `type_id`. **Used by:** `aircraft` (`type_id`), `crew_members` (`type_rating_id`).

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `type_id` | Model number (1–5). | ID | No |
| `model` | 747-8F, 777F, 767-300F, A330-200F or 737-800BCF. | text | No |
| `icao_type_designator` | Official type code: B748, B77L, B763, A332, B738. | text | No |
| `manufacturer` | Boeing or Airbus. | text | No |
| `engine_count` | 2 or 4. | count | No |
| `engine_model` | Engine name, e.g. GE90-110B1. | text | No |
| `max_payload_kg` | Heaviest cargo load. | kg | No |
| `max_volume_m3` | Largest cargo volume. | m³ | No |
| `max_range_km` | Longest distance it can fly. No flight is longer. | km | No |
| `cruise_speed_kmh` | Cruising speed. Information only: flight times use 780 km/h for all models. | km/h | No |
| `max_takeoff_weight_kg` | MTOW: most it may weigh at take-off (aircraft + cargo + fuel). | kg | No |
| `operating_empty_weight_kg` | OEW: empty aircraft, ready to fly. OEW + max payload ≤ MTOW. | kg | No |
| `fuel_capacity_kg` | Most fuel the tanks hold. | kg | No |
| `fuel_burn_kg_per_hour` | Average fuel used per hour. | kg/hour | No |
| `main_deck_positions` | Pallet places on the main deck. | count | No |
| `wingspan_m` | Wing tip to wing tip. | metres | No |

### 4.4 aircraft

**One row:** one aircraft (fictional registration). **Rows:** 22 (20 active, 1 in maintenance, 1 retired). **Key:** `aircraft_id`. **Links:** `type_id` → aircraft_types, `airline_id` → airlines, `home_airport_id` → airports. **Used by:** `flights`, `maintenance_records`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `aircraft_id` | Aircraft number (1–22). | ID | No |
| `tail_number` | Registration. Prefix shows the country: N (USA), TC- (Turkey), B- (Hong Kong), D- (Germany), A6- (UAE). Unique. | text | No |
| `serial_number` | Manufacturer serial number (MSN). Unique. | text | No |
| `type_id` | Model → aircraft_types. | ID | No |
| `airline_id` | Operating airline → airlines. | ID | No |
| `home_airport_id` | Home base → airports. Its first flight of the year leaves from here. | ID | No |
| `registration_country` | Country of registration (the airline's country). | text | No |
| `year_manufactured` | Year built. | year | No |
| `delivery_date` | Date the airline got it (year built or the year after). | date | No |
| `ownership` | `owned` or `leased`. | code | No |
| `lessor_name` | Leasing company. | text | Yes: owned |
| `lease_end_date` | Lease end (2026–2033). | date | Yes: owned |
| `total_flight_hours` | Hours flown up to 1 January 2025. 2025 flights are not added. | hours | No |
| `total_cycles` | Take-off/landing cycles up to 1 January 2025. | count | No |
| `last_heavy_check_date` | Last heavy check (C-check) before 2025. | date | Yes: in service under 5 years (5 aircraft) |
| `status` | `active` (flies), `maintenance` (grounded for a long check) or `retired`. Only active aircraft have flights. | code | No |

### 4.5 customers

**One row:** a customer company (fictional). **Rows:** 63. **Key:** `customer_id`. **Used by:** `shipments`, `payments`, `insurance_claims`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `customer_id` | Customer number (1–63). | ID | No |
| `account_code` | CUS-0001 to CUS-0063. Unique. | text | No |
| `name` | Company name. Not unique: "Orchid Motors" is in Canada and the United Kingdom. Name + country is unique. | text | No |
| `customer_type` | `shipper` (own goods), `freight_forwarder` (moves goods for others), `retailer` or `manufacturer`. | code | No |
| `country` | Customer's country (13). Not tied to where its shipments fly. | text | No |
| `city`, `address_line`, `postal_code` | Address (fictional). | text | No |
| `contact_name`, `contact_email`, `contact_phone` | Contact person (fictional). | text | No |
| `website` | Company website (fictional). | text | Yes: none (9 customers) |
| `sales_region` | `north_america`, `south_america`, `europe`, `middle_east` or `asia_pacific`. | code | No |
| `credit_limit_usd` | Most the customer may owe; depends on type. Information only: not checked. | USD | No |
| `payment_terms_days` | Days to pay: 15, 30, 45 or 60. Copied to every invoice. | days | No |
| `is_known_shipper` | 1 = security-approved shipper. | flag | No |
| `loyalty_tier` | `bronze`, `silver`, `gold` or `platinum`, by number of shipments (see 5.8). | code | No |
| `created_date` | Account opened (2018–2024). | date | No |

### 4.6 warehouses

**One row:** a cargo warehouse at an airport. **Rows:** 54 (2–4 per airport). **Key:** `warehouse_id`. **Links:** `airport_id` → airports. **Used by:** `incidents`, `customs_declarations`, `tracking_events`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `warehouse_id` | Warehouse number (1–54). | ID | No |
| `warehouse_code` | Airport + W + number, e.g. FRA-W1. W1 is always the general warehouse. | text | No |
| `airport_id` | Airport → airports. | ID | No |
| `operator_name` | Ground-handling company (fictional; 5). | text | No |
| `warehouse_type` | `general`, `cold_chain` (cold rooms), `dangerous_goods` or `express`. | code | No |
| `floor_area_m2` | Floor area. | m² | No |
| `capacity_tonnes` | Cargo it can store at once. | tonnes | No |
| `cold_room_count` | Cold rooms (0 = none). Cold-chain warehouses always have some. | count | No |
| `min_temperature_c` | Coldest room: −25, −20 or 2. | °C | Yes: no cold rooms |
| `dock_door_count` | Truck doors. | count | No |
| `has_dg_area` | 1 = has a dangerous-goods area (always 1 for `dangerous_goods`). | flag | No |
| `is_bonded` | 1 = customs-bonded: goods wait here for customs, and declarations are lodged here. Every W1 is bonded. | flag | No |
| `security_level` | `standard` or `high`. | code | No |
| `operates_24h` | 1 = open 24 hours. | flag | No |
| `opened_year` | Year opened (1985–2023). | year | No |
| `monthly_rent_usd` | Rent per month. | USD/month | No |

### 4.7 crew_members

**One row:** a pilot or loadmaster (fictional people). **Rows:** 235 (97 captains, 117 first officers, 21 loadmasters). **Key:** `crew_member_id`. **Links:** `airline_id` → airlines, `base_airport_id` → airports, `type_rating_id` → aircraft_types. **Used by:** `crew_assignments`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `crew_member_id` | Person number (1–235). | ID | No |
| `employee_number` | Airline code + 5 digits, e.g. MC-12345. Unique. | text | No |
| `first_name`, `last_name`, `email` | Name and work e-mail (fictional; e-mail unique). | text | No |
| `airline_id` | Employer → airlines. | ID | No |
| `base_airport_id` | Home base → airports. | ID | No |
| `crew_rank` | `captain`, `first_officer` (co-pilot) or `loadmaster` (cargo loading specialist). | code | No |
| `type_rating_id` | Model the pilot may fly → aircraft_types. | ID | Yes: loadmasters |
| `license_number` | Pilot licence: ATPL for captains, CPL for first officers, e.g. GE-ATPL-112188. Unique. | text | Yes: loadmasters |
| `license_expiry_date` | Licence expiry. 10 expired during 2025. | date | Yes: loadmasters |
| `medical_expiry_date` | Medical certificate expiry (all in 2026). | date | Yes: loadmasters |
| `hire_date` | Date hired (2005–2024). | date | No |
| `seniority_number` | Seniority by hire date (1 = first hired). Unique per airline. | number | No |
| `total_flight_hours` | Career hours (fixed; 2025 flights not added). | hours | No |
| `is_active` | 1 = working. 0 = inactive (17 people, never on a flight). | flag | No |

### 4.8 flights

**One row:** one flight of one aircraft. **Rows:** 2,252 (2,092 completed, 92 cancelled, 68 scheduled). **Key:** `flight_id`. **Links:** `aircraft_id` → aircraft; `origin_airport_id`, `destination_airport_id` → airports. The airline comes through the aircraft. **Used by:** `crew_assignments`, `fuel_uplifts`, `flight_cargo`, `tracking_events`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `flight_id` | Flight number, in order of scheduled departure. | ID | No |
| `flight_number` | Airline code + 3 digits, e.g. EA412. Reused on different days; number + scheduled departure is unique. | text | No |
| `flight_type` | `scheduled` (regular) or `charter` (hired; about 12%). | code | No |
| `aircraft_id` | Aircraft → aircraft. | ID | No |
| `origin_airport_id`, `destination_airport_id` | Departure and arrival airports (never the same). | ID | No |
| `scheduled_departure`, `scheduled_arrival` | Planned times. | UTC time | No |
| `actual_departure`, `actual_arrival` | Real times. | UTC time | Yes: cancelled or not flown yet |
| `departure_stand`, `arrival_stand` | Parking places, e.g. C12 (C, F or K + number). | text | No |
| `distance_km` | Great-circle distance. | km | No |
| `planned_cruise_altitude_ft` | Planned cruise height (28,000–41,000). | feet | No |
| `takeoff_weight_kg` | Empty aircraft + cargo + fuel (see 5.9). | kg | Yes: did not fly |
| `weather_at_departure` | `clear`, `cloudy`, `rain`, `snow`, `fog` or `thunderstorm`. | code | Yes: scheduled (future) |
| `delay_code` | IATA reason for a late departure: 31 documents late, 41 technical fault, 63 late crew boarding, 71 weather at departure, 81 air traffic limits on route, 89 airport limits, 93 late inbound aircraft. | code | Yes: 15 minutes late or less, or did not fly |
| `cancellation_reason` | `weather`, `technical`, `crew`, `commercial` or `atc`. | code | Yes: not cancelled |
| `status` | `completed` (flown), `cancelled` or `scheduled` (after today). | code | No |

### 4.9 crew_assignments

**One row:** one crew member on one flight. **Rows:** 5,630. **Key:** `assignment_id`. **Links:** `flight_id` → flights, `crew_member_id` → crew_members. A person appears at most once per flight.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `assignment_id` | Assignment number. | ID | No |
| `flight_id` | Flight → flights. Cancelled flights have no crew. | ID | No |
| `crew_member_id` | Person → crew_members. | ID | No |
| `duty_role` | `captain`, `first_officer`, `relief_pilot` (extra pilot on flights planned over 9 hours; always a first officer) or `loadmaster`. | code | No |
| `is_pilot_flying` | 1 = this pilot flies the aircraft. Exactly one per flight (captain or first officer). | flag | No |
| `report_time` | Duty start = scheduled departure − 90 min. | UTC time | No |
| `release_time` | Duty end = actual arrival + 30 min (scheduled arrival if not flown yet). | UTC time | No |
| `block_minutes_credited` | Minutes from actual departure to actual arrival. | minutes | Yes: not flown yet |
| `rest_minutes_before` | Rest since the person's previous duty. Always ≥ 720 (12 h). | minutes | Yes: first duty |
| `per_diem_usd` | 3.50 USD per duty hour, + 45 USD if a hotel is needed. | USD | No |
| `hotel_required` | 1 = the flight ends away from the person's base. | flag | No |
| `assignment_status` | `completed` (flown) or `rostered` (planned). | code | No |

### 4.10 maintenance_records

**One row:** one check or repair on one aircraft. **Rows:** 450 (443 completed, 6 planned, 1 in progress). **Key:** `maintenance_id`. **Links:** `aircraft_id` → aircraft, `airport_id` → airports.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `maintenance_id` | Job number, in order of start time. | ID | No |
| `work_order_number` | e.g. WO-2025-00001. Unique. | text | No |
| `aircraft_id` | Aircraft → aircraft. | ID | No |
| `airport_id` | Where the work is done (where the aircraft last landed) → airports. | ID | No |
| `check_type` | `line` (a few hours), `A_check` (about a day), `B_check` (1–2 days), `C_check` (weeks; only the grounded aircraft) or `unscheduled` (fault repair). | code | No |
| `ata_chapter` | Aircraft system repaired, as an ATA chapter (e.g. 32 = landing gear). | number | Yes: not unscheduled |
| `mro_provider` | The airline's own technicians or an outside maintenance company. | text | No |
| `start_time` | Start of work. | UTC time | No |
| `end_time` | End of work. | UTC time | Yes: in progress (1 job) |
| `labor_hours` | Technician hours. | hours | Yes: not completed |
| `parts_cost_usd` | Spare parts cost. | USD | Yes: not completed |
| `labor_cost_usd` | Labour cost. | USD | Yes: not completed |
| `deferred_items_count` | Small faults left for later (0 if not completed). | count | No |
| `is_aog` | 1 = "aircraft on ground": an unexpected fault grounded it. Only unscheduled repairs. | flag | No |
| `next_due_date` | Next check due: 90 days after an A-check, 240 after a B-check. | date | Yes: not an A- or B-check |
| `status` | `completed`, `in_progress` or `planned` (starts after today). | code | No |

### 4.11 fuel_uplifts

**One row:** the fuel loaded before one completed flight. **Rows:** 2,092 (one per completed flight). **Key:** `fuel_uplift_id`. **Links:** `flight_id` → flights, `airport_id` → airports (departure airport).

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `fuel_uplift_id` | Fuelling number. | ID | No |
| `fuel_ticket_number` | Receipt, e.g. FT-FRA-000123. Unique. | text | No |
| `flight_id` | Flight → flights (completed only; one per flight). | ID | No |
| `airport_id` | Departure airport → airports. | ID | No |
| `supplier_name` | Fuel company (fictional; 2 per airport). | text | No |
| `fuel_type` | `Jet A` (USA) or `Jet A-1` (elsewhere). | code | No |
| `delivery_method` | `hydrant` (pipe under the stand) or `truck`. | code | No |
| `uplift_time` | 35–100 min before actual departure. | UTC time | No |
| `quantity_kg` | Fuel loaded, by weight. | kg | No |
| `quantity_litres` | Fuel loaded, by volume. | litres | No |
| `density_kg_per_l` | Weight of one litre (0.785–0.825). | kg/litre | No |
| `price_usd_per_litre` | Price; depends on region and month. | USD/litre | No |
| `total_cost_usd` | Litres × price. | USD | No |
| `saf_blend_pct` | Share of sustainable aviation fuel. At least 2% in Germany and the Netherlands; 0 for about 90% of uplifts elsewhere. | percent | No |
| `fuel_burned_kg` | Fuel used; never more than loaded. | kg | No |
| `co2_emissions_kg` | 3.16 × fuel burned. | kg | No |

### 4.12 shipments

**One row:** the goods a customer sends under one air waybill. **Rows:** 3,110 (2,897 delivered, 12 in transit, 91 booked, 110 cancelled). **Key:** `shipment_id`. **Links:** `customer_id` → customers; `origin_airport_id`, `destination_airport_id` → airports. **Used by:** `flight_cargo`, `invoices`, `customs_declarations`, `tracking_events`. Its flights come through `flight_cargo`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `shipment_id` | Shipment number, in order of booking date. | ID | No |
| `awb_number` | Air waybill: airline prefix (901 MC, 902 BF, 903 SK, 904 EA, 905 GC), "-", 7-digit serial and a check digit (serial mod 7), e.g. 901-10053470. Prefix = airline of the first flight. Unique. | text | No |
| `customer_id` | Customer who booked and pays → customers. | ID | No |
| `customer_reference` | Customer's order number, e.g. PO-12345. | text | Yes: none given (968) |
| `consignee_name` | Receiving company (fictional). | text | No |
| `origin_airport_id`, `destination_airport_id` | Start and final destination (never the same). | ID | No |
| `booking_date` | Booking date, 1–11 days before the first flight. | date | No |
| `requested_delivery_date` | Customer's wished date: booking + 2–4 days (express), 4–7 (standard) or 6–12 (economy). Only a wish: over half of handovers are later. | date | No |
| `service_level` | `express`, `standard` or `economy`. | code | No |
| `commodity_category` | `electronics`, `pharmaceuticals`, `perishables` (food, flowers), `automotive_parts`, `apparel` (clothing), `machinery` or `documents`. | code | No |
| `pieces` | Number of packages. | count | No |
| `total_weight_kg` | Real weight. | kg | No |
| `total_volume_m3` | Volume. | m³ | No |
| `chargeable_weight_kg` | Weight used for pricing: the larger of real weight and volume × 167. | kg | No |
| `declared_value_usd` | Value stated by the customer (for customs and insurance). | USD | No |
| `is_dangerous_goods` | 1 = dangerous goods. Only electronics, automotive parts, machinery and pharmaceuticals. | flag | No |
| `dg_class` | UN class: 2.2 (non-flammable gas), 3 (flammable liquid), 8 (corrosive) or 9 (other, e.g. lithium batteries). | code | Yes: not dangerous |
| `is_temperature_controlled` | 1 = must stay in a temperature range. Exactly the pharmaceuticals and perishables. | flag | No |
| `min_temperature_c`, `max_temperature_c` | Allowed range: 2–8 or 15–25 (pharmaceuticals); 0–4, −25 to −18 or 10–14 (perishables). | °C | Yes: not controlled |
| `status` | `booked`, `in_transit`, `delivered` or `cancelled` (see 5.2). `delivered` means landed, not handed over. | code | No |

### 4.13 flight_cargo

**One row:** one leg: which flight carries which shipment. **Rows:** 3,818 (3,000 first legs, 818 second legs). **Key:** `flight_cargo_id`. **Links:** `shipment_id` → shipments, `flight_id` → flights. **Used by:** `incidents`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `flight_cargo_id` | Leg number. | ID | No |
| `shipment_id` | Shipment → shipments. | ID | No |
| `flight_id` | Flight → flights. Never a cancelled flight. | ID | No |
| `leg_number` | 1 = first flight, 2 = connecting flight. | number | No |
| `uld_type` | How it is loaded. PMC, PAG = main-deck pallets; AKE = lower-hold container; RKN = cooled lower-hold container; BULK = loose (documents and shipments under 60 kg). | code | No |
| `uld_number` | Pallet or container ID: type + 5 digits + airline code, e.g. PMC12345EA. | text | Yes: BULK |
| `deck` | `main` (PMC, PAG) or `lower` (AKE, RKN, BULK). | code | No |
| `position_code` | MD01… (main deck), LD01… (lower deck) or BLK (loose). | text | No |
| `load_sequence` | Loading order on the flight. Unique per flight. | number | No |
| `seal_number` | Security seal, e.g. SL123456. Only electronics and pharmaceuticals worth over 50,000 USD in a ULD. | text | Yes: no seal |
| `loaded_at` | Loading time, 45–240 min before actual departure. | UTC time | Yes: not flown yet |
| `leg_status` | `flown` or `planned`. | code | No |

### 4.14 invoices

**One row:** the bill for one shipment. **Rows:** 2,909 (one per shipment that has departed: in transit or delivered). **Key:** `invoice_id`. **Links:** `shipment_id` → shipments (one invoice each); the customer comes through the shipment. **Used by:** `payments`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `invoice_id` | Invoice number. | ID | No |
| `invoice_number` | e.g. INV-2025-000001. Unique. | text | No |
| `shipment_id` | Shipment billed → shipments. Unique. | ID | No |
| `issued_date` | The day the first flight actually departed. | date | No |
| `due_date` | Issued date + payment terms. | date | No |
| `payment_terms_days` | 15, 30, 45 or 60, copied from the customer. | days | No |
| `freight_charge_usd` | Basic price (what is left after the other parts). | USD | No |
| `fuel_surcharge_usd` | Fuel charge, 12–18% of the total. | USD | No |
| `security_fee_usd` | Screening fee, by weight. | USD | No |
| `handling_fee_usd` | Handling fee, by weight. | USD | No |
| `dg_surcharge_usd` | Dangerous-goods charge (8% of the total); 0 for other goods. | USD | No |
| `discount_usd` | 2–6% for gold and platinum customers; 0 for others. | USD | No |
| `amount_usd` | Total = freight + fuel + security + handling + DG − discount. At least 75 USD. | USD | No |
| `sent_via` | `email`, `portal` or `edi` (computer-to-computer). | code | No |
| `status` | `unpaid`, `partially_paid` or `paid` (see 5.5). | code | No |

### 4.15 payments

**One row:** one payment for an invoice. **Rows:** 2,544. **Key:** `payment_id`. **Links:** `invoice_id` → invoices, `customer_id` → customers. An invoice has 0, 1 or 2 payments.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `payment_id` | Payment number. | ID | No |
| `payment_reference` | PAY- + date + number, e.g. PAY-20250120-00083. Unique. | text | No |
| `invoice_id` | Invoice paid → invoices. | ID | No |
| `customer_id` | Payer → customers. Always the invoiced shipment's customer. | ID | No |
| `payment_date` | Date received (on or after the invoice date, never after today). | date | No |
| `amount_usd` | Amount in USD. | USD | No |
| `original_currency` | USD, EUR, GBP, CAD, CNY, TRY, AED, KRW, JPY, SGD, BRL or INR. Card payments are always USD. | code | No |
| `original_amount` | Amount in that currency. | currency | No |
| `exchange_rate_to_usd` | USD per 1 unit of that currency (1 for USD). | USD/unit | No |
| `method` | `wire_transfer`, `ach` (low-cost bank transfer) or `credit_card`. | code | No |
| `bank_charges_usd` | Wire 15–45 USD, ACH 0–1.50 USD, card 2.5% of the amount. | USD | No |
| `is_reconciled` | 1 = matched in the accounts. Most payments from the last 5 days are not yet. | flag | No |

### 4.16 incidents

**One row:** one problem with a shipment on a flown leg. **Rows:** 160. **Key:** `incident_id`. **Links:** `flight_cargo_id` → flight_cargo, `airport_id` → airports, `warehouse_id` → warehouses. **Used by:** `insurance_claims`.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `incident_id` | Incident number. | ID | No |
| `flight_cargo_id` | Leg where it happened → flight_cargo. Always a flown leg. | ID | No |
| `airport_id` | Where reported = the leg's destination → airports. | ID | No |
| `warehouse_id` | Warehouse involved, at that airport → warehouses. | ID | Yes: none (51) |
| `incident_type` | `damage`, `delay`, `missing_documents`, `temperature_excursion` (too warm or too cold; only pharmaceuticals and perishables) or `loss`. | code | No |
| `severity` | `low`, `medium` or `high`. | code | No |
| `root_cause` | `handling`, `packaging`, `weather`, `documentation`, `equipment` or `unknown` (depends on type, see 5.6). | code | No |
| `reported_by` | `ground_handler`, `crew`, `customer` or `customs`. | code | No |
| `reported_at` | Time reported (never after today). | UTC time | No |
| `pieces_affected` | Packages affected. | count | Yes: delays and missing documents |
| `delay_minutes` | Delay caused (about 2 hours to 2 days). | minutes | Yes: not a delay |
| `claim_amount_usd` | Money asked for: damage 5–60% of declared value, loss 100%, temperature excursion 10–80%. | USD | Yes: nothing claimed (82) |
| `corrective_action` | `repacked`, `rerouted`, `compensated`, `documents_supplied` or `no_action`. | code | Yes: not resolved |
| `resolved` | 1 = closed. Only incidents reported more than 14 days before today can be closed. | flag | No |
| `resolved_at` | Time closed. | UTC time | Yes: not resolved |

### 4.17 insurance_claims

**One row:** one insurance claim for an incident. **Rows:** 78 (one per incident with a claim amount). **Key:** `claim_id`. **Links:** `incident_id` → incidents (at most one claim each), `customer_id` → customers (shipment owner).

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `claim_id` | Claim number. | ID | No |
| `claim_number` | e.g. CLM-2025-00001. Unique. | text | No |
| `incident_id` | Incident → incidents. Unique. | ID | No |
| `customer_id` | Claimant = shipment owner → customers. | ID | No |
| `policy_number` | Customer's policy, e.g. POL-0001-ATL (one per customer). | text | No |
| `insurer_name` | Insurer (fictional; 3). | text | No |
| `coverage_type` | `all_risk` (almost any cause) or `named_perils` (listed causes only; rejected more often). | code | No |
| `filed_date` | Filed 1–10 days after the incident. | date | No |
| `claimed_amount_usd` | = the incident's claim amount. | USD | No |
| `deductible_usd` | Part the customer always pays: 500, 1,000 or 2,500. | USD | No |
| `approved_amount_usd` | (claimed − deductible) × 70–100%. 0 when the claim is below the deductible (7 claims). | USD | Yes: not decided, or rejected |
| `status` | `filed`, `under_review`, `approved`, `rejected` or `paid` (see 5.6). | code | No |
| `decision_date` | Insurer's decision. | date | Yes: no decision yet |
| `rejection_reason` | `inadequate_packaging`, `late_notification`, `excluded_cause` or `insufficient_documentation`. | code | Yes: not rejected |
| `settlement_date` | Date paid out. | date | Yes: not paid |
| `adjuster_name` | Insurance employee (fictional). | text | No |

### 4.18 customs_declarations

**One row:** one export or import declaration for one shipment. **Rows:** 4,181 (2,102 exports, 2,079 imports). **Key:** `declaration_id`. **Links:** `shipment_id` → shipments (at most one export and one import each), `warehouse_id` → warehouses (the bonded warehouse used).

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `declaration_id` | Declaration number. | ID | No |
| `declaration_number` | EX- or IM- + airport + number, e.g. EX-FRA-000123. Unique. | text | No |
| `shipment_id` | Shipment → shipments. | ID | No |
| `warehouse_id` | Bonded warehouse: at the origin for exports, at the destination for imports. | ID | No |
| `declaration_type` | `export` or `import`. | code | No |
| `customs_country` | Country of that airport. | text | No |
| `hs_code` | 6-digit product code used by customs (list below). | text | No |
| `goods_description` | Text for the HS code. | text | No |
| `customs_value_usd` | = declared value. | USD | No |
| `duty_rate_pct` | Import duty rate (see 5.4). 0 for exports. | percent | No |
| `duty_amount_usd` | Value × rate ÷ 100. 0 for exports. | USD | No |
| `vat_amount_usd` | Import VAT = (value + duty) × VAT rate. 0 for exports. | USD | No |
| `broker_name` | Customs broker (fictional). | text | No |
| `inspection_required` | 1 = goods were physically checked (about 7% of exports, 11% of imports). | flag | No |
| `inspection_result` | `passed` or `discrepancy`. | code | Yes: not inspected |
| `submitted_at` | Time lodged. | UTC time | No |
| `cleared_at` | Time released. | UTC time | Yes: pending or held |
| `status` | `pending`, `cleared` or `held` (see 5.4). | code | No |

**HS codes used**

| Goods | HS codes |
|---|---|
| electronics | 847130 portable computers, 851762 network equipment, 854231 integrated circuits |
| pharmaceuticals | 300490 packaged medicaments, 300215 immunological products |
| perishables | 030214 fresh salmon, 060311 fresh cut roses, 080510 fresh oranges |
| automotive_parts | 870899 motor vehicle parts, 840991 engine parts |
| apparel | 610910 cotton t-shirts, 620342 cotton trousers |
| machinery | 842959 excavating machinery, 848180 industrial valves |
| documents | 490199 printed documents |

### 4.19 tracking_events

**One row:** one status scan of a shipment. **Rows:** 22,104. **Key:** `event_id`. **Links:** `shipment_id` → shipments, `flight_id` → flights, `airport_id` → airports, `warehouse_id` → warehouses.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `event_id` | Scan number. | ID | No |
| `shipment_id` | Shipment → shipments. | ID | No |
| `flight_id` | Flight departed or arrived on → flights. | ID | Yes: not DEP or ARR |
| `airport_id` | Where the scan happened → airports. | ID | No |
| `warehouse_id` | Warehouse of the scan → warehouses. | ID | Yes: not RCS, RCF, NFD or DLV |
| `event_code` | What happened (list below). | code | No |
| `event_time` | Scan time, never after today. DEP and ARR use the flight's actual times. | UTC time | No |
| `pieces` | Packages scanned (always the shipment's pieces). | count | No |
| `weight_kg` | Scale weight: within about 2% of the booked weight (1% plus rounding to 0.1 kg). | kg | Yes: not RCS |
| `temperature_c` | Probe reading; only temperature-controlled shipments, on RCS, ARR, RCF and DLV scans. | °C | Yes: no reading |
| `recorded_by` | `system`, `ground_handler` (hand scanner) or `customer_portal` (customer online). | code | No |
| `scanner_id` | Hand scanner, e.g. SCN-FRA-123. | text | Yes: not a ground_handler scan |

**Event codes**

| Code | Meaning | Where | Recorded by | Rows |
|---|---|---|---|---:|
| BKD | Booked | origin airport | customer_portal or system | 3,110 |
| RCS | Received from shipper and weighed | origin warehouse | ground_handler | 2,935 |
| DEP | Departed on a flight (one per flown leg) | departure airport | system | 3,688 |
| ARR | Arrived on a flight (one per flown leg) | arrival airport | system | 3,688 |
| RCF | Received from the flight | destination warehouse | ground_handler | 2,897 |
| NFD | Receiver notified | destination warehouse | ground_handler | 2,838 |
| DLV | Handed over to the receiver | destination warehouse | ground_handler | 2,838 |
| CAN | Booking cancelled | origin airport | customer_portal or system | 110 |

### 4.20 benchmark_meta

**One row:** one dataset setting. **Rows:** 5. **Key:** `meta_key`. Not linked to other tables.

| Column | Meaning | Unit / type | Empty? |
|---|---|---|---|
| `meta_key` | `as_of_timestamp`, `generator_seed`, `engine`, `note` or `schema_version`. | text | No |
| `meta_value` | 2025-12-20 00:00:00 ("today"), 42 (random seed), SQLite 3.25+, a note saying all names are fictional (true for companies and people; airport and aircraft model names are real), and "2 (20 tables, 300 columns)". | text | No |

## 5. Business rules

The validation scripts check these rules. In the committed report, all checks pass.

### 5.1 Flights

- **Flight chain:** each flight leaves from where the aircraft's previous non-cancelled flight landed. The first flight leaves from the home airport. An aircraft is never on two flights at once. No flight is longer than the model's range.
- **Flight time:** planned time = distance ÷ 780 km/h + 50 minutes (all models). Actual time is 20 minutes shorter to 30 minutes longer.
- **Departure delays** (2,092 completed flights):
  - 1,455 (69.6%) left between 5 minutes early and 15 minutes late.
  - 537 (25.7%) left 21 minutes to 4 hours late.
  - 100 (4.8%) left 4 to 8 hours late.
  - Every flight more than 15 minutes late has a delay code (637 flights).
- **Flight numbers** start with the operating airline's code.
- **Weather cancellations** always had snow, fog or a thunderstorm.

| Status | Meaning | Flights | What is filled |
|---|---|---:|---|
| completed | Flown, landed before today | 2,092 | actual times, take-off weight, weather, one fuel uplift, crew; its cargo legs are flown |
| cancelled | Did not fly (about 4% of past flights) | 92 | cancellation reason, weather; no actual times, crew, cargo or fuel |
| scheduled | Departs after today | 68 | rostered crew, maybe planned cargo; no actual times, weather or fuel |

No flight is in the air at "today".

### 5.2 Shipments and their legs

- 110 of the 3,110 shipments were cancelled before flying and have no legs. The other 3,000 have flights: 2,182 one flight, 818 two. That is 3,818 legs on 1,748 of the 2,252 flights.
- Each leg carries the whole shipment. A shipment is never split.
- Cargo goes only on non-cancelled flights. No leg departs before the booking date.
- Shipments on one flight never exceed the model's weight or volume. Main-deck pallets never exceed the main-deck positions.

| Status | Meaning | Rule | Shipments |
|---|---|---|---:|
| cancelled | Cancelled, never flew | no legs | 110 |
| booked | Waiting for its first flight | legs, none flown | 91 |
| in_transit | Between its two flights | some legs flown | 12 |
| delivered | Landed at the final destination | all legs flown | 2,897 |

**"Delivered" does not mean handed over.** It only means the last flight landed. Handover is the DLV scan. It comes after RCF (received at the warehouse), import release (if needed) and NFD (receiver notified). 59 delivered shipments have no DLV, because import customs is holding them.

### 5.3 Tracking events

- **Order:** BKD → RCS → DEP → ARR (a second DEP → ARR for a connection) → RCF → NFD → DLV. A cancelled shipment has only BKD → CAN.
- **Nothing after today:** each chain stops where the shipment is today. 65 booked shipments have only BKD. An in-transit shipment stops after its first ARR. A held import stops at RCF.
- **Flight scans:** DEP and ARR use the flight's actual times and airports, only for flown legs.
- **Handover:** NFD and DLV come only after a cleared import (when needed).
- **Temperature:** only temperature-controlled shipments have readings. Out-of-range readings appear only on ARR scans of legs with a temperature-excursion incident (5 readings).

### 5.4 Customs

- **When customs is needed:** only when origin and destination are in different customs areas. Germany and the Netherlands are one area (EU). Every other country is its own area; Hong Kong and China are separate. Of the 3,000 shipments with flights, 2,155 cross a border and 845 do not (631 inside the US, 143 inside Germany, 71 between Germany and the Netherlands).
- **Export:** lodged at a bonded warehouse at the origin, 8–48 hours before leg 1's actual departure (scheduled departure if it has not flown yet). If leg 1 has flown, the export was cleared at least 45 minutes before departure. 53 booked cross-border shipments have no export declaration yet. 2 exports are still pending.
- **Import:** lodged at a bonded warehouse at the destination, 15–60 minutes after the last landing. Only delivered shipments have one. About 11% are inspected; about a quarter of those find a discrepancy, and the goods are held (59 shipments).

| Status | Meaning | Rows |
|---|---|---:|
| pending | Lodged, no decision yet (only exports here) | 2 |
| cleared | Released (`cleared_at` filled) | 4,120 |
| held | Stopped after a discrepancy (only imports here) | 59 |

- **Money:** customs value = declared value; duty = value × rate ÷ 100; VAT = (value + duty) × VAT rate. Exports have no duty or VAT.
- **VAT rates:** Germany 19%, Netherlands 21%, Turkey 20%, China 13%, South Korea 10%, Japan 10%, Singapore 9%, UAE 5%. US, Qatar, Hong Kong: 0.
- **Duty rates:** pharmaceuticals and documents 0; electronics 0–2.5%; machinery 1.5–4%; automotive parts 2.5–4.5%; perishables 4–12%; apparel 8–16%. Always 0 in Hong Kong and Singapore. A flat 5% in the UAE and Qatar, except duty-free goods.

### 5.5 Invoices and payments

- A shipment gets one invoice once its first flight departs (in_transit or delivered). Booked and cancelled shipments have none.
- Invoice date = the day leg 1 actually departed. Due date = invoice date + payment terms.

| Status | Meaning | Invoices |
|---|---|---:|
| unpaid | No payment yet | 828 |
| partially_paid | Part received | 212 |
| paid | Fully paid | 1,869 |

- 1,618 invoices were paid in one payment and 463 in two. Payments never exceed the invoice amount.
- A payment's customer is always the invoiced shipment's customer.

### 5.6 Incidents and insurance claims

- Incidents happen only on flown legs (about 4% of them) and are reported at the leg's destination.

| Type | Incidents | Root causes | Money claimed? |
|---|---:|---|---|
| damage | 63 | handling, packaging | always: 5–60% of declared value |
| delay | 40 | weather, equipment, handling | never |
| missing_documents | 41 | documentation | never |
| temperature_excursion | 5 | equipment, handling | 4 of 5: 10–80% of value |
| loss | 11 | handling, unknown | always: 100% of declared value |

- **Closing:** only incidents reported more than 14 days before today can be resolved; about 70% of those are. 109 resolved, 51 open.
- **Claims:** every incident with a claim amount has one claim (78), filed 1–10 days later. Claimed amount = incident claim amount, never above the declared value.
- **Claim status** depends on days since filing (up to today):

| Status | Rule | Claims |
|---|---|---:|
| filed | under 7 days | 0 (allowed, none in data) |
| under_review | 7–39 days | 3 |
| rejected | 40+ days, rejected (30% chance with named-perils, 12% with all-risk) | 5 |
| approved | 40+ days, accepted, not paid yet | 3 |
| paid | accepted and paid 5–30 days after the decision | 67 |

- **Dates:** filed ≤ decision ≤ settlement ≤ today.

### 5.7 Crew

- Every non-cancelled flight has exactly 1 captain and 1 first officer; one of them is the pilot flying. Flights planned over 9 hours also have a relief pilot (456 flights). About 40% of flights carry a loadmaster.
- Crew fly only their own airline's aircraft. Pilots fly only their rated model, only while their licence is valid. Nobody has two duties at once. Rest between duties is at least 12 hours.
- **Never rostered (21):** the 17 inactive crew members and the 4 pilots of Gulf Crescent's grounded A330-200F fleet.

### 5.8 Customers

- **Loyalty tier:** customers are ranked by non-cancelled shipments. Top 10% platinum (7), next 20% gold (12), next 30% silver (19), rest bronze (25).
- **Discounts:** gold and platinum get 2–6% on every invoice. Bronze and silver get none.

### 5.9 How the numbers add up

**Weights**
- Chargeable weight = larger of `total_weight_kg` and `total_volume_m3` × 167, rounded to 0.1 kg. Volume wins for 1,358 shipments (44%).
- On every flight: total shipment weight ≤ `max_payload_kg`, total volume ≤ `max_volume_m3`.
- Take-off weight = empty weight + all cargo on board + fuel loaded (within 1 kg). Never above `max_takeoff_weight_kg`.

**Fuel**
- `quantity_kg` = `quantity_litres` × `density_kg_per_l` (within 1 kg).
- `total_cost_usd` = `quantity_litres` × `price_usd_per_litre` (within 0.01 USD).
- `co2_emissions_kg` = 3.16 × `fuel_burned_kg`.
- Fuel burned ≤ fuel loaded ≤ tank capacity. Fuel loaded = trip fuel (hours × burn per hour) + 5% + 45 minutes reserve, capped by tank size and MTOW.

**Invoices**
- `amount_usd` = freight + fuel + security + handling + DG − discount (within 0.01 USD).
- The total comes first: real weight × 2.80 USD/kg × service factor × goods factor × random 0.9–1.1, at least 75 USD. Service: express 1.6, standard 1.0, economy 0.65. Goods: documents 2.0, pharmaceuticals 1.5, perishables 1.2, electronics 1.1, automotive parts and apparel 0.9, machinery 0.8. Price uses real weight, not chargeable weight.
- Then it is split: fuel 12–18%; security 0.11 USD/kg (min 10 USD) and handling 0.07 USD/kg (min 20 USD), each at most 12%; DG 8%; discount 2–6%. Freight is the rest.

**Payments**
- `original_amount` × `exchange_rate_to_usd` = `amount_usd` (within 0.05 USD).
- Payments for one invoice add up to at most its amount.

**Customs and claims**
- Duty = value × rate ÷ 100. VAT = (value + duty) × VAT rate.
- Approved = (claimed − deductible) × 70–100%, never below 0. Approved ≤ claimed ≤ declared value.

## 6. Deliberate edge cases

Built in on purpose, so questions can test tricky SQL (missing matches, duplicates, empty values).

| Edge case | Details |
|---|---|
| Customers who never ship | 3: Tidewater Textiles, Ironbridge Pharma, Sterling Pharma (no shipments, invoices or payments) |
| One name in two countries | "Orchid Motors": customer 2 (United Kingdom) and 8 (Canada) |
| Aircraft that never fly | 2: A6-786J (in maintenance), N723X (retired) |
| Delivered but held by customs | 59: landed, import held, no NFD or DLV |
| Expired pilot licences | 10 expired in 2025; not rostered after expiry |
| Crew never rostered | 21: 17 inactive + 4 pilots of the grounded A330-200F fleet |
| Cancelled shipments | 110: no legs, no invoice, only BKD and CAN |
| Connections | 818 shipments fly on two flights |
| Flights with no cargo | 402 completed and 10 scheduled |
| Long delays | 100 flights over 4 hours late (up to 8 hours) |
| Invoices paid in two parts | 463 |
| Partly paid and unpaid invoices | 212 partly paid, 828 unpaid |
| Late payments | 1,112 payments after the due date |
| Airports without a cold-chain warehouse | 5: LAX, MIA, NRT, PVG, SIN |
| Shipments needing no customs | 845 domestic or Germany ↔ Netherlands |
| Cross-border, no declaration yet | 53 booked shipments (export not lodged before today) |
| Incidents without a claim | 82: all delays, all missing documents, 1 temperature excursion |
| Root causes with no claim | documentation and weather |
| Rejected claims | 5 (no approved amount) |
| Claims paid 0 USD | 7 (claim below the deductible) |
| Allowed values never used | Claim status `filed`. Customs `pending` only for exports, `held` only for imports. |
| Handovers after the requested date | 1,522 of 2,838 |

## 7. Simplifications and limitations

- **One unit, at most two flights:** a shipment is never split and flies on at most two flights.
- **One speed:** all flight times use 780 km/h + 50 minutes.
- **Crew location:** not tracked between duties. Only airline, rating, licence and rest are checked.
- **Today:** no flight is in the air at "today". Future flights are scheduled. Cargo goes only on non-cancelled flights.
- **Fuel:** a simple model. Fuel loaded counts as all fuel on board. Prices and exchange rates follow a smooth monthly pattern.
- **Prices and limits:** prices use real weight. Credit limits are not enforced. Requested delivery dates are not planned for.
- **Fixed totals:** aircraft hours and cycles, and crew hours, are fixed starting values; 2025 flights do not update them.
- **Illustrative figures:** duty and VAT rates are not real tariffs. Airport and aircraft figures are approximate.
- **Fictional names and numbers:** companies, people, registrations, flight numbers and addresses.
- **Stored statuses:** shipment, invoice, claim and customs statuses are stored, but always agree with the underlying rows.
- **Dates as text:** other database engines need different date functions.

## 8. The questions

### 8.1 Size

- **120 base questions:** 40 easy, 40 moderate, 40 hard.
- **4 styles each:** 480 questions (160 per level).
- **One answer per base question:** the four styles ask the same thing and share one correct ("gold") SQL query. So style differences show the effect of wording alone.

### 8.2 Difficulty levels

| Level | What the SQL needs |
|---|---|
| Easy | One table with a filter, count, sum, average, maximum or simple grouping |
| Moderate | Joins of 2–4 tables, GROUP BY … HAVING, missing matches (NOT EXISTS, LEFT JOIN), date differences, percentages, top-N lists |
| Hard | Several steps (CTEs), rankings and running totals (window functions: ROW_NUMBER, DENSE_RANK, NTILE, LAG), "for every" questions, self-joins, cumulative shares, joins that repeat rows if done carelessly |

**How big the gold queries are:** how many tables each gold query reads (each extra table needs a join), and its length.

| Level | 1 table | 2 | 3 | 4 | 5 | 6 | Avg tables | Avg length |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Easy | 40 | – | – | – | – | – | 1.0 | 11 words |
| Moderate | 13 | 19 | 6 | 2 | – | – | 1.9 | 28 words |
| Hard | 8 | 9 | 14 | 5 | 3 | 1 | 2.7 | 56 words |

- **Easy:** one table, no join or subquery; 3 of 40 use GROUP BY.
- **Moderate:** 27 of 40 read two or more tables. 37 use GROUP BY, 5 HAVING, 5 date arithmetic, 2 subqueries, 2 top-N (LIMIT).
- **Hard:** 32 of 40 read two or more tables (up to six). 39 use GROUP BY, 18 CTEs, 13 date arithmetic (`julianday`/`date`; 4 more group by month with `substr`), 11 window functions, 10 HAVING, 8 top-N, 6 subqueries. Table count is not the only difficulty: 8 hard questions read one table but need running totals, rankings or several steps.

### 8.3 Styles

| Style | ID ending | Sounds like | Example (E14, longest flight) |
|---|---|---|---|
| Casual | -CAS | Everyday language, no table or column names | "What's the longest flight distance we have, in km?" |
| Schema aware | -SCH | Names tables and columns | "Return MAX(distance_km) from flights." |
| Business / executive | -BIZ | Management and KPI words | "What is the longest sector length in our flight programme, in kilometres?" |
| Vague | -VAG | Short and unclear; the answer spec says what is meant | "Longest flight?" |

### 8.4 One example per level, in all four styles

| Style | Easy (E01) | Moderate (M09) | Hard (H09) |
|---|---|---|---|
| Casual | How many of our airports are cargo hubs? | Which airports have 4 or more warehouses, and how many? | Which planes have landed at every single cargo hub airport? |
| Schema aware | Count the rows in airports where is_cargo_hub = 1. | Count warehouses per iata_code (join on airport_id) and keep airports with COUNT >= 4. | Return tail_number whose completed flights reached, as destination, every airports row with is_cargo_hub = 1. |
| Business | For the network overview, how many cargo hub stations do we operate through? | Which stations have a large warehouse footprint of at least four facilities? | Which airframes have full hub-network coverage on completed flights? |
| Vague | How many hubs are there? | Airports with lots of warehouses? | Planes that have been everywhere? |

### 8.5 What a question record contains

| Field | Meaning |
|---|---|
| `id` | e.g. E14-VAG (base E14, vague style) |
| `base_id` | Base question shared by the four styles, e.g. E14 |
| `difficulty` | easy, moderate or hard |
| `style` | casual, schema_aware, business_executive or vague |
| `concepts` | SQL skills tested, e.g. GROUP BY, HAVING, CTE |
| `question` | The question text |
| `question_template` | Same text; in schema-aware questions, names are placeholders like `[[airports.iata_code]]` |
| `answer_spec` | What a correct answer contains: columns, filters, rounding, order. E.g. M09: "Columns: iata_code, number of warehouses; only airports with at least 4 warehouses; ordered by iata_code." |
| `gold_sql` | The correct SQL |

### 8.6 How answers are checked

- **Matching results:** a model's SQL is correct when it returns the same rows as the gold query (`evaluation/evaluate.py`). Row and column order are ignored. Numbers match to the gold value's precision: 62.2 accepts 62.23, not 62.3.
- **No ties in top-N answers:** if the 5th and 6th items of a top-5 list were tied, either answer would be right, and a correct model query could be marked wrong. `validation/test_gold.py` runs each gold query that ends in LIMIT without the limit and checks the last kept row and the first cut row differ. All 10 such queries pass. In M04, the 5th route (DXB → IST) has 43 flights and the 6th (FRA → LEJ) has 42. When a spec names a tie-breaker, the gold SQL sorts by it too.

### 8.7 Reasoning hints

Every question has a reasoning hint (`hints/hints_normal.jsonl`, 480 hints). A hint walks through the solution: the question, the tables and columns used, the goal, six steps (source, joins, filters, grouping, ordering, traps) and the gold SQL.

**Never show a hint to a model while it answers that question.** The hint contains the answer. `evaluation/run_ollama.py` does not use hints: its prompt has only the schema and the question (plus the answer spec with `--with-spec`). If you train or prompt a model with hints, test it only on base questions whose hints it has not seen, because the four styles share one gold SQL.
