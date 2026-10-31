-- Validation checks for the Air Cargo Flights database (NORMAL schema; the variants hold identical rows).
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

-- ===================================================== v2: aircraft, flights, fuel
-- @check aircraft_delivered_before_first_flight | error | An aircraft is delivered before its first scheduled departure
SELECT COUNT(*) FROM aircraft a
WHERE a.delivery_date > (SELECT MIN(substr(f.scheduled_departure, 1, 10)) FROM flights f WHERE f.aircraft_id = a.aircraft_id);

-- @check heavy_check_after_delivery | error | The last heavy check is after delivery and before 2025
SELECT COUNT(*) FROM aircraft WHERE last_heavy_check_date < delivery_date OR last_heavy_check_date >= '2025-01-01';

-- @check takeoff_weight_within_mtow | error | Take-off weight never exceeds the type's maximum take-off weight
SELECT COUNT(*) FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
WHERE f.takeoff_weight_kg > t.max_takeoff_weight_kg;

-- @check takeoff_weight_equals_components | error | Take-off weight = empty weight + cargo on board + fuel uplifted (+-1 kg)
SELECT COUNT(*) FROM flights f
JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
JOIN fuel_uplifts u ON u.flight_id = f.flight_id
LEFT JOIN (SELECT fc.flight_id, SUM(s.total_weight_kg) AS kg FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
           GROUP BY fc.flight_id) c ON c.flight_id = f.flight_id
WHERE abs(f.takeoff_weight_kg - (t.operating_empty_weight_kg + COALESCE(c.kg, 0) + u.quantity_kg)) > 1;

-- @check weather_cancellations_have_bad_weather | error | Flights cancelled for weather had snow, fog or thunderstorms
SELECT COUNT(*) FROM flights WHERE cancellation_reason = 'weather' AND weather_at_departure NOT IN ('snow', 'fog', 'thunderstorm');

-- @check delay_code_iff_departure_late | error | A delay code is present exactly for completed flights departing > 15 min late
SELECT COUNT(*) FROM flights WHERE status = 'completed'
AND (delay_code IS NOT NULL) <> ((julianday(actual_departure) - julianday(scheduled_departure)) * 1440 > 15.001);

-- @check one_fuel_uplift_per_completed_flight | error | Every completed flight has exactly one fuel uplift; other flights have none
SELECT (SELECT COUNT(*) FROM flights f WHERE f.status = 'completed' AND NOT EXISTS (SELECT 1 FROM fuel_uplifts u WHERE u.flight_id = f.flight_id))
     + (SELECT COUNT(*) FROM fuel_uplifts u JOIN flights f ON f.flight_id = u.flight_id WHERE f.status <> 'completed');

-- @check fuel_uplift_at_origin_before_departure | error | Fuel is uplifted at the departure airport before actual departure
SELECT COUNT(*) FROM fuel_uplifts u JOIN flights f ON f.flight_id = u.flight_id
WHERE u.airport_id <> f.origin_airport_id OR u.uplift_time >= f.actual_departure;

-- @check fuel_within_tank_capacity | error | Uplifted fuel fits in the tanks of the aircraft type
SELECT COUNT(*) FROM fuel_uplifts u JOIN flights f ON f.flight_id = u.flight_id
JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
WHERE u.quantity_kg > t.fuel_capacity_kg;

-- @check fuel_quantities_and_cost_consistent | error | kg = litres x density (+-1 kg); cost = litres x price (+-0.01); CO2 = 3.16 x burned (+-1)
SELECT COUNT(*) FROM fuel_uplifts
WHERE abs(quantity_litres * density_kg_per_l - quantity_kg) > 1
   OR abs(quantity_litres * price_usd_per_litre - total_cost_usd) > 0.01
   OR abs(fuel_burned_kg * 3.16 - co2_emissions_kg) > 1;

-- @check fuel_type_matches_country | error | Jet A is used at US airports, Jet A-1 everywhere else
SELECT COUNT(*) FROM fuel_uplifts u JOIN airports a ON a.airport_id = u.airport_id
WHERE (u.fuel_type = 'Jet A') <> (a.country = 'United States');

