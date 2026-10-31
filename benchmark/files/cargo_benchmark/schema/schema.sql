-- Air Cargo Flights benchmark database -- NORMAL (human-readable) schema, SQLite 3.25+
-- 20 tables, 300 columns. This file is the single source of truth: the MIXED and CRYPTIC
-- variants (schema_mixed.sql, schema_cryptic.sql) are generated from it by scripts/build_variants.py.
-- Conventions: all timestamps are UTC text 'YYYY-MM-DD HH:MM:SS'; dates are 'YYYY-MM-DD'; money is USD.
PRAGMA foreign_keys = ON;

-- ============================================================ reference data
CREATE TABLE benchmark_meta (
    meta_key   TEXT PRIMARY KEY,
    meta_value TEXT NOT NULL
);

CREATE TABLE airports (
    airport_id              INTEGER PRIMARY KEY,
    iata_code               TEXT NOT NULL UNIQUE CHECK (length(iata_code) = 3),
    icao_code               TEXT NOT NULL UNIQUE CHECK (length(icao_code) = 4),
    name                    TEXT NOT NULL,
    city                    TEXT NOT NULL,
    country                 TEXT NOT NULL,
    region                  TEXT NOT NULL CHECK (region IN ('north_america', 'europe', 'middle_east', 'asia_pacific')),
    timezone                TEXT NOT NULL,                       -- IANA name, e.g. 'Europe/Berlin'
    latitude                REAL NOT NULL CHECK (latitude  BETWEEN  -90 AND  90),
    longitude               REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    elevation_m             INTEGER NOT NULL,
    runway_count            INTEGER NOT NULL CHECK (runway_count >= 1),
    longest_runway_m        INTEGER NOT NULL CHECK (longest_runway_m > 0),
    is_cargo_hub            INTEGER NOT NULL DEFAULT 0 CHECK (is_cargo_hub IN (0, 1)),
    annual_cargo_capacity_t INTEGER NOT NULL CHECK (annual_cargo_capacity_t > 0),
    has_24h_customs         INTEGER NOT NULL CHECK (has_24h_customs IN (0, 1)),
    night_curfew            INTEGER NOT NULL CHECK (night_curfew IN (0, 1))
);

CREATE TABLE airlines (
    airline_id          INTEGER PRIMARY KEY,
    iata_code           TEXT NOT NULL UNIQUE CHECK (length(iata_code) = 2),
    icao_code           TEXT NOT NULL UNIQUE CHECK (length(icao_code) = 3),
    name                TEXT NOT NULL UNIQUE,
    callsign            TEXT NOT NULL UNIQUE,
    country             TEXT NOT NULL,
    headquarters_city   TEXT NOT NULL,
    founded_year        INTEGER NOT NULL CHECK (founded_year BETWEEN 1900 AND 2025),
    home_hub_airport_id INTEGER NOT NULL REFERENCES airports(airport_id),
    alliance            TEXT CHECK (alliance IS NULL OR alliance IN ('CargoLink', 'SkyFreight Alliance')),
    is_cargo_only       INTEGER NOT NULL CHECK (is_cargo_only IN (0, 1)),
    aoc_number          TEXT NOT NULL UNIQUE,                    -- air operator certificate
    website             TEXT NOT NULL,
    contact_email       TEXT NOT NULL
);

CREATE TABLE aircraft_types (
    type_id                    INTEGER PRIMARY KEY,
    model                      TEXT NOT NULL UNIQUE,
    icao_type_designator       TEXT NOT NULL UNIQUE,
    manufacturer               TEXT NOT NULL,
    engine_count               INTEGER NOT NULL CHECK (engine_count IN (2, 4)),
    engine_model               TEXT NOT NULL,
    max_payload_kg             INTEGER NOT NULL CHECK (max_payload_kg > 0),
    max_volume_m3              REAL    NOT NULL CHECK (max_volume_m3 > 0),
    max_range_km               INTEGER NOT NULL CHECK (max_range_km > 0),
    cruise_speed_kmh           INTEGER NOT NULL CHECK (cruise_speed_kmh > 0),
    max_takeoff_weight_kg      INTEGER NOT NULL CHECK (max_takeoff_weight_kg > 0),
    operating_empty_weight_kg  INTEGER NOT NULL CHECK (operating_empty_weight_kg > 0),
    fuel_capacity_kg           INTEGER NOT NULL CHECK (fuel_capacity_kg > 0),
    fuel_burn_kg_per_hour      INTEGER NOT NULL CHECK (fuel_burn_kg_per_hour > 0),
    main_deck_positions        INTEGER NOT NULL CHECK (main_deck_positions > 0),
    wingspan_m                 REAL    NOT NULL CHECK (wingspan_m > 0),
    CHECK (operating_empty_weight_kg + max_payload_kg <= max_takeoff_weight_kg)
);

