# Entity–Relationship Diagram

```mermaid
erDiagram
    airlines       ||--o{ aircraft      : operates
    aircraft_types ||--o{ aircraft      : "is of type"
    aircraft       ||--o{ flights       : flies
    airports       ||--o{ flights       : "origin / destination"
    customers      ||--o{ shipments     : books
    airports       ||--o{ shipments     : "origin / destination"
    shipments      ||--o{ flight_cargo  : "travels as legs"
    flights        ||--o{ flight_cargo  : carries
    flight_cargo   ||--o{ incidents     : "may have"
    shipments      ||--o| invoices      : "billed by"
    invoices       ||--o{ payments      : "settled by"
    customers      ||--o{ payments      : pays

    airlines { int airline_id PK  text iata_code UK  text name UK  text country }
    airports { int airport_id PK  text iata_code UK  text name  text city  text country  real latitude  real longitude  int is_cargo_hub }
    aircraft_types { int type_id PK  text model UK  text manufacturer  int max_payload_kg  real max_volume_m3  int max_range_km }
    aircraft { int aircraft_id PK  text tail_number UK  int type_id FK  int airline_id FK  int year_manufactured  text status }
    customers { int customer_id PK  text name  text country  text customer_type  int payment_terms_days  text created_date }
    flights { int flight_id PK  text flight_number  int aircraft_id FK  int origin_airport_id FK  int destination_airport_id FK  text scheduled_departure  text scheduled_arrival  text actual_departure  text actual_arrival  int distance_km  text status }
    shipments { int shipment_id PK  int customer_id FK  int origin_airport_id FK  int destination_airport_id FK  text booking_date  text service_level  text commodity_category  int pieces  real total_weight_kg  real total_volume_m3  real declared_value_usd  text status }
    flight_cargo { int flight_cargo_id PK  int shipment_id FK  int flight_id FK  int leg_number  text leg_status }
    invoices { int invoice_id PK  int shipment_id FK_UK  text issued_date  text due_date  real amount_usd  text status }
    payments { int payment_id PK  int invoice_id FK  int customer_id FK  text payment_date  real amount_usd  text method }
    incidents { int incident_id PK  int flight_cargo_id FK  text incident_type  text severity  text reported_at  real claim_amount_usd  int resolved }
```

`benchmark_meta(meta_key, meta_value)` is a stand-alone helper table holding the dataset's as-of timestamp (`2025-12-20 00:00:00`) and generator seed.
