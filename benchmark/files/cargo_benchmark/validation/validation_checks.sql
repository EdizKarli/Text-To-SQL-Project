-- Validation checks for the Air Cargo Flights database.
-- Format: "-- @check <name> | <error|warning|info> | <description>" followed by ONE query returning a single number.
--   error   : counts violations; expected result is 0 (the runner fails if not).
--   warning : unusual-but-possibly-valid data; reported, never fails.
--   info    : descriptive coverage numbers; reported only.
-- The as-of moment of the dataset is stored in benchmark_meta('as_of_timestamp').

-- ===================================================== flights / aircraft
-- @check flight_prefix_matches_airline | error | Flight number prefix equals the operating airline's IATA code
SELECT COUNT(*) FROM flights f
JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN airlines al ON al.airline_id = a.airline_id
WHERE substr(f.flight_number, 1, 2) <> al.iata_code;

-- @check flight_within_aircraft_range | error | Flight distance does not exceed the aircraft type's range
SELECT COUNT(*) FROM flights f
JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id
WHERE f.distance_km > t.max_range_km;

-- @check flights_only_on_active_aircraft | error | Maintenance/retired aircraft have no flights
SELECT COUNT(*) FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id WHERE a.status <> 'active';

-- @check aircraft_no_overlapping_flights | error | One aircraft is never on two non-cancelled flights at once
SELECT COUNT(*) FROM flights f1
JOIN flights f2 ON f1.aircraft_id = f2.aircraft_id AND f1.flight_id < f2.flight_id
 AND f1.status <> 'cancelled' AND f2.status <> 'cancelled'
 AND f1.scheduled_departure < f2.scheduled_arrival AND f2.scheduled_departure < f1.scheduled_arrival;

-- @check aircraft_location_continuity | error | Each flight departs from where the aircraft's previous non-cancelled flight landed
WITH seq AS (
  SELECT origin_airport_id AS o,
         LAG(destination_airport_id) OVER (PARTITION BY aircraft_id ORDER BY scheduled_departure) AS prev_dest
  FROM flights WHERE status <> 'cancelled')
SELECT COUNT(*) FROM seq WHERE prev_dest IS NOT NULL AND prev_dest <> o;

-- @check completed_flights_landed_before_as_of | error | Completed flights have landed before the as-of moment
SELECT COUNT(*) FROM flights
WHERE status = 'completed' AND actual_arrival > (SELECT meta_value FROM benchmark_meta WHERE meta_key = 'as_of_timestamp');

-- @check scheduled_flights_depart_after_as_of | error | Scheduled flights depart after the as-of moment
SELECT COUNT(*) FROM flights
WHERE status = 'scheduled' AND scheduled_departure < (SELECT meta_value FROM benchmark_meta WHERE meta_key = 'as_of_timestamp');

-- @check extreme_departure_delays | warning | Completed flights departing more than 6 hours late (valid but unusual)
SELECT COUNT(*) FROM flights WHERE status = 'completed'
AND (julianday(actual_departure) - julianday(scheduled_departure)) * 24 > 6;

-- ===================================================== cargo loading
-- @check no_cargo_on_cancelled_flights | error | Cancelled flights carry no cargo
SELECT COUNT(*) FROM flight_cargo fc JOIN flights f ON f.flight_id = fc.flight_id WHERE f.status = 'cancelled';

-- @check leg_status_matches_flight_status | error | A leg is 'flown' exactly when its flight is completed
SELECT COUNT(*) FROM flight_cargo fc JOIN flights f ON f.flight_id = fc.flight_id
WHERE (fc.leg_status = 'flown') <> (f.status = 'completed');

-- @check flight_payload_and_volume_not_exceeded | error | Loaded weight/volume never exceeds the aircraft type's limits
SELECT COUNT(*) FROM (
  SELECT fc.flight_id, SUM(s.total_weight_kg) AS w, SUM(s.total_volume_m3) AS v
  FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id GROUP BY fc.flight_id) x
JOIN flights f ON f.flight_id = x.flight_id
JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id
WHERE x.w > t.max_payload_kg OR x.v > t.max_volume_m3;

-- ===================================================== shipments and their legs
-- @check first_leg_starts_at_shipment_origin | error | Leg 1 departs from the shipment's origin
SELECT COUNT(*) FROM flight_cargo fc
JOIN flights f ON f.flight_id = fc.flight_id JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE fc.leg_number = 1 AND f.origin_airport_id <> s.origin_airport_id;