CREATE TABLE aircraft (
    aircraft_id           INTEGER PRIMARY KEY,
    tail_number           TEXT NOT NULL UNIQUE,
    serial_number         TEXT NOT NULL UNIQUE,                  -- manufacturer serial number (MSN)
    type_id               INTEGER NOT NULL REFERENCES aircraft_types(type_id),
    airline_id            INTEGER NOT NULL REFERENCES airlines(airline_id),
    home_airport_id       INTEGER NOT NULL REFERENCES airports(airport_id),
    registration_country  TEXT NOT NULL,
    year_manufactured     INTEGER NOT NULL CHECK (year_manufactured BETWEEN 1990 AND 2025),
    delivery_date         TEXT NOT NULL,
    ownership             TEXT NOT NULL CHECK (ownership IN ('owned', 'leased')),
    lessor_name           TEXT,
    lease_end_date        TEXT,
    total_flight_hours    INTEGER NOT NULL CHECK (total_flight_hours >= 0),
    total_cycles          INTEGER NOT NULL CHECK (total_cycles >= 0),
    last_heavy_check_date TEXT,
    status                TEXT NOT NULL CHECK (status IN ('active', 'maintenance', 'retired')),
    CHECK ((ownership = 'leased') = (lessor_name IS NOT NULL AND lease_end_date IS NOT NULL)),
    CHECK (CAST(substr(delivery_date, 1, 4) AS INTEGER) >= year_manufactured)
);

CREATE TABLE customers (
    customer_id        INTEGER PRIMARY KEY,
    account_code       TEXT NOT NULL UNIQUE,
    name               TEXT NOT NULL,
    customer_type      TEXT NOT NULL CHECK (customer_type IN ('shipper', 'freight_forwarder', 'retailer', 'manufacturer')),
    country            TEXT NOT NULL,
    city               TEXT NOT NULL,
    address_line       TEXT NOT NULL,
    postal_code        TEXT NOT NULL,
    contact_name       TEXT NOT NULL,
    contact_email      TEXT NOT NULL,
    contact_phone      TEXT NOT NULL,
    website            TEXT,
    sales_region       TEXT NOT NULL CHECK (sales_region IN ('north_america', 'south_america', 'europe', 'middle_east', 'asia_pacific')),
    credit_limit_usd   REAL NOT NULL CHECK (credit_limit_usd > 0),
    payment_terms_days INTEGER NOT NULL CHECK (payment_terms_days IN (15, 30, 45, 60)),
    is_known_shipper   INTEGER NOT NULL CHECK (is_known_shipper IN (0, 1)),   -- security-screened shipper status
    loyalty_tier       TEXT NOT NULL CHECK (loyalty_tier IN ('bronze', 'silver', 'gold', 'platinum')),
    created_date       TEXT NOT NULL,
    UNIQUE (name, country)          -- the same name may exist in different countries
);