-- ===================================================== v2: crew
-- @check crew_role_matches_rank | error | captain role -> captain; first_officer/relief_pilot -> first officer; loadmaster -> loadmaster
SELECT COUNT(*) FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
WHERE m.crew_rank <> CASE ca.duty_role WHEN 'captain' THEN 'captain' WHEN 'loadmaster' THEN 'loadmaster' ELSE 'first_officer' END;

-- @check crew_airline_and_type_rating_match_aircraft | error | Crew belong to the operating airline; pilots are rated on the aircraft type
SELECT COUNT(*) FROM crew_assignments ca
JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
JOIN flights f ON f.flight_id = ca.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
WHERE m.airline_id <> a.airline_id OR (m.crew_rank <> 'loadmaster' AND m.type_rating_id <> a.type_id);

-- @check crew_license_valid_on_duty | error | Pilots never fly after their licence expiry date
SELECT COUNT(*) FROM crew_assignments ca
JOIN crew_members m ON m.crew_member_id = ca.crew_member_id JOIN flights f ON f.flight_id = ca.flight_id
WHERE m.license_expiry_date < substr(f.scheduled_departure, 1, 10);

-- @check inactive_crew_not_rostered | error | Inactive crew members have no assignments
SELECT COUNT(*) FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id WHERE m.is_active = 0;

-- @check flight_crew_complement | error | Each non-cancelled flight has 1 captain, 1 first officer, exactly 1 pilot flying; cancelled flights have no crew
SELECT (SELECT COUNT(*) FROM flights f WHERE f.status <> 'cancelled' AND (
          (SELECT COUNT(*) FROM crew_assignments ca WHERE ca.flight_id = f.flight_id AND ca.duty_role = 'captain') <> 1
       OR (SELECT COUNT(*) FROM crew_assignments ca WHERE ca.flight_id = f.flight_id AND ca.duty_role = 'first_officer') <> 1
       OR (SELECT COUNT(*) FROM crew_assignments ca WHERE ca.flight_id = f.flight_id AND ca.is_pilot_flying = 1) <> 1))
     + (SELECT COUNT(*) FROM crew_assignments ca JOIN flights f ON f.flight_id = ca.flight_id WHERE f.status = 'cancelled');

-- @check crew_no_overlapping_duties | error | A crew member is never on two duties at once
SELECT COUNT(*) FROM crew_assignments a JOIN crew_assignments b
  ON a.crew_member_id = b.crew_member_id AND a.assignment_id < b.assignment_id
 AND a.report_time < b.release_time AND b.report_time < a.release_time;

-- @check crew_rest_minutes_consistent | error | rest_minutes_before = minutes since the previous release, and always >= 12 h
WITH x AS (
  SELECT rest_minutes_before AS r, report_time,
         LAG(release_time) OVER (PARTITION BY crew_member_id ORDER BY report_time) AS prev_rel
  FROM crew_assignments)
SELECT COUNT(*) FROM x
WHERE (prev_rel IS NULL) <> (r IS NULL)
   OR abs(r - (julianday(report_time) - julianday(prev_rel)) * 1440) > 1
   OR r < 720;

-- @check crew_block_and_hotel_consistent | error | Credited block minutes equal the flight's actual block time; hotel iff landing away from base
SELECT COUNT(*) FROM crew_assignments ca
JOIN flights f ON f.flight_id = ca.flight_id JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
WHERE (f.status = 'completed' AND abs(ca.block_minutes_credited - (julianday(f.actual_arrival) - julianday(f.actual_departure)) * 1440) > 1)
   OR ca.hotel_required <> (f.destination_airport_id <> m.base_airport_id)
   OR (ca.assignment_status = 'completed') <> (f.status = 'completed');

-- ===================================================== v2: maintenance
-- @check maintenance_no_overlap_with_flights | error | An aircraft is never in maintenance during one of its non-cancelled flights
SELECT COUNT(*) FROM maintenance_records m JOIN flights f ON f.aircraft_id = m.aircraft_id AND f.status <> 'cancelled'
WHERE m.start_time < COALESCE(f.actual_arrival, f.scheduled_arrival)
  AND COALESCE(m.end_time, '9999-12-31') > COALESCE(f.actual_departure, f.scheduled_departure);

