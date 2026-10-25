-- Air Cargo Flights benchmark database -- schema (SQLite 3.25+)
-- Conventions: all timestamps are UTC text 'YYYY-MM-DD HH:MM:SS'; dates are 'YYYY-MM-DD'.
PRAGMA foreign_keys = ON;

CREATE TABLE benchmark_meta (
    meta_key   TEXT PRIMARY KEY,
    meta_value TEXT NOT NULL
);

CREATE TABLE airlines (
    airline_id INTEGER PRIMARY KEY,
    iata_code  TEXT NOT NULL UNIQUE CHECK (length(iata_code) = 2),
    name       TEXT NOT NULL UNIQUE,
    country    TEXT NOT NULL
);

CREATE TABLE airports (
    airport_id   INTEGER PRIMARY KEY,
    iata_code    TEXT NOT NULL UNIQUE CHECK (length(iata_code) = 3),
    name         TEXT NOT NULL,
    city         TEXT NOT NULL,
    country      TEXT NOT NULL,
    latitude     REAL NOT NULL CHECK (latitude  BETWEEN  -90 AND  90),
    longitude    REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    is_cargo_hub INTEGER NOT NULL DEFAULT 0 CHECK (is_cargo_hub IN (0, 1))
);

CREATE TABLE aircraft_types (
    type_id        INTEGER PRIMARY KEY,
    model          TEXT NOT NULL UNIQUE,
    manufacturer   TEXT NOT NULL,
    max_payload_kg INTEGER NOT NULL CHECK (max_payload_kg > 0),
    max_volume_m3  REAL    NOT NULL CHECK (max_volume_m3 > 0),
    max_range_km   INTEGER NOT NULL CHECK (max_range_km > 0)
);

CREATE TABLE aircraft (
    aircraft_id       INTEGER PRIMARY KEY,
    tail_number       TEXT NOT NULL UNIQUE,
    type_id           INTEGER NOT NULL REFERENCES aircraft_types(type_id),
    airline_id        INTEGER NOT NULL REFERENCES airlines(airline_id),
    year_manufactured INTEGER NOT NULL CHECK (year_manufactured BETWEEN 1990 AND 2025),
    status            TEXT NOT NULL CHECK (status IN ('active', 'maintenance', 'retired'))
);

CREATE TABLE customers (
    customer_id        INTEGER PRIMARY KEY,
    name               TEXT NOT NULL,
    country            TEXT NOT NULL,
    customer_type      TEXT NOT NULL CHECK (customer_type IN ('shipper', 'freight_forwarder', 'retailer', 'manufacturer')),
    payment_terms_days INTEGER NOT NULL CHECK (payment_terms_days IN (15, 30, 45, 60)),
    created_date       TEXT NOT NULL,
    UNIQUE (name, country)          -- the same name may exist in different countries
);

CREATE TABLE flights (
    flight_id             INTEGER PRIMARY KEY,
    flight_number         TEXT NOT NULL,          -- airline IATA code + 3 digits
    aircraft_id           INTEGER NOT NULL REFERENCES aircraft(aircraft_id),
    origin_airport_id     INTEGER NOT NULL REFERENCES airports(airport_id),
    destination_airport_id INTEGER NOT NULL REFERENCES airports(airport_id),
    scheduled_departure   TEXT NOT NULL,
    scheduled_arrival     TEXT NOT NULL,
    actual_departure      TEXT,
    actual_arrival        TEXT,
    distance_km           INTEGER NOT NULL CHECK (distance_km > 0),
    status                TEXT NOT NULL CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    UNIQUE (flight_number, scheduled_departure),
    CHECK (origin_airport_id <> destination_airport_id),
    CHECK (scheduled_arrival > scheduled_departure),
    CHECK (
        (status = 'completed' AND actual_departure IS NOT NULL AND actual_arrival IS NOT NULL
                              AND actual_arrival > actual_departure)
     OR (status <> 'completed' AND actual_departure IS NULL AND actual_arrival IS NULL)
    )
);