CREATE TABLE warehouses (
    warehouse_id            INTEGER PRIMARY KEY,
    warehouse_code          TEXT NOT NULL UNIQUE,
    airport_id              INTEGER NOT NULL REFERENCES airports(airport_id),
    operator_name           TEXT NOT NULL,                       -- ground-handling company
    warehouse_type          TEXT NOT NULL CHECK (warehouse_type IN ('general', 'cold_chain', 'dangerous_goods', 'express')),
    floor_area_m2           INTEGER NOT NULL CHECK (floor_area_m2 > 0),
    capacity_tonnes         INTEGER NOT NULL CHECK (capacity_tonnes > 0),
    cold_room_count         INTEGER NOT NULL CHECK (cold_room_count >= 0),
    min_temperature_c       REAL,                                -- coldest room; NULL when no cold rooms
    dock_door_count         INTEGER NOT NULL CHECK (dock_door_count > 0),
    has_dg_area             INTEGER NOT NULL CHECK (has_dg_area IN (0, 1)),
    is_bonded               INTEGER NOT NULL CHECK (is_bonded IN (0, 1)),   -- customs-bonded
    security_level          TEXT NOT NULL CHECK (security_level IN ('standard', 'high')),
    operates_24h            INTEGER NOT NULL CHECK (operates_24h IN (0, 1)),
    opened_year             INTEGER NOT NULL CHECK (opened_year BETWEEN 1950 AND 2025),
    monthly_rent_usd        REAL NOT NULL CHECK (monthly_rent_usd > 0),
    CHECK ((cold_room_count = 0) = (min_temperature_c IS NULL)),
    CHECK (warehouse_type <> 'cold_chain' OR cold_room_count > 0),
    CHECK (warehouse_type <> 'dangerous_goods' OR has_dg_area = 1)
);

-- ============================================================ crew
CREATE TABLE crew_members (
    crew_member_id      INTEGER PRIMARY KEY,
    employee_number     TEXT NOT NULL UNIQUE,
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    email               TEXT NOT NULL UNIQUE,
    airline_id          INTEGER NOT NULL REFERENCES airlines(airline_id),
    base_airport_id     INTEGER NOT NULL REFERENCES airports(airport_id),
    crew_rank           TEXT NOT NULL CHECK (crew_rank IN ('captain', 'first_officer', 'loadmaster')),
    type_rating_id      INTEGER REFERENCES aircraft_types(type_id),   -- pilots only
    license_number      TEXT UNIQUE,                                  -- pilots only
    license_expiry_date TEXT,                                         -- pilots only
    medical_expiry_date TEXT,                                         -- pilots only
    hire_date           TEXT NOT NULL,
    seniority_number    INTEGER NOT NULL CHECK (seniority_number >= 1),
    total_flight_hours  INTEGER NOT NULL CHECK (total_flight_hours >= 0),
    is_active           INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    UNIQUE (airline_id, seniority_number),
    CHECK ((crew_rank = 'loadmaster') = (type_rating_id IS NULL)),
    CHECK ((crew_rank = 'loadmaster') = (license_number IS NULL AND license_expiry_date IS NULL AND medical_expiry_date IS NULL))
);

-- ============================================================ operations
CREATE TABLE flights (
    flight_id                  INTEGER PRIMARY KEY,
    flight_number              TEXT NOT NULL,          -- airline IATA code + 3 digits
    flight_type                TEXT NOT NULL CHECK (flight_type IN ('scheduled', 'charter')),
    aircraft_id                INTEGER NOT NULL REFERENCES aircraft(aircraft_id),
    origin_airport_id          INTEGER NOT NULL REFERENCES airports(airport_id),
    destination_airport_id     INTEGER NOT NULL REFERENCES airports(airport_id),
    scheduled_departure        TEXT NOT NULL,
    scheduled_arrival          TEXT NOT NULL,
    actual_departure           TEXT,
    actual_arrival             TEXT,
    departure_stand            TEXT NOT NULL,
    arrival_stand              TEXT NOT NULL,
    distance_km                INTEGER NOT NULL CHECK (distance_km > 0),
    planned_cruise_altitude_ft INTEGER NOT NULL CHECK (planned_cruise_altitude_ft BETWEEN 20000 AND 43000),
    takeoff_weight_kg          INTEGER,                -- completed flights only
    weather_at_departure       TEXT CHECK (weather_at_departure IS NULL OR weather_at_departure IN
                                   ('clear', 'cloudy', 'rain', 'snow', 'fog', 'thunderstorm')),   -- NULL for future flights
    delay_code                 TEXT,                   -- IATA delay code, completed flights departing > 15 min late
    cancellation_reason        TEXT CHECK (cancellation_reason IS NULL OR cancellation_reason IN
                                   ('weather', 'technical', 'crew', 'commercial', 'atc')),
    status                     TEXT NOT NULL CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    UNIQUE (flight_number, scheduled_departure),
    CHECK (origin_airport_id <> destination_airport_id),
    CHECK (scheduled_arrival > scheduled_departure),
    CHECK (
        (status = 'completed' AND actual_departure IS NOT NULL AND actual_arrival IS NOT NULL
                              AND actual_arrival > actual_departure)
     OR (status <> 'completed' AND actual_departure IS NULL AND actual_arrival IS NULL)
    ),
    CHECK ((status = 'completed') = (takeoff_weight_kg IS NOT NULL)),
    CHECK ((status = 'cancelled') = (cancellation_reason IS NOT NULL)),
    CHECK ((status = 'scheduled') = (weather_at_departure IS NULL)),
    CHECK (delay_code IS NULL OR status = 'completed')
);