-- @check last_leg_ends_at_shipment_destination | error | The final leg lands at the shipment's destination
SELECT COUNT(*) FROM flight_cargo fc
JOIN flights f ON f.flight_id = fc.flight_id JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE fc.leg_number = (SELECT MAX(leg_number) FROM flight_cargo x WHERE x.shipment_id = fc.shipment_id)
  AND f.destination_airport_id <> s.destination_airport_id;

-- @check leg_numbers_contiguous | error | Leg numbers run 1..n without gaps
SELECT COUNT(*) FROM (SELECT shipment_id FROM flight_cargo GROUP BY shipment_id HAVING MAX(leg_number) <> COUNT(*));

-- @check legs_connect_in_space_and_time | error | Consecutive legs connect at one airport with >= 12h between scheduled arrival and next departure
WITH l AS (
  SELECT f.origin_airport_id AS o, f.scheduled_departure AS sd,
         LAG(f.destination_airport_id) OVER w AS pd, LAG(f.scheduled_arrival) OVER w AS pa
  FROM flight_cargo fc JOIN flights f ON f.flight_id = fc.flight_id
  WINDOW w AS (PARTITION BY fc.shipment_id ORDER BY fc.leg_number))
SELECT COUNT(*) FROM l WHERE pd IS NOT NULL AND (pd <> o OR datetime(pa, '+12 hours') > sd);

-- @check first_departure_not_before_booking | error | Leg 1 departs on or after the booking date
SELECT COUNT(*) FROM flight_cargo fc
JOIN flights f ON f.flight_id = fc.flight_id JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE fc.leg_number = 1 AND substr(f.scheduled_departure, 1, 10) < s.booking_date;

-- @check booking_not_after_as_of | error | No booking is dated after the as-of day
SELECT COUNT(*) FROM shipments
WHERE booking_date > substr((SELECT meta_value FROM benchmark_meta WHERE meta_key = 'as_of_timestamp'), 1, 10);

-- @check shipment_status_matches_legs | error | cancelled=no legs, delivered=all flown, in_transit=some flown, booked=none flown
WITH x AS (
  SELECT s.shipment_id, s.status, COUNT(fc.flight_cargo_id) AS n, COALESCE(SUM(fc.leg_status = 'flown'), 0) AS fl
  FROM shipments s LEFT JOIN flight_cargo fc ON fc.shipment_id = s.shipment_id GROUP BY s.shipment_id)
SELECT COUNT(*) FROM x WHERE status <> CASE WHEN n = 0 THEN 'cancelled' WHEN fl = n THEN 'delivered'
                                            WHEN fl > 0 THEN 'in_transit' ELSE 'booked' END;

-- @check shipment_density_plausible | warning | Shipments outside 30-700 kg/m3 (valid but unusual)
SELECT COUNT(*) FROM shipments WHERE total_weight_kg / total_volume_m3 NOT BETWEEN 30 AND 700;

-- ===================================================== invoices and payments
-- @check invoice_exists_iff_shipment_departed | error | in_transit/delivered shipments have an invoice; booked/cancelled do not
SELECT (SELECT COUNT(*) FROM shipments s LEFT JOIN invoices i ON i.shipment_id = s.shipment_id
        WHERE s.status IN ('in_transit', 'delivered') AND i.invoice_id IS NULL)
     + (SELECT COUNT(*) FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id
        WHERE s.status IN ('booked', 'cancelled'));

-- @check invoice_issued_on_first_departure | error | Invoice issue date equals the date leg 1 actually departed
SELECT COUNT(*) FROM invoices i
JOIN flight_cargo fc ON fc.shipment_id = i.shipment_id AND fc.leg_number = 1
JOIN flights f ON f.flight_id = fc.flight_id
WHERE i.issued_date <> substr(f.actual_departure, 1, 10);

-- @check invoice_due_date_matches_terms | error | Due date = issue date + customer's payment terms
SELECT COUNT(*) FROM invoices i
JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
WHERE i.due_date <> date(i.issued_date, '+' || c.payment_terms_days || ' days');

-- @check invoice_status_matches_payments | error | paid / partially_paid / unpaid agrees with the payments received
SELECT COUNT(*) FROM (
  SELECT i.amount_usd AS a, i.status AS st,
         COALESCE((SELECT ROUND(SUM(p.amount_usd), 2) FROM payments p WHERE p.invoice_id = i.invoice_id), 0) AS paid
  FROM invoices i)
WHERE st <> CASE WHEN paid >= a THEN 'paid' WHEN paid > 0 THEN 'partially_paid' ELSE 'unpaid' END;

-- @check no_overpayment | error | Payments for an invoice never exceed its amount
SELECT COUNT(*) FROM (
  SELECT i.amount_usd AS a, (SELECT ROUND(SUM(p.amount_usd), 2) FROM payments p WHERE p.invoice_id = i.invoice_id) AS paid
  FROM invoices i) WHERE paid > a;