-- @check maintenance_at_aircraft_location | error | Maintenance happens where the aircraft's previous non-cancelled flight landed
SELECT COUNT(*) FROM maintenance_records m
WHERE EXISTS (SELECT 1 FROM flights f WHERE f.aircraft_id = m.aircraft_id)
  AND m.airport_id <> (SELECT f.destination_airport_id FROM flights f
                       WHERE f.aircraft_id = m.aircraft_id AND f.status <> 'cancelled' AND f.scheduled_departure < m.start_time
                       ORDER BY f.scheduled_departure DESC LIMIT 1);

-- @check maintenance_status_matches_as_of | error | completed ends before the as-of moment, planned starts after it, in_progress spans it
SELECT COUNT(*) FROM maintenance_records, (SELECT meta_value AS now FROM benchmark_meta WHERE meta_key = 'as_of_timestamp')
WHERE (status = 'completed' AND end_time > now) OR (status = 'planned' AND start_time < now)
   OR (status = 'in_progress' AND start_time > now);

-- @check grounded_aircraft_in_maintenance | error | Aircraft with status 'maintenance' have an in-progress maintenance record
SELECT COUNT(*) FROM aircraft a WHERE a.status = 'maintenance'
AND NOT EXISTS (SELECT 1 FROM maintenance_records m WHERE m.aircraft_id = a.aircraft_id AND m.status = 'in_progress');

-- ===================================================== v2: warehouses, shipments, loading
-- @check every_airport_has_bonded_warehouse | error | Each airport has at least one customs-bonded warehouse
SELECT COUNT(*) FROM airports a WHERE NOT EXISTS (SELECT 1 FROM warehouses w WHERE w.airport_id = a.airport_id AND w.is_bonded = 1);

-- @check awb_check_digit | error | Air waybill serial: last digit = first 7 serial digits mod 7
SELECT COUNT(*) FROM shipments
WHERE awb_number NOT GLOB '[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
   OR CAST(substr(awb_number, 5, 7) AS INTEGER) % 7 <> CAST(substr(awb_number, 12, 1) AS INTEGER);

-- @check chargeable_weight_rule | error | Chargeable weight = max(actual weight, volume x 167), to one rounding unit (0.1 kg)
SELECT COUNT(*) FROM shipments
WHERE abs(chargeable_weight_kg - max(total_weight_kg, total_volume_m3 * 167)) > 0.1001;

-- @check temperature_control_matches_commodity | error | Exactly pharmaceuticals and perishables are temperature-controlled; documents are never dangerous goods
SELECT COUNT(*) FROM shipments
WHERE is_temperature_controlled <> (commodity_category IN ('pharmaceuticals', 'perishables'))
   OR (commodity_category = 'documents' AND is_dangerous_goods = 1);

-- @check main_deck_positions_not_exceeded | error | Main-deck ULDs per flight never exceed the type's main-deck positions
SELECT COUNT(*) FROM (SELECT fc.flight_id, COUNT(*) AS n FROM flight_cargo fc WHERE fc.deck = 'main' GROUP BY fc.flight_id) x
JOIN flights f ON f.flight_id = x.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id WHERE x.n > t.main_deck_positions;

-- @check uld_positions_unique_per_flight | error | No two ULDs occupy the same position on one flight (bulk hold excluded)
SELECT COUNT(*) FROM (SELECT flight_id, position_code FROM flight_cargo WHERE position_code <> 'BLK'
                      GROUP BY flight_id, position_code HAVING COUNT(*) > 1);

-- @check loaded_before_departure | error | Flown legs were loaded before the flight actually departed
SELECT COUNT(*) FROM flight_cargo fc JOIN flights f ON f.flight_id = fc.flight_id WHERE fc.loaded_at >= f.actual_departure;

-- ===================================================== v2: billing
-- @check invoice_components_sum_to_total | error | freight + fuel + security + handling + DG surcharges - discount = amount (+-0.011)
SELECT COUNT(*) FROM invoices
WHERE abs(freight_charge_usd + fuel_surcharge_usd + security_fee_usd + handling_fee_usd + dg_surcharge_usd - discount_usd - amount_usd) > 0.011;