CREATE TABLE crew_assignments (
    assignment_id          INTEGER PRIMARY KEY,
    flight_id              INTEGER NOT NULL REFERENCES flights(flight_id),
    crew_member_id         INTEGER NOT NULL REFERENCES crew_members(crew_member_id),
    duty_role              TEXT NOT NULL CHECK (duty_role IN ('captain', 'first_officer', 'relief_pilot', 'loadmaster')),
    is_pilot_flying        INTEGER NOT NULL CHECK (is_pilot_flying IN (0, 1)),
    report_time            TEXT NOT NULL,
    release_time           TEXT NOT NULL,
    block_minutes_credited INTEGER,                    -- completed flights only
    rest_minutes_before    INTEGER,                    -- since this crew member's previous release; NULL for first duty
    per_diem_usd           REAL NOT NULL CHECK (per_diem_usd >= 0),
    hotel_required         INTEGER NOT NULL CHECK (hotel_required IN (0, 1)),
    assignment_status      TEXT NOT NULL CHECK (assignment_status IN ('rostered', 'completed')),
    UNIQUE (flight_id, crew_member_id),
    CHECK (release_time > report_time),
    CHECK (is_pilot_flying = 0 OR duty_role IN ('captain', 'first_officer')),
    CHECK ((assignment_status = 'completed') = (block_minutes_credited IS NOT NULL))
);

CREATE TABLE maintenance_records (
    maintenance_id       INTEGER PRIMARY KEY,
    work_order_number    TEXT NOT NULL UNIQUE,
    aircraft_id          INTEGER NOT NULL REFERENCES aircraft(aircraft_id),
    airport_id           INTEGER NOT NULL REFERENCES airports(airport_id),
    check_type           TEXT NOT NULL CHECK (check_type IN ('line', 'A_check', 'B_check', 'C_check', 'unscheduled')),
    ata_chapter          INTEGER CHECK (ata_chapter IS NULL OR ata_chapter BETWEEN 5 AND 80),  -- system worked on (unscheduled)
    mro_provider         TEXT NOT NULL,
    start_time           TEXT NOT NULL,
    end_time             TEXT,                          -- NULL while in progress
    labor_hours          REAL,
    parts_cost_usd       REAL CHECK (parts_cost_usd IS NULL OR parts_cost_usd >= 0),
    labor_cost_usd       REAL CHECK (labor_cost_usd IS NULL OR labor_cost_usd >= 0),
    deferred_items_count INTEGER NOT NULL CHECK (deferred_items_count >= 0),
    is_aog               INTEGER NOT NULL CHECK (is_aog IN (0, 1)),        -- aircraft on ground (unplanned)
    next_due_date        TEXT,
    status               TEXT NOT NULL CHECK (status IN ('planned', 'in_progress', 'completed')),
    CHECK (end_time IS NULL OR end_time > start_time),
    CHECK ((status = 'in_progress') = (end_time IS NULL)),
    CHECK ((status = 'completed') = (labor_hours IS NOT NULL AND parts_cost_usd IS NOT NULL AND labor_cost_usd IS NOT NULL)),
    CHECK ((check_type = 'unscheduled') = (ata_chapter IS NOT NULL)),
    CHECK (is_aog = 0 OR check_type = 'unscheduled')
);