CREATE TABLE shipments (
    shipment_id            INTEGER PRIMARY KEY,
    customer_id            INTEGER NOT NULL REFERENCES customers(customer_id),
    origin_airport_id      INTEGER NOT NULL REFERENCES airports(airport_id),
    destination_airport_id INTEGER NOT NULL REFERENCES airports(airport_id),
    booking_date           TEXT NOT NULL,
    service_level          TEXT NOT NULL CHECK (service_level IN ('express', 'standard', 'economy')),
    commodity_category     TEXT NOT NULL CHECK (commodity_category IN
        ('electronics', 'pharmaceuticals', 'perishables', 'automotive_parts', 'apparel', 'machinery', 'documents')),
    pieces                 INTEGER NOT NULL CHECK (pieces > 0),
    total_weight_kg        REAL NOT NULL CHECK (total_weight_kg > 0),
    total_volume_m3        REAL NOT NULL CHECK (total_volume_m3 > 0),
    declared_value_usd     REAL NOT NULL CHECK (declared_value_usd >= 0),
    status                 TEXT NOT NULL CHECK (status IN ('booked', 'in_transit', 'delivered', 'cancelled')),
    CHECK (origin_airport_id <> destination_airport_id)
);

-- A shipment travels on 1..n flights (connections). Each leg carries the whole shipment.
CREATE TABLE flight_cargo (
    flight_cargo_id INTEGER PRIMARY KEY,
    shipment_id     INTEGER NOT NULL REFERENCES shipments(shipment_id),
    flight_id       INTEGER NOT NULL REFERENCES flights(flight_id),
    leg_number      INTEGER NOT NULL CHECK (leg_number >= 1),
    leg_status      TEXT NOT NULL CHECK (leg_status IN ('planned', 'flown')),
    UNIQUE (shipment_id, leg_number),
    UNIQUE (shipment_id, flight_id)
);

CREATE TABLE invoices (
    invoice_id  INTEGER PRIMARY KEY,
    shipment_id INTEGER NOT NULL UNIQUE REFERENCES shipments(shipment_id),
    issued_date TEXT NOT NULL,
    due_date    TEXT NOT NULL,
    amount_usd  REAL NOT NULL CHECK (amount_usd > 0),
    status      TEXT NOT NULL CHECK (status IN ('unpaid', 'partially_paid', 'paid')),
    CHECK (due_date >= issued_date)
);

CREATE TABLE payments (
    payment_id   INTEGER PRIMARY KEY,
    invoice_id   INTEGER NOT NULL REFERENCES invoices(invoice_id),
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    payment_date TEXT NOT NULL,
    amount_usd   REAL NOT NULL CHECK (amount_usd > 0),
    method       TEXT NOT NULL CHECK (method IN ('wire_transfer', 'ach', 'credit_card'))
);

CREATE TABLE incidents (
    incident_id      INTEGER PRIMARY KEY,
    flight_cargo_id  INTEGER NOT NULL REFERENCES flight_cargo(flight_cargo_id),
    incident_type    TEXT NOT NULL CHECK (incident_type IN
        ('damage', 'delay', 'missing_documents', 'temperature_excursion', 'loss')),
    severity         TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    reported_at      TEXT NOT NULL,
    claim_amount_usd REAL CHECK (claim_amount_usd IS NULL OR claim_amount_usd >= 0),
    resolved         INTEGER NOT NULL CHECK (resolved IN (0, 1))
);

-- Indexes justified by the intended query patterns
CREATE INDEX idx_aircraft_type        ON aircraft(type_id);
CREATE INDEX idx_flights_aircraft_dep ON flights(aircraft_id, scheduled_departure);
CREATE INDEX idx_flights_route        ON flights(origin_airport_id, destination_airport_id);
CREATE INDEX idx_shipments_customer   ON shipments(customer_id);
CREATE INDEX idx_flight_cargo_flight  ON flight_cargo(flight_id);
CREATE INDEX idx_payments_invoice     ON payments(invoice_id);
CREATE INDEX idx_incidents_cargo      ON incidents(flight_cargo_id);