-- @check invoice_rules_follow_customer_and_goods | error | Invoice terms = customer terms; DG surcharge only for DG; discount only for gold/platinum
SELECT COUNT(*) FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
WHERE i.payment_terms_days <> c.payment_terms_days
   OR (i.dg_surcharge_usd > 0) <> (s.is_dangerous_goods = 1)
   OR (i.discount_usd > 0 AND c.loyalty_tier NOT IN ('gold', 'platinum'));

-- @check payment_fx_consistent | error | original amount x exchange rate = USD amount (+-0.05)
SELECT COUNT(*) FROM payments WHERE abs(round(original_amount * exchange_rate_to_usd, 2) - amount_usd) > 0.05;

-- ===================================================== v2: incidents and insurance
-- @check incident_location_consistent | error | Incident airport = destination of its leg; its warehouse (if any) is at that airport
SELECT COUNT(*) FROM incidents i
JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN flights f ON f.flight_id = fc.flight_id
LEFT JOIN warehouses w ON w.warehouse_id = i.warehouse_id
WHERE i.airport_id <> f.destination_airport_id OR (w.warehouse_id IS NOT NULL AND w.airport_id <> i.airport_id);

-- @check claims_match_incidents | error | Claimed amount = incident claim; claim customer = shipment customer; filed after the incident
SELECT COUNT(*) FROM insurance_claims c
JOIN incidents i ON i.incident_id = c.incident_id
JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE i.claim_amount_usd IS NULL OR abs(c.claimed_amount_usd - i.claim_amount_usd) > 0.001
   OR c.customer_id <> s.customer_id OR c.filed_date < substr(i.reported_at, 1, 10);

-- @check claim_dates_ordered | error | filed <= decision <= settlement <= as-of day
SELECT COUNT(*) FROM insurance_claims, (SELECT substr(meta_value, 1, 10) AS today FROM benchmark_meta WHERE meta_key = 'as_of_timestamp')
WHERE decision_date < filed_date OR settlement_date < decision_date OR filed_date > today
   OR decision_date > today OR settlement_date > today;

-- ===================================================== v2: customs
-- @check customs_only_cross_border | error | Declarations exist only when origin and destination are in different customs territories (DE+NL = EU)
SELECT COUNT(*) FROM customs_declarations d
JOIN shipments s ON s.shipment_id = d.shipment_id
JOIN airports o ON o.airport_id = s.origin_airport_id JOIN airports t ON t.airport_id = s.destination_airport_id
WHERE (CASE WHEN o.country IN ('Germany', 'Netherlands') THEN 'EU' ELSE o.country END)
    = (CASE WHEN t.country IN ('Germany', 'Netherlands') THEN 'EU' ELSE t.country END);

-- @check customs_lodged_at_bonded_warehouse | error | Export at an origin bonded warehouse, import at a destination one; country matches the airport
SELECT COUNT(*) FROM customs_declarations d
JOIN shipments s ON s.shipment_id = d.shipment_id
JOIN warehouses w ON w.warehouse_id = d.warehouse_id JOIN airports a ON a.airport_id = w.airport_id
WHERE w.is_bonded = 0 OR a.country <> d.customs_country
   OR w.airport_id <> CASE d.declaration_type WHEN 'export' THEN s.origin_airport_id ELSE s.destination_airport_id END;

-- @check customs_amounts_consistent | error | Customs value = declared value; duty = value x rate; export duty and VAT are zero
SELECT COUNT(*) FROM customs_declarations d JOIN shipments s ON s.shipment_id = d.shipment_id
WHERE abs(d.customs_value_usd - s.declared_value_usd) > 0.001
   OR abs(d.duty_amount_usd - round(d.customs_value_usd * d.duty_rate_pct / 100, 2)) > 0.011;

-- @check customs_timing | error | Exports are cleared before leg 1 departs; imports are lodged after the final leg arrives
SELECT (SELECT COUNT(*) FROM customs_declarations d
        JOIN flight_cargo fc ON fc.shipment_id = d.shipment_id AND fc.leg_number = 1 JOIN flights f ON f.flight_id = fc.flight_id
        WHERE d.declaration_type = 'export' AND f.status = 'completed' AND (d.status <> 'cleared' OR d.cleared_at >= f.actual_departure))
     + (SELECT COUNT(*) FROM customs_declarations d JOIN shipments s ON s.shipment_id = d.shipment_id
        JOIN flight_cargo fc ON fc.shipment_id = d.shipment_id
         AND fc.leg_number = (SELECT MAX(x.leg_number) FROM flight_cargo x WHERE x.shipment_id = d.shipment_id)
        JOIN flights f ON f.flight_id = fc.flight_id
        WHERE d.declaration_type = 'import' AND (s.status <> 'delivered' OR d.submitted_at < f.actual_arrival));