CREATE TABLE fuel_uplifts (
    fuel_uplift_id        INTEGER PRIMARY KEY,
    fuel_ticket_number    TEXT NOT NULL UNIQUE,
    flight_id             INTEGER NOT NULL UNIQUE REFERENCES flights(flight_id),   -- completed flights only
    airport_id            INTEGER NOT NULL REFERENCES airports(airport_id),
    supplier_name         TEXT NOT NULL,
    fuel_type             TEXT NOT NULL CHECK (fuel_type IN ('Jet A', 'Jet A-1')),
    delivery_method       TEXT NOT NULL CHECK (delivery_method IN ('hydrant', 'truck')),
    uplift_time           TEXT NOT NULL,
    quantity_kg           INTEGER NOT NULL CHECK (quantity_kg > 0),
    quantity_litres       INTEGER NOT NULL CHECK (quantity_litres > 0),
    density_kg_per_l      REAL NOT NULL CHECK (density_kg_per_l BETWEEN 0.775 AND 0.840),
    price_usd_per_litre   REAL NOT NULL CHECK (price_usd_per_litre > 0),
    total_cost_usd        REAL NOT NULL CHECK (total_cost_usd > 0),
    saf_blend_pct         REAL NOT NULL CHECK (saf_blend_pct BETWEEN 0 AND 50),       -- sustainable aviation fuel share
    fuel_burned_kg        INTEGER NOT NULL CHECK (fuel_burned_kg > 0),
    co2_emissions_kg      INTEGER NOT NULL CHECK (co2_emissions_kg > 0),
    CHECK (fuel_burned_kg <= quantity_kg)
);

-- ============================================================ commercial
CREATE TABLE shipments (
    shipment_id               INTEGER PRIMARY KEY,
    awb_number                TEXT NOT NULL UNIQUE,     -- air waybill 'PPP-NNNNNNNN'
    customer_id               INTEGER NOT NULL REFERENCES customers(customer_id),
    customer_reference        TEXT,
    consignee_name            TEXT NOT NULL,
    origin_airport_id         INTEGER NOT NULL REFERENCES airports(airport_id),
    destination_airport_id    INTEGER NOT NULL REFERENCES airports(airport_id),
    booking_date              TEXT NOT NULL,
    requested_delivery_date   TEXT NOT NULL,
    service_level             TEXT NOT NULL CHECK (service_level IN ('express', 'standard', 'economy')),
    commodity_category        TEXT NOT NULL CHECK (commodity_category IN
        ('electronics', 'pharmaceuticals', 'perishables', 'automotive_parts', 'apparel', 'machinery', 'documents')),
    pieces                    INTEGER NOT NULL CHECK (pieces > 0),
    total_weight_kg           REAL NOT NULL CHECK (total_weight_kg > 0),
    total_volume_m3           REAL NOT NULL CHECK (total_volume_m3 > 0),
    chargeable_weight_kg      REAL NOT NULL,            -- max(actual weight, volume * 167)
    declared_value_usd        REAL NOT NULL CHECK (declared_value_usd >= 0),
    is_dangerous_goods        INTEGER NOT NULL CHECK (is_dangerous_goods IN (0, 1)),
    dg_class                  TEXT CHECK (dg_class IS NULL OR dg_class IN ('2.2', '3', '8', '9')),
    is_temperature_controlled INTEGER NOT NULL CHECK (is_temperature_controlled IN (0, 1)),
    min_temperature_c         REAL,
    max_temperature_c         REAL,
    status                    TEXT NOT NULL CHECK (status IN ('booked', 'in_transit', 'delivered', 'cancelled')),
    CHECK (origin_airport_id <> destination_airport_id),
    CHECK (requested_delivery_date > booking_date),
    CHECK (chargeable_weight_kg >= total_weight_kg),
    CHECK ((is_dangerous_goods = 1) = (dg_class IS NOT NULL)),
    CHECK ((is_temperature_controlled = 1) = (min_temperature_c IS NOT NULL AND max_temperature_c IS NOT NULL)),
    CHECK (min_temperature_c IS NULL OR min_temperature_c < max_temperature_c)
);