-- @check payment_customer_matches_shipment_customer | error | A payment's customer is the customer who owns the invoiced shipment
SELECT COUNT(*) FROM payments p
JOIN invoices i ON i.invoice_id = p.invoice_id JOIN shipments s ON s.shipment_id = i.shipment_id
WHERE p.customer_id <> s.customer_id;

-- @check payment_dates_in_range | error | Payment date is on/after invoice issue date and not after the as-of day
SELECT COUNT(*) FROM payments p JOIN invoices i ON i.invoice_id = p.invoice_id
WHERE p.payment_date < i.issued_date
   OR p.payment_date > substr((SELECT meta_value FROM benchmark_meta WHERE meta_key = 'as_of_timestamp'), 1, 10);

-- ===================================================== incidents
-- @check incident_only_on_flown_leg | error | Incidents are attached to legs that were actually flown
SELECT COUNT(*) FROM incidents i JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id WHERE fc.leg_status <> 'flown';

-- @check temperature_incident_commodity | error | Temperature excursions only for pharmaceuticals/perishables
SELECT COUNT(*) FROM incidents i
JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE i.incident_type = 'temperature_excursion' AND s.commodity_category NOT IN ('pharmaceuticals', 'perishables');

-- @check claim_not_above_declared_value | error | Claim amount never exceeds the shipment's declared value
SELECT COUNT(*) FROM incidents i
JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE i.claim_amount_usd > s.declared_value_usd;

-- @check incident_report_time_in_range | error | Incident reported after the flight departed and not after the as-of moment
SELECT COUNT(*) FROM incidents i
JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN flights f ON f.flight_id = fc.flight_id
WHERE i.reported_at < f.actual_departure
   OR i.reported_at > (SELECT meta_value FROM benchmark_meta WHERE meta_key = 'as_of_timestamp');

-- ===================================================== coverage and distribution
-- @check coverage_flight_statuses | error | Every flight status appears at least once
WITH e(v) AS (VALUES ('scheduled'), ('completed'), ('cancelled')) SELECT COUNT(*) FROM e WHERE v NOT IN (SELECT status FROM flights);

-- @check coverage_shipment_statuses | error | Every shipment status appears at least once
WITH e(v) AS (VALUES ('booked'), ('in_transit'), ('delivered'), ('cancelled')) SELECT COUNT(*) FROM e WHERE v NOT IN (SELECT status FROM shipments);

-- @check coverage_invoice_statuses | error | Every invoice status appears at least once
WITH e(v) AS (VALUES ('unpaid'), ('partially_paid'), ('paid')) SELECT COUNT(*) FROM e WHERE v NOT IN (SELECT status FROM invoices);

-- @check coverage_incident_types | error | Every incident type appears at least once
WITH e(v) AS (VALUES ('damage'), ('delay'), ('missing_documents'), ('temperature_excursion'), ('loss'))
SELECT COUNT(*) FROM e WHERE v NOT IN (SELECT incident_type FROM incidents);

-- @check coverage_commodities | error | Every commodity category appears at least once
WITH e(v) AS (VALUES ('electronics'), ('pharmaceuticals'), ('perishables'), ('automotive_parts'), ('apparel'), ('machinery'), ('documents'))
SELECT COUNT(*) FROM e WHERE v NOT IN (SELECT commodity_category FROM shipments);

-- @check multi_leg_shipments_present | error | At least some shipments need a connection (2+ legs)
SELECT CASE WHEN COUNT(*) > 0 THEN 0 ELSE 1 END FROM (SELECT shipment_id FROM flight_cargo GROUP BY shipment_id HAVING COUNT(*) > 1);

-- @check customers_without_shipments | info | Customers who never booked (kept on purpose for LEFT JOIN / NOT EXISTS questions)
SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.customer_id = c.customer_id);

-- @check duplicate_customer_names | info | Customer names that occur in more than one country (kept on purpose)
SELECT COUNT(*) FROM (SELECT name FROM customers GROUP BY name HAVING COUNT(*) > 1);

-- @check aircraft_never_flown | info | Aircraft without any flight (maintenance/retired, kept on purpose)
SELECT COUNT(*) FROM aircraft a WHERE NOT EXISTS (SELECT 1 FROM flights f WHERE f.aircraft_id = a.aircraft_id);

-- @check flights_without_cargo | info | Non-cancelled flights carrying no cargo (empty legs / repositioning)
SELECT COUNT(*) FROM flights f WHERE f.status <> 'cancelled' AND NOT EXISTS (SELECT 1 FROM flight_cargo fc WHERE fc.flight_id = f.flight_id);