-- ===================================================== v2: tracking
-- @check tracking_not_after_as_of | error | No tracking event is later than the as-of moment
SELECT COUNT(*) FROM tracking_events WHERE event_time > (SELECT meta_value FROM benchmark_meta WHERE meta_key = 'as_of_timestamp');

-- @check tracking_flight_events_match_flights | error | DEP/ARR events carry the flight's actual time and airport, and only for flights the shipment flies on
SELECT COUNT(*) FROM tracking_events e JOIN flights f ON f.flight_id = e.flight_id
WHERE (e.event_code = 'DEP' AND (e.event_time <> f.actual_departure OR e.airport_id <> f.origin_airport_id))
   OR (e.event_code = 'ARR' AND (e.event_time <> f.actual_arrival OR e.airport_id <> f.destination_airport_id))
   OR NOT EXISTS (SELECT 1 FROM flight_cargo fc WHERE fc.shipment_id = e.shipment_id AND fc.flight_id = e.flight_id);

-- @check tracking_chronology | error | BKD first; RCS before the first DEP; RCF < NFD < DLV after the last ARR
WITH t AS (
  SELECT shipment_id,
         MIN(CASE WHEN event_code = 'BKD' THEN event_time END) AS bkd,
         MIN(CASE WHEN event_code = 'RCS' THEN event_time END) AS rcs,
         MIN(CASE WHEN event_code = 'DEP' THEN event_time END) AS dep1,
         MAX(CASE WHEN event_code = 'ARR' THEN event_time END) AS arr_last,
         MIN(CASE WHEN event_code = 'RCF' THEN event_time END) AS rcf,
         MIN(CASE WHEN event_code = 'NFD' THEN event_time END) AS nfd,
         MIN(CASE WHEN event_code = 'DLV' THEN event_time END) AS dlv,
         MIN(event_time) AS first_ev
  FROM tracking_events GROUP BY shipment_id)
SELECT COUNT(*) FROM t
WHERE bkd IS NULL OR bkd > first_ev OR rcs >= dep1 OR rcf <= arr_last OR nfd <= rcf OR dlv <= nfd;

-- @check delivery_requires_import_clearance | error | DLV only after a cleared import (if one is needed); held/pending imports block delivery
SELECT COUNT(*) FROM tracking_events e JOIN customs_declarations d ON d.shipment_id = e.shipment_id AND d.declaration_type = 'import'
WHERE e.event_code IN ('NFD', 'DLV') AND (d.status <> 'cleared' OR e.event_time <= d.cleared_at);

-- @check tracking_event_presence | error | Every shipment has a BKD event; exactly the cancelled ones have a CAN event; weight only on RCS
SELECT (SELECT COUNT(*) FROM shipments s WHERE NOT EXISTS (SELECT 1 FROM tracking_events e WHERE e.shipment_id = s.shipment_id AND e.event_code = 'BKD'))
     + (SELECT COUNT(*) FROM shipments s WHERE (s.status = 'cancelled')
                <> EXISTS (SELECT 1 FROM tracking_events e WHERE e.shipment_id = s.shipment_id AND e.event_code = 'CAN'));

-- @check temperature_readings_only_controlled | error | Temperature readings exist only for temperature-controlled shipments
SELECT COUNT(*) FROM tracking_events e JOIN shipments s ON s.shipment_id = e.shipment_id
WHERE e.temperature_c IS NOT NULL AND s.is_temperature_controlled = 0;

-- @check out_of_range_readings_have_incident | error | Every out-of-range probe reading belongs to a shipment with a temperature_excursion incident
SELECT COUNT(DISTINCT e.shipment_id) FROM tracking_events e JOIN shipments s ON s.shipment_id = e.shipment_id
WHERE e.temperature_c NOT BETWEEN s.min_temperature_c AND s.max_temperature_c
  AND NOT EXISTS (SELECT 1 FROM flight_cargo fc JOIN incidents i ON i.flight_cargo_id = fc.flight_cargo_id
                  WHERE fc.shipment_id = s.shipment_id AND i.incident_type = 'temperature_excursion');

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