-- A shipment travels on 1..n flights (connections). Each leg carries the whole shipment in one ULD.
CREATE TABLE flight_cargo (
    flight_cargo_id INTEGER PRIMARY KEY,
    shipment_id     INTEGER NOT NULL REFERENCES shipments(shipment_id),
    flight_id       INTEGER NOT NULL REFERENCES flights(flight_id),
    leg_number      INTEGER NOT NULL CHECK (leg_number >= 1),
    uld_type        TEXT NOT NULL CHECK (uld_type IN ('PMC', 'PAG', 'AKE', 'RKN', 'BULK')),   -- unit load device
    uld_number      TEXT,                                -- NULL for bulk-loaded cargo
    deck            TEXT NOT NULL CHECK (deck IN ('main', 'lower')),
    position_code   TEXT NOT NULL,
    load_sequence   INTEGER NOT NULL CHECK (load_sequence >= 1),
    seal_number     TEXT,                                -- security seal on high-value ULDs
    loaded_at       TEXT,                                -- flown legs only
    leg_status      TEXT NOT NULL CHECK (leg_status IN ('planned', 'flown')),
    UNIQUE (shipment_id, leg_number),
    UNIQUE (shipment_id, flight_id),
    UNIQUE (flight_id, load_sequence),
    CHECK ((uld_type = 'BULK') = (uld_number IS NULL)),
    CHECK ((uld_type IN ('PMC', 'PAG')) = (deck = 'main')),
    CHECK ((leg_status = 'flown') = (loaded_at IS NOT NULL))
);

CREATE TABLE invoices (
    invoice_id          INTEGER PRIMARY KEY,
    invoice_number      TEXT NOT NULL UNIQUE,
    shipment_id         INTEGER NOT NULL UNIQUE REFERENCES shipments(shipment_id),
    issued_date         TEXT NOT NULL,
    due_date            TEXT NOT NULL,
    payment_terms_days  INTEGER NOT NULL CHECK (payment_terms_days IN (15, 30, 45, 60)),
    freight_charge_usd  REAL NOT NULL CHECK (freight_charge_usd > 0),
    fuel_surcharge_usd  REAL NOT NULL CHECK (fuel_surcharge_usd >= 0),
    security_fee_usd    REAL NOT NULL CHECK (security_fee_usd >= 0),
    handling_fee_usd    REAL NOT NULL CHECK (handling_fee_usd >= 0),
    dg_surcharge_usd    REAL NOT NULL CHECK (dg_surcharge_usd >= 0),
    discount_usd        REAL NOT NULL CHECK (discount_usd >= 0),
    amount_usd          REAL NOT NULL CHECK (amount_usd > 0),   -- total due = charges + fees + surcharges - discount
    sent_via            TEXT NOT NULL CHECK (sent_via IN ('email', 'portal', 'edi')),
    status              TEXT NOT NULL CHECK (status IN ('unpaid', 'partially_paid', 'paid')),
    CHECK (due_date >= issued_date)
);

CREATE TABLE payments (
    payment_id           INTEGER PRIMARY KEY,
    payment_reference    TEXT NOT NULL UNIQUE,
    invoice_id           INTEGER NOT NULL REFERENCES invoices(invoice_id),
    customer_id          INTEGER NOT NULL REFERENCES customers(customer_id),
    payment_date         TEXT NOT NULL,
    amount_usd           REAL NOT NULL CHECK (amount_usd > 0),
    original_currency    TEXT NOT NULL CHECK (length(original_currency) = 3),
    original_amount      REAL NOT NULL CHECK (original_amount > 0),
    exchange_rate_to_usd REAL NOT NULL CHECK (exchange_rate_to_usd > 0),   -- USD per 1 unit of original currency
    method               TEXT NOT NULL CHECK (method IN ('wire_transfer', 'ach', 'credit_card')),
    bank_charges_usd     REAL NOT NULL CHECK (bank_charges_usd >= 0),
    is_reconciled        INTEGER NOT NULL CHECK (is_reconciled IN (0, 1)),
    CHECK (original_currency <> 'USD' OR exchange_rate_to_usd = 1)
);

CREATE TABLE incidents (
    incident_id       INTEGER PRIMARY KEY,
    flight_cargo_id   INTEGER NOT NULL REFERENCES flight_cargo(flight_cargo_id),
    airport_id        INTEGER NOT NULL REFERENCES airports(airport_id),         -- where it was reported
    warehouse_id      INTEGER REFERENCES warehouses(warehouse_id),              -- handling warehouse, if any
    incident_type     TEXT NOT NULL CHECK (incident_type IN
        ('damage', 'delay', 'missing_documents', 'temperature_excursion', 'loss')),
    severity          TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    root_cause        TEXT NOT NULL CHECK (root_cause IN ('handling', 'packaging', 'weather', 'documentation', 'equipment', 'unknown')),
    reported_by       TEXT NOT NULL CHECK (reported_by IN ('ground_handler', 'crew', 'customer', 'customs')),
    reported_at       TEXT NOT NULL,
    pieces_affected   INTEGER CHECK (pieces_affected IS NULL OR pieces_affected >= 1),
    delay_minutes     INTEGER CHECK (delay_minutes IS NULL OR delay_minutes > 0),
    claim_amount_usd  REAL CHECK (claim_amount_usd IS NULL OR claim_amount_usd >= 0),
    corrective_action TEXT CHECK (corrective_action IS NULL OR corrective_action IN
        ('repacked', 'rerouted', 'compensated', 'documents_supplied', 'no_action')),
    resolved          INTEGER NOT NULL CHECK (resolved IN (0, 1)),
    resolved_at       TEXT,
    CHECK ((resolved = 1) = (resolved_at IS NOT NULL)),
    CHECK ((resolved = 1) = (corrective_action IS NOT NULL)),
    CHECK (resolved_at IS NULL OR resolved_at > reported_at),
    CHECK ((incident_type = 'delay') = (delay_minutes IS NOT NULL))
);

CREATE TABLE insurance_claims (
    claim_id            INTEGER PRIMARY KEY,
    claim_number        TEXT NOT NULL UNIQUE,
    incident_id         INTEGER NOT NULL UNIQUE REFERENCES incidents(incident_id),
    customer_id         INTEGER NOT NULL REFERENCES customers(customer_id),
    policy_number       TEXT NOT NULL,
    insurer_name        TEXT NOT NULL,
    coverage_type       TEXT NOT NULL CHECK (coverage_type IN ('all_risk', 'named_perils')),
    filed_date          TEXT NOT NULL,
    claimed_amount_usd  REAL NOT NULL CHECK (claimed_amount_usd >= 0),
    deductible_usd      REAL NOT NULL CHECK (deductible_usd >= 0),
    approved_amount_usd REAL CHECK (approved_amount_usd IS NULL OR approved_amount_usd >= 0),
    status              TEXT NOT NULL CHECK (status IN ('filed', 'under_review', 'approved', 'rejected', 'paid')),
    decision_date       TEXT,
    rejection_reason    TEXT CHECK (rejection_reason IS NULL OR rejection_reason IN
        ('inadequate_packaging', 'late_notification', 'excluded_cause', 'insufficient_documentation')),
    settlement_date     TEXT,
    adjuster_name       TEXT NOT NULL,
    CHECK ((status IN ('approved', 'paid')) = (approved_amount_usd IS NOT NULL)),
    CHECK ((status IN ('approved', 'rejected', 'paid')) = (decision_date IS NOT NULL)),
    CHECK ((status = 'rejected') = (rejection_reason IS NOT NULL)),
    CHECK ((status = 'paid') = (settlement_date IS NOT NULL)),
    CHECK (approved_amount_usd IS NULL OR approved_amount_usd <= claimed_amount_usd)
);