-- @check coverage_v2_categories | error | Every warehouse type, check type, crew rank, customs status and claim status appears
WITH e(t, v) AS (VALUES ('w', 'general'), ('w', 'cold_chain'), ('w', 'dangerous_goods'), ('w', 'express'),
                        ('m', 'line'), ('m', 'A_check'), ('m', 'B_check'), ('m', 'C_check'), ('m', 'unscheduled'),
                        ('r', 'captain'), ('r', 'first_officer'), ('r', 'loadmaster'),
                        ('d', 'pending'), ('d', 'cleared'), ('d', 'held'),
                        ('c', 'under_review'), ('c', 'approved'), ('c', 'rejected'), ('c', 'paid'))
SELECT COUNT(*) FROM e WHERE v NOT IN (
  SELECT warehouse_type FROM warehouses WHERE t = 'w' UNION ALL SELECT check_type FROM maintenance_records WHERE t = 'm'
  UNION ALL SELECT crew_rank FROM crew_members WHERE t = 'r' UNION ALL SELECT status FROM customs_declarations WHERE t = 'd'
  UNION ALL SELECT status FROM insurance_claims WHERE t = 'c');

-- @check coverage_event_codes | error | Every tracking event code appears at least once
WITH e(v) AS (VALUES ('BKD'), ('RCS'), ('DEP'), ('ARR'), ('RCF'), ('NFD'), ('DLV'), ('CAN'))
SELECT COUNT(*) FROM e WHERE v NOT IN (SELECT event_code FROM tracking_events);

-- @check customers_without_shipments | info | Customers who never booked (kept on purpose for LEFT JOIN / NOT EXISTS questions)
SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.customer_id = c.customer_id);

-- @check duplicate_customer_names | info | Customer names that occur in more than one country (kept on purpose)
SELECT COUNT(*) FROM (SELECT name FROM customers GROUP BY name HAVING COUNT(*) > 1);

-- @check aircraft_never_flown | info | Aircraft without any flight (maintenance/retired, kept on purpose)
SELECT COUNT(*) FROM aircraft a WHERE NOT EXISTS (SELECT 1 FROM flights f WHERE f.aircraft_id = a.aircraft_id);

-- @check flights_without_cargo | info | Non-cancelled flights carrying no cargo (empty legs / repositioning)
SELECT COUNT(*) FROM flights f WHERE f.status <> 'cancelled' AND NOT EXISTS (SELECT 1 FROM flight_cargo fc WHERE fc.flight_id = f.flight_id);

-- @check delivered_without_dlv_scan | info | Delivered (landed) shipments with no DLV scan yet: import held by customs (kept on purpose)
SELECT COUNT(*) FROM shipments s WHERE s.status = 'delivered'
AND NOT EXISTS (SELECT 1 FROM tracking_events e WHERE e.shipment_id = s.shipment_id AND e.event_code = 'DLV');

-- @check crew_never_rostered | info | Crew members without any assignment (inactive or on a grounded fleet; kept on purpose)
SELECT COUNT(*) FROM crew_members m WHERE NOT EXISTS (SELECT 1 FROM crew_assignments a WHERE a.crew_member_id = m.crew_member_id);

-- @check pilots_with_expired_licence | info | Pilots whose licence expired before the as-of day (grounded after expiry)
SELECT COUNT(*) FROM crew_members WHERE license_expiry_date < '2025-12-20';

-- @check airports_without_cold_chain | info | Airports without a cold-chain warehouse (temperature cargo handled in general warehouses)
SELECT COUNT(*) FROM airports a WHERE NOT EXISTS (SELECT 1 FROM warehouses w WHERE w.airport_id = a.airport_id AND w.warehouse_type = 'cold_chain');

-- @check domestic_shipments_without_customs | info | Non-cancelled shipments needing no customs (domestic or intra-EU)
SELECT COUNT(*) FROM shipments s WHERE s.status <> 'cancelled'
AND NOT EXISTS (SELECT 1 FROM customs_declarations d WHERE d.shipment_id = s.shipment_id);