-- ============================================================ border and tracking
CREATE TABLE customs_declarations (
    declaration_id      INTEGER PRIMARY KEY,
    declaration_number  TEXT NOT NULL UNIQUE,
    shipment_id         INTEGER NOT NULL REFERENCES shipments(shipment_id),
    warehouse_id        INTEGER NOT NULL REFERENCES warehouses(warehouse_id),    -- bonded warehouse where it is lodged
    declaration_type    TEXT NOT NULL CHECK (declaration_type IN ('export', 'import')),
    customs_country     TEXT NOT NULL,
    hs_code             TEXT NOT NULL CHECK (length(hs_code) = 6),               -- harmonized system tariff code
    goods_description   TEXT NOT NULL,
    customs_value_usd   REAL NOT NULL CHECK (customs_value_usd >= 0),
    duty_rate_pct       REAL NOT NULL CHECK (duty_rate_pct >= 0),
    duty_amount_usd     REAL NOT NULL CHECK (duty_amount_usd >= 0),
    vat_amount_usd      REAL NOT NULL CHECK (vat_amount_usd >= 0),
    broker_name         TEXT NOT NULL,
    inspection_required INTEGER NOT NULL CHECK (inspection_required IN (0, 1)),
    inspection_result   TEXT CHECK (inspection_result IS NULL OR inspection_result IN ('passed', 'discrepancy')),
    submitted_at        TEXT NOT NULL,
    cleared_at          TEXT,
    status              TEXT NOT NULL CHECK (status IN ('pending', 'cleared', 'held')),
    UNIQUE (shipment_id, declaration_type),
    CHECK ((status = 'cleared') = (cleared_at IS NOT NULL)),
    CHECK (cleared_at IS NULL OR cleared_at > submitted_at),
    CHECK (inspection_result IS NULL OR inspection_required = 1),
    CHECK (status <> 'held' OR inspection_result = 'discrepancy'),
    CHECK (declaration_type = 'import' OR (duty_amount_usd = 0 AND vat_amount_usd = 0))
);

CREATE TABLE tracking_events (
    event_id      INTEGER PRIMARY KEY,
    shipment_id   INTEGER NOT NULL REFERENCES shipments(shipment_id),
    flight_id     INTEGER REFERENCES flights(flight_id),             -- DEP / ARR events only
    airport_id    INTEGER NOT NULL REFERENCES airports(airport_id),
    warehouse_id  INTEGER REFERENCES warehouses(warehouse_id),       -- RCS / RCF / NFD / DLV events only
    event_code    TEXT NOT NULL CHECK (event_code IN ('BKD', 'RCS', 'DEP', 'ARR', 'RCF', 'NFD', 'DLV', 'CAN')),
    event_time    TEXT NOT NULL,
    pieces        INTEGER NOT NULL CHECK (pieces >= 0),
    weight_kg     REAL,                                              -- scale weight, RCS events only
    temperature_c REAL,                                              -- probe reading, temperature-controlled shipments only
    recorded_by   TEXT NOT NULL CHECK (recorded_by IN ('system', 'ground_handler', 'customer_portal')),
    scanner_id    TEXT,                                              -- handheld scanner, ground-handler events only
    CHECK ((event_code IN ('DEP', 'ARR')) = (flight_id IS NOT NULL)),
    CHECK ((event_code IN ('RCS', 'RCF', 'NFD', 'DLV')) = (warehouse_id IS NOT NULL)),
    CHECK ((recorded_by = 'ground_handler') = (scanner_id IS NOT NULL)),
    CHECK (weight_kg IS NULL OR event_code = 'RCS')
);

-- ============================================================ indexes justified by the intended query patterns
CREATE INDEX idx_aircraft_type          ON aircraft(type_id);
CREATE INDEX idx_flights_aircraft_dep   ON flights(aircraft_id, scheduled_departure);
CREATE INDEX idx_flights_route          ON flights(origin_airport_id, destination_airport_id);
CREATE INDEX idx_shipments_customer     ON shipments(customer_id);
CREATE INDEX idx_flight_cargo_flight    ON flight_cargo(flight_id);
CREATE INDEX idx_payments_invoice       ON payments(invoice_id);
CREATE INDEX idx_incidents_cargo        ON incidents(flight_cargo_id);
CREATE INDEX idx_crew_assign_crew       ON crew_assignments(crew_member_id, report_time);
CREATE INDEX idx_maintenance_aircraft   ON maintenance_records(aircraft_id, start_time);
CREATE INDEX idx_warehouses_airport     ON warehouses(airport_id);
CREATE INDEX idx_customs_shipment       ON customs_declarations(shipment_id);
CREATE INDEX idx_tracking_shipment_time ON tracking_events(shipment_id, event_time);
