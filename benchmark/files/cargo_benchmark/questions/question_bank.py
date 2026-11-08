"""Question bank: 240 base questions (80 easy, 80 moderate, 80 hard), each with ONE Gold SQL query (normal schema)
and FOUR phrasings of the same information need:

  casual              everyday language, no schema terms
  schema_aware        names tables/columns explicitly; [[table]] and [[table.column]] are placeholders that
                      build_questions.py / build_variants.py render with the names of each schema variant
  business_executive  KPI / management vocabulary
  vague               short and underspecified; the answer_spec records the intended reading

Edit questions here, then run questions/build_questions.py and scripts/build_variants.py.
"""
AS_OF = "2025-12-20"
STYLES = ("casual", "schema_aware", "business_executive", "vague")
EASY = [
("E01", ["COUNT", "WHERE"], "One value: number of airports with is_cargo_hub = 1.",
 "SELECT COUNT(*) AS hub_airports FROM airports WHERE is_cargo_hub = 1"),
("E02", ["filtering", "ORDER BY"], "Column: iata_code of airports with night_curfew = 1, ordered by iata_code.",
 "SELECT iata_code FROM airports WHERE night_curfew = 1 ORDER BY iata_code"),
("E03", ["filtering"], "Column: name of airlines whose alliance is 'CargoLink', ordered by name.",
 "SELECT name FROM airlines WHERE alliance = 'CargoLink' ORDER BY name"),
("E04", ["filtering"], "Column: model of aircraft types made by 'Airbus', ordered by model.",
 "SELECT model FROM aircraft_types WHERE manufacturer = 'Airbus' ORDER BY model"),
("E05", ["COUNT", "WHERE"], "One value: number of aircraft with ownership = 'leased'.",
 "SELECT COUNT(*) AS leased_aircraft FROM aircraft WHERE ownership = 'leased'"),
("E06", ["filtering", "<>"], "Columns: tail_number, status of aircraft whose status is not 'active', ordered by tail_number.",
 "SELECT tail_number, status FROM aircraft WHERE status <> 'active' ORDER BY tail_number"),
("E07", ["GROUP BY", "COUNT"], "Columns: loyalty_tier, number of customers; one row per tier, ordered by tier.",
 "SELECT loyalty_tier, COUNT(*) AS customers FROM customers GROUP BY loyalty_tier ORDER BY loyalty_tier"),
("E08", ["filtering", "ORDER BY"], "Columns: name, city of customers with country 'Germany', ordered by name then city.",
 "SELECT name, city FROM customers WHERE country = 'Germany' ORDER BY name, city"),
("E09", ["GROUP BY", "COUNT"], "Columns: warehouse_type, number of warehouses; ordered by type.",
 "SELECT warehouse_type, COUNT(*) AS warehouses FROM warehouses GROUP BY warehouse_type ORDER BY warehouse_type"),
("E10", ["SUM", "WHERE"], "One value: SUM(floor_area_m2) of warehouses of type 'cold_chain'.",
 "SELECT SUM(floor_area_m2) AS cold_chain_area_m2 FROM warehouses WHERE warehouse_type = 'cold_chain'"),
("E11", ["COUNT", "AND"], "One value: crew members with crew_rank 'captain' and is_active = 1.",
 "SELECT COUNT(*) AS active_captains FROM crew_members WHERE crew_rank = 'captain' AND is_active = 1"),
("E12", ["AVG", "ROUND"], "One value: AVG(total_flight_hours) of crew members with rank 'first_officer' (active or not), rounded to 1 decimal.",
 "SELECT ROUND(AVG(total_flight_hours), 1) AS avg_flight_hours FROM crew_members WHERE crew_rank = 'first_officer'"),
("E13", ["COUNT", "WHERE"], "One value: number of flights with flight_type 'charter' (any status).",
 "SELECT COUNT(*) AS charter_flights FROM flights WHERE flight_type = 'charter'"),
("E14", ["MAX"], "One value: the largest distance_km of any flight.",
 "SELECT MAX(distance_km) AS longest_distance_km FROM flights"),
("E15", ["COUNT", "AND"], "One value: cancelled flights with cancellation_reason 'technical'.",
 "SELECT COUNT(*) AS technical_cancellations FROM flights WHERE status = 'cancelled' AND cancellation_reason = 'technical'"),
("E16", ["COUNT", "WHERE"], "One value: flights (any status) with weather_at_departure 'thunderstorm'.",
 "SELECT COUNT(*) AS thunderstorm_flights FROM flights WHERE weather_at_departure = 'thunderstorm'"),
("E17", ["COUNT", "WHERE"], "One value: crew assignments with hotel_required = 1.",
 "SELECT COUNT(*) AS hotel_assignments FROM crew_assignments WHERE hotel_required = 1"),
("E18", ["COUNT", "WHERE"], "One value: maintenance records with is_aog = 1.",
 "SELECT COUNT(*) AS aog_events FROM maintenance_records WHERE is_aog = 1"),
("E19", ["SUM", "AND"], "One value: SUM(parts_cost_usd) of completed 'unscheduled' maintenance, rounded to 2 decimals.",
 "SELECT ROUND(SUM(parts_cost_usd), 2) AS unscheduled_parts_cost_usd FROM maintenance_records WHERE check_type = 'unscheduled' AND status = 'completed'"),
("E20", ["COUNT", "WHERE"], "One value: fuel uplifts with delivery_method 'truck'.",
 "SELECT COUNT(*) AS truck_uplifts FROM fuel_uplifts WHERE delivery_method = 'truck'"),
("E21", ["AVG", "ROUND"], "One value: AVG(density_kg_per_l) over all fuel uplifts, rounded to 3 decimals.",
 "SELECT ROUND(AVG(density_kg_per_l), 3) AS avg_density_kg_per_l FROM fuel_uplifts"),
("E22", ["SUM", "WHERE"], "One value: SUM(quantity_litres) of fuel uplifts with fuel_type 'Jet A'.",
 "SELECT SUM(quantity_litres) AS jet_a_litres FROM fuel_uplifts WHERE fuel_type = 'Jet A'"),
("E23", ["COUNT", "WHERE"], "One value: shipments (any status) with service_level 'express'.",
 "SELECT COUNT(*) AS express_shipments FROM shipments WHERE service_level = 'express'"),
("E24", ["MAX"], "One value: the largest total_weight_kg of any shipment.",
 "SELECT MAX(total_weight_kg) AS heaviest_shipment_kg FROM shipments"),
("E25", ["COUNT", "WHERE"], "One value: shipments with is_temperature_controlled = 1 (any status).",
 "SELECT COUNT(*) AS temperature_controlled_shipments FROM shipments WHERE is_temperature_controlled = 1"),
("E26", ["AVG", "ROUND"], "One value: AVG(declared_value_usd) of 'electronics' shipments (any status), rounded to 2 decimals.",
 "SELECT ROUND(AVG(declared_value_usd), 2) AS avg_electronics_value_usd FROM shipments WHERE commodity_category = 'electronics'"),
("E27", ["COUNT", "WHERE"], "One value: flight_cargo rows (shipment legs) with deck 'lower'.",
 "SELECT COUNT(*) AS lower_deck_legs FROM flight_cargo WHERE deck = 'lower'"),
("E28", ["COUNT", "WHERE"], "One value: flight_cargo rows with uld_type 'BULK'.",
 "SELECT COUNT(*) AS bulk_legs FROM flight_cargo WHERE uld_type = 'BULK'"),
("E29", ["COUNT", "WHERE"], "One value: invoices with sent_via 'edi'.",
 "SELECT COUNT(*) AS edi_invoices FROM invoices WHERE sent_via = 'edi'"),
("E30", ["SUM", "ROUND"], "One value: SUM(discount_usd) over all invoices, rounded to 2 decimals.",
 "SELECT ROUND(SUM(discount_usd), 2) AS total_discount_usd FROM invoices"),
("E31", ["COUNT", "WHERE"], "One value: payments with method 'credit_card'.",
 "SELECT COUNT(*) AS card_payments FROM payments WHERE method = 'credit_card'"),
("E32", ["COUNT", "SUM"], "Two values: number of payments with original_currency 'EUR' and SUM(original_amount) of them, rounded to 2 decimals.",
 "SELECT COUNT(*) AS eur_payments, ROUND(SUM(original_amount), 2) AS total_eur FROM payments WHERE original_currency = 'EUR'"),
("E33", ["GROUP BY", "COUNT"], "Columns: severity, number of incidents; ordered by severity.",
 "SELECT severity, COUNT(*) AS incidents FROM incidents GROUP BY severity ORDER BY severity"),
("E34", ["COUNT", "WHERE"], "One value: incidents with resolved = 0.",
 "SELECT COUNT(*) AS open_incidents FROM incidents WHERE resolved = 0"),
("E35", ["filtering", "ORDER BY"], "Column: claim_number of insurance claims with status 'rejected', ordered.",
 "SELECT claim_number FROM insurance_claims WHERE status = 'rejected' ORDER BY claim_number"),
("E36", ["AVG", "ROUND"], "One value: AVG(claimed_amount_usd) over all insurance claims, rounded to 2 decimals.",
 "SELECT ROUND(AVG(claimed_amount_usd), 2) AS avg_claimed_usd FROM insurance_claims"),
("E37", ["COUNT", "AND"], "One value: customs declarations with declaration_type 'import' and status 'held'.",
 "SELECT COUNT(*) AS held_imports FROM customs_declarations WHERE declaration_type = 'import' AND status = 'held'"),
("E38", ["COUNT", "WHERE"], "One value: customs declarations (export or import) with inspection_required = 1.",
 "SELECT COUNT(*) AS inspections FROM customs_declarations WHERE inspection_required = 1"),
("E39", ["COUNT", "WHERE"], "One value: tracking events with event_code 'DLV'.",
 "SELECT COUNT(*) AS dlv_scans FROM tracking_events WHERE event_code = 'DLV'"),
("E40", ["MAX"], "One value: the highest temperature_c reading in tracking events.",
 "SELECT MAX(temperature_c) AS max_reading_c FROM tracking_events"),
]

MODERATE = [
("M01", ["LEFT JOIN", "GROUP BY"], "Columns: airline name, number of aircraft (any status); all airlines; ordered by count DESC, name.",
 """SELECT al.name AS airline_name, COUNT(a.aircraft_id) AS aircraft
FROM airlines al LEFT JOIN aircraft a ON a.airline_id = al.airline_id
GROUP BY al.airline_id, al.name ORDER BY aircraft DESC, airline_name"""),
("M02", ["JOIN", "GROUP BY"], "Columns: model, number of aircraft with status 'active'; models without active aircraft are omitted; ordered by model.",
 """SELECT t.model, COUNT(*) AS active_aircraft
FROM aircraft a JOIN aircraft_types t ON t.type_id = a.type_id
WHERE a.status = 'active' GROUP BY t.type_id, t.model ORDER BY t.model"""),
("M03", ["JOIN", "COUNT"], "One value: completed flights whose origin airport is IST.",
 """SELECT COUNT(*) AS completed_ist_departures
FROM flights f JOIN airports a ON a.airport_id = f.origin_airport_id
WHERE a.iata_code = 'IST' AND f.status = 'completed'"""),
("M04", ["JOIN x2", "GROUP BY", "LIMIT"], "Columns: origin IATA, destination IATA, completed flights; the 5 directed routes with most completed flights (ties by origin, destination).",
 """SELECT o.iata_code AS origin, d.iata_code AS destination, COUNT(*) AS completed_flights
FROM flights f JOIN airports o ON o.airport_id = f.origin_airport_id JOIN airports d ON d.airport_id = f.destination_airport_id
WHERE f.status = 'completed'
GROUP BY o.iata_code, d.iata_code ORDER BY completed_flights DESC, origin, destination LIMIT 5"""),
("M05", ["multi-hop join", "date arithmetic", "AVG"], "Columns: airline name, average arrival delay in minutes (actual - scheduled arrival, completed flights, early = negative), rounded to 1 decimal; ordered by delay DESC, airline name.",
 """SELECT al.name AS airline_name,
       ROUND(AVG((julianday(f.actual_arrival) - julianday(f.scheduled_arrival)) * 1440), 1) AS avg_arrival_delay_min
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN airlines al ON al.airline_id = a.airline_id
WHERE f.status = 'completed' GROUP BY al.airline_id, al.name ORDER BY avg_arrival_delay_min DESC, airline_name"""),
("M06", ["multi-hop join", "GROUP BY"], "Columns: airline name, number of cancelled flights; ordered by count DESC, name.",
 """SELECT al.name AS airline_name, COUNT(*) AS cancelled_flights
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN airlines al ON al.airline_id = a.airline_id
WHERE f.status = 'cancelled' GROUP BY al.airline_id, al.name ORDER BY cancelled_flights DESC, airline_name"""),
("M07", ["multi-hop join", "SUM", "unit conversion"], "Columns: airline name, CO2 in tonnes (SUM(co2_emissions_kg)/1000 over its fuel uplifts), rounded to 1 decimal; ordered DESC.",
 """SELECT al.name AS airline_name, ROUND(SUM(u.co2_emissions_kg) / 1000.0, 1) AS co2_tonnes
FROM fuel_uplifts u JOIN flights f ON f.flight_id = u.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN airlines al ON al.airline_id = a.airline_id
GROUP BY al.airline_id, al.name ORDER BY co2_tonnes DESC, airline_name"""),
("M08", ["JOIN", "AVG"], "Columns: airport region, AVG(price_usd_per_litre) of fuel uplifts at airports in that region, rounded to 4 decimals; ordered DESC.",
 """SELECT ap.region, ROUND(AVG(u.price_usd_per_litre), 4) AS avg_price_usd_per_litre
FROM fuel_uplifts u JOIN airports ap ON ap.airport_id = u.airport_id
GROUP BY ap.region ORDER BY avg_price_usd_per_litre DESC, ap.region"""),
("M09", ["JOIN", "GROUP BY", "HAVING"], "Columns: iata_code, number of warehouses; only airports with at least 4 warehouses; ordered by iata_code.",
 """SELECT a.iata_code, COUNT(*) AS warehouses
FROM warehouses w JOIN airports a ON a.airport_id = w.airport_id
GROUP BY a.airport_id, a.iata_code HAVING COUNT(*) >= 4 ORDER BY a.iata_code"""),
("M10", ["JOIN", "GROUP BY", "HAVING"], "Columns: iata_code, number of bonded warehouses; only airports with more than one; ordered by iata_code.",
 """SELECT a.iata_code, COUNT(*) AS bonded_warehouses
FROM warehouses w JOIN airports a ON a.airport_id = w.airport_id
WHERE w.is_bonded = 1 GROUP BY a.airport_id, a.iata_code HAVING COUNT(*) > 1 ORDER BY a.iata_code"""),
("M11", ["JOIN", "GROUP BY"], "Columns: base airport iata_code, number of active crew members based there; ordered by count DESC, iata_code.",
 """SELECT a.iata_code, COUNT(*) AS active_crew
FROM crew_members m JOIN airports a ON a.airport_id = m.base_airport_id
WHERE m.is_active = 1 GROUP BY a.airport_id, a.iata_code ORDER BY active_crew DESC, a.iata_code"""),
("M12", ["GROUP BY", "AVG"], "Columns: duty_role, AVG(per_diem_usd) rounded to 2 decimals; ordered by duty_role.",
 """SELECT duty_role, ROUND(AVG(per_diem_usd), 2) AS avg_per_diem_usd
FROM crew_assignments GROUP BY duty_role ORDER BY duty_role"""),
("M13", ["multi-hop join", "date arithmetic", "SUM"], "Columns: airline name, total actual block hours (actual arrival - actual departure) of completed flights, rounded to 1 decimal; ordered DESC.",
 """SELECT al.name AS airline_name,
       ROUND(SUM((julianday(f.actual_arrival) - julianday(f.actual_departure)) * 24), 1) AS block_hours
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN airlines al ON al.airline_id = a.airline_id
WHERE f.status = 'completed' GROUP BY al.airline_id, al.name ORDER BY block_hours DESC, airline_name"""),
("M14", ["GROUP BY", "SUM", "expression"], "Columns: check_type, number of completed records, total cost (parts + labour) rounded to 2 decimals; ordered by cost DESC.",
 """SELECT check_type, COUNT(*) AS completed_records, ROUND(SUM(parts_cost_usd + labor_cost_usd), 2) AS total_cost_usd
FROM maintenance_records WHERE status = 'completed' GROUP BY check_type ORDER BY total_cost_usd DESC, check_type"""),
("M15", ["NOT EXISTS", "anti-join"], "Column: tail_number of aircraft without any maintenance record; ordered.",
 """SELECT a.tail_number FROM aircraft a
WHERE NOT EXISTS (SELECT 1 FROM maintenance_records m WHERE m.aircraft_id = a.aircraft_id) ORDER BY a.tail_number"""),
("M16", ["JOIN", "GROUP BY", "HAVING"], "Columns: customer name, country, number of non-cancelled shipments; only customers with more than 100; ordered by count DESC, customer_id.",
 """SELECT c.name, c.country, COUNT(*) AS shipments
FROM customers c JOIN shipments s ON s.customer_id = c.customer_id
WHERE s.status <> 'cancelled' GROUP BY c.customer_id, c.name, c.country HAVING COUNT(*) > 100
ORDER BY shipments DESC, c.customer_id"""),
("M17", ["GROUP BY", "AVG"], "Columns: commodity_category, AVG(chargeable_weight_kg) of delivered shipments, rounded to 1 decimal; ordered by category.",
 """SELECT commodity_category, ROUND(AVG(chargeable_weight_kg), 1) AS avg_chargeable_kg
FROM shipments WHERE status = 'delivered' GROUP BY commodity_category ORDER BY commodity_category"""),
("M18", ["multi-hop join", "SUM"], "Columns: customer sales_region, SUM(invoice amount_usd) rounded to 2 decimals; ordered DESC.",
 """SELECT c.sales_region, ROUND(SUM(i.amount_usd), 2) AS invoiced_usd
FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
GROUP BY c.sales_region ORDER BY invoiced_usd DESC, c.sales_region"""),
("M19", ["JOIN", "GROUP BY"], "Columns: origin iata_code, number of dangerous-goods shipments (any status) from there; ordered by count DESC, iata_code.",
 """SELECT a.iata_code, COUNT(*) AS dg_shipments
FROM shipments s JOIN airports a ON a.airport_id = s.origin_airport_id
WHERE s.is_dangerous_goods = 1 GROUP BY a.airport_id, a.iata_code ORDER BY dg_shipments DESC, a.iata_code"""),
("M20", ["GROUP BY", "COUNT", "SUM"], "Columns: method, number of payments, SUM(amount_usd) rounded to 2 decimals; ordered by method.",
 """SELECT method, COUNT(*) AS payments, ROUND(SUM(amount_usd), 2) AS total_usd
FROM payments GROUP BY method ORDER BY method"""),
("M21", ["GROUP BY", "WHERE"], "Columns: sent_via, number of invoices with status 'paid'; ordered by sent_via.",
 "SELECT sent_via, COUNT(*) AS paid_invoices FROM invoices WHERE status = 'paid' GROUP BY sent_via ORDER BY sent_via"),
("M22", ["JOIN", "date arithmetic", "AVG"], "Columns: payment method, average days between invoice issued_date and payment_date over all payments, rounded to 1 decimal; ordered by method.",
 """SELECT p.method, ROUND(AVG(julianday(p.payment_date) - julianday(i.issued_date)), 1) AS avg_days_to_pay
FROM payments p JOIN invoices i ON i.invoice_id = p.invoice_id GROUP BY p.method ORDER BY p.method"""),
("M23", ["JOIN", "GROUP BY", "conditional aggregation"], "Columns: customer name, number of unpaid invoices (status 'unpaid'); only customers with at least 20; ordered by count DESC, customer_id.",
 """SELECT c.name, COUNT(*) AS unpaid_invoices
FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
WHERE i.status = 'unpaid' GROUP BY c.customer_id, c.name HAVING COUNT(*) >= 20 ORDER BY unpaid_invoices DESC, c.customer_id"""),
("M24", ["JOIN", "GROUP BY", "LIMIT"], "Columns: iata_code, number of incidents reported at that airport; top 5 by count (ties by iata_code).",
 """SELECT a.iata_code, COUNT(*) AS incidents
FROM incidents i JOIN airports a ON a.airport_id = i.airport_id
GROUP BY a.airport_id, a.iata_code ORDER BY incidents DESC, a.iata_code LIMIT 5"""),
("M25", ["multi-hop join", "GROUP BY"], "Columns: commodity_category, number of incidents on its shipments' legs; ordered by count DESC, category.",
 """SELECT s.commodity_category, COUNT(*) AS incidents
FROM incidents i JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN shipments s ON s.shipment_id = fc.shipment_id
GROUP BY s.commodity_category ORDER BY incidents DESC, s.commodity_category"""),
("M26", ["GROUP BY", "SUM", "WHERE"], "Columns: insurer_name, number of paid claims, SUM(approved_amount_usd) of them rounded to 2 decimals; ordered by insurer.",
 """SELECT insurer_name, COUNT(*) AS paid_claims, ROUND(SUM(approved_amount_usd), 2) AS paid_out_usd
FROM insurance_claims WHERE status = 'paid' GROUP BY insurer_name ORDER BY insurer_name"""),
("M27", ["conditional aggregation", "percentages"], "Columns: coverage_type, number of claims, rejection rate in percent (rejected / all claims * 100) rounded to 1 decimal; ordered by coverage_type.",
 """SELECT coverage_type, COUNT(*) AS claims,
       ROUND(100.0 * SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) / COUNT(*), 1) AS rejection_rate_pct
FROM insurance_claims GROUP BY coverage_type ORDER BY coverage_type"""),
("M28", ["JOIN", "GROUP BY", "SUM"], "Columns: commodity_category, SUM(duty_amount_usd) over import declarations (any status), rounded to 2 decimals; ordered DESC.",
 """SELECT s.commodity_category, ROUND(SUM(d.duty_amount_usd), 2) AS import_duty_usd
FROM customs_declarations d JOIN shipments s ON s.shipment_id = d.shipment_id
WHERE d.declaration_type = 'import' GROUP BY s.commodity_category ORDER BY import_duty_usd DESC, s.commodity_category"""),
("M29", ["GROUP BY", "AND"], "Columns: broker_name, number of cleared import declarations; ordered by count DESC, broker.",
 """SELECT broker_name, COUNT(*) AS cleared_imports FROM customs_declarations
WHERE declaration_type = 'import' AND status = 'cleared' GROUP BY broker_name ORDER BY cleared_imports DESC, broker_name"""),
("M30", ["date arithmetic", "AVG", "HAVING"], "Columns: customs_country, number of cleared exports, average clearance hours (submitted to cleared) rounded to 2 decimals; countries with at least 100 cleared exports; ordered by hours DESC.",
 """SELECT customs_country, COUNT(*) AS cleared_exports,
       ROUND(AVG((julianday(cleared_at) - julianday(submitted_at)) * 24), 2) AS avg_clearance_hours
FROM customs_declarations WHERE declaration_type = 'export' AND status = 'cleared'
GROUP BY customs_country HAVING COUNT(*) >= 100 ORDER BY avg_clearance_hours DESC, customs_country"""),
("M31", ["JOIN", "GROUP BY"], "Columns: warehouse_type, number of RCS (received-from-shipper) tracking events at warehouses of that type; ordered by type.",
 """SELECT w.warehouse_type, COUNT(*) AS rcs_scans
FROM tracking_events e JOIN warehouses w ON w.warehouse_id = e.warehouse_id
WHERE e.event_code = 'RCS' GROUP BY w.warehouse_type ORDER BY w.warehouse_type"""),
("M32", ["GROUP BY", "AVG"], "Columns: service_level, AVG(pieces) over all shipments rounded to 2 decimals; ordered by service_level.",
 "SELECT service_level, ROUND(AVG(pieces), 2) AS avg_pieces FROM shipments GROUP BY service_level ORDER BY service_level"),
("M33", ["JOIN", "date filtering", "GROUP BY"], "Columns: tail_number, number of flights (any status) scheduled to depart in December 2025; ordered by tail_number.",
 """SELECT a.tail_number, COUNT(*) AS december_flights
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
WHERE f.scheduled_departure >= '2025-12-01' AND f.scheduled_departure < '2026-01-01'
GROUP BY a.aircraft_id, a.tail_number ORDER BY a.tail_number"""),
("M34", ["CTE", "AVG of counts"], "Columns: model, average number of shipments per flight over flights that carry at least one shipment, rounded to 2 decimals; ordered by model.",
 """WITH n AS (SELECT flight_id, COUNT(*) AS shipments FROM flight_cargo GROUP BY flight_id)
SELECT t.model, ROUND(AVG(n.shipments), 2) AS avg_shipments_per_flight
FROM n JOIN flights f ON f.flight_id = n.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id GROUP BY t.type_id, t.model ORDER BY t.model"""),
("M35", ["JOIN", "GROUP BY", "SUM"], "Columns: deck, SUM(total_weight_kg) of shipments on flown legs on that deck, rounded to 1 decimal; ordered by deck.",
 """SELECT fc.deck, ROUND(SUM(s.total_weight_kg), 1) AS kg_flown
FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE fc.leg_status = 'flown' GROUP BY fc.deck ORDER BY fc.deck"""),
("M36", ["GROUP BY", "date arithmetic"], "Columns: delay_code, number of flights, average departure delay in minutes rounded to 1 decimal; flights with a delay code only; ordered by delay_code.",
 """SELECT delay_code, COUNT(*) AS flights,
       ROUND(AVG((julianday(actual_departure) - julianday(scheduled_departure)) * 1440), 1) AS avg_delay_min
FROM flights WHERE delay_code IS NOT NULL GROUP BY delay_code ORDER BY delay_code"""),
("M37", ["GROUP BY", "COUNT", "SUM"], "Columns: sales_region, number of customers, SUM(credit_limit_usd); ordered by sales_region.",
 """SELECT sales_region, COUNT(*) AS customers, SUM(credit_limit_usd) AS total_credit_limit_usd
FROM customers GROUP BY sales_region ORDER BY sales_region"""),
("M38", ["JOIN", "GROUP BY"], "Columns: crew_rank, number of active crew members type-rated on the '747-8F'; ordered by rank.",
 """SELECT m.crew_rank, COUNT(*) AS rated_crew
FROM crew_members m JOIN aircraft_types t ON t.type_id = m.type_rating_id
WHERE t.model = '747-8F' AND m.is_active = 1 GROUP BY m.crew_rank ORDER BY m.crew_rank"""),
("M39", ["NOT EXISTS", "anti-join"], "Column: iata_code of airports with no warehouse of type 'cold_chain'; ordered.",
 """SELECT a.iata_code FROM airports a
WHERE NOT EXISTS (SELECT 1 FROM warehouses w WHERE w.airport_id = a.airport_id AND w.warehouse_type = 'cold_chain')
ORDER BY a.iata_code"""),
("M40", ["GROUP BY", "SUM"], "Columns: supplier_name, SUM(quantity_litres) supplied; ordered by litres DESC.",
 """SELECT supplier_name, SUM(quantity_litres) AS litres
FROM fuel_uplifts GROUP BY supplier_name ORDER BY litres DESC, supplier_name"""),
]

HARD = [
("H01", ["CTE", "ROW_NUMBER", "tie-breaking"], "Columns: airline name, tail_number, completed flights: per airline the aircraft with most completed flights (ties: smaller tail_number); ordered by airline name.",
 """WITH c AS (
  SELECT a.airline_id, a.tail_number, COUNT(*) AS completed_flights
  FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
  WHERE f.status = 'completed' GROUP BY a.aircraft_id, a.airline_id, a.tail_number
), r AS (
  SELECT c.*, ROW_NUMBER() OVER (PARTITION BY airline_id ORDER BY completed_flights DESC, tail_number) AS rn FROM c
)
SELECT al.name AS airline_name, r.tail_number, r.completed_flights
FROM r JOIN airlines al ON al.airline_id = r.airline_id WHERE r.rn = 1 ORDER BY airline_name"""),
("H02", ["CTE", "ROW_NUMBER", "multi-hop join"], "Columns: destination iata_code, airline name, completed arrivals: per destination airport the airline with most completed arrivals (ties: airline name); ordered by iata_code.",
 """WITH c AS (
  SELECT f.destination_airport_id AS ap, a.airline_id, COUNT(*) AS arrivals
  FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
  WHERE f.status = 'completed' GROUP BY f.destination_airport_id, a.airline_id
), r AS (
  SELECT c.ap, al.name, c.arrivals,
         ROW_NUMBER() OVER (PARTITION BY c.ap ORDER BY c.arrivals DESC, al.name) AS rn
  FROM c JOIN airlines al ON al.airline_id = c.airline_id
)
SELECT ap.iata_code, r.name AS airline_name, r.arrivals AS completed_arrivals
FROM r JOIN airports ap ON ap.airport_id = r.ap WHERE r.rn = 1 ORDER BY ap.iata_code"""),
("H03", ["window SUM", "running total", "date functions"], "Columns: month 'YYYY-MM' of issued_date, invoiced amount that month, running total since January; both rounded to 2 decimals; 2025 only; ordered by month.",
 """WITH m AS (
  SELECT substr(issued_date, 1, 7) AS month, SUM(amount_usd) AS invoiced
  FROM invoices WHERE issued_date >= '2025-01-01' AND issued_date < '2026-01-01' GROUP BY substr(issued_date, 1, 7)
)
SELECT month, ROUND(invoiced, 2) AS invoiced_usd, ROUND(SUM(invoiced) OVER (ORDER BY month), 2) AS cumulative_usd
FROM m ORDER BY month"""),
("H04", ["LAG", "month over month"], "Columns: month 'YYYY-MM' of actual_departure, completed flights, change versus the previous month (NULL for the first month); ordered by month.",
 """WITH m AS (
  SELECT substr(actual_departure, 1, 7) AS month, COUNT(*) AS completed_flights
  FROM flights WHERE status = 'completed' GROUP BY substr(actual_departure, 1, 7)
)
SELECT month, completed_flights, completed_flights - LAG(completed_flights) OVER (ORDER BY month) AS change_vs_previous
FROM m ORDER BY month"""),
("H05", ["LAG", "CTE", "date arithmetic", "LIMIT"], "Columns: tail_number, average ground time in hours between an aircraft's completed flight's actual arrival and its next completed flight's actual departure, rounded to 1 decimal; the 5 aircraft with the shortest average; ties by tail_number.",
 """WITH s AS (
  SELECT aircraft_id, actual_departure,
         LAG(actual_arrival) OVER (PARTITION BY aircraft_id ORDER BY actual_departure) AS prev_arrival
  FROM flights WHERE status = 'completed'
)
SELECT a.tail_number, ROUND(AVG((julianday(s.actual_departure) - julianday(s.prev_arrival)) * 24), 1) AS avg_ground_hours
FROM s JOIN aircraft a ON a.aircraft_id = s.aircraft_id
WHERE s.prev_arrival IS NOT NULL
GROUP BY a.aircraft_id, a.tail_number ORDER BY avg_ground_hours ASC, a.tail_number LIMIT 5"""),
("H06", ["CTE", "share of total", "scalar subquery"], "Columns: customer name, invoiced USD (rounded 2), share of all invoiced revenue in percent (rounded 2); customers with share above 4%; ordered by share DESC.",
 """WITH r AS (
  SELECT s.customer_id, SUM(i.amount_usd) AS revenue
  FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id GROUP BY s.customer_id
)
SELECT c.name, ROUND(r.revenue, 2) AS invoiced_usd,
       ROUND(100.0 * r.revenue / (SELECT SUM(amount_usd) FROM invoices), 2) AS share_pct
FROM r JOIN customers c ON c.customer_id = r.customer_id
WHERE 100.0 * r.revenue / (SELECT SUM(amount_usd) FROM invoices) > 4
ORDER BY share_pct DESC"""),
("H07", ["CTE", "DENSE_RANK", "multi-hop join"], "Columns: rank (DENSE_RANK by tonnes), origin iata_code, tonnes of cargo departing on flown legs (SUM(total_weight_kg)/1000, rounded 1); airports ranked 1-5; ordered by rank, iata_code.",
 """WITH t AS (
  SELECT f.origin_airport_id AS ap, SUM(s.total_weight_kg) / 1000.0 AS tonnes
  FROM flight_cargo fc JOIN flights f ON f.flight_id = fc.flight_id JOIN shipments s ON s.shipment_id = fc.shipment_id
  WHERE fc.leg_status = 'flown' GROUP BY f.origin_airport_id
), r AS (SELECT ap, tonnes, DENSE_RANK() OVER (ORDER BY tonnes DESC) AS rnk FROM t)
SELECT r.rnk AS tonnage_rank, a.iata_code, ROUND(r.tonnes, 1) AS tonnes
FROM r JOIN airports a ON a.airport_id = r.ap WHERE r.rnk <= 5 ORDER BY r.rnk, a.iata_code"""),
("H08", ["CTE", "join multiplication", "capacity ratio"], "Columns: model, number of completed flights whose loaded volume (sum of shipment total_volume_m3) exceeded 50% of the type's max_volume_m3; models with none omitted; ordered by model.",
 """WITH v AS (
  SELECT fc.flight_id, SUM(s.total_volume_m3) AS m3
  FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id GROUP BY fc.flight_id
)
SELECT t.model, COUNT(*) AS half_full_flights
FROM v JOIN flights f ON f.flight_id = v.flight_id AND f.status = 'completed'
JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
WHERE v.m3 > 0.5 * t.max_volume_m3 GROUP BY t.type_id, t.model ORDER BY t.model"""),
("H09", ["relational division", "COUNT DISTINCT", "scalar subquery"], "Column: tail_number of aircraft whose completed flights landed at every airport flagged as a cargo hub; ordered by tail_number.",
 """SELECT a.tail_number
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN airports p ON p.airport_id = f.destination_airport_id
WHERE f.status = 'completed' AND p.is_cargo_hub = 1
GROUP BY a.aircraft_id, a.tail_number
HAVING COUNT(DISTINCT p.airport_id) = (SELECT COUNT(*) FROM airports WHERE is_cargo_hub = 1) ORDER BY a.tail_number"""),
("H10", ["expression filter", "GROUP BY"], "Columns: customs_country, number of import declarations whose duty + VAT exceeds 20% of the customs value; countries with none omitted; ordered by count DESC, country.",
 """SELECT customs_country, COUNT(*) AS high_tax_imports
FROM customs_declarations
WHERE declaration_type = 'import' AND duty_amount_usd + vat_amount_usd > 0.2 * customs_value_usd
GROUP BY customs_country ORDER BY high_tax_imports DESC, customs_country"""),
("H11", ["self-join on events", "date arithmetic", "HAVING", "LIMIT"], "Columns: warehouse_code, delivered shipments, average hours between the RCF and DLV events of the same shipment at that warehouse (rounded 2); warehouses with at least 20 such shipments; the 3 with the longest average.",
 """SELECT w.warehouse_code, COUNT(*) AS deliveries,
       ROUND(AVG((julianday(d.event_time) - julianday(r.event_time)) * 24), 2) AS avg_dwell_hours
FROM tracking_events r
JOIN tracking_events d ON d.shipment_id = r.shipment_id AND d.event_code = 'DLV'
JOIN warehouses w ON w.warehouse_id = r.warehouse_id
WHERE r.event_code = 'RCF'
GROUP BY w.warehouse_id, w.warehouse_code HAVING COUNT(*) >= 20
ORDER BY avg_dwell_hours DESC, w.warehouse_code LIMIT 3"""),
("H12", ["CTE", "MIN per group", "date arithmetic", "LIMIT"], "Columns: origin iata_code, average hours between a shipment's RCS scan and its first DEP event (rounded 2); shipments that departed only; the 5 airports with the longest average.",
 """WITH t AS (
  SELECT shipment_id,
         MIN(CASE WHEN event_code = 'RCS' THEN event_time END) AS rcs,
         MIN(CASE WHEN event_code = 'DEP' THEN event_time END) AS dep
  FROM tracking_events GROUP BY shipment_id
)
SELECT a.iata_code, ROUND(AVG((julianday(t.dep) - julianday(t.rcs)) * 24), 2) AS avg_hours_rcs_to_departure
FROM t JOIN shipments s ON s.shipment_id = t.shipment_id JOIN airports a ON a.airport_id = s.origin_airport_id
WHERE t.rcs IS NOT NULL AND t.dep IS NOT NULL
GROUP BY a.airport_id, a.iata_code ORDER BY avg_hours_rcs_to_departure DESC, a.iata_code LIMIT 5"""),
("H13", ["ROW_NUMBER", "multi-hop join"], "Columns: model, work_order_number, cost (parts + labour, rounded 2): per aircraft model the most expensive completed maintenance record; ordered by model.",
 """WITH m AS (
  SELECT t.model, r.work_order_number, r.parts_cost_usd + r.labor_cost_usd AS cost,
         ROW_NUMBER() OVER (PARTITION BY t.type_id ORDER BY r.parts_cost_usd + r.labor_cost_usd DESC, r.work_order_number) AS rn
  FROM maintenance_records r JOIN aircraft a ON a.aircraft_id = r.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
  WHERE r.status = 'completed'
)
SELECT model, work_order_number, ROUND(cost, 2) AS cost_usd FROM m WHERE rn = 1 ORDER BY model"""),
("H14", ["conditional aggregation", "percentages", "multi-hop join"], "Columns: airline name, completed flights, percentage departing more than 15 minutes late (rounded 1); ordered by percentage DESC.",
 """SELECT al.name AS airline_name, COUNT(*) AS completed_flights,
       ROUND(100.0 * SUM(CASE WHEN (julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 1440 > 15 THEN 1 ELSE 0 END) / COUNT(*), 1) AS late_departure_pct
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN airlines al ON al.airline_id = a.airline_id
WHERE f.status = 'completed' GROUP BY al.airline_id, al.name ORDER BY late_departure_pct DESC, airline_name"""),
("H15", ["multi-hop join", "ratio", "AVG"], "Columns: loyalty_tier, average discount as a percentage of the pre-discount total (discount / (amount + discount) * 100) per invoice, rounded 2; ordered by tier.",
 """SELECT c.loyalty_tier, ROUND(AVG(100.0 * i.discount_usd / (i.amount_usd + i.discount_usd)), 2) AS avg_discount_pct
FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
GROUP BY c.loyalty_tier ORDER BY c.loyalty_tier"""),
("H16", ["multi-hop join", "cross-table comparison"], "Columns: tail_number, number of completed flights whose takeoff_weight_kg exceeded 95% of the type's max_takeoff_weight_kg; aircraft with none omitted; ordered by count DESC, tail_number.",
 """SELECT a.tail_number, COUNT(*) AS heavy_takeoffs
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
WHERE f.takeoff_weight_kg > 0.95 * t.max_takeoff_weight_kg
GROUP BY a.aircraft_id, a.tail_number ORDER BY heavy_takeoffs DESC, a.tail_number"""),
("H17", ["conditional aggregation", "date filtering"], "Columns: original_currency, average exchange_rate_to_usd for payments dated January-June 2025 and July-December 2025 (each rounded 6); non-USD currencies only; ordered by currency.",
 """SELECT original_currency,
       ROUND(AVG(CASE WHEN payment_date < '2025-07-01' THEN exchange_rate_to_usd END), 6) AS avg_rate_h1,
       ROUND(AVG(CASE WHEN payment_date >= '2025-07-01' THEN exchange_rate_to_usd END), 6) AS avg_rate_h2
FROM payments WHERE original_currency <> 'USD' AND payment_date >= '2025-01-01'
GROUP BY original_currency ORDER BY original_currency"""),
("H18", ["self-join", "date arithmetic", "GROUP BY"], "Columns: connecting airport iata_code, number of two-leg shipments whose ground time there (leg 2 actual departure - leg 1 actual arrival) exceeded 48 hours; both legs flown; ordered by count DESC, iata_code.",
 """SELECT a.iata_code, COUNT(*) AS long_connections
FROM flight_cargo l1
JOIN flight_cargo l2 ON l2.shipment_id = l1.shipment_id AND l2.leg_number = 2
JOIN flights f1 ON f1.flight_id = l1.flight_id JOIN flights f2 ON f2.flight_id = l2.flight_id
JOIN airports a ON a.airport_id = f1.destination_airport_id
WHERE l1.leg_number = 1 AND f1.status = 'completed' AND f2.status = 'completed'
  AND (julianday(f2.actual_departure) - julianday(f1.actual_arrival)) * 24 > 48
GROUP BY a.airport_id, a.iata_code ORDER BY long_connections DESC, a.iata_code"""),
("H19", ["date arithmetic", "AVG", "WHERE"], "Columns: insurer_name, number of paid claims, average days from filed_date to settlement_date (rounded 1); ordered by average ASC.",
 """SELECT insurer_name, COUNT(*) AS paid_claims,
       ROUND(AVG(julianday(settlement_date) - julianday(filed_date)), 1) AS avg_days_to_settle
FROM insurance_claims WHERE status = 'paid' GROUP BY insurer_name ORDER BY avg_days_to_settle ASC, insurer_name"""),
("H20", ["self-join", "GROUP BY", "LIMIT"], "Columns: captain employee_number, first officer employee_number, completed flights flown together (captain + first_officer roles on the same flight); pairs with at least 10 flights together; ordered by count DESC, captain, first officer.",
 """SELECT mc.employee_number AS captain, mf.employee_number AS first_officer, COUNT(*) AS flights_together
FROM crew_assignments c
JOIN crew_assignments fo ON fo.flight_id = c.flight_id AND fo.duty_role = 'first_officer'
JOIN crew_members mc ON mc.crew_member_id = c.crew_member_id JOIN crew_members mf ON mf.crew_member_id = fo.crew_member_id
WHERE c.duty_role = 'captain' AND c.assignment_status = 'completed'
GROUP BY mc.employee_number, mf.employee_number HAVING COUNT(*) >= 10 ORDER BY flights_together DESC, captain, first_officer"""),
("H21", ["conditional aggregation", "HAVING", "quarters"], "Columns: origin iata_code, completed departures in Q3 2025 (Jul-Sep, by actual_departure), in Q4 2025 (Oct-Dec); airports where Q4 > Q3; ordered by iata_code.",
 """SELECT a.iata_code,
       SUM(CASE WHEN f.actual_departure >= '2025-07-01' AND f.actual_departure < '2025-10-01' THEN 1 ELSE 0 END) AS q3_departures,
       SUM(CASE WHEN f.actual_departure >= '2025-10-01' AND f.actual_departure < '2026-01-01' THEN 1 ELSE 0 END) AS q4_departures
FROM flights f JOIN airports a ON a.airport_id = f.origin_airport_id
WHERE f.status = 'completed'
GROUP BY a.airport_id, a.iata_code
HAVING q4_departures > q3_departures ORDER BY a.iata_code"""),
("H22", ["NOT EXISTS", "date window", "multi-hop join"], f"Columns: customer name, number of invoices not fully paid (status unpaid or partially_paid); only customers with no payment at all in the 60 days before {AS_OF} (payment_date >= 2025-10-21); ordered by count DESC, customer_id.",
 f"""SELECT c.name, COUNT(*) AS open_invoices
FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
WHERE i.status IN ('unpaid', 'partially_paid')
  AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.customer_id = c.customer_id AND p.payment_date >= date('{AS_OF}', '-60 days'))
GROUP BY c.customer_id, c.name ORDER BY open_invoices DESC, c.customer_id"""),
("H23", ["EXISTS x2", "multi-hop join"], "Columns: model, number of flights (any status) carrying at least one dangerous-goods shipment AND at least one temperature-controlled shipment; ordered by model.",
 """SELECT t.model, COUNT(*) AS mixed_flights
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
WHERE EXISTS (SELECT 1 FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
              WHERE fc.flight_id = f.flight_id AND s.is_dangerous_goods = 1)
  AND EXISTS (SELECT 1 FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
              WHERE fc.flight_id = f.flight_id AND s.is_temperature_controlled = 1)
GROUP BY t.type_id, t.model ORDER BY t.model"""),
("H24", ["NTILE", "CTE"], "Columns: commodity_category, number of its shipments in the heaviest quarter of all shipments (NTILE(4) over total_weight_kg, ties by shipment_id); ordered by count DESC, category.",
 """WITH q AS (SELECT commodity_category, NTILE(4) OVER (ORDER BY total_weight_kg, shipment_id) AS quartile FROM shipments)
SELECT commodity_category, COUNT(*) AS heaviest_quartile_shipments
FROM q WHERE quartile = 4 GROUP BY commodity_category ORDER BY heaviest_quartile_shipments DESC, commodity_category"""),
("H25", ["date arithmetic", "MIN/MAX", "HAVING", "LIMIT"], "Columns: customer name, non-cancelled shipments, average days between bookings = (last booking_date - first booking_date) / (shipments - 1), rounded 2; customers with at least 20 such shipments; the 5 with the shortest average, ties by customer_id.",
 """SELECT c.name, COUNT(*) AS shipments,
       ROUND((julianday(MAX(s.booking_date)) - julianday(MIN(s.booking_date))) / (COUNT(*) - 1), 2) AS avg_days_between_bookings
FROM customers c JOIN shipments s ON s.customer_id = c.customer_id
WHERE s.status <> 'cancelled'
GROUP BY c.customer_id, c.name HAVING COUNT(*) >= 20
ORDER BY avg_days_between_bookings ASC, c.customer_id LIMIT 5"""),
("H26", ["SUM", "HAVING", "date filtering"], "Columns: employee_number, block hours credited (SUM(block_minutes_credited)/60, rounded 1) on completed assignments reporting in November 2025; crew above 40 hours; ordered by hours DESC, employee_number.",
 """SELECT m.employee_number, ROUND(SUM(ca.block_minutes_credited) / 60.0, 1) AS november_block_hours
FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
WHERE ca.assignment_status = 'completed' AND ca.report_time >= '2025-11-01' AND ca.report_time < '2025-12-01'
GROUP BY m.crew_member_id, m.employee_number HAVING SUM(ca.block_minutes_credited) / 60.0 > 40
ORDER BY november_block_hours DESC, m.employee_number"""),
("H27", ["multi-hop join", "conditional aggregation", "dates"], "Columns: loyalty_tier, shipments handed over (with a DLV event), on-time percentage (DLV date <= requested_delivery_date) rounded 1; ordered by tier.",
 """SELECT c.loyalty_tier, COUNT(*) AS delivered,
       ROUND(100.0 * SUM(CASE WHEN substr(e.event_time, 1, 10) <= s.requested_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS on_time_pct
FROM shipments s JOIN tracking_events e ON e.shipment_id = s.shipment_id AND e.event_code = 'DLV'
JOIN customers c ON c.customer_id = s.customer_id
GROUP BY c.loyalty_tier ORDER BY c.loyalty_tier"""),
("H28", ["conditional aggregation", "date functions", "percentages"], "Columns: booking month 'YYYY-MM', shipments booked, express share in percent (rounded 1); all bookings incl. cancelled; ordered by month.",
 """SELECT substr(booking_date, 1, 7) AS month, COUNT(*) AS bookings,
       ROUND(100.0 * SUM(CASE WHEN service_level = 'express' THEN 1 ELSE 0 END) / COUNT(*), 1) AS express_share_pct
FROM shipments GROUP BY substr(booking_date, 1, 7) ORDER BY month"""),
("H29", ["CTE", "compare with group average"], "Columns: airline name, tail_number, completed block hours (rounded 1) of aircraft whose completed block hours exceed the average of their airline's flying aircraft; ordered by airline name, hours DESC.",
 """WITH h AS (
  SELECT a.airline_id, a.tail_number, SUM((julianday(f.actual_arrival) - julianday(f.actual_departure)) * 24) AS hours
  FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
  WHERE f.status = 'completed' GROUP BY a.aircraft_id, a.airline_id, a.tail_number
), avg_h AS (SELECT airline_id, AVG(hours) AS avg_hours FROM h GROUP BY airline_id)
SELECT al.name AS airline_name, h.tail_number, ROUND(h.hours, 1) AS block_hours
FROM h JOIN avg_h ON avg_h.airline_id = h.airline_id JOIN airlines al ON al.airline_id = h.airline_id
WHERE h.hours > avg_h.avg_hours ORDER BY airline_name, block_hours DESC"""),
("H30", ["CTE", "join multiplication", "HAVING", "LIMIT"], "Columns: origin iata, destination iata, flights, average payload load factor in percent (cargo kg on the flight / max_payload_kg * 100, rounded 1) over completed flights carrying cargo; routes with at least 10 such flights; top 5 by load factor.",
 """WITH l AS (
  SELECT fc.flight_id, SUM(s.total_weight_kg) AS kg
  FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id GROUP BY fc.flight_id
)
SELECT o.iata_code AS origin, d.iata_code AS destination, COUNT(*) AS flights,
       ROUND(AVG(l.kg * 100.0 / t.max_payload_kg), 1) AS avg_load_factor_pct
FROM l JOIN flights f ON f.flight_id = l.flight_id AND f.status = 'completed'
JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
JOIN airports o ON o.airport_id = f.origin_airport_id JOIN airports d ON d.airport_id = f.destination_airport_id
GROUP BY o.iata_code, d.iata_code HAVING COUNT(*) >= 10
ORDER BY avg_load_factor_pct DESC, origin, destination LIMIT 5"""),
("H31", ["LEFT JOIN", "multi-hop join", "HAVING", "COALESCE"], "Columns: customer name, incidents on their shipments, approved claim amount on those incidents (approved or paid claims; 0 if none, rounded 2); customers with at least 4 incidents; ordered by incidents DESC, customer_id.",
 """SELECT c.name, COUNT(*) AS incidents,
       ROUND(COALESCE(SUM(CASE WHEN ic.status IN ('approved', 'paid') THEN ic.approved_amount_usd END), 0), 2) AS approved_usd
FROM incidents i
JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN shipments s ON s.shipment_id = fc.shipment_id
JOIN customers c ON c.customer_id = s.customer_id
LEFT JOIN insurance_claims ic ON ic.incident_id = i.incident_id
GROUP BY c.customer_id, c.name HAVING COUNT(*) >= 4 ORDER BY incidents DESC, c.customer_id"""),
("H32", ["LAG", "CTE", "delay propagation"], "Columns: airline name, number of completed flights departing more than 60 minutes late whose aircraft's previous completed flight arrived more than 60 minutes late; ordered by count DESC, name.",
 """WITH s AS (
  SELECT f.aircraft_id,
         (julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 1440 AS dep_delay,
         LAG((julianday(f.actual_arrival) - julianday(f.scheduled_arrival)) * 1440)
             OVER (PARTITION BY f.aircraft_id ORDER BY f.actual_departure) AS prev_arr_delay
  FROM flights f WHERE f.status = 'completed'
)
SELECT al.name AS airline_name, COUNT(*) AS knock_on_delays
FROM s JOIN aircraft a ON a.aircraft_id = s.aircraft_id JOIN airlines al ON al.airline_id = a.airline_id
WHERE s.dep_delay > 60 AND s.prev_arr_delay > 60
GROUP BY al.airline_id, al.name ORDER BY knock_on_delays DESC, airline_name"""),
("H33", ["relational division", "COUNT DISTINCT", "HAVING"], "Columns: customer_id, name of customers whose non-cancelled shipments went to every cargo-hub airport (as destination); ordered by customer_id.",
 """SELECT c.customer_id, c.name
FROM customers c JOIN shipments s ON s.customer_id = c.customer_id JOIN airports a ON a.airport_id = s.destination_airport_id
WHERE s.status <> 'cancelled' AND a.is_cargo_hub = 1
GROUP BY c.customer_id, c.name
HAVING COUNT(DISTINCT a.airport_id) = (SELECT COUNT(*) FROM airports WHERE is_cargo_hub = 1) ORDER BY c.customer_id"""),
("H34", ["MAX per group", "date arithmetic", "LIMIT"], f"Columns: tail_number, end of its latest completed maintenance, days from that end to {AS_OF} (integer); active aircraft only; the 5 with the most days, ties by tail_number.",
 f"""SELECT a.tail_number, MAX(m.end_time) AS last_maintenance_end,
       CAST(julianday('{AS_OF}') - julianday(MAX(m.end_time)) AS INTEGER) AS days_since_maintenance
FROM aircraft a JOIN maintenance_records m ON m.aircraft_id = a.aircraft_id
WHERE a.status = 'active' AND m.status = 'completed'
GROUP BY a.aircraft_id, a.tail_number ORDER BY days_since_maintenance DESC, a.tail_number LIMIT 5"""),
("H35", ["window AVG", "difference to overall", "LIMIT"], "Columns: iata_code, average fuel price per litre at that airport (rounded 4), difference from the average price over all uplifts (rounded 4); the 5 most expensive airports.",
 """WITH p AS (SELECT airport_id, AVG(price_usd_per_litre) AS avg_price FROM fuel_uplifts GROUP BY airport_id)
SELECT a.iata_code, ROUND(p.avg_price, 4) AS avg_price_usd_per_litre,
       ROUND(p.avg_price - (SELECT AVG(price_usd_per_litre) FROM fuel_uplifts), 4) AS diff_vs_network
FROM p JOIN airports a ON a.airport_id = p.airport_id ORDER BY p.avg_price DESC, a.iata_code LIMIT 5"""),
("H36", ["MAX", "GROUP BY", "LIMIT"], "Columns: employee_number, crew_rank, longest rest between two consecutive duties in hours (MAX(rest_minutes_before)/60, rounded 1); the 5 longest, ties by employee_number.",
 """SELECT m.employee_number, m.crew_rank, ROUND(MAX(ca.rest_minutes_before) / 60.0, 1) AS longest_rest_hours
FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
GROUP BY m.crew_member_id, m.employee_number, m.crew_rank
ORDER BY MAX(ca.rest_minutes_before) DESC, m.employee_number LIMIT 5"""),
("H37", ["multi-hop join", "date arithmetic", "GROUP BY"], "Columns: origin iata_code, number of cleared export declarations cleared less than 2 hours before the shipment's leg-1 actual departure; airports with none omitted; ordered by count DESC, iata_code.",
 """SELECT a.iata_code, COUNT(*) AS last_minute_clearances
FROM customs_declarations d
JOIN flight_cargo fc ON fc.shipment_id = d.shipment_id AND fc.leg_number = 1
JOIN flights f ON f.flight_id = fc.flight_id
JOIN airports a ON a.airport_id = f.origin_airport_id
WHERE d.declaration_type = 'export' AND d.status = 'cleared' AND f.status = 'completed'
  AND (julianday(f.actual_departure) - julianday(d.cleared_at)) * 24 < 2
GROUP BY a.airport_id, a.iata_code ORDER BY last_minute_clearances DESC, a.iata_code"""),
("H38", ["window SUM", "cumulative percentage"], "Columns: commodity_category, declared value of its non-cancelled shipments (rounded 2), cumulative share of the total in percent when categories are ordered by value DESC (rounded 2); ordered by value DESC.",
 """WITH v AS (SELECT commodity_category, SUM(declared_value_usd) AS value FROM shipments WHERE status <> 'cancelled' GROUP BY commodity_category)
SELECT commodity_category, ROUND(value, 2) AS declared_value_usd,
       ROUND(100.0 * SUM(value) OVER (ORDER BY value DESC) / SUM(value) OVER (), 2) AS cumulative_share_pct
FROM v ORDER BY value DESC"""),
("H39", ["CTE", "ROW_NUMBER", "HAVING"], "Columns: customer name, most frequent destination iata_code of their non-cancelled shipments, shipments to it; customers with at least 60 non-cancelled shipments; ties by iata_code; ordered by customer_id.",
 """WITH c AS (
  SELECT s.customer_id, a.iata_code, COUNT(*) AS n
  FROM shipments s JOIN airports a ON a.airport_id = s.destination_airport_id
  WHERE s.status <> 'cancelled' GROUP BY s.customer_id, a.iata_code
), r AS (
  SELECT c.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY n DESC, iata_code) AS rn,
         SUM(n) OVER (PARTITION BY customer_id) AS total
  FROM c
)
SELECT cu.name, r.iata_code AS top_destination, r.n AS shipments
FROM r JOIN customers cu ON cu.customer_id = r.customer_id
WHERE r.rn = 1 AND r.total >= 60 ORDER BY r.customer_id"""),
("H40", ["self-join", "date arithmetic", "multi-hop join"], "Columns: customer_type, invoices paid in exactly two payments, average days between the first and second payment (rounded 1); ordered by customer_type.",
 """WITH two AS (
  SELECT invoice_id, MIN(payment_date) AS first_pay, MAX(payment_date) AS second_pay
  FROM payments GROUP BY invoice_id HAVING COUNT(*) = 2
)
SELECT c.customer_type, COUNT(*) AS two_part_invoices,
       ROUND(AVG(julianday(t.second_pay) - julianday(t.first_pay)), 1) AS avg_days_between
FROM two t JOIN invoices i ON i.invoice_id = t.invoice_id JOIN shipments s ON s.shipment_id = i.shipment_id
JOIN customers c ON c.customer_id = s.customer_id
GROUP BY c.customer_type ORDER BY c.customer_type"""),
]

# ------------------------------------------------------------------ phrasings: id -> (casual, schema_aware, business_executive, vague)
TALK_EASY = {
"E01": ("How many of our airports are cargo hubs?",
        "Count the rows in [[airports]] where [[airports.is_cargo_hub]] = 1.",
        "For the network overview, how many cargo hub stations do we operate through?",
        "How many hubs are there?"),
"E02": ("Which airports have a night flight curfew? Just give me their codes.",
        "List [[airports.iata_code]] from [[airports]] where [[airports.night_curfew]] = 1, sorted by code.",
        "Which stations in our network operate under a night curfew? List the airport codes for the ops risk register.",
        "Where can't we fly at night?"),
"E03": ("Which airlines are in the CargoLink alliance?",
        "Return [[airlines.name]] from [[airlines]] where [[airlines.alliance]] = 'CargoLink', sorted by name.",
        "Which carriers belong to the CargoLink alliance partnership?",
        "Who's in CargoLink?"),
"E04": ("Which aircraft models are made by Airbus?",
        "Select [[aircraft_types.model]] from [[aircraft_types]] where [[aircraft_types.manufacturer]] = 'Airbus'.",
        "Which freighter models in our fleet mix are sourced from Airbus?",
        "Airbus models?"),
"E05": ("How many of the planes are leased instead of owned?",
        "How many rows in [[aircraft]] have [[aircraft.ownership]] = 'leased'?",
        "How many airframes in the fleet are held on lease contracts?",
        "How many leased ones do we have?"),
"E06": ("Which planes aren't in active service right now, and what's their status?",
        "List [[aircraft.tail_number]] and [[aircraft.status]] from [[aircraft]] where [[aircraft.status]] is not 'active'.",
        "Which airframes are currently out of service, and are they in maintenance or retired?",
        "Which planes are out?"),
"E07": ("How many customers are there in each loyalty tier?",
        "Count rows of [[customers]] grouped by [[customers.loyalty_tier]].",
        "What does the customer base look like by loyalty tier? Give me the headcount per tier.",
        "Customer tiers breakdown?"),
"E08": ("Which customers are based in Germany, and in which city?",
        "Select [[customers.name]] and [[customers.city]] from [[customers]] where [[customers.country]] = 'Germany'.",
        "List our German accounts together with their home city.",
        "German customers?"),
"E09": ("How many warehouses do we have of each type?",
        "Count rows of [[warehouses]] grouped by [[warehouses.warehouse_type]].",
        "How is our warehouse footprint split across facility types?",
        "Warehouses by type?"),
"E10": ("How much floor space do the cold-chain warehouses have in total?",
        "Sum [[warehouses.floor_area_m2]] in [[warehouses]] where [[warehouses.warehouse_type]] = 'cold_chain'.",
        "What is our total cold-chain warehouse footprint in square metres?",
        "How big is the cold chain space?"),
"E11": ("How many captains are currently active?",
        "Count rows in [[crew_members]] with [[crew_members.crew_rank]] = 'captain' and [[crew_members.is_active]] = 1.",
        "What is our active captain headcount?",
        "How many captains are working for us?"),
"E12": ("On average, how many flight hours do our first officers have?",
        "Average [[crew_members.total_flight_hours]] over [[crew_members]] rows with [[crew_members.crew_rank]] = 'first_officer', rounded to 1 decimal.",
        "What is the average experience level, in flight hours, of our first officer pool?",
        "How experienced are the first officers?"),
"E13": ("How many charter flights are there?",
        "Count rows in [[flights]] where [[flights.flight_type]] = 'charter'.",
        "How many charter flights are in the programme, all statuses included?",
        "Charters, how many?"),
"E14": ("What's the longest flight distance we have, in km?",
        "Return MAX([[flights.distance_km]]) from [[flights]].",
        "What is the longest sector length in our flight programme, in kilometres?",
        "Longest flight?"),
"E15": ("How many flights got cancelled because of technical problems?",
        "Count [[flights]] with [[flights.status]] = 'cancelled' and [[flights.cancellation_reason]] = 'technical'.",
        "How many cancellations were driven by technical issues?",
        "Technical cancellations?"),
"E16": ("How many flights had a thunderstorm at departure?",
        "Count rows in [[flights]] where [[flights.weather_at_departure]] = 'thunderstorm'.",
        "How many flights were exposed to thunderstorm conditions at departure?",
        "How many thunderstorm flights?"),
"E17": ("How many crew duties needed a hotel stay?",
        "Count rows in [[crew_assignments]] with [[crew_assignments.hotel_required]] = 1.",
        "How many crew assignments triggered a hotel requirement?",
        "Hotel nights?"),
"E18": ("How many times was a plane grounded unexpectedly (AOG)?",
        "Count rows in [[maintenance_records]] where [[maintenance_records.is_aog]] = 1.",
        "How many aircraft-on-ground events have we recorded?",
        "How many AOGs?"),
"E19": ("How much did we spend on parts for finished unscheduled repairs?",
        "Sum [[maintenance_records.parts_cost_usd]] over [[maintenance_records]] where [[maintenance_records.check_type]] = 'unscheduled' and [[maintenance_records.status]] = 'completed', rounded to 2 decimals.",
        "What was the total parts spend on completed unscheduled maintenance, in USD?",
        "Parts cost for unscheduled work?"),
"E20": ("How many times was fuel delivered by truck?",
        "Count rows in [[fuel_uplifts]] where [[fuel_uplifts.delivery_method]] = 'truck'.",
        "How many fuel uplifts relied on truck delivery rather than hydrant?",
        "Truck fuelling count?"),
"E21": ("What's the average fuel density we got, in kg per litre?",
        "Average [[fuel_uplifts.density_kg_per_l]] over [[fuel_uplifts]], rounded to 3 decimals.",
        "What is the average fuel density across all uplifts?",
        "Typical fuel density?"),
"E22": ("How many litres of Jet A did we load in total?",
        "Sum [[fuel_uplifts.quantity_litres]] in [[fuel_uplifts]] where [[fuel_uplifts.fuel_type]] = 'Jet A'.",
        "What is our total Jet A volume uplifted, in litres?",
        "How much Jet A?"),
"E23": ("How many express shipments are there?",
        "Count rows in [[shipments]] where [[shipments.service_level]] = 'express'.",
        "How many bookings came in on the express product?",
        "Express count?"),
"E24": ("What's the heaviest shipment we've had, in kg?",
        "Return MAX([[shipments.total_weight_kg]]) from [[shipments]].",
        "What is the largest single consignment weight on record?",
        "Heaviest one?"),
"E25": ("How many shipments need temperature control?",
        "Count rows in [[shipments]] where [[shipments.is_temperature_controlled]] = 1.",
        "How many consignments fall into our temperature-controlled product?",
        "How many cool shipments?"),
"E26": ("What's the average declared value of an electronics shipment?",
        "Average [[shipments.declared_value_usd]] for [[shipments]] with [[shipments.commodity_category]] = 'electronics', rounded to 2 decimals.",
        "What is the average declared value per electronics consignment, in USD?",
        "How valuable are electronics shipments?"),
"E27": ("How many shipment legs were loaded on the lower deck?",
        "Count rows in [[flight_cargo]] where [[flight_cargo.deck]] = 'lower'.",
        "How many cargo legs used lower-deck capacity?",
        "Lower deck loads?"),
"E28": ("How many shipment legs went as loose bulk cargo?",
        "Count rows in [[flight_cargo]] where [[flight_cargo.uld_type]] = 'BULK'.",
        "How many legs were handled as bulk rather than in a ULD?",
        "How much bulk?"),
"E29": ("How many invoices were sent by EDI?",
        "Count rows in [[invoices]] where [[invoices.sent_via]] = 'edi'.",
        "How many invoices went out through the EDI channel?",
        "EDI invoices?"),
"E30": ("How much discount have we given on invoices in total?",
        "Sum [[invoices.discount_usd]] over [[invoices]], rounded to 2 decimals.",
        "What is the total value of discounts granted on our invoices, in USD?",
        "Total discounts?"),
"E31": ("How many payments were made by credit card?",
        "Count rows in [[payments]] where [[payments.method]] = 'credit_card'.",
        "How many customer payments came in via credit card?",
        "Card payments?"),
"E32": ("How many payments came in euros, and how many euros was that in total?",
        "Count rows in [[payments]] with [[payments.original_currency]] = 'EUR' and sum their [[payments.original_amount]], rounded to 2 decimals.",
        "What is our EUR-denominated collection volume: number of payments and total euros received?",
        "Euro payments?"),
"E33": ("How many incidents were there at each severity level?",
        "Count rows in [[incidents]] grouped by [[incidents.severity]].",
        "What is the incident profile by severity level?",
        "Incidents by severity?"),
"E34": ("How many incidents are still not resolved?",
        "Count rows in [[incidents]] where [[incidents.resolved]] = 0.",
        "How many incident cases remain open?",
        "Open incidents?"),
"E35": ("Which insurance claims were rejected? Give me the claim numbers.",
        "List [[insurance_claims.claim_number]] from [[insurance_claims]] where [[insurance_claims.status]] = 'rejected'.",
        "Which claim references were declined by insurers?",
        "Rejected claims?"),
"E36": ("What's the average amount people claim on insurance?",
        "Average [[insurance_claims.claimed_amount_usd]] over [[insurance_claims]], rounded to 2 decimals.",
        "What is the average claim size we file with insurers, in USD?",
        "Typical claim amount?"),
"E37": ("How many import declarations are being held by customs?",
        "Count rows in [[customs_declarations]] with [[customs_declarations.declaration_type]] = 'import' and [[customs_declarations.status]] = 'held'.",
        "How many inbound customs entries are currently on hold?",
        "Customs holds?"),
"E38": ("How many customs declarations needed an inspection?",
        "Count rows in [[customs_declarations]] where [[customs_declarations.inspection_required]] = 1.",
        "How many customs filings were selected for physical inspection?",
        "Inspections?"),
"E39": ("How many shipments were handed over to the receiver (DLV scans)?",
        "Count rows in [[tracking_events]] where [[tracking_events.event_code]] = 'DLV'.",
        "How many proof-of-delivery scans have we recorded?",
        "Deliveries?"),
"E40": ("What's the warmest temperature reading we've recorded on a shipment?",
        "Return MAX([[tracking_events.temperature_c]]) from [[tracking_events]].",
        "What is the highest temperature reading logged across our cold-chain tracking?",
        "Hottest reading?"),
}

TALK_MODERATE = {
"M01": ("How many planes does each airline have? Include every airline, biggest fleet first.",
        "Join [[airlines]] to [[aircraft]] on [[aircraft.airline_id]] and count aircraft per [[airlines.name]], keeping airlines without aircraft; order by count descending, then name.",
        "Give me the fleet size per carrier, largest first.",
        "Fleet per airline?"),
"M02": ("How many active planes do we have of each model?",
        "Count [[aircraft]] with [[aircraft.status]] = 'active' per [[aircraft_types.model]], joining on [[aircraft.type_id]]; order by model.",
        "What is the active fleet count by aircraft type?",
        "Active planes by model?"),
"M03": ("How many completed flights took off from Istanbul (IST)?",
        "Count [[flights]] with [[flights.status]] = 'completed' whose [[flights.origin_airport_id]] matches the [[airports]] row with [[airports.iata_code]] = 'IST'.",
        "What is our completed departure volume out of IST?",
        "How busy was IST?"),
"M04": ("What are the 5 routes with the most completed flights? Show from, to and the count.",
        "Join [[flights]] to [[airports]] twice (origin and destination), count completed flights per origin and destination [[airports.iata_code]], and return the top 5.",
        "Which five directed lanes carried the most completed flights?",
        "Top routes?"),
"M05": ("On average, how many minutes late does each airline arrive on completed flights?",
        "For [[flights]] with [[flights.status]] = 'completed', average ([[flights.actual_arrival]] - [[flights.scheduled_arrival]]) in minutes per [[airlines.name]] (via [[aircraft]]), rounded to 1 decimal, highest first.",
        "What is the average arrival delay in minutes per carrier, as an on-time performance KPI?",
        "Which airline is the latest?"),
"M06": ("How many flights did each airline cancel?",
        "Count [[flights]] with [[flights.status]] = 'cancelled' per [[airlines.name]], joining through [[aircraft]]; order by count descending.",
        "Show cancellation volume by carrier.",
        "Cancellations per airline?"),
"M07": ("How many tonnes of CO2 did each airline's flights produce?",
        "Sum [[fuel_uplifts.co2_emissions_kg]] / 1000 per [[airlines.name]], joining [[fuel_uplifts]] -> [[flights]] -> [[aircraft]] -> [[airlines]], rounded to 1 decimal.",
        "What is each carrier's carbon footprint in tonnes of CO2 for the sustainability report?",
        "Emissions by airline?"),
"M08": ("What's the average fuel price per litre in each region?",
        "Average [[fuel_uplifts.price_usd_per_litre]] per [[airports.region]] of the uplift airport, rounded to 4 decimals.",
        "How do fuel prices per litre compare across our regions?",
        "Where's fuel expensive?"),
"M09": ("Which airports have 4 or more warehouses, and how many?",
        "Count [[warehouses]] per [[airports.iata_code]] (join on [[warehouses.airport_id]]) and keep airports with COUNT >= 4.",
        "Which stations have a large warehouse footprint of at least four facilities?",
        "Airports with lots of warehouses?"),
"M10": ("Which airports have more than one bonded warehouse?",
        "Count [[warehouses]] with [[warehouses.is_bonded]] = 1 per [[airports.iata_code]] and keep counts above 1.",
        "At which stations do we have more than one customs-bonded facility?",
        "Airports with several bonded warehouses?"),
"M11": ("How many active crew members are based at each airport?",
        "Count [[crew_members]] with [[crew_members.is_active]] = 1 per base airport [[airports.iata_code]] (via [[crew_members.base_airport_id]]), most first.",
        "What is our active crew headcount per crew base?",
        "Crew per base?"),
"M12": ("What's the average per diem for each crew role?",
        "Average [[crew_assignments.per_diem_usd]] grouped by [[crew_assignments.duty_role]], rounded to 2 decimals.",
        "What is our average per diem cost per duty role?",
        "Per diems by role?"),
"M13": ("How many hours did each airline actually fly on completed flights?",
        "Sum ([[flights.actual_arrival]] - [[flights.actual_departure]]) in hours for completed [[flights]] per [[airlines.name]], rounded to 1 decimal.",
        "What is the total block-hour output per carrier?",
        "Flying hours per airline?"),
"M14": ("For finished maintenance, how many jobs and how much money per type of check?",
        "For [[maintenance_records]] with [[maintenance_records.status]] = 'completed', count rows and sum [[maintenance_records.parts_cost_usd]] + [[maintenance_records.labor_cost_usd]] per [[maintenance_records.check_type]].",
        "Break down completed maintenance spend and volume by check type, most expensive first.",
        "Maintenance cost by check?"),
"M15": ("Which planes have never had any maintenance logged?",
        "Return [[aircraft.tail_number]] for [[aircraft]] with no matching row in [[maintenance_records]].",
        "Which airframes have no maintenance history in our records?",
        "Planes without maintenance?"),
"M16": ("Which customers sent more than 100 shipments (not counting cancelled ones)?",
        "Count non-cancelled [[shipments]] per [[customers.name]] and [[customers.country]], keeping counts above 100.",
        "Who are our high-volume accounts with over 100 active shipments?",
        "Biggest customers?"),
"M17": ("For delivered shipments, what's the average chargeable weight per type of goods?",
        "Average [[shipments.chargeable_weight_kg]] per [[shipments.commodity_category]] where [[shipments.status]] = 'delivered', rounded to 1 decimal.",
        "What is the average billable weight per delivered consignment by commodity?",
        "Average weight by commodity?"),
"M18": ("How much did we invoice in each sales region?",
        "Sum [[invoices.amount_usd]] per [[customers.sales_region]], joining [[invoices]] -> [[shipments]] -> [[customers]], rounded to 2 decimals.",
        "What is invoiced revenue by sales region?",
        "Revenue by region?"),
"M19": ("How many dangerous-goods shipments start at each airport?",
        "Count [[shipments]] with [[shipments.is_dangerous_goods]] = 1 per origin [[airports.iata_code]], most first.",
        "Where does our dangerous-goods volume originate?",
        "DG by airport?"),
"M20": ("How many payments and how much money came in per payment method?",
        "Count [[payments]] and sum [[payments.amount_usd]] grouped by [[payments.method]].",
        "Show collections by payment channel: transaction count and USD value.",
        "Payments by method?"),
"M21": ("How many paid invoices went out through each sending channel?",
        "Count [[invoices]] with [[invoices.status]] = 'paid' grouped by [[invoices.sent_via]].",
        "How do fully settled invoices split across delivery channels?",
        "Paid invoices by channel?"),
"M22": ("How many days after the invoice do people pay, on average, for each payment method?",
        "Average ([[payments.payment_date]] - [[invoices.issued_date]]) in days per [[payments.method]], joining on [[payments.invoice_id]], rounded to 1 decimal.",
        "What is our average days-to-collect per payment method?",
        "How fast do people pay?"),
"M23": ("Which customers have 20 or more unpaid invoices?",
        "Count [[invoices]] with [[invoices.status]] = 'unpaid' per [[customers.name]] (via [[shipments]]) and keep counts >= 20.",
        "Which accounts carry at least 20 unpaid invoices?",
        "Who owes us the most invoices?"),
"M24": ("Which 5 airports had the most incidents reported?",
        "Count [[incidents]] per [[airports.iata_code]] via [[incidents.airport_id]] and return the top 5.",
        "Which five stations are our incident hotspots?",
        "Problem airports?"),
"M25": ("How many incidents happened for each type of goods?",
        "Count [[incidents]] per [[shipments.commodity_category]], joining [[incidents]] -> [[flight_cargo]] -> [[shipments]].",
        "What is the incident count by commodity line?",
        "Incidents by goods type?"),
"M26": ("For each insurer, how many claims were paid out and for how much?",
        "For [[insurance_claims]] with [[insurance_claims.status]] = 'paid', count rows and sum [[insurance_claims.approved_amount_usd]] per [[insurance_claims.insurer_name]].",
        "What has each insurer paid out to us: number of settled claims and USD amount?",
        "Payouts by insurer?"),
"M27": ("For each kind of insurance coverage, how many claims were there and what percent got rejected?",
        "Per [[insurance_claims.coverage_type]], count [[insurance_claims]] and compute the percentage with [[insurance_claims.status]] = 'rejected', rounded to 1 decimal.",
        "What is the claim rejection rate by coverage type?",
        "Which coverage gets rejected more?"),
"M28": ("How much import duty was charged for each type of goods?",
        "Sum [[customs_declarations.duty_amount_usd]] for [[customs_declarations.declaration_type]] = 'import' per [[shipments.commodity_category]], rounded to 2 decimals.",
        "What is our import duty exposure by commodity?",
        "Duty by goods?"),
"M29": ("How many imports did each customs broker get cleared?",
        "Count [[customs_declarations]] with [[customs_declarations.declaration_type]] = 'import' and [[customs_declarations.status]] = 'cleared' per [[customs_declarations.broker_name]].",
        "Rank our customs brokers by cleared import volume.",
        "Busiest brokers?"),
"M30": ("In countries with at least 100 cleared exports, how long does export clearance take on average, in hours?",
        "For cleared exports in [[customs_declarations]], average ([[customs_declarations.cleared_at]] - [[customs_declarations.submitted_at]]) in hours per [[customs_declarations.customs_country]], keeping countries with at least 100 rows.",
        "What is the average export clearance lead time by country, for countries with meaningful volume (100+)?",
        "Slowest export customs?"),
"M31": ("How many shipments were received from shippers at each kind of warehouse?",
        "Count [[tracking_events]] with [[tracking_events.event_code]] = 'RCS' per [[warehouses.warehouse_type]], joining on [[tracking_events.warehouse_id]].",
        "How is inbound acceptance volume split across warehouse types?",
        "Acceptance by warehouse type?"),
"M32": ("How many pieces does a shipment have on average for each service level?",
        "Average [[shipments.pieces]] grouped by [[shipments.service_level]], rounded to 2 decimals.",
        "What is the average piece count per consignment by product?",
        "Pieces per service?"),
"M33": ("How many flights is each plane scheduled for in December 2025?",
        "Count [[flights]] with [[flights.scheduled_departure]] in December 2025 per [[aircraft.tail_number]].",
        "What does December 2025 utilisation look like per airframe, in number of flights?",
        "December flights per plane?"),
"M34": ("On flights that carry cargo, how many shipments are on board on average, per plane model?",
        "Count [[flight_cargo]] rows per [[flight_cargo.flight_id]], then average those counts per [[aircraft_types.model]], rounded to 2 decimals.",
        "What is the average consolidation level, shipments per loaded flight, by aircraft type?",
        "Shipments per flight?"),
"M35": ("How many kilos were flown on the main deck versus the lower deck?",
        "Sum [[shipments.total_weight_kg]] for [[flight_cargo]] rows with [[flight_cargo.leg_status]] = 'flown', grouped by [[flight_cargo.deck]].",
        "How is flown tonnage split between main deck and lower deck, in kg?",
        "Main vs lower deck?"),
"M36": ("For each delay code, how many flights and how many minutes late on average at departure?",
        "Group [[flights]] with a non-null [[flights.delay_code]] by code; count them and average ([[flights.actual_departure]] - [[flights.scheduled_departure]]) in minutes.",
        "Give me the delay-code analysis: frequency and average departure delay per code.",
        "Delay reasons?"),
"M37": ("How many customers and how much total credit limit do we have in each sales region?",
        "Group [[customers]] by [[customers.sales_region]]; count rows and sum [[customers.credit_limit_usd]].",
        "What is our credit exposure by sales region: accounts and total credit lines?",
        "Credit by region?"),
"M38": ("How many active captains and first officers are qualified to fly the 747-8F?",
        "Count active [[crew_members]] per [[crew_members.crew_rank]] whose [[crew_members.type_rating_id]] points to the [[aircraft_types]] row with [[aircraft_types.model]] = '747-8F'.",
        "What is our 747-8F qualified pilot pool by rank?",
        "Who can fly the 747?"),
"M39": ("Which airports don't have a cold-chain warehouse?",
        "Return [[airports.iata_code]] for [[airports]] with no [[warehouses]] row of [[warehouses.warehouse_type]] = 'cold_chain'.",
        "Where are the gaps in our cold-chain warehouse coverage?",
        "Airports without cold storage?"),
"M40": ("How many litres of fuel did each supplier deliver?",
        "Sum [[fuel_uplifts.quantity_litres]] grouped by [[fuel_uplifts.supplier_name]], largest first.",
        "What is our fuel volume by supplier?",
        "Fuel suppliers?"),
}

TALK_HARD = {
"H01": ("For each airline, which plane flew the most completed flights, and how many?",
        "Per [[airlines.name]], find the [[aircraft.tail_number]] with the most [[flights]] where [[flights.status]] = 'completed' (ties: smaller tail number), with the count.",
        "Which airframe is the workhorse of each carrier, by completed flights?",
        "Each airline's busiest plane?"),
"H02": ("For each airport, which airline landed there most often on completed flights?",
        "For each destination [[airports.iata_code]], return the [[airlines.name]] with the most completed [[flights]] arriving there (ties: airline name) and the count.",
        "Who is the dominant carrier at each station by completed arrivals?",
        "Top airline per airport?"),
"H03": ("How much did we invoice each month in 2025, and what's the running total over the year?",
        "Group [[invoices]] issued in 2025 by month of [[invoices.issued_date]]; sum [[invoices.amount_usd]] and add a running SUM over months.",
        "Show monthly billed revenue for 2025 with a year-to-date cumulative line.",
        "Revenue over the year?"),
"H04": ("How many flights were completed each month, and how much did that go up or down from the month before?",
        "Count completed [[flights]] per month of [[flights.actual_departure]] and compute the difference to the previous month with LAG.",
        "Give me completed flight volume per month with the month-over-month change.",
        "How did flights change month to month?"),
"H05": ("Which 5 planes have the shortest average time on the ground between completed flights?",
        "For each aircraft, order completed [[flights]] by [[flights.actual_departure]], take each departure minus the previous [[flights.actual_arrival]] in hours, average per [[aircraft.tail_number]] and return the 5 smallest.",
        "Which five airframes have the fastest average turnaround between completed flights?",
        "Quickest turnarounds?"),
"H06": ("Which customers make up more than 4% of everything we invoiced, and what's their share?",
        "Sum [[invoices.amount_usd]] per [[customers.name]] (via [[shipments]]), divide by the total of all invoices, and keep customers above 4%.",
        "Which accounts each contribute over 4% of total invoiced revenue? Show revenue and share.",
        "Who are the key accounts by revenue share?"),
"H07": ("Rank the airports by how many tonnes of cargo flew out of them, and show the top 5 ranks.",
        "Sum [[shipments.total_weight_kg]] / 1000 for flown [[flight_cargo]] legs per origin airport of the [[flights]], DENSE_RANK them by tonnes, and keep ranks 1 to 5.",
        "Give me the outbound tonnage league table for our top 5 stations.",
        "Biggest export airports?"),
"H08": ("For each plane model, how many completed flights were more than half full by volume?",
        "Sum [[shipments.total_volume_m3]] per flight over [[flight_cargo]], then count completed [[flights]] whose sum exceeds 0.5 x [[aircraft_types.max_volume_m3]], per [[aircraft_types.model]].",
        "How many completed flights per aircraft type exceeded 50% volumetric load factor?",
        "Which models fly half full?"),
"H09": ("Which planes have landed at every single cargo hub airport?",
        "Return [[aircraft.tail_number]] whose completed [[flights]] reached, as destination, every [[airports]] row with [[airports.is_cargo_hub]] = 1.",
        "Which airframes have full hub-network coverage on completed flights?",
        "Planes that have been everywhere?"),
"H10": ("In which countries did import taxes (duty plus VAT) go above 20% of the goods value, and how often?",
        "Count import rows in [[customs_declarations]] where [[customs_declarations.duty_amount_usd]] + [[customs_declarations.vat_amount_usd]] > 0.2 x [[customs_declarations.customs_value_usd]], per [[customs_declarations.customs_country]].",
        "In which markets does the import tax burden exceed 20% of customs value, and on how many entries?",
        "Where are import taxes high?"),
"H11": ("Which 3 warehouses keep delivered goods the longest between arriving from the flight and handing them over?",
        "Join [[tracking_events]] RCF rows to the same shipment's DLV row, average the hours in between per [[warehouses.warehouse_code]] of the RCF event, keep warehouses with at least 20 shipments and return the 3 longest.",
        "Which three warehouses have the longest import dwell time from flight arrival to consignee delivery?",
        "Slowest delivery warehouses?"),
"H12": ("At which 5 airports do shipments wait the longest between being dropped off and flying out?",
        "Per shipment take the first RCS and first DEP [[tracking_events.event_time]], average the gap in hours per origin [[airports.iata_code]] of the [[shipments]], and return the 5 longest.",
        "Which five origin stations have the longest acceptance-to-departure lead time?",
        "Where does cargo sit longest before flying?"),
"H13": ("For each plane model, what was the single most expensive finished maintenance job?",
        "Per [[aircraft_types.model]], return the completed [[maintenance_records]] row with the highest [[maintenance_records.parts_cost_usd]] + [[maintenance_records.labor_cost_usd]]: its [[maintenance_records.work_order_number]] and cost.",
        "What was the costliest completed work order per aircraft type?",
        "Most expensive repair per model?"),
"H14": ("For each airline, what percentage of completed flights left more than 15 minutes late?",
        "Per [[airlines.name]], count completed [[flights]] and the percentage where [[flights.actual_departure]] is more than 15 minutes after [[flights.scheduled_departure]].",
        "What is the departure delay rate (D15) per carrier?",
        "Who's late most often?"),
"H15": ("For each loyalty tier, what's the average discount as a percent of the invoice before discount?",
        "Per [[customers.loyalty_tier]], average 100 x [[invoices.discount_usd]] / ([[invoices.amount_usd]] + [[invoices.discount_usd]]) over [[invoices]], rounded to 2 decimals.",
        "What average discount rate does each loyalty tier actually receive?",
        "Discounts by tier?"),
"H16": ("Which planes took off at more than 95% of their maximum takeoff weight, and how many times?",
        "Count [[flights]] per [[aircraft.tail_number]] where [[flights.takeoff_weight_kg]] > 0.95 x [[aircraft_types.max_takeoff_weight_kg]].",
        "Which airframes are operating close to their structural limit (over 95% of MTOW), and how often?",
        "Heavy takeoffs?"),
"H17": ("For each foreign currency, what was the average exchange rate in the first half of 2025 versus the second half?",
        "For [[payments]] with [[payments.original_currency]] <> 'USD', average [[payments.exchange_rate_to_usd]] for payment dates before 2025-07-01 and from 2025-07-01, per currency.",
        "How did FX rates on our collections move between H1 and H2 2025, by currency?",
        "Exchange rates first vs second half?"),
"H18": ("At which connecting airports did two-leg shipments sit more than 48 hours between flights?",
        "Self-join [[flight_cargo]] legs 1 and 2 of the same shipment, both on completed [[flights]]; count cases where leg 2 [[flights.actual_departure]] - leg 1 [[flights.actual_arrival]] > 48 hours, per connecting [[airports.iata_code]].",
        "Where are transfer shipments missing connections by more than two days?",
        "Long layovers?"),
"H19": ("For each insurer, how many claims were paid and how many days did it take on average from filing to payment?",
        "For paid [[insurance_claims]], count rows and average [[insurance_claims.settlement_date]] - [[insurance_claims.filed_date]] in days per [[insurance_claims.insurer_name]].",
        "Which insurer settles fastest? Show paid claims and average days to settlement.",
        "How quick are insurers?"),
"H20": ("Which captain and first officer pairs flew together on at least 10 completed flights?",
        "Self-join [[crew_assignments]] on [[crew_assignments.flight_id]] (captain row with [[crew_assignments.assignment_status]] = 'completed', first_officer row) and count flights per pair of [[crew_members.employee_number]]; keep pairs with at least 10.",
        "Which cockpit pairings are our most frequent (10+ completed flights together)?",
        "Pilots who always fly together?"),
"H21": ("Which airports had more completed departures in Q4 2025 than in Q3? Show both numbers.",
        "Per origin [[airports.iata_code]], count completed [[flights]] with [[flights.actual_departure]] in July-September and in October-December 2025; keep airports where Q4 > Q3.",
        "Which stations grew outbound completed flights quarter over quarter from Q3 to Q4?",
        "Which airports grew lately?"),
"H22": ("Which customers still have open invoices but haven't paid anything in the last 60 days, and how many invoices are open?",
        "Count [[invoices]] with [[invoices.status]] in ('unpaid', 'partially_paid') per [[customers.name]], keeping customers with no [[payments]] row dated on or after 2025-10-21.",
        "Which accounts have open receivables and no cash received in the past 60 days? That's our collections watch list.",
        "Who stopped paying?"),
"H23": ("For each plane model, how many flights carried both dangerous goods and temperature-controlled cargo?",
        "Count [[flights]] per [[aircraft_types.model]] that have at least one [[flight_cargo]] shipment with [[shipments.is_dangerous_goods]] = 1 and at least one with [[shipments.is_temperature_controlled]] = 1.",
        "How often do we mix dangerous goods and temperature-sensitive cargo on the same flight, by aircraft type?",
        "Flights with mixed risky cargo?"),
"H24": ("If we split all shipments into four equal groups by weight, how many of the heaviest group belong to each type of goods?",
        "Apply NTILE(4) over [[shipments]] ordered by [[shipments.total_weight_kg]] (then [[shipments.shipment_id]]) and count the rows in quartile 4 per [[shipments.commodity_category]].",
        "What is the commodity mix of our heaviest 25% of shipments?",
        "What are the heavy shipments?"),
"H25": ("Among customers with at least 20 shipments, which 5 book most often, measured by average days between bookings?",
        "For customers with >= 20 non-cancelled [[shipments]], compute (MAX - MIN [[shipments.booking_date]]) / (count - 1) in days and return the 5 smallest.",
        "Which five accounts have the highest booking frequency (shortest average interval between bookings)?",
        "Most frequent bookers?"),
"H26": ("Which crew members logged more than 40 block hours on completed duties in November 2025?",
        "Sum [[crew_assignments.block_minutes_credited]] / 60 for completed [[crew_assignments]] with [[crew_assignments.report_time]] in November 2025, per [[crew_members.employee_number]]; keep sums above 40.",
        "Which crew members exceeded 40 credited block hours in November 2025?",
        "Who flew a lot in November?"),
"H27": ("For each loyalty tier, how many shipments were handed over and what share arrived on or before the requested date?",
        "Join [[shipments]] to their DLV [[tracking_events]]; per [[customers.loyalty_tier]] count them and the percentage where the event date <= [[shipments.requested_delivery_date]].",
        "What is our on-time delivery rate by loyalty tier?",
        "Are good customers delivered on time?"),
"H28": ("For each booking month, how many shipments were booked and what share was express?",
        "Group [[shipments]] by month of [[shipments.booking_date]]; count rows and the percentage with [[shipments.service_level]] = 'express'.",
        "Show monthly booking volume and express product share.",
        "Express trend?"),
"H29": ("Which planes flew more hours than the average plane of their own airline?",
        "Sum completed block hours per [[aircraft.tail_number]] from [[flights]] actual times, compare with the average over that airline's aircraft, and return the ones above it with [[airlines.name]].",
        "Which airframes are above their carrier's average utilisation in block hours?",
        "Overworked planes?"),
"H30": ("Which 5 routes with at least 10 loaded completed flights have the highest average load by weight?",
        "Per flight sum [[shipments.total_weight_kg]] over [[flight_cargo]], divide by [[aircraft_types.max_payload_kg]], average per origin/destination [[airports.iata_code]] pair over completed [[flights]], keep pairs with >= 10 flights and return the top 5.",
        "Which five lanes have the best payload load factor (minimum 10 loaded flights)?",
        "Fullest routes?"),
"H31": ("Which customers had at least 4 incidents on their shipments, and how much insurance money was approved for them?",
        "Count [[incidents]] per [[customers.name]] (via [[flight_cargo]] and [[shipments]]), LEFT JOIN [[insurance_claims]] and sum [[insurance_claims.approved_amount_usd]] for approved or paid claims (0 if none); keep customers with >= 4 incidents.",
        "Which accounts are incident-prone (4+ incidents), and what has been approved in claims for them?",
        "Customers with lots of problems?"),
"H32": ("For each airline, how often did a flight leave over an hour late right after the same plane's previous flight arrived over an hour late?",
        "Using LAG over each aircraft's completed [[flights]] by [[flights.actual_departure]], count flights with departure delay > 60 min whose previous flight's arrival delay > 60 min, per [[airlines.name]].",
        "How many knock-on delays (over 60 minutes, caused by a late inbound aircraft) did each carrier suffer?",
        "Delays spreading?"),
"H33": ("Which customers have shipped to every single cargo hub airport?",
        "Return [[customers.customer_id]] and [[customers.name]] whose non-cancelled [[shipments]] have destinations covering every [[airports]] row with [[airports.is_cargo_hub]] = 1.",
        "Which accounts use our entire hub network as destinations?",
        "Customers everywhere?"),
"H34": ("Which 5 active planes have gone the longest since their last finished maintenance?",
        "For active [[aircraft]], take MAX([[maintenance_records.end_time]]) of completed [[maintenance_records]] and the days until 2025-12-20; return the 5 largest.",
        "Which five airframes are longest overdue since their last completed maintenance visit?",
        "Planes due for maintenance?"),
"H35": ("Which 5 airports have the most expensive fuel, and how much above the network average is it?",
        "Average [[fuel_uplifts.price_usd_per_litre]] per [[airports.iata_code]] and subtract the average over all [[fuel_uplifts]]; return the 5 highest.",
        "Which five stations carry the biggest fuel price premium versus our network average?",
        "Expensive fuel places?"),
"H36": ("Which 5 crew members had the longest break between two duties, in hours?",
        "Take MAX([[crew_assignments.rest_minutes_before]]) / 60 per [[crew_members.employee_number]] (with [[crew_members.crew_rank]]) and return the 5 largest.",
        "Which five crew members had the longest gap between duties?",
        "Longest breaks?"),
"H37": ("At which airports did export customs clear less than 2 hours before the plane actually left?",
        "Join cleared export [[customs_declarations]] to the leg-1 [[flight_cargo]] row and its completed [[flights]]; count cases where [[flights.actual_departure]] - [[customs_declarations.cleared_at]] < 2 hours, per origin [[airports.iata_code]].",
        "Where are export clearances landing dangerously close to departure (under 2 hours)?",
        "Last-minute customs?"),
"H38": ("Rank goods types by total declared value and show what share of the total we reach as we add them up.",
        "Sum [[shipments.declared_value_usd]] of non-cancelled [[shipments]] per [[shipments.commodity_category]], order by value descending and add a cumulative percentage with window SUM.",
        "Give me a Pareto view of declared value by commodity with cumulative share.",
        "Which goods matter most by value?"),
"H39": ("For customers with at least 60 shipments, where do they ship to most often?",
        "Per customer with >= 60 non-cancelled [[shipments]], return the destination [[airports.iata_code]] with the most shipments (ties: smaller code) and that count.",
        "What is the primary destination market of each major account (60+ shipments)?",
        "Favourite destinations?"),
"H40": ("For invoices paid in exactly two payments, how many days are there between the two, by type of customer?",
        "Find [[payments]] grouped by [[payments.invoice_id]] with exactly 2 rows; average MAX - MIN [[payments.payment_date]] per [[customers.customer_type]] (via [[invoices]] and [[shipments]]), with the count.",
        "For split payments, how long does the second instalment take by customer segment?",
        "Instalment gaps?"),
}

# ---------------------------------------------------------------------------------------------------------
# Extension (960 questions): base questions E41-E80, M41-M80, H41-H80, written in the same format as above.
# ---------------------------------------------------------------------------------------------------------
EASY += [
("E41", ["filtering", "ORDER BY"], "Column: iata_code of airports with has_24h_customs = 0, ordered by iata_code.",
 "SELECT iata_code FROM airports WHERE has_24h_customs = 0 ORDER BY iata_code"),
("E42", ["filtering", ">=", "ORDER BY"], "Columns: iata_code, runway_count of airports with at least 5 runways; ordered by runway_count DESC, iata_code.",
 "SELECT iata_code, runway_count FROM airports WHERE runway_count >= 5 ORDER BY runway_count DESC, iata_code"),
("E43", ["COUNT", "WHERE"], "One value: tracking events with recorded_by 'customer_portal'.",
 "SELECT COUNT(*) AS portal_events FROM tracking_events WHERE recorded_by = 'customer_portal'"),
("E44", ["filtering", "<", "ORDER BY"], "Columns: name, founded_year of airlines founded before 2000; ordered by founded_year.",
 "SELECT name, founded_year FROM airlines WHERE founded_year < 2000 ORDER BY founded_year"),
("E45", ["filtering"], "Column: name of airlines with is_cargo_only = 0 (they also carry passengers), ordered by name.",
 "SELECT name FROM airlines WHERE is_cargo_only = 0 ORDER BY name"),
("E46", ["ORDER BY", "LIMIT"], "Columns: model, max_payload_kg of the aircraft type with the largest max_payload_kg (one row).",
 "SELECT model, max_payload_kg FROM aircraft_types ORDER BY max_payload_kg DESC LIMIT 1"),
("E47", ["filtering", ">=", "ORDER BY"], "Columns: model, max_range_km of aircraft types with max_range_km of at least 8000; ordered by max_range_km DESC.",
 "SELECT model, max_range_km FROM aircraft_types WHERE max_range_km >= 8000 ORDER BY max_range_km DESC"),
("E48", ["COUNT", "<"], "One value: aircraft with year_manufactured before 2010 (any status).",
 "SELECT COUNT(*) AS aircraft_before_2010 FROM aircraft WHERE year_manufactured < 2010"),
("E49", ["filtering", "AND", "date comparison"], "Columns: tail_number, lessor_name, lease_end_date of leased aircraft whose lease ends before 2030-01-01; ordered by lease_end_date.",
 "SELECT tail_number, lessor_name, lease_end_date FROM aircraft WHERE ownership = 'leased' AND lease_end_date < '2030-01-01' ORDER BY lease_end_date"),
("E50", ["ORDER BY", "LIMIT"], "Columns: tail_number, total_flight_hours of the aircraft with the most total_flight_hours (one row).",
 "SELECT tail_number, total_flight_hours FROM aircraft ORDER BY total_flight_hours DESC LIMIT 1"),
("E51", ["COUNT", "WHERE"], "One value: customers with is_known_shipper = 0.",
 "SELECT COUNT(*) AS unknown_shippers FROM customers WHERE is_known_shipper = 0"),
("E52", ["ORDER BY", "LIMIT"], "Columns: name, credit_limit_usd of the 5 customers with the highest credit_limit_usd; ordered by credit_limit_usd DESC.",
 "SELECT name, credit_limit_usd FROM customers ORDER BY credit_limit_usd DESC LIMIT 5"),
("E53", ["COUNT", "date filtering"], "One value: customers whose created_date is in 2024.",
 "SELECT COUNT(*) AS customers_created_2024 FROM customers WHERE created_date >= '2024-01-01' AND created_date < '2025-01-01'"),
("E54", ["AVG", "ROUND"], "One value: AVG(credit_limit_usd) of customers with loyalty_tier 'platinum', rounded to 2 decimals.",
 "SELECT ROUND(AVG(credit_limit_usd), 2) AS avg_platinum_credit_limit_usd FROM customers WHERE loyalty_tier = 'platinum'"),
("E55", ["filtering", "ORDER BY"], "Column: warehouse_code of warehouses with operates_24h = 0, ordered by warehouse_code.",
 "SELECT warehouse_code FROM warehouses WHERE operates_24h = 0 ORDER BY warehouse_code"),
("E56", ["ORDER BY", "LIMIT"], "Columns: warehouse_code, monthly_rent_usd of the 3 warehouses with the highest monthly_rent_usd; ordered by rent DESC.",
 "SELECT warehouse_code, monthly_rent_usd FROM warehouses ORDER BY monthly_rent_usd DESC LIMIT 3"),
("E57", ["AVG", "AND", "ROUND"], "One value: AVG(duty_rate_pct) of import declarations with customs_country 'Japan', rounded to 2 decimals.",
 "SELECT ROUND(AVG(duty_rate_pct), 2) AS avg_japan_duty_rate_pct FROM customs_declarations WHERE declaration_type = 'import' AND customs_country = 'Japan'"),
("E58", ["COUNT", "AND"], "One value: warehouses with is_bonded = 1 and security_level 'high'.",
 "SELECT COUNT(*) AS bonded_high_security FROM warehouses WHERE is_bonded = 1 AND security_level = 'high'"),
("E59", ["COUNT", "date comparison"], "One value: crew members whose license_expiry_date is before 2026-01-01 (crew without a licence are not counted).",
 "SELECT COUNT(*) AS licences_expiring_2025 FROM crew_members WHERE license_expiry_date < '2026-01-01'"),
("E60", ["ORDER BY", "LIMIT"], "Columns: employee_number, first_name, last_name, hire_date of the crew member hired first (one row).",
 "SELECT employee_number, first_name, last_name, hire_date FROM crew_members ORDER BY hire_date LIMIT 1"),
("E61", ["COUNT", "AND"], "One value: incidents with incident_type 'damage' and root_cause 'packaging'.",
 "SELECT COUNT(*) AS packaging_damage FROM incidents WHERE incident_type = 'damage' AND root_cause = 'packaging'"),
("E62", ["COUNT", "WHERE"], "One value: flights with status 'scheduled' (not yet flown).",
 "SELECT COUNT(*) AS scheduled_flights FROM flights WHERE status = 'scheduled'"),
("E63", ["AVG", "ROUND"], "One value: AVG(distance_km) of completed flights, rounded to 1 decimal.",
 "SELECT ROUND(AVG(distance_km), 1) AS avg_distance_km FROM flights WHERE status = 'completed'"),
("E64", ["COUNT", "WHERE"], "One value: flights with delay_code '93' (any status).",
 "SELECT COUNT(*) AS delay_93_flights FROM flights WHERE delay_code = '93'"),
("E65", ["IN", "ORDER BY"], "Columns: claim_number, claimed_amount_usd of insurance claims with status 'filed' or 'under_review'; ordered by claim_number.",
 "SELECT claim_number, claimed_amount_usd FROM insurance_claims WHERE status IN ('filed', 'under_review') ORDER BY claim_number"),
("E66", ["SUM", "WHERE", "ROUND"], "One value: SUM(per_diem_usd) of crew assignments with duty_role 'loadmaster' (any status), rounded to 2 decimals.",
 "SELECT ROUND(SUM(per_diem_usd), 2) AS loadmaster_per_diem_usd FROM crew_assignments WHERE duty_role = 'loadmaster'"),
("E67", ["COUNT", "WHERE"], "One value: crew assignments with assignment_status 'rostered'.",
 "SELECT COUNT(*) AS rostered_assignments FROM crew_assignments WHERE assignment_status = 'rostered'"),
("E68", ["AVG", "ROUND"], "One value: AVG(block_minutes_credited) of completed crew assignments, rounded to 1 decimal.",
 "SELECT ROUND(AVG(block_minutes_credited), 1) AS avg_block_minutes FROM crew_assignments WHERE assignment_status = 'completed'"),
("E69", ["DISTINCT", "ORDER BY"], "Column: the distinct mro_provider names in maintenance records, ordered by name.",
 "SELECT DISTINCT mro_provider FROM maintenance_records ORDER BY mro_provider"),
("E70", ["SUM", "AND", "ROUND"], "One value: SUM(labor_hours) of completed 'A_check' maintenance, rounded to 1 decimal.",
 "SELECT ROUND(SUM(labor_hours), 1) AS a_check_labor_hours FROM maintenance_records WHERE check_type = 'A_check' AND status = 'completed'"),
("E71", ["filtering", "<>", "ORDER BY"], "Columns: work_order_number, status of maintenance records whose status is not 'completed'; ordered by work_order_number.",
 "SELECT work_order_number, status FROM maintenance_records WHERE status <> 'completed' ORDER BY work_order_number"),
("E72", ["COUNT", ">"], "One value: fuel uplifts with saf_blend_pct greater than 0.",
 "SELECT COUNT(*) AS saf_uplifts FROM fuel_uplifts WHERE saf_blend_pct > 0"),
("E73", ["MAX"], "One value: the largest total_cost_usd of any fuel uplift.",
 "SELECT MAX(total_cost_usd) AS max_fuel_bill_usd FROM fuel_uplifts"),
("E74", ["SUM", "WHERE", "ROUND"], "One value: SUM(total_cost_usd) of fuel uplifts from supplier 'Skyline Fuels', rounded to 2 decimals.",
 "SELECT ROUND(SUM(total_cost_usd), 2) AS skyline_fuel_cost_usd FROM fuel_uplifts WHERE supplier_name = 'Skyline Fuels'"),
("E75", ["COUNT", "WHERE"], "One value: shipments with status 'cancelled'.",
 "SELECT COUNT(*) AS cancelled_shipments FROM shipments WHERE status = 'cancelled'"),
("E76", ["GROUP BY", "IS NOT NULL"], "Columns: dg_class, number of shipments; dangerous-goods shipments only (dg_class not NULL), any status; ordered by dg_class.",
 "SELECT dg_class, COUNT(*) AS shipments FROM shipments WHERE dg_class IS NOT NULL GROUP BY dg_class ORDER BY dg_class"),
("E77", ["SUM", "WHERE"], "One value: SUM(pieces) of shipments with commodity_category 'pharmaceuticals' (any status).",
 "SELECT SUM(pieces) AS pharma_pieces FROM shipments WHERE commodity_category = 'pharmaceuticals'"),
("E78", ["COUNT", "WHERE"], "One value: flight_cargo rows with leg_number = 2 (second legs of connecting shipments).",
 "SELECT COUNT(*) AS second_legs FROM flight_cargo WHERE leg_number = 2"),
("E79", ["COUNT", ">"], "One value: invoices with dg_surcharge_usd greater than 0.",
 "SELECT COUNT(*) AS invoices_with_dg_surcharge FROM invoices WHERE dg_surcharge_usd > 0"),
("E80", ["COUNT", "WHERE"], "One value: payments with is_reconciled = 0.",
 "SELECT COUNT(*) AS unreconciled_payments FROM payments WHERE is_reconciled = 0"),
]

MODERATE += [
("M41", ["JOIN", "foreign key"], "Columns: airline name, iata_code of its home hub airport; ordered by airline name.",
 """SELECT al.name AS airline_name, ap.iata_code AS home_hub
FROM airlines al JOIN airports ap ON ap.airport_id = al.home_hub_airport_id ORDER BY airline_name"""),
("M42", ["JOIN", "GROUP BY"], "Columns: manufacturer, number of aircraft (any status) built by it; ordered by manufacturer.",
 """SELECT t.manufacturer, COUNT(*) AS aircraft
FROM aircraft a JOIN aircraft_types t ON t.type_id = a.type_id GROUP BY t.manufacturer ORDER BY t.manufacturer"""),
("M43", ["GROUP BY", "HAVING"], "Columns: country, number of customers; only countries with at least 5 customers; ordered by count DESC, country.",
 """SELECT country, COUNT(*) AS customers FROM customers GROUP BY country HAVING COUNT(*) >= 5
ORDER BY customers DESC, country"""),
("M44", ["JOIN", "GROUP BY", "WHERE"], "Columns: iata_code, completed departures; airports in region 'europe' only; ordered by count DESC, iata_code.",
 """SELECT ap.iata_code, COUNT(*) AS completed_departures
FROM flights f JOIN airports ap ON ap.airport_id = f.origin_airport_id
WHERE ap.region = 'europe' AND f.status = 'completed'
GROUP BY ap.airport_id, ap.iata_code ORDER BY completed_departures DESC, ap.iata_code"""),
("M45", ["GROUP BY two columns"], "Columns: flight_type, status, number of flights; one row per combination that occurs; ordered by flight_type, status.",
 "SELECT flight_type, status, COUNT(*) AS flights FROM flights GROUP BY flight_type, status ORDER BY flight_type, status"),
("M46", ["anti-join", "NOT EXISTS"], "Column: tail_number of aircraft that have no flight at all (any status); ordered.",
 """SELECT a.tail_number FROM aircraft a
WHERE NOT EXISTS (SELECT 1 FROM flights f WHERE f.aircraft_id = a.aircraft_id) ORDER BY a.tail_number"""),
("M47", ["anti-join", "LEFT JOIN"], "Column: name of customers with no shipment at all; ordered by name.",
 """SELECT c.name FROM customers c LEFT JOIN shipments s ON s.customer_id = c.customer_id
WHERE s.shipment_id IS NULL ORDER BY c.name"""),
("M48", ["JOIN", "conditional aggregation"], "Columns: airline name, active crew members, active captains among them; ordered by airline name.",
 """SELECT al.name AS airline_name, COUNT(*) AS active_crew,
       SUM(CASE WHEN m.crew_rank = 'captain' THEN 1 ELSE 0 END) AS active_captains
FROM crew_members m JOIN airlines al ON al.airline_id = m.airline_id
WHERE m.is_active = 1 GROUP BY al.airline_id, al.name ORDER BY airline_name"""),
("M49", ["JOIN", "SUM", "LIMIT"], "Columns: iata_code, SUM(quantity_litres) of fuel uplifted there; the 5 airports with the most litres; ordered DESC.",
 """SELECT ap.iata_code, SUM(fu.quantity_litres) AS litres
FROM fuel_uplifts fu JOIN airports ap ON ap.airport_id = fu.airport_id
GROUP BY ap.airport_id, ap.iata_code ORDER BY litres DESC LIMIT 5"""),
("M50", ["multi-hop join", "AVG"], "Columns: airline name, AVG(saf_blend_pct) over the fuel uplifts of its flights, rounded to 2 decimals; ordered by average DESC.",
 """SELECT al.name AS airline_name, ROUND(AVG(fu.saf_blend_pct), 2) AS avg_saf_pct
FROM fuel_uplifts fu JOIN flights f ON f.flight_id = fu.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN airlines al ON al.airline_id = a.airline_id
GROUP BY al.airline_id, al.name ORDER BY avg_saf_pct DESC, airline_name"""),
("M51", ["GROUP BY", "WHERE"], "Columns: mro_provider, number of AOG maintenance records (is_aog = 1); providers without AOG omitted; ordered by count DESC, provider.",
 """SELECT mro_provider, COUNT(*) AS aog_records FROM maintenance_records WHERE is_aog = 1
GROUP BY mro_provider ORDER BY aog_records DESC, mro_provider"""),
("M52", ["JOIN", "SUM", "LIMIT"], "Columns: tail_number, total cost (parts + labour) of its completed maintenance, rounded to 2 decimals; the 5 most expensive aircraft.",
 """SELECT a.tail_number, ROUND(SUM(m.parts_cost_usd + m.labor_cost_usd), 2) AS maintenance_cost_usd
FROM maintenance_records m JOIN aircraft a ON a.aircraft_id = m.aircraft_id
WHERE m.status = 'completed' GROUP BY a.aircraft_id, a.tail_number ORDER BY maintenance_cost_usd DESC LIMIT 5"""),
("M53", ["JOIN", "GROUP BY", "HAVING"], "Columns: iata_code, number of maintenance records done at that airport; only airports with at least 30; ordered by count DESC, iata_code.",
 """SELECT ap.iata_code, COUNT(*) AS maintenance_records
FROM maintenance_records m JOIN airports ap ON ap.airport_id = m.airport_id
GROUP BY ap.airport_id, ap.iata_code HAVING COUNT(*) >= 30 ORDER BY maintenance_records DESC, ap.iata_code"""),
("M54", ["JOIN", "GROUP BY", "LIMIT"], "Columns: destination iata_code, number of delivered shipments to it; the top 5 destinations.",
 """SELECT ap.iata_code, COUNT(*) AS delivered_shipments
FROM shipments s JOIN airports ap ON ap.airport_id = s.destination_airport_id
WHERE s.status = 'delivered' GROUP BY ap.airport_id, ap.iata_code ORDER BY delivered_shipments DESC LIMIT 5"""),
("M55", ["JOIN", "GROUP BY", "SUM"], "Columns: customer_type, number of shipments (any status), SUM(declared_value_usd) rounded to 2 decimals; ordered by customer_type.",
 """SELECT c.customer_type, COUNT(*) AS shipments, ROUND(SUM(s.declared_value_usd), 2) AS declared_value_usd
FROM shipments s JOIN customers c ON c.customer_id = s.customer_id GROUP BY c.customer_type ORDER BY c.customer_type"""),
("M56", ["date grouping", "substr", "WHERE"], "Columns: booking month 'YYYY-MM', number of temperature-controlled shipments booked that month (any status); ordered by month.",
 """SELECT substr(booking_date, 1, 7) AS booking_month, COUNT(*) AS temp_controlled_shipments
FROM shipments WHERE is_temperature_controlled = 1 GROUP BY substr(booking_date, 1, 7) ORDER BY booking_month"""),
("M57", ["JOIN", "GROUP BY", "AVG"], "Columns: uld_type, number of shipment legs, AVG(total_weight_kg) of the shipments on those legs rounded to 1 decimal; ordered by uld_type.",
 """SELECT fc.uld_type, COUNT(*) AS legs, ROUND(AVG(s.total_weight_kg), 1) AS avg_shipment_kg
FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id GROUP BY fc.uld_type ORDER BY fc.uld_type"""),
("M58", ["multi-hop join", "date comparison", "GROUP BY"], "Columns: customer sales_region, number of overdue invoices (status not 'paid' and due_date before 2025-12-20); ordered by count DESC, region.",
 """SELECT c.sales_region, COUNT(*) AS overdue_invoices
FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
WHERE i.status <> 'paid' AND i.due_date < '2025-12-20'
GROUP BY c.sales_region ORDER BY overdue_invoices DESC, c.sales_region"""),
("M59", ["JOIN", "GROUP BY", "AVG"], "Columns: service_level, AVG(amount_usd) of its invoices rounded to 2 decimals; ordered by service_level.",
 """SELECT s.service_level, ROUND(AVG(i.amount_usd), 2) AS avg_invoice_usd
FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id GROUP BY s.service_level ORDER BY s.service_level"""),
("M60", ["GROUP BY", "<>", "SUM"], "Columns: original_currency, number of payments, SUM(amount_usd) rounded to 2 decimals; non-USD payments only; ordered by sum DESC.",
 """SELECT original_currency, COUNT(*) AS payments, ROUND(SUM(amount_usd), 2) AS amount_usd
FROM payments WHERE original_currency <> 'USD' GROUP BY original_currency ORDER BY amount_usd DESC"""),
("M61", ["JOIN", "SUM", "LIMIT"], "Columns: customer name, SUM(bank_charges_usd) of its payments rounded to 2 decimals; the 5 customers with the highest bank charges.",
 """SELECT c.name, ROUND(SUM(p.bank_charges_usd), 2) AS bank_charges_usd
FROM payments p JOIN customers c ON c.customer_id = p.customer_id
GROUP BY c.customer_id, c.name ORDER BY bank_charges_usd DESC LIMIT 5"""),
("M62", ["GROUP BY", "conditional aggregation"], "Columns: root_cause, number of incidents, number of resolved incidents; ordered by root_cause.",
 """SELECT root_cause, COUNT(*) AS incidents, SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) AS resolved_incidents
FROM incidents GROUP BY root_cause ORDER BY root_cause"""),
("M63", ["multi-hop join", "GROUP BY"], "Columns: airline name (airline operating the flight of the incident's shipment leg), number of incidents; ordered by count DESC, name.",
 """SELECT al.name AS airline_name, COUNT(*) AS incidents
FROM incidents i JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id JOIN flights f ON f.flight_id = fc.flight_id
JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN airlines al ON al.airline_id = a.airline_id
GROUP BY al.airline_id, al.name ORDER BY incidents DESC, airline_name"""),
("M64", ["JOIN", "GROUP BY", "HAVING"], "Columns: customer name, number of insurance claims, SUM(claimed_amount_usd) rounded to 2 decimals; customers with at least 3 claims; ordered by claims DESC, name.",
 """SELECT c.name, COUNT(*) AS claims, ROUND(SUM(ic.claimed_amount_usd), 2) AS claimed_usd
FROM insurance_claims ic JOIN customers c ON c.customer_id = ic.customer_id
GROUP BY c.customer_id, c.name HAVING COUNT(*) >= 3 ORDER BY claims DESC, c.name"""),
("M65", ["GROUP BY", "WHERE"], "Columns: customs_country, number of declarations with status 'held'; ordered by count DESC, country.",
 """SELECT customs_country, COUNT(*) AS held_declarations FROM customs_declarations WHERE status = 'held'
GROUP BY customs_country ORDER BY held_declarations DESC, customs_country"""),
("M66", ["GROUP BY", "SUM", "LIMIT"], "Columns: goods_description, SUM(customs_value_usd) of import declarations rounded to 2 decimals; the top 5 goods.",
 """SELECT goods_description, ROUND(SUM(customs_value_usd), 2) AS import_value_usd
FROM customs_declarations WHERE declaration_type = 'import'
GROUP BY goods_description ORDER BY import_value_usd DESC LIMIT 5"""),
("M67", ["JOIN", "GROUP BY", "LIMIT"], "Columns: warehouse_code, number of customs declarations lodged at it; the 5 warehouses with most declarations.",
 """SELECT w.warehouse_code, COUNT(*) AS declarations
FROM customs_declarations cd JOIN warehouses w ON w.warehouse_id = cd.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_code ORDER BY declarations DESC LIMIT 5"""),
("M68", ["JOIN", "GROUP BY", "LIMIT"], "Columns: iata_code, number of NFD (notified for delivery) tracking events at that airport; the 5 airports with most.",
 """SELECT ap.iata_code, COUNT(*) AS nfd_events
FROM tracking_events te JOIN airports ap ON ap.airport_id = te.airport_id
WHERE te.event_code = 'NFD' GROUP BY ap.airport_id, ap.iata_code ORDER BY nfd_events DESC LIMIT 5"""),
("M69", ["anti-join", "NOT EXISTS", "GROUP BY"], "Columns: destination iata_code, number of shipments with status 'delivered' that have no DLV tracking event (not yet handed over); airports with none omitted; ordered by count DESC, iata_code.",
 """SELECT ap.iata_code, COUNT(*) AS delivered_not_handed_over
FROM shipments s JOIN airports ap ON ap.airport_id = s.destination_airport_id
WHERE s.status = 'delivered'
  AND NOT EXISTS (SELECT 1 FROM tracking_events te WHERE te.shipment_id = s.shipment_id AND te.event_code = 'DLV')
GROUP BY ap.airport_id, ap.iata_code ORDER BY delivered_not_handed_over DESC, ap.iata_code"""),
("M70", ["JOIN", "GROUP BY", "LIMIT"], "Columns: employee_number, number of completed assignments as pilot flying (is_pilot_flying = 1); the 3 crew members with most (ties at the top by employee_number).",
 """SELECT m.employee_number, COUNT(*) AS sectors_flown
FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
WHERE ca.is_pilot_flying = 1 AND ca.assignment_status = 'completed'
GROUP BY m.crew_member_id, m.employee_number ORDER BY sectors_flown DESC, m.employee_number LIMIT 3"""),
("M71", ["JOIN", "GROUP BY", "AVG"], "Columns: base airport iata_code, number of active captains based there, AVG(total_flight_hours) of them rounded to 0 decimals; ordered by iata_code.",
 """SELECT ap.iata_code, COUNT(*) AS active_captains, ROUND(AVG(m.total_flight_hours), 0) AS avg_flight_hours
FROM crew_members m JOIN airports ap ON ap.airport_id = m.base_airport_id
WHERE m.crew_rank = 'captain' AND m.is_active = 1 GROUP BY ap.airport_id, ap.iata_code ORDER BY ap.iata_code"""),
("M72", ["multi-hop join", "SUM"], "Columns: airline name (the crew member's airline), SUM(per_diem_usd) of completed assignments rounded to 2 decimals; ordered by sum DESC.",
 """SELECT al.name AS airline_name, ROUND(SUM(ca.per_diem_usd), 2) AS per_diem_usd
FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id JOIN airlines al ON al.airline_id = m.airline_id
WHERE ca.assignment_status = 'completed' GROUP BY al.airline_id, al.name ORDER BY per_diem_usd DESC"""),
("M73", ["GROUP BY", "date arithmetic", "IS NOT NULL"], "Columns: weather_at_departure, number of completed flights, average departure delay in minutes (actual - scheduled departure) rounded to 1 decimal; flights without weather omitted; ordered by delay DESC.",
 """SELECT weather_at_departure, COUNT(*) AS completed_flights,
       ROUND(AVG((julianday(actual_departure) - julianday(scheduled_departure)) * 1440), 1) AS avg_departure_delay_min
FROM flights WHERE status = 'completed' AND weather_at_departure IS NOT NULL
GROUP BY weather_at_departure ORDER BY avg_departure_delay_min DESC"""),
("M74", ["date grouping", "substr", "WHERE"], "Columns: month 'YYYY-MM' of scheduled_departure, number of cancelled flights; months without cancellations omitted; ordered by month.",
 """SELECT substr(scheduled_departure, 1, 7) AS month, COUNT(*) AS cancelled_flights
FROM flights WHERE status = 'cancelled' GROUP BY substr(scheduled_departure, 1, 7) ORDER BY month"""),
("M75", ["LEFT JOIN", "conditional aggregation"], "Columns: airline name, owned aircraft, leased aircraft (any status, 0 if none); ordered by airline name.",
 """SELECT al.name AS airline_name,
       SUM(CASE WHEN a.ownership = 'owned' THEN 1 ELSE 0 END) AS owned_aircraft,
       SUM(CASE WHEN a.ownership = 'leased' THEN 1 ELSE 0 END) AS leased_aircraft
FROM airlines al LEFT JOIN aircraft a ON a.airline_id = al.airline_id
GROUP BY al.airline_id, al.name ORDER BY airline_name"""),
("M76", ["JOIN", "GROUP BY", "WHERE"], "Columns: iata_code, number of warehouses, SUM(floor_area_m2); airports in region 'asia_pacific'; ordered by area DESC.",
 """SELECT ap.iata_code, COUNT(*) AS warehouses, SUM(w.floor_area_m2) AS floor_area_m2
FROM warehouses w JOIN airports ap ON ap.airport_id = w.airport_id
WHERE ap.region = 'asia_pacific' GROUP BY ap.airport_id, ap.iata_code ORDER BY floor_area_m2 DESC"""),
("M77", ["JOIN", "date arithmetic", "AVG"], "Columns: origin iata_code, average days between booking_date and requested_delivery_date of express shipments (any status) rounded to 2; ordered by iata_code.",
 """SELECT ap.iata_code, ROUND(AVG(julianday(s.requested_delivery_date) - julianday(s.booking_date)), 2) AS avg_requested_days
FROM shipments s JOIN airports ap ON ap.airport_id = s.origin_airport_id
WHERE s.service_level = 'express' GROUP BY ap.airport_id, ap.iata_code ORDER BY ap.iata_code"""),
("M78", ["GROUP BY", "AVG"], "Columns: payment_terms_days, number of invoices, AVG(amount_usd) rounded to 2 decimals; ordered by payment_terms_days.",
 """SELECT payment_terms_days, COUNT(*) AS invoices, ROUND(AVG(amount_usd), 2) AS avg_amount_usd
FROM invoices GROUP BY payment_terms_days ORDER BY payment_terms_days"""),
("M79", ["JOIN", "GROUP BY", "HAVING"], "Columns: customer name, number of dangerous-goods shipments (any status); customers with at least 8; ordered by count DESC, name.",
 """SELECT c.name, COUNT(*) AS dg_shipments
FROM shipments s JOIN customers c ON c.customer_id = s.customer_id
WHERE s.is_dangerous_goods = 1 GROUP BY c.customer_id, c.name HAVING COUNT(*) >= 8 ORDER BY dg_shipments DESC, c.name"""),
("M80", ["multi-hop join", "AVG"], "Columns: aircraft model, AVG(fuel_burned_kg) per fuel uplift (one per flight) rounded to 0 decimals; ordered by average DESC.",
 """SELECT t.model, ROUND(AVG(fu.fuel_burned_kg), 0) AS avg_fuel_burned_kg
FROM fuel_uplifts fu JOIN flights f ON f.flight_id = fu.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id GROUP BY t.type_id, t.model ORDER BY avg_fuel_burned_kg DESC"""),
]

HARD += [
("H41", ["CTE", "ROW_NUMBER", "multi-hop join"], "Columns: sales_region, customer name, invoiced USD rounded to 2: per sales region the customer with the largest SUM(invoices.amount_usd) (ties: smaller customer_id); ordered by sales_region.",
 """WITH r AS (
  SELECT c.customer_id, c.name, c.sales_region, SUM(i.amount_usd) AS invoiced
  FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
  GROUP BY c.customer_id, c.name, c.sales_region
), k AS (
  SELECT r.*, ROW_NUMBER() OVER (PARTITION BY sales_region ORDER BY invoiced DESC, customer_id) AS rn FROM r
)
SELECT sales_region, name, ROUND(invoiced, 2) AS invoiced_usd FROM k WHERE rn = 1 ORDER BY sales_region"""),
("H42", ["CTE", "moving average", "window frame"], "Columns: month 'YYYY-MM' of uplift_time, fuel cost that month, 3-month moving average (this month and the 2 before; fewer at the start), both rounded to 2; ordered by month.",
 """WITH m AS (
  SELECT substr(uplift_time, 1, 7) AS month, SUM(total_cost_usd) AS cost FROM fuel_uplifts GROUP BY substr(uplift_time, 1, 7)
)
SELECT month, ROUND(cost, 2) AS fuel_cost_usd,
       ROUND(AVG(cost) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m_usd
FROM m ORDER BY month"""),
("H43", ["CTE", "LAG", "date arithmetic", "LIMIT"], "Columns: tail_number, longest gap in days between the start_time of two consecutive completed maintenance records of the same aircraft (rounded 1); the 5 aircraft with the longest gap.",
 """WITH g AS (
  SELECT aircraft_id,
         julianday(start_time) - julianday(LAG(start_time) OVER (PARTITION BY aircraft_id ORDER BY start_time)) AS gap_days
  FROM maintenance_records WHERE status = 'completed'
)
SELECT a.tail_number, ROUND(MAX(g.gap_days), 1) AS longest_gap_days
FROM g JOIN aircraft a ON a.aircraft_id = g.aircraft_id
GROUP BY a.aircraft_id, a.tail_number ORDER BY MAX(g.gap_days) DESC LIMIT 5"""),
("H44", ["CTE", "ROW_NUMBER", "SUM"], "Columns: airline name, captain employee_number, credited block hours (SUM(block_minutes_credited)/60 over completed assignments in the 'captain' duty role, rounded 1): per airline the captain with most hours (ties: employee_number); ordered by airline name.",
 """WITH h AS (
  SELECT m.airline_id, m.employee_number, SUM(ca.block_minutes_credited) AS minutes
  FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
  WHERE ca.duty_role = 'captain' AND ca.assignment_status = 'completed'
  GROUP BY m.crew_member_id, m.airline_id, m.employee_number
), r AS (
  SELECT h.*, ROW_NUMBER() OVER (PARTITION BY airline_id ORDER BY minutes DESC, employee_number) AS rn FROM h
)
SELECT al.name AS airline_name, r.employee_number, ROUND(r.minutes / 60.0, 1) AS block_hours
FROM r JOIN airlines al ON al.airline_id = r.airline_id WHERE r.rn = 1 ORDER BY airline_name"""),
("H45", ["conditional aggregation", "HAVING", "half-years"], "Columns: customer name, invoiced USD in H1 2025 (issued Jan-Jun), in H2 2025 (Jul-Dec), both rounded 2; customers whose H2 amount is more than 1.5 times the H1 amount; ordered by name.",
 """SELECT c.name,
       ROUND(SUM(CASE WHEN i.issued_date < '2025-07-01' THEN i.amount_usd ELSE 0 END), 2) AS h1_usd,
       ROUND(SUM(CASE WHEN i.issued_date >= '2025-07-01' THEN i.amount_usd ELSE 0 END), 2) AS h2_usd
FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
WHERE i.issued_date >= '2025-01-01' AND i.issued_date < '2026-01-01'
GROUP BY c.customer_id, c.name
HAVING SUM(CASE WHEN i.issued_date >= '2025-07-01' THEN i.amount_usd ELSE 0 END)
     > 1.5 * SUM(CASE WHEN i.issued_date < '2025-07-01' THEN i.amount_usd ELSE 0 END)
ORDER BY c.name"""),
("H46", ["CTE", "aggregate before join", "LEFT JOIN", "LIMIT"], "Columns: customer name, open balance in USD = invoice amount minus payments received, summed over its invoices with status 'unpaid' or 'partially_paid' (rounded 2); the 5 customers with the largest open balance.",
 """WITH paid AS (
  SELECT invoice_id, SUM(amount_usd) AS paid_usd FROM payments GROUP BY invoice_id
)
SELECT c.name, ROUND(SUM(i.amount_usd - COALESCE(p.paid_usd, 0)), 2) AS open_balance_usd
FROM invoices i LEFT JOIN paid p ON p.invoice_id = i.invoice_id
JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers c ON c.customer_id = s.customer_id
WHERE i.status IN ('unpaid', 'partially_paid')
GROUP BY c.customer_id, c.name ORDER BY open_balance_usd DESC LIMIT 5"""),
("H47", ["NOT EXISTS", "conditional aggregation", "percentage"], "Columns: model, completed flights, completed flights without any shipment leg, share of such empty flights in percent (rounded 1); ordered by model.",
 """SELECT t.model, COUNT(*) AS completed_flights,
       SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM flight_cargo fc WHERE fc.flight_id = f.flight_id) THEN 1 ELSE 0 END) AS empty_flights,
       ROUND(100.0 * SUM(CASE WHEN NOT EXISTS (SELECT 1 FROM flight_cargo fc WHERE fc.flight_id = f.flight_id) THEN 1 ELSE 0 END) / COUNT(*), 1) AS empty_pct
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
WHERE f.status = 'completed' GROUP BY t.type_id, t.model ORDER BY t.model"""),
("H48", ["two CTEs", "ratio of aggregates", "LIMIT"], "Columns: iata_code, shipments originating there (any status), incidents reported at that airport, incidents per 1000 originating shipments (rounded 2); the 5 airports with the highest rate.",
 """WITH s AS (
  SELECT origin_airport_id AS airport_id, COUNT(*) AS shipments FROM shipments GROUP BY origin_airport_id
), i AS (
  SELECT airport_id, COUNT(*) AS incidents FROM incidents GROUP BY airport_id
)
SELECT ap.iata_code, s.shipments, i.incidents, ROUND(1000.0 * i.incidents / s.shipments, 2) AS incidents_per_1000
FROM airports ap JOIN s ON s.airport_id = ap.airport_id JOIN i ON i.airport_id = ap.airport_id
ORDER BY incidents_per_1000 DESC LIMIT 5"""),
("H49", ["relational division", "HAVING COUNT DISTINCT", "scalar subquery"], "Columns: operator_name of warehouse operators that run at least one warehouse at every airport in region 'europe'; ordered.",
 """SELECT w.operator_name
FROM warehouses w JOIN airports ap ON ap.airport_id = w.airport_id
WHERE ap.region = 'europe'
GROUP BY w.operator_name
HAVING COUNT(DISTINCT w.airport_id) = (SELECT COUNT(*) FROM airports WHERE region = 'europe')
ORDER BY w.operator_name"""),
("H50", ["CTE", "DENSE_RANK", "second highest"], "Columns: commodity_category, awb_number, declared_value_usd of the shipment with the second-highest declared value in each category (any status); ordered by category.",
 """WITH r AS (
  SELECT commodity_category, awb_number, declared_value_usd,
         DENSE_RANK() OVER (PARTITION BY commodity_category ORDER BY declared_value_usd DESC) AS dr
  FROM shipments
)
SELECT commodity_category, awb_number, declared_value_usd FROM r WHERE dr = 2 ORDER BY commodity_category"""),
("H51", ["CTE", "window SUM", "share within group"], "Columns: airline name, model, completed flights of that airline on that model, share of the airline's completed flights in percent (rounded 1); ordered by airline name, flights DESC.",
 """WITH c AS (
  SELECT a.airline_id, t.model, COUNT(*) AS flights
  FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id JOIN aircraft_types t ON t.type_id = a.type_id
  WHERE f.status = 'completed' GROUP BY a.airline_id, t.model
)
SELECT al.name AS airline_name, c.model, c.flights,
       ROUND(100.0 * c.flights / SUM(c.flights) OVER (PARTITION BY c.airline_id), 1) AS share_pct
FROM c JOIN airlines al ON al.airline_id = c.airline_id ORDER BY airline_name, c.flights DESC"""),
("H52", ["CTE", "median", "ROW_NUMBER", "COUNT OVER"], "Columns: service_level, median chargeable_weight_kg of its delivered shipments (mean of the two middle values when the count is even, rounded 1); ordered by service_level.",
 """WITH o AS (
  SELECT service_level, chargeable_weight_kg,
         ROW_NUMBER() OVER (PARTITION BY service_level ORDER BY chargeable_weight_kg) AS rn,
         COUNT(*) OVER (PARTITION BY service_level) AS n
  FROM shipments WHERE status = 'delivered'
)
SELECT service_level, ROUND(AVG(chargeable_weight_kg), 1) AS median_chargeable_kg
FROM o WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
GROUP BY service_level ORDER BY service_level"""),
("H53", ["CTE", "ROW_NUMBER", "first per group"], "Columns: service_level of each customer's first shipment (earliest booking_date, ties by smaller shipment_id, any status), number of customers; ordered by service_level.",
 """WITH f AS (
  SELECT customer_id, service_level,
         ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY booking_date, shipment_id) AS rn
  FROM shipments
)
SELECT service_level, COUNT(*) AS customers FROM f WHERE rn = 1 GROUP BY service_level ORDER BY service_level"""),
("H54", ["correlated subquery", "MIN", "date arithmetic"], "Columns: airline name, AOG maintenance events (completed, is_aog = 1) followed by a completed flight of the same aircraft, average hours from the maintenance end_time to that aircraft's first completed departure after it (rounded 1); ordered by airline name.",
 """WITH r AS (
  SELECT a.airline_id,
         (SELECT MIN(f.actual_departure) FROM flights f
          WHERE f.aircraft_id = m.aircraft_id AND f.status = 'completed' AND f.actual_departure >= m.end_time) AS next_departure,
         m.end_time
  FROM maintenance_records m JOIN aircraft a ON a.aircraft_id = m.aircraft_id
  WHERE m.is_aog = 1 AND m.status = 'completed'
)
SELECT al.name AS airline_name, COUNT(*) AS aog_events,
       ROUND(AVG((julianday(next_departure) - julianday(end_time)) * 24), 1) AS avg_hours_to_next_departure
FROM r JOIN airlines al ON al.airline_id = r.airline_id
WHERE next_departure IS NOT NULL GROUP BY al.airline_id, al.name ORDER BY airline_name"""),
("H55", ["CTE", "running total", "strftime"], "Columns: year of created_date, customers created that year, cumulative customers up to that year; ordered by year.",
 """WITH y AS (
  SELECT substr(created_date, 1, 4) AS year, COUNT(*) AS new_customers FROM customers GROUP BY substr(created_date, 1, 4)
)
SELECT year, new_customers, SUM(new_customers) OVER (ORDER BY year) AS cumulative_customers FROM y ORDER BY year"""),
("H56", ["CTE", "ROW_NUMBER", "top N per group"], "Columns: airline name, origin iata_code, destination iata_code, completed flights: each airline's 3 busiest directed routes (ties: origin code, then destination code); ordered by airline name, flights DESC, origin, destination.",
 """WITH c AS (
  SELECT a.airline_id, o.iata_code AS origin, d.iata_code AS destination, COUNT(*) AS flights
  FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
  JOIN airports o ON o.airport_id = f.origin_airport_id JOIN airports d ON d.airport_id = f.destination_airport_id
  WHERE f.status = 'completed' GROUP BY a.airline_id, o.iata_code, d.iata_code
), r AS (
  SELECT c.*, ROW_NUMBER() OVER (PARTITION BY airline_id ORDER BY flights DESC, origin, destination) AS rn FROM c
)
SELECT al.name AS airline_name, r.origin, r.destination, r.flights
FROM r JOIN airlines al ON al.airline_id = r.airline_id WHERE r.rn <= 3
ORDER BY airline_name, r.flights DESC, r.origin, r.destination"""),
("H57", ["conditional aggregation", "HAVING", "percentage"], "Columns: employee_number, completed pilot duties (duty_role captain or first_officer), pilot-flying share in percent (rounded 1); pilots with at least 20 such duties and a share below 35%; ordered by share, employee_number.",
 """SELECT m.employee_number, COUNT(*) AS pilot_duties,
       ROUND(100.0 * SUM(ca.is_pilot_flying) / COUNT(*), 1) AS pilot_flying_pct
FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
WHERE ca.assignment_status = 'completed' AND ca.duty_role IN ('captain', 'first_officer')
GROUP BY m.crew_member_id, m.employee_number
HAVING COUNT(*) >= 20 AND 100.0 * SUM(ca.is_pilot_flying) / COUNT(*) < 35
ORDER BY pilot_flying_pct, m.employee_number"""),
("H58", ["CASE buckets", "date arithmetic", "GROUP BY expression"], "Columns: ageing bucket of invoices with status not 'paid' by days past due_date on 2025-12-20 ('not due', '1-30', '31-60', '61+'), number of invoices, SUM(amount_usd) rounded 2; ordered by the bucket order above.",
 """WITH b AS (
  SELECT amount_usd,
         CASE WHEN julianday('2025-12-20') - julianday(due_date) <= 0 THEN 'not due'
              WHEN julianday('2025-12-20') - julianday(due_date) <= 30 THEN '1-30'
              WHEN julianday('2025-12-20') - julianday(due_date) <= 60 THEN '31-60'
              ELSE '61+' END AS bucket
  FROM invoices WHERE status <> 'paid'
)
SELECT bucket, COUNT(*) AS invoices, ROUND(SUM(amount_usd), 2) AS amount_usd FROM b GROUP BY bucket
ORDER BY CASE bucket WHEN 'not due' THEN 0 WHEN '1-30' THEN 1 WHEN '31-60' THEN 2 ELSE 3 END"""),
("H59", ["CTE", "ROW_NUMBER", "month grouping"], "Columns: airline name, month 'YYYY-MM' (by actual_departure) with the most completed flights for that airline (ties: earlier month), completed flights that month; ordered by airline name.",
 """WITH c AS (
  SELECT a.airline_id, substr(f.actual_departure, 1, 7) AS month, COUNT(*) AS flights
  FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
  WHERE f.status = 'completed' GROUP BY a.airline_id, substr(f.actual_departure, 1, 7)
), r AS (
  SELECT c.*, ROW_NUMBER() OVER (PARTITION BY airline_id ORDER BY flights DESC, month) AS rn FROM c
)
SELECT al.name AS airline_name, r.month, r.flights FROM r JOIN airlines al ON al.airline_id = r.airline_id
WHERE r.rn = 1 ORDER BY airline_name"""),
("H60", ["two-level aggregation", "join multiplication trap"], "Columns: model, average number of crew assigned per completed flight (rounded 2); ordered by model.",
 """WITH c AS (
  SELECT ca.flight_id, COUNT(*) AS crew FROM crew_assignments ca GROUP BY ca.flight_id
)
SELECT t.model, ROUND(AVG(c.crew), 2) AS avg_crew_per_flight
FROM flights f JOIN c ON c.flight_id = f.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id
WHERE f.status = 'completed' GROUP BY t.type_id, t.model ORDER BY t.model"""),
("H61", ["multi-hop join", "ratio of sums"], "Columns: model, fuel burned per 100 km over completed flights with a fuel uplift = SUM(fuel_burned_kg) / SUM(distance_km) * 100 (rounded 1); ordered by the ratio DESC.",
 """SELECT t.model, ROUND(SUM(fu.fuel_burned_kg) * 100.0 / SUM(f.distance_km), 1) AS fuel_kg_per_100km
FROM fuel_uplifts fu JOIN flights f ON f.flight_id = fu.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id
WHERE f.status = 'completed' GROUP BY t.type_id, t.model ORDER BY fuel_kg_per_100km DESC"""),
("H62", ["JOIN", "conditional aggregation", "HAVING", "LIMIT"], "Columns: customer name, payments, share of payments made after the invoice's due_date in percent (rounded 1); customers with at least 30 payments; the 5 with the highest late share.",
 """SELECT c.name, COUNT(*) AS payments,
       ROUND(100.0 * SUM(CASE WHEN p.payment_date > i.due_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS late_pct
FROM payments p JOIN invoices i ON i.invoice_id = p.invoice_id JOIN customers c ON c.customer_id = p.customer_id
GROUP BY c.customer_id, c.name HAVING COUNT(*) >= 30
ORDER BY 100.0 * SUM(CASE WHEN p.payment_date > i.due_date THEN 1 ELSE 0 END) / COUNT(*) DESC LIMIT 5"""),
("H63", ["self-join", "COUNT DISTINCT", "HAVING"], "Columns: captain employee_number, number of different first officers flown with (completed assignments, roles captain and first_officer on the same flight); captains with at least 11; ordered by count DESC, employee_number.",
 """SELECT m.employee_number, COUNT(DISTINCT fo.crew_member_id) AS distinct_first_officers
FROM crew_assignments cp
JOIN crew_assignments fo ON fo.flight_id = cp.flight_id AND fo.duty_role = 'first_officer' AND fo.assignment_status = 'completed'
JOIN crew_members m ON m.crew_member_id = cp.crew_member_id
WHERE cp.duty_role = 'captain' AND cp.assignment_status = 'completed'
GROUP BY m.crew_member_id, m.employee_number HAVING COUNT(DISTINCT fo.crew_member_id) >= 11
ORDER BY distinct_first_officers DESC, m.employee_number"""),
("H64", ["scalar subquery", "HAVING", "comparison with overall average"], "Columns: destination iata_code, average arrival delay in minutes of completed flights there (rounded 1); only airports whose average is above the average over all completed flights; ordered by delay DESC.",
 """SELECT ap.iata_code, ROUND(AVG((julianday(f.actual_arrival) - julianday(f.scheduled_arrival)) * 1440), 1) AS avg_arrival_delay_min
FROM flights f JOIN airports ap ON ap.airport_id = f.destination_airport_id
WHERE f.status = 'completed'
GROUP BY ap.airport_id, ap.iata_code
HAVING AVG((julianday(f.actual_arrival) - julianday(f.scheduled_arrival)) * 1440)
     > (SELECT AVG((julianday(actual_arrival) - julianday(scheduled_arrival)) * 1440) FROM flights WHERE status = 'completed')
ORDER BY avg_arrival_delay_min DESC"""),
("H65", ["CTE", "COUNT DISTINCT", "date()", "LIMIT"], "Columns: tail_number, completed block hours per day flown = SUM(actual arrival - actual departure in hours) / number of distinct actual_departure dates (rounded 2); the 5 highest.",
 """SELECT a.tail_number,
       ROUND(SUM((julianday(f.actual_arrival) - julianday(f.actual_departure)) * 24)
             / COUNT(DISTINCT date(f.actual_departure)), 2) AS block_hours_per_day
FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
WHERE f.status = 'completed' GROUP BY a.aircraft_id, a.tail_number ORDER BY block_hours_per_day DESC LIMIT 5"""),
("H66", ["self-join", "date arithmetic", "HAVING"], "Columns: customs_country of the import declaration, shipments with a cleared export and a cleared import declaration, average hours from the export's cleared_at to the import's cleared_at (rounded 1); countries with at least 100 such shipments; ordered by hours DESC, country.",
 """SELECT im.customs_country, COUNT(*) AS shipments,
       ROUND(AVG((julianday(im.cleared_at) - julianday(ex.cleared_at)) * 24), 1) AS avg_hours_export_to_import
FROM customs_declarations im
JOIN customs_declarations ex ON ex.shipment_id = im.shipment_id AND ex.declaration_type = 'export' AND ex.status = 'cleared'
WHERE im.declaration_type = 'import' AND im.status = 'cleared'
GROUP BY im.customs_country HAVING COUNT(*) >= 100 ORDER BY avg_hours_export_to_import DESC, im.customs_country"""),
("H67", ["JOIN events", "date arithmetic", "MAX"], "Columns: service_level, shipments handed over (with a DLV event), average days from booking_date to the DLV event time (rounded 2), longest such time in days (rounded 2); ordered by service_level.",
 """SELECT s.service_level, COUNT(*) AS handed_over,
       ROUND(AVG(julianday(te.event_time) - julianday(s.booking_date)), 2) AS avg_days_to_handover,
       ROUND(MAX(julianday(te.event_time) - julianday(s.booking_date)), 2) AS max_days_to_handover
FROM shipments s JOIN tracking_events te ON te.shipment_id = s.shipment_id AND te.event_code = 'DLV'
GROUP BY s.service_level ORDER BY s.service_level"""),
("H68", ["multi-hop join", "date arithmetic", "conditional aggregation"], "Columns: insurer_name, claims, average days from the incident's reported_at to the claim's filed_date (rounded 1), share of claims with status 'paid' in percent (rounded 1); ordered by insurer_name.",
 """SELECT ic.insurer_name, COUNT(*) AS claims,
       ROUND(AVG(julianday(ic.filed_date) - julianday(i.reported_at)), 1) AS avg_days_to_file,
       ROUND(100.0 * SUM(CASE WHEN ic.status = 'paid' THEN 1 ELSE 0 END) / COUNT(*), 1) AS paid_pct
FROM insurance_claims ic JOIN incidents i ON i.incident_id = ic.incident_id
GROUP BY ic.insurer_name ORDER BY ic.insurer_name"""),
("H69", ["CTE", "DENSE_RANK", "top N per group with ties"], "Columns: sales_region, customer name, non-cancelled shipments, dense rank within the region: customers ranked 1 to 2 by shipments in their sales region (ties share a rank); ordered by region, rank, name.",
 """WITH c AS (
  SELECT cu.sales_region, cu.name, COUNT(*) AS shipments
  FROM shipments s JOIN customers cu ON cu.customer_id = s.customer_id
  WHERE s.status <> 'cancelled' GROUP BY cu.customer_id, cu.sales_region, cu.name
), r AS (
  SELECT c.*, DENSE_RANK() OVER (PARTITION BY sales_region ORDER BY shipments DESC) AS region_rank FROM c
)
SELECT sales_region, name, shipments, region_rank FROM r WHERE region_rank <= 2 ORDER BY sales_region, region_rank, name"""),
("H70", ["strftime('%w')", "CASE", "GROUP BY expression"], "Columns: weekday number of scheduled_departure (0 = Sunday ... 6 = Saturday), completed flights, average departure delay in minutes (rounded 1); ordered by weekday number.",
 """SELECT CAST(strftime('%w', scheduled_departure) AS INTEGER) AS weekday, COUNT(*) AS completed_flights,
       ROUND(AVG((julianday(actual_departure) - julianday(scheduled_departure)) * 1440), 1) AS avg_departure_delay_min
FROM flights WHERE status = 'completed' GROUP BY CAST(strftime('%w', scheduled_departure) AS INTEGER) ORDER BY weekday"""),
("H71", ["CTE", "COUNT DISTINCT", "two-level aggregation"], "Columns: airline name, completed flights carrying shipments of at least 3 different customers; ordered by count DESC, name.",
 """WITH m AS (
  SELECT fc.flight_id FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
  GROUP BY fc.flight_id HAVING COUNT(DISTINCT s.customer_id) >= 3
)
SELECT al.name AS airline_name, COUNT(*) AS multi_customer_flights
FROM m JOIN flights f ON f.flight_id = m.flight_id JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN airlines al ON al.airline_id = a.airline_id
WHERE f.status = 'completed' GROUP BY al.airline_id, al.name ORDER BY multi_customer_flights DESC, airline_name"""),
("H72", ["CTE", "NTILE", "share of total"], "Columns: revenue quintile (NTILE(5) over customers by invoiced USD DESC, ties by customer_id; 1 = top), customers in it, invoiced USD (rounded 2), share of all invoiced revenue in percent (rounded 1); ordered by quintile.",
 """WITH r AS (
  SELECT s.customer_id, SUM(i.amount_usd) AS revenue
  FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id GROUP BY s.customer_id
), q AS (
  SELECT r.*, NTILE(5) OVER (ORDER BY revenue DESC, customer_id) AS quintile FROM r
)
SELECT quintile, COUNT(*) AS customers, ROUND(SUM(revenue), 2) AS invoiced_usd,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM r), 1) AS share_pct
FROM q GROUP BY quintile ORDER BY quintile"""),
("H73", ["anti-join", "NOT EXISTS", "GROUP BY"], "Columns: origin iata_code, temperature-controlled shipments (any status) originating there; only airports without any 'cold_chain' warehouse; ordered by count DESC, iata_code.",
 """SELECT ap.iata_code, COUNT(*) AS temp_controlled_shipments
FROM shipments s JOIN airports ap ON ap.airport_id = s.origin_airport_id
WHERE s.is_temperature_controlled = 1
  AND NOT EXISTS (SELECT 1 FROM warehouses w WHERE w.airport_id = ap.airport_id AND w.warehouse_type = 'cold_chain')
GROUP BY ap.airport_id, ap.iata_code ORDER BY temp_controlled_shipments DESC, ap.iata_code"""),
("H74", ["WITH RECURSIVE", "LEFT JOIN", "zero-filled series"], "Columns: every month '2025-01' to '2025-12', number of flights with cancellation_reason 'weather' scheduled that month (0 when none); ordered by month.",
 """WITH RECURSIVE months(m) AS (
  SELECT '2025-01-01' UNION ALL SELECT date(m, '+1 month') FROM months WHERE m < '2025-12-01'
)
SELECT substr(months.m, 1, 7) AS month, COUNT(f.flight_id) AS weather_cancellations
FROM months LEFT JOIN flights f
  ON substr(f.scheduled_departure, 1, 7) = substr(months.m, 1, 7) AND f.cancellation_reason = 'weather'
GROUP BY months.m ORDER BY month"""),
("H75", ["gaps and islands", "ROW_NUMBER", "julianday"], "Columns: tail_number, longest run of consecutive calendar days with at least one completed departure (by date of actual_departure); aircraft with a run of at least 3 days; ordered by run DESC, tail_number.",
 """WITH d AS (
  SELECT DISTINCT aircraft_id, date(actual_departure) AS day FROM flights WHERE status = 'completed'
), g AS (
  SELECT aircraft_id, day,
         julianday(day) - ROW_NUMBER() OVER (PARTITION BY aircraft_id ORDER BY day) AS grp
  FROM d
), runs AS (
  SELECT aircraft_id, grp, COUNT(*) AS run_days FROM g GROUP BY aircraft_id, grp
)
SELECT a.tail_number, MAX(r.run_days) AS longest_run_days
FROM runs r JOIN aircraft a ON a.aircraft_id = r.aircraft_id
GROUP BY a.aircraft_id, a.tail_number HAVING MAX(r.run_days) >= 3 ORDER BY longest_run_days DESC, a.tail_number"""),
("H76", ["CTE", "AVG OVER PARTITION", "comparison with group average"], "Columns: customer name, customer_type, average invoice amount_usd of the customer, average over the customers of the same type (mean of the customer averages), both rounded 2; customers at least 1.5 times their type average; ordered by customer_type, name.",
 """WITH c AS (
  SELECT cu.customer_id, cu.name, cu.customer_type, AVG(i.amount_usd) AS avg_invoice
  FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id JOIN customers cu ON cu.customer_id = s.customer_id
  GROUP BY cu.customer_id, cu.name, cu.customer_type
), t AS (
  SELECT c.*, AVG(avg_invoice) OVER (PARTITION BY customer_type) AS type_avg FROM c
)
SELECT name, customer_type, ROUND(avg_invoice, 2) AS avg_invoice_usd, ROUND(type_avg, 2) AS type_avg_usd
FROM t WHERE avg_invoice >= 1.5 * type_avg ORDER BY customer_type, name"""),
("H77", ["date arithmetic", "conditional aggregation", "resolved only"], "Columns: severity, resolved incidents, average days from reported_at to resolved_at (rounded 1), share resolved within 30 days in percent (rounded 1); ordered by severity.",
 """SELECT severity, COUNT(*) AS resolved_incidents,
       ROUND(AVG(julianday(resolved_at) - julianday(reported_at)), 1) AS avg_days_to_resolve,
       ROUND(100.0 * SUM(CASE WHEN julianday(resolved_at) - julianday(reported_at) <= 30 THEN 1 ELSE 0 END) / COUNT(*), 1) AS within_30d_pct
FROM incidents WHERE resolved = 1 GROUP BY severity ORDER BY severity"""),
("H78", ["CTE", "ROW_NUMBER", "derived ratio"], "Columns: commodity_category, awb_number, invoice USD per chargeable kg (amount_usd / chargeable_weight_kg, rounded 2): per category the invoiced shipment with the highest yield (ties: smaller shipment_id); ordered by category.",
 """WITH y AS (
  SELECT s.commodity_category, s.awb_number, s.shipment_id, i.amount_usd / s.chargeable_weight_kg AS usd_per_kg
  FROM invoices i JOIN shipments s ON s.shipment_id = i.shipment_id
), r AS (
  SELECT y.*, ROW_NUMBER() OVER (PARTITION BY commodity_category ORDER BY usd_per_kg DESC, shipment_id) AS rn FROM y
)
SELECT commodity_category, awb_number, ROUND(usd_per_kg, 2) AS usd_per_chargeable_kg FROM r WHERE rn = 1 ORDER BY commodity_category"""),
("H79", ["CTE", "window SUM", "market share"], "Columns: month 'YYYY-MM' (Oct-Dec 2025, by actual_departure), airline name, completed flights, share of that month's completed flights in percent (rounded 1); ordered by month, flights DESC, airline name.",
 """WITH c AS (
  SELECT substr(f.actual_departure, 1, 7) AS month, a.airline_id, COUNT(*) AS flights
  FROM flights f JOIN aircraft a ON a.aircraft_id = f.aircraft_id
  WHERE f.status = 'completed' AND f.actual_departure >= '2025-10-01' AND f.actual_departure < '2026-01-01'
  GROUP BY substr(f.actual_departure, 1, 7), a.airline_id
)
SELECT c.month, al.name AS airline_name, c.flights,
       ROUND(100.0 * c.flights / SUM(c.flights) OVER (PARTITION BY c.month), 1) AS share_pct
FROM c JOIN airlines al ON al.airline_id = c.airline_id ORDER BY c.month, c.flights DESC, airline_name"""),
("H80", ["self-join on legs", "multi-hop join", "GROUP BY"], "Columns: airline name of leg 1, number of two-leg shipments whose leg 2 is flown by a different airline (interline); ordered by count DESC, name.",
 """SELECT al.name AS first_leg_airline, COUNT(*) AS interline_shipments
FROM flight_cargo l1
JOIN flight_cargo l2 ON l2.shipment_id = l1.shipment_id AND l2.leg_number = 2
JOIN flights f1 ON f1.flight_id = l1.flight_id JOIN aircraft a1 ON a1.aircraft_id = f1.aircraft_id
JOIN flights f2 ON f2.flight_id = l2.flight_id JOIN aircraft a2 ON a2.aircraft_id = f2.aircraft_id
JOIN airlines al ON al.airline_id = a1.airline_id
WHERE l1.leg_number = 1 AND a1.airline_id <> a2.airline_id
GROUP BY al.airline_id, al.name ORDER BY interline_shipments DESC, first_leg_airline"""),
]

TALK_EASY.update({
"E41": ("Which airports don't have customs open around the clock? Just the codes.",
        "List [[airports.iata_code]] from [[airports]] where [[airports.has_24h_customs]] = 0, sorted by code.",
        "Which stations lack 24-hour customs clearance? Give the airport codes for the night-operations review.",
        "No 24h customs where?"),
"E42": ("Which airports have five or more runways, and how many does each have?",
        "Return [[airports.iata_code]] and [[airports.runway_count]] from [[airports]] where [[airports.runway_count]] >= 5, most runways first, then by code.",
        "Which stations in the network offer five or more runways? Show the runway count per airport code.",
        "Airports with lots of runways?"),
"E43": ("How many tracking scans came in through the customer portal?",
        "Count the rows in [[tracking_events]] where [[tracking_events.recorded_by]] = 'customer_portal'.",
        "What is the volume of shipment status events captured via the customer self-service portal?",
        "Portal scans?"),
"E44": ("Which airlines were founded before 2000, and in what year?",
        "Select [[airlines.name]] and [[airlines.founded_year]] from [[airlines]] where [[airlines.founded_year]] < 2000, ordered by year.",
        "Which of our partner carriers were established before 2000? List them with their founding year.",
        "Old airlines?"),
"E45": ("Which airlines aren't pure cargo operators?",
        "List [[airlines.name]] from [[airlines]] where [[airlines.is_cargo_only]] = 0, sorted by name.",
        "Which carriers run a mixed passenger and cargo business rather than a freighter-only model?",
        "Not cargo-only airlines?"),
"E46": ("Which aircraft type can carry the most payload, and how much?",
        "From [[aircraft_types]] return [[aircraft_types.model]] and [[aircraft_types.max_payload_kg]] for the row with the highest [[aircraft_types.max_payload_kg]].",
        "Which freighter model in our fleet mix has the highest payload capability, in kg?",
        "Biggest plane?"),
"E47": ("Which aircraft types can fly at least 8,000 km, and what's their range?",
        "Select [[aircraft_types.model]], [[aircraft_types.max_range_km]] from [[aircraft_types]] where [[aircraft_types.max_range_km]] >= 8000, longest range first.",
        "Which models give us long-haul reach of 8,000 km or more? Show the range of each.",
        "Long-range models?"),
"E48": ("How many of our planes were built before 2010?",
        "Count rows in [[aircraft]] where [[aircraft.year_manufactured]] < 2010.",
        "How many airframes in the fleet were manufactured before 2010, for the fleet renewal case?",
        "How many old planes?"),
"E49": ("Which leased planes have leases ending before 2030, who are they leased from, and when do the leases end?",
        "Return [[aircraft.tail_number]], [[aircraft.lessor_name]], [[aircraft.lease_end_date]] from [[aircraft]] where [[aircraft.ownership]] = 'leased' and [[aircraft.lease_end_date]] < '2030-01-01', ordered by end date.",
        "Which leased airframes come off lease before 2030? List tail, lessor and lease expiry for the fleet planning committee.",
        "Leases ending soon?"),
"E50": ("Which plane has the most flight hours on it, and how many?",
        "From [[aircraft]] return [[aircraft.tail_number]] and [[aircraft.total_flight_hours]] of the row with the largest [[aircraft.total_flight_hours]].",
        "Which airframe carries the highest accumulated flight hours in the fleet?",
        "Most used plane?"),
"E51": ("How many customers aren't known shippers?",
        "Count rows in [[customers]] with [[customers.is_known_shipper]] = 0.",
        "How many accounts lack known-shipper security status and so need extra screening?",
        "Unscreened customers?"),
"E52": ("Which five customers have the biggest credit limits, and what are they?",
        "Return [[customers.name]] and [[customers.credit_limit_usd]] from [[customers]], top 5 by [[customers.credit_limit_usd]] descending.",
        "Who are the five accounts with the highest approved credit exposure, and at what limit?",
        "Top credit limits?"),
"E53": ("How many customers signed up with us in 2024?",
        "Count rows in [[customers]] whose [[customers.created_date]] falls in 2024.",
        "How many new accounts did we onboard in calendar year 2024?",
        "New customers last year?"),
"E54": ("What's the average credit limit of our platinum customers?",
        "Return AVG([[customers.credit_limit_usd]]) over [[customers]] where [[customers.loyalty_tier]] = 'platinum', rounded to 2 decimals.",
        "What is the mean credit line extended to platinum-tier accounts, in USD?",
        "Platinum credit?"),
"E55": ("Which warehouses aren't open 24 hours? Give me their codes.",
        "List [[warehouses.warehouse_code]] from [[warehouses]] where [[warehouses.operates_24h]] = 0, sorted.",
        "Which handling facilities do not run a 24/7 operation? Provide the warehouse codes.",
        "Warehouses that close?"),
"E56": ("Which three warehouses have the highest monthly rent, and how much is it?",
        "Return [[warehouses.warehouse_code]] and [[warehouses.monthly_rent_usd]] from [[warehouses]], top 3 by [[warehouses.monthly_rent_usd]] descending.",
        "Which three facilities carry the highest monthly lease cost, and what do we pay for each?",
        "Priciest warehouses?"),
"E57": ("On average, what duty rate do we pay on imports into Japan?",
        "Return AVG([[customs_declarations.duty_rate_pct]]) from [[customs_declarations]] where [[customs_declarations.declaration_type]] = 'import' and [[customs_declarations.customs_country]] = 'Japan', rounded to 2.",
        "What is the average import duty rate, in percent, applied to our consignments entering Japan?",
        "Japan duty rate?"),
"E58": ("How many warehouses are both bonded and high security?",
        "Count rows in [[warehouses]] with [[warehouses.is_bonded]] = 1 and [[warehouses.security_level]] = 'high'.",
        "How many facilities combine customs-bonded status with a high security rating?",
        "Bonded high-security sites?"),
"E59": ("How many crew licences run out before 2026?",
        "Count rows in [[crew_members]] whose [[crew_members.license_expiry_date]] is before '2026-01-01'.",
        "How many crew licences lapse before the start of 2026, for the compliance tracker?",
        "Licences expiring?"),
"E60": ("Who's our longest-serving crew member, going by hire date?",
        "From [[crew_members]] return [[crew_members.employee_number]], [[crew_members.first_name]], [[crew_members.last_name]], [[crew_members.hire_date]] of the earliest [[crew_members.hire_date]].",
        "Which crew member has the longest tenure with us, and when were they hired?",
        "Earliest hire?"),
"E61": ("How many damage incidents were caused by bad packaging?",
        "Count rows in [[incidents]] where [[incidents.incident_type]] = 'damage' and [[incidents.root_cause]] = 'packaging'.",
        "How many cargo damage cases trace back to packaging failures?",
        "Packaging damage count?"),
"E62": ("How many flights are still scheduled and haven't flown yet?",
        "Count rows in [[flights]] where [[flights.status]] = 'scheduled'.",
        "How many departures remain on the forward schedule?",
        "Upcoming flights?"),
"E63": ("How far is an average completed flight, in km?",
        "Return AVG([[flights.distance_km]]) over [[flights]] where [[flights.status]] = 'completed', rounded to 1 decimal.",
        "What is the average stage length of the sectors we actually operated, in kilometres?",
        "Average flight length?"),
"E64": ("How many flights got delay code 93?",
        "Count rows in [[flights]] where [[flights.delay_code]] = '93'.",
        "How many sectors were coded with IATA delay code 93 (reactionary, aircraft rotation)?",
        "Code 93 delays?"),
"E65": ("Which insurance claims are still open, and how much was claimed on each?",
        "Return [[insurance_claims.claim_number]] and [[insurance_claims.claimed_amount_usd]] from [[insurance_claims]] where [[insurance_claims.status]] is 'filed' or 'under_review', ordered by claim number.",
        "Which claims are still awaiting a decision from the insurer, and what is the claimed exposure on each?",
        "Open claims?"),
"E66": ("How much per diem have loadmasters been paid in total?",
        "Return SUM([[crew_assignments.per_diem_usd]]) from [[crew_assignments]] where [[crew_assignments.duty_role]] = 'loadmaster', rounded to 2.",
        "What is the total per diem spend on loadmaster duties, in USD?",
        "Loadmaster allowances?"),
"E67": ("How many crew assignments are rostered but not flown yet?",
        "Count rows in [[crew_assignments]] where [[crew_assignments.assignment_status]] = 'rostered'.",
        "How many crew duties are currently on the forward roster?",
        "Rostered duties?"),
"E68": ("On average, how many block minutes does a completed crew duty get credited?",
        "Return AVG([[crew_assignments.block_minutes_credited]]) over [[crew_assignments]] where [[crew_assignments.assignment_status]] = 'completed', rounded to 1.",
        "What is the average credited block time per completed crew duty, in minutes?",
        "Average block minutes?"),
"E69": ("Which maintenance companies have worked on our planes?",
        "List the DISTINCT [[maintenance_records.mro_provider]] values in [[maintenance_records]], sorted.",
        "Which MRO providers appear in our maintenance history? One line each.",
        "Who does our maintenance?"),
"E70": ("How many labour hours went into completed A-checks?",
        "Return SUM([[maintenance_records.labor_hours]]) from [[maintenance_records]] where [[maintenance_records.check_type]] = 'A_check' and [[maintenance_records.status]] = 'completed', rounded to 1.",
        "What is the total labour-hour consumption of completed A-checks?",
        "A-check hours?"),
"E71": ("Which maintenance jobs aren't finished yet, and what state are they in?",
        "Return [[maintenance_records.work_order_number]], [[maintenance_records.status]] from [[maintenance_records]] where [[maintenance_records.status]] <> 'completed', ordered by work order.",
        "Which work orders are still open (planned or in progress)? List each with its status.",
        "Open work orders?"),
"E72": ("How many fuel uplifts had some sustainable aviation fuel blended in?",
        "Count rows in [[fuel_uplifts]] where [[fuel_uplifts.saf_blend_pct]] > 0.",
        "How many refuelling events included a SAF blend, for the sustainability report?",
        "SAF uplifts?"),
"E73": ("What's the biggest single fuel bill we've had?",
        "Return MAX([[fuel_uplifts.total_cost_usd]]) from [[fuel_uplifts]].",
        "What was the highest cost of a single fuel uplift, in USD?",
        "Biggest fuel bill?"),
"E74": ("How much have we spent on fuel from Skyline Fuels?",
        "Return SUM([[fuel_uplifts.total_cost_usd]]) from [[fuel_uplifts]] where [[fuel_uplifts.supplier_name]] = 'Skyline Fuels', rounded to 2.",
        "What is our total fuel spend with the supplier Skyline Fuels?",
        "Skyline spend?"),
"E75": ("How many shipments got cancelled?",
        "Count rows in [[shipments]] where [[shipments.status]] = 'cancelled'.",
        "How many bookings were cancelled before carriage?",
        "Cancellations?"),
"E76": ("How many dangerous goods shipments do we have in each DG class?",
        "Group [[shipments]] where [[shipments.dg_class]] IS NOT NULL by [[shipments.dg_class]] and count rows, ordered by class.",
        "What is the split of our dangerous-goods bookings by hazard class?",
        "DG classes?"),
"E77": ("How many pieces of pharma cargo have been booked in total?",
        "Return SUM([[shipments.pieces]]) from [[shipments]] where [[shipments.commodity_category]] = 'pharmaceuticals'.",
        "What is the total piece count booked in the pharmaceuticals vertical?",
        "Pharma pieces?"),
"E78": ("How many shipment legs were the second leg of a connection?",
        "Count rows in [[flight_cargo]] where [[flight_cargo.leg_number]] = 2.",
        "How many onward (second-sector) legs did we handle for connecting shipments?",
        "Second legs?"),
"E79": ("How many invoices included a dangerous goods surcharge?",
        "Count rows in [[invoices]] where [[invoices.dg_surcharge_usd]] > 0.",
        "How many invoices carried a DG surcharge line?",
        "DG surcharge invoices?"),
"E80": ("How many payments haven't been reconciled yet?",
        "Count rows in [[payments]] with [[payments.is_reconciled]] = 0.",
        "How many receipts are still unreconciled in finance?",
        "Unreconciled?"),
})

TALK_MODERATE.update({
"M41": ("What's the home hub airport of each airline?",
        "Join [[airlines]] to [[airports]] on [[airlines.home_hub_airport_id]] = [[airports.airport_id]]; return [[airlines.name]] and [[airports.iata_code]], ordered by airline name.",
        "Where is each carrier's home hub? Give the airport code per airline.",
        "Airline hubs?"),
"M42": ("How many of our planes are Airbus and how many are Boeing?",
        "Join [[aircraft]] to [[aircraft_types]] on [[aircraft.type_id]] and count [[aircraft]] rows per [[aircraft_types.manufacturer]], ordered by manufacturer.",
        "What is the fleet split by airframe manufacturer?",
        "Fleet by maker?"),
"M43": ("Which countries have at least five of our customers, and how many each?",
        "Group [[customers]] by [[customers.country]], count rows, keep groups with COUNT(*) >= 5; order by count descending, then country.",
        "In which countries do we hold five or more customer accounts? Rank them by account count.",
        "Where are most customers?"),
"M44": ("How many completed flights left from each European airport?",
        "Join [[flights]] to [[airports]] on [[flights.origin_airport_id]]; for [[airports.region]] = 'europe' and [[flights.status]] = 'completed', count per [[airports.iata_code]], most first.",
        "How many completed departures did each European station generate? Rank the stations.",
        "Europe departures?"),
"M45": ("How do our flights break down by type and status?",
        "Group [[flights]] by [[flights.flight_type]] and [[flights.status]], count rows, order by type then status.",
        "Give me the flight count matrix of scheduled vs charter operations by flight status.",
        "Flights by type and status?"),
"M46": ("Which planes have never had a single flight?",
        "Return [[aircraft.tail_number]] for rows in [[aircraft]] with no matching row in [[flights]] on [[flights.aircraft_id]], sorted.",
        "Which airframes have not been assigned to any flight at all?",
        "Planes not flying?"),
"M47": ("Which customers have never shipped anything with us?",
        "Return [[customers.name]] from [[customers]] that have no row in [[shipments]] with the same [[shipments.customer_id]], sorted by name.",
        "Which accounts have zero shipment activity on record?",
        "Inactive customers?"),
"M48": ("For each airline, how many active crew do they have, and how many of them are captains?",
        "Join [[crew_members]] to [[airlines]]; for [[crew_members.is_active]] = 1 return per [[airlines.name]] COUNT(*) and the count where [[crew_members.crew_rank]] = 'captain'; order by airline name.",
        "What is each carrier's active crew headcount, and how many commanders are in it?",
        "Crew per airline?"),
"M49": ("At which five airports did we take on the most fuel, in litres?",
        "Join [[fuel_uplifts]] to [[airports]] on [[fuel_uplifts.airport_id]]; SUM([[fuel_uplifts.quantity_litres]]) per [[airports.iata_code]]; top 5 descending.",
        "Which five stations account for the largest fuel uplift volumes, in litres?",
        "Where do we fuel most?"),
"M50": ("Which airline uses the most sustainable aviation fuel on average?",
        "Join [[fuel_uplifts]] to [[flights]], [[aircraft]] and [[airlines]]; AVG([[fuel_uplifts.saf_blend_pct]]) per [[airlines.name]] rounded to 2, highest first.",
        "Rank the carriers by their average SAF blend percentage across all uplifts.",
        "SAF by airline?"),
"M51": ("How many AOG jobs has each maintenance company handled?",
        "Count rows of [[maintenance_records]] with [[maintenance_records.is_aog]] = 1 per [[maintenance_records.mro_provider]]; order by count descending, then provider.",
        "Which MRO providers handle our aircraft-on-ground events, and how many each?",
        "AOG by MRO?"),
"M52": ("Which five planes cost the most to maintain, counting finished jobs only?",
        "Join [[maintenance_records]] to [[aircraft]]; for [[maintenance_records.status]] = 'completed' SUM([[maintenance_records.parts_cost_usd]] + [[maintenance_records.labor_cost_usd]]) per [[aircraft.tail_number]], rounded to 2; top 5.",
        "Which five airframes drove the highest completed maintenance spend (parts plus labour)?",
        "Most expensive planes to fix?"),
"M53": ("Which airports have done at least 30 maintenance jobs, and how many?",
        "Join [[maintenance_records]] to [[airports]] on [[maintenance_records.airport_id]]; count per [[airports.iata_code]] with HAVING COUNT(*) >= 30; order by count descending, code.",
        "Which stations are our main maintenance bases, with 30 or more work orders each?",
        "Maintenance bases?"),
"M54": ("Which five airports received the most delivered shipments?",
        "Join [[shipments]] to [[airports]] on [[shipments.destination_airport_id]]; count rows with [[shipments.status]] = 'delivered' per [[airports.iata_code]]; top 5.",
        "What are our top five inbound destinations by delivered shipments?",
        "Top destinations?"),
"M55": ("For each type of customer, how many shipments and how much declared value do we have?",
        "Join [[shipments]] to [[customers]]; per [[customers.customer_type]] return COUNT(*) and SUM([[shipments.declared_value_usd]]) rounded to 2, ordered by type.",
        "Break down shipment volume and declared cargo value by customer segment.",
        "Value by customer type?"),
"M56": ("How many temperature-controlled shipments were booked each month?",
        "Count [[shipments]] with [[shipments.is_temperature_controlled]] = 1 grouped by substr([[shipments.booking_date]], 1, 7), ordered by month.",
        "What is the monthly booking trend for our temperature-controlled product?",
        "Cold shipments per month?"),
"M57": ("For each kind of ULD, how many legs did we load and how heavy was the average shipment on them?",
        "Join [[flight_cargo]] to [[shipments]]; per [[flight_cargo.uld_type]] return COUNT(*) and AVG([[shipments.total_weight_kg]]) rounded to 1; order by ULD type.",
        "By unit load device type, how many legs were built and what was the average shipment weight per leg?",
        "ULD stats?"),
"M58": ("How many unpaid invoices are past their due date, by customer region?",
        "Join [[invoices]] to [[shipments]] and [[customers]]; count invoices with [[invoices.status]] <> 'paid' and [[invoices.due_date]] < '2025-12-20' per [[customers.sales_region]]; most first.",
        "Where is our overdue receivables count concentrated, by sales region?",
        "Overdue invoices by region?"),
"M59": ("What's the average invoice for each service level?",
        "Join [[invoices]] to [[shipments]]; AVG([[invoices.amount_usd]]) per [[shipments.service_level]] rounded to 2, ordered by service level.",
        "What is the average billed value per shipment for each product tier (express, standard, economy)?",
        "Invoice size by service?"),
"M60": ("For each foreign currency we got paid in, how many payments were there and what were they worth in dollars?",
        "From [[payments]] where [[payments.original_currency]] <> 'USD', group by [[payments.original_currency]]: COUNT(*) and SUM([[payments.amount_usd]]) rounded to 2; largest sum first.",
        "What is our non-dollar cash collection by currency, in count and USD value?",
        "Foreign currency payments?"),
"M61": ("Which five customers paid the most in bank charges?",
        "Join [[payments]] to [[customers]] on [[payments.customer_id]]; SUM([[payments.bank_charges_usd]]) per [[customers.name]] rounded to 2; top 5.",
        "Which five accounts incur the highest bank fees on their remittances?",
        "Bank fees by customer?"),
"M62": ("For each root cause, how many incidents were there and how many got resolved?",
        "Group [[incidents]] by [[incidents.root_cause]]: COUNT(*) and the count with [[incidents.resolved]] = 1; order by root cause.",
        "Give the incident count and the resolved count per root cause category.",
        "Incidents by cause?"),
"M63": ("Which airline's flights had the most cargo incidents?",
        "Join [[incidents]] to [[flight_cargo]], [[flights]], [[aircraft]] and [[airlines]]; count incidents per [[airlines.name]], most first.",
        "Rank the operating carriers by the number of cargo incidents on their flights.",
        "Incidents per airline?"),
"M64": ("Which customers have filed three or more insurance claims, and how much have they claimed?",
        "Join [[insurance_claims]] to [[customers]] on [[insurance_claims.customer_id]]; per [[customers.name]] COUNT(*) and SUM([[insurance_claims.claimed_amount_usd]]) rounded to 2; HAVING COUNT(*) >= 3; order by count descending, name.",
        "Which accounts are repeat claimants (three or more claims), and what is their total claimed amount?",
        "Frequent claimants?"),
"M65": ("In which countries do our customs declarations get held, and how often?",
        "Count rows of [[customs_declarations]] with [[customs_declarations.status]] = 'held' per [[customs_declarations.customs_country]]; most first, then country.",
        "Which customs jurisdictions hold our declarations most often?",
        "Customs holds?"),
"M66": ("Which five kinds of goods brought in the most import value through customs?",
        "From [[customs_declarations]] with [[customs_declarations.declaration_type]] = 'import', SUM([[customs_declarations.customs_value_usd]]) per [[customs_declarations.goods_description]] rounded to 2; top 5.",
        "What are our top five import commodities by declared customs value?",
        "Top imports?"),
"M67": ("Which five warehouses handle the most customs paperwork?",
        "Join [[customs_declarations]] to [[warehouses]] on [[customs_declarations.warehouse_id]]; count per [[warehouses.warehouse_code]]; top 5.",
        "Which five facilities process the highest number of customs declarations?",
        "Busiest customs warehouses?"),
"M68": ("At which five airports do customers get notified to pick up cargo most often?",
        "Join [[tracking_events]] to [[airports]]; count rows with [[tracking_events.event_code]] = 'NFD' per [[airports.iata_code]]; top 5.",
        "Which five stations issue the most notifications for delivery (NFD)?",
        "Most NFDs?"),
"M69": ("Which airports have shipments marked delivered that were never actually handed over?",
        "Join [[shipments]] to [[airports]] on [[shipments.destination_airport_id]]; count [[shipments]] with [[shipments.status]] = 'delivered' and no [[tracking_events]] row with [[tracking_events.event_code]] = 'DLV'; per [[airports.iata_code]], most first.",
        "Where do we have landed-but-not-released consignments (delivered status, no DLV handover scan), by destination?",
        "Delivered but not handed over?"),
"M70": ("Which three pilots have flown the most completed sectors as pilot flying?",
        "Join [[crew_assignments]] to [[crew_members]]; count rows with [[crew_assignments.is_pilot_flying]] = 1 and [[crew_assignments.assignment_status]] = 'completed' per [[crew_members.employee_number]]; top 3 (ties by employee number).",
        "Who are the three most active handling pilots by completed sectors flown?",
        "Who flies the most?"),
"M71": ("At each base, how many active captains are there and how many flight hours do they average?",
        "Join [[crew_members]] to [[airports]] on [[crew_members.base_airport_id]]; for [[crew_members.crew_rank]] = 'captain' and [[crew_members.is_active]] = 1, COUNT(*) and AVG([[crew_members.total_flight_hours]]) rounded to 0 per [[airports.iata_code]]; order by code.",
        "What is the active captain headcount and average experience (flight hours) at each crew base?",
        "Captains per base?"),
"M72": ("How much per diem has each airline paid its crew on completed duties?",
        "Join [[crew_assignments]] to [[crew_members]] and [[airlines]] (via [[crew_members.airline_id]]); SUM([[crew_assignments.per_diem_usd]]) where [[crew_assignments.assignment_status]] = 'completed', rounded to 2, per [[airlines.name]]; largest first.",
        "Rank the carriers by crew per diem cost on completed duties.",
        "Per diem by airline?"),
"M73": ("How late do completed flights leave in each kind of weather?",
        "From [[flights]] where [[flights.status]] = 'completed' and [[flights.weather_at_departure]] IS NOT NULL: per weather COUNT(*) and AVG(([[flights.actual_departure]] - [[flights.scheduled_departure]]) in minutes) rounded to 1; worst first.",
        "What is the average departure delay by weather condition at departure?",
        "Weather delays?"),
"M74": ("How many flights were cancelled each month?",
        "Count [[flights]] with [[flights.status]] = 'cancelled' grouped by substr([[flights.scheduled_departure]], 1, 7), ordered by month.",
        "Show the monthly flight cancellation count.",
        "Cancellations per month?"),
"M75": ("How many owned and how many leased planes does each airline have?",
        "LEFT JOIN [[airlines]] to [[aircraft]]; per [[airlines.name]] count rows with [[aircraft.ownership]] = 'owned' and with 'leased' (0 if none); order by airline name.",
        "What is the owned versus leased fleet mix for each carrier?",
        "Owned vs leased?"),
"M76": ("For each Asia-Pacific airport, how many warehouses and how much floor space do we have?",
        "Join [[warehouses]] to [[airports]]; for [[airports.region]] = 'asia_pacific' return COUNT(*) and SUM([[warehouses.floor_area_m2]]) per [[airports.iata_code]]; largest area first.",
        "What is our warehouse footprint (facilities and square metres) at each Asia-Pacific station?",
        "APAC warehouse space?"),
"M77": ("For express shipments, how many days do customers give us between booking and requested delivery, by origin airport?",
        "Join [[shipments]] to [[airports]] on [[shipments.origin_airport_id]]; for [[shipments.service_level]] = 'express' AVG(julianday([[shipments.requested_delivery_date]]) - julianday([[shipments.booking_date]])) rounded to 2 per [[airports.iata_code]]; order by code.",
        "What lead time do express customers request from booking to delivery, by origin station?",
        "Express lead times?"),
"M78": ("For each payment term, how many invoices are there and what's the average amount?",
        "Group [[invoices]] by [[invoices.payment_terms_days]]: COUNT(*) and AVG([[invoices.amount_usd]]) rounded to 2; order by terms.",
        "Break down invoice count and average ticket size by credit terms.",
        "Invoices by terms?"),
"M79": ("Which customers ship dangerous goods most often (at least 8 times)?",
        "Join [[shipments]] to [[customers]]; count rows with [[shipments.is_dangerous_goods]] = 1 per [[customers.name]], HAVING COUNT(*) >= 8; order by count descending, name.",
        "Which accounts are our heavy DG shippers, with eight or more dangerous-goods bookings?",
        "Big DG customers?"),
"M80": ("For each aircraft model, how much fuel does a flight burn on average?",
        "Join [[fuel_uplifts]] to [[flights]], [[aircraft]] and [[aircraft_types]]; AVG([[fuel_uplifts.fuel_burned_kg]]) per [[aircraft_types.model]] rounded to 0; highest first.",
        "What is the average trip fuel burn per sector for each fleet type?",
        "Fuel burn by model?"),
})

TALK_HARD.update({
"H41": ("In each sales region, which customer have we invoiced the most, and how much?",
        "Per [[customers.sales_region]], find the [[customers.name]] with the largest SUM([[invoices.amount_usd]]) (via [[shipments]]; ties: smaller [[customers.customer_id]]) and that sum rounded to 2.",
        "Who is the top revenue account in each sales region?",
        "Best customer per region?"),
"H42": ("What did we spend on fuel each month, and what's the three-month moving average?",
        "Per month of [[fuel_uplifts.uplift_time]], SUM([[fuel_uplifts.total_cost_usd]]) and AVG of that monthly sum over the current and 2 preceding months (window ROWS 2 PRECEDING), both rounded to 2.",
        "Show monthly fuel spend with a rolling three-month average to smooth out the trend.",
        "Fuel cost trend?"),
"H43": ("Which five planes went the longest between two maintenance jobs, and how many days was that?",
        "For completed [[maintenance_records]], use LAG([[maintenance_records.start_time]]) per [[maintenance_records.aircraft_id]] to get gaps in days; return [[aircraft.tail_number]] and the largest gap rounded to 1; top 5.",
        "Which five airframes had the longest interval between consecutive maintenance visits?",
        "Longest without maintenance?"),
"H44": ("In each airline, which captain has logged the most block hours as captain, and how many?",
        "Per [[crew_members.airline_id]], the [[crew_members.employee_number]] with the largest SUM([[crew_assignments.block_minutes_credited]])/60 over completed [[crew_assignments]] with [[crew_assignments.duty_role]] = 'captain' (ties: employee number); return [[airlines.name]], employee number and hours rounded to 1.",
        "Who is the most productive commander at each carrier, measured by credited block hours?",
        "Top captain per airline?"),
"H45": ("Which customers did we invoice more than 1.5 times as much in the second half of 2025 as in the first half?",
        "Per [[customers.name]] (via [[shipments]]), SUM([[invoices.amount_usd]]) for [[invoices.issued_date]] in Jan-Jun and in Jul-Dec 2025, rounded to 2; keep customers where H2 > 1.5 * H1; order by name.",
        "Which accounts grew billed revenue by more than 50% from H1 to H2 2025? Show both halves.",
        "Customers growing fast?"),
"H46": ("Which five customers owe us the most on invoices that aren't fully paid?",
        "For [[invoices]] with [[invoices.status]] in ('unpaid', 'partially_paid'), subtract the SUM([[payments.amount_usd]]) per invoice (0 if none) from [[invoices.amount_usd]]; sum per [[customers.name]] (via [[shipments]]) rounded to 2; top 5.",
        "Which five accounts carry the largest outstanding receivable balance after partial payments?",
        "Who owes us most?"),
"H47": ("For each aircraft model, how many completed flights flew with no cargo at all, and what share is that?",
        "Per [[aircraft_types.model]], count completed [[flights]], those with no row in [[flight_cargo]], and that share in percent rounded to 1; order by model.",
        "What share of operated sectors per fleet type flew empty, without any booked shipment leg?",
        "Empty flights?"),
"H48": ("Which five airports have the most incidents compared with the number of shipments starting there?",
        "Count [[shipments]] per [[shipments.origin_airport_id]] and [[incidents]] per [[incidents.airport_id]] separately, join both to [[airports]]; return [[airports.iata_code]], both counts and 1000 * incidents / shipments rounded to 2; top 5 by the rate.",
        "Which five stations have the worst incident rate per 1,000 originating shipments?",
        "Riskiest airports?"),
"H49": ("Which warehouse operators have a warehouse at every European airport?",
        "Return [[warehouses.operator_name]] whose [[warehouses]] cover every [[airports]] row with [[airports.region]] = 'europe' (COUNT(DISTINCT [[warehouses.airport_id]]) = number of European airports); sorted.",
        "Which handling partners offer full coverage across all our European stations?",
        "Operators everywhere in Europe?"),
"H50": ("For each commodity type, which shipment has the second-highest declared value, and what is it?",
        "Per [[shipments.commodity_category]], rank [[shipments]] by [[shipments.declared_value_usd]] with DENSE_RANK descending and return [[shipments.awb_number]] and value where the rank is 2; order by category.",
        "What is the runner-up shipment by declared value in each commodity vertical?",
        "Second most valuable per category?"),
"H51": ("For each airline, how many completed flights did each aircraft model fly, and what share of the airline's flights is that?",
        "Count completed [[flights]] per [[airlines.name]] and [[aircraft_types.model]]; add 100 * count / SUM(count) OVER (PARTITION BY airline) rounded to 1; order by airline, count descending.",
        "What is each carrier's flying mix by fleet type, as a share of its completed sectors?",
        "Fleet usage mix?"),
"H52": ("What's the median chargeable weight of delivered shipments for each service level?",
        "For [[shipments]] with [[shipments.status]] = 'delivered', compute the median [[shipments.chargeable_weight_kg]] per [[shipments.service_level]] with ROW_NUMBER and COUNT windows (average of the two middle values if even), rounded to 1.",
        "What is the typical (median) chargeable weight per delivered shipment in each product tier?",
        "Typical shipment weight?"),
"H53": ("When customers first shipped with us, which service level did they pick? Count customers per level.",
        "For each [[shipments.customer_id]], take the row with the earliest [[shipments.booking_date]] (ties: smaller [[shipments.shipment_id]]) and count customers per [[shipments.service_level]]; order by service level.",
        "Which product do customers choose for their very first booking? Give the customer count by service level.",
        "First shipment service?"),
"H54": ("After an AOG repair, how many hours does it take before the plane flies again, by airline?",
        "For completed [[maintenance_records]] with [[maintenance_records.is_aog]] = 1, find the MIN([[flights.actual_departure]]) of a completed flight of the same aircraft at or after [[maintenance_records.end_time]]; per [[airlines.name]] count events with such a flight and average the hours between, rounded to 1.",
        "What is our average return-to-service time after aircraft-on-ground events, by carrier?",
        "AOG recovery time?"),
"H55": ("How many customers did we gain each year, and what's the running total?",
        "Group [[customers]] by the year of [[customers.created_date]], count rows, and add SUM(count) OVER (ORDER BY year); order by year.",
        "Show customer acquisition per year with the cumulative account base.",
        "Customer growth?"),
"H56": ("What are the three busiest routes of each airline?",
        "Per [[airlines.name]], count completed [[flights]] per ([[flights.origin_airport_id]], [[flights.destination_airport_id]]) as [[airports.iata_code]] pairs, and keep the top 3 with ROW_NUMBER (ties: origin code, then destination code).",
        "For each carrier, which three directed city pairs carry the most completed flights?",
        "Top routes per airline?"),
"H57": ("Which pilots with at least 20 completed duties are pilot flying less than 35% of the time?",
        "For completed [[crew_assignments]] with [[crew_assignments.duty_role]] in ('captain', 'first_officer'), per [[crew_members.employee_number]] return COUNT(*) and 100 * SUM([[crew_assignments.is_pilot_flying]]) / COUNT(*) rounded to 1; keep COUNT(*) >= 20 and share < 35; order by share, employee number.",
        "Which pilots get too few handling sectors (below 35% pilot flying) given at least 20 completed duties?",
        "Pilots who rarely fly?"),
"H58": ("How do our unpaid invoices age as of 20 December 2025: not due, 1-30, 31-60 and over 60 days late?",
        "For [[invoices]] with [[invoices.status]] <> 'paid', bucket julianday('2025-12-20') - julianday([[invoices.due_date]]) into 'not due', '1-30', '31-60', '61+'; per bucket COUNT(*) and SUM([[invoices.amount_usd]]) rounded to 2, in that order.",
        "Give me the receivables ageing schedule: count and value by days past due.",
        "Invoice ageing?"),
"H59": ("For each airline, which month was the busiest for completed flights?",
        "Per [[airlines.name]], count completed [[flights]] per month of [[flights.actual_departure]] and keep the month with most (ties: earlier month) with its count.",
        "What was each carrier's peak month of operations in 2025?",
        "Peak month per airline?"),
"H60": ("On average, how many crew are on a completed flight, for each aircraft model?",
        "Count [[crew_assignments]] per [[crew_assignments.flight_id]] first, then AVG of that count over completed [[flights]] per [[aircraft_types.model]], rounded to 2.",
        "What is the average crew complement per operated sector by fleet type?",
        "Crew per flight?"),
"H61": ("How much fuel does each aircraft model burn per 100 km?",
        "Over completed [[flights]] joined to [[fuel_uplifts]], [[aircraft]] and [[aircraft_types]]: SUM([[fuel_uplifts.fuel_burned_kg]]) * 100 / SUM([[flights.distance_km]]) per [[aircraft_types.model]], rounded to 1; highest first.",
        "What is the fuel intensity of each fleet type, in kg burned per 100 km flown?",
        "Fuel efficiency?"),
"H62": ("Among customers with at least 30 payments, which five pay late most often?",
        "Join [[payments]] to [[invoices]] and [[customers]]; per [[customers.name]] COUNT(*) and the share with [[payments.payment_date]] > [[invoices.due_date]] in percent rounded to 1; HAVING COUNT(*) >= 30; top 5 by share.",
        "Which five regular payers have the worst payment discipline, by share of late payments?",
        "Late payers?"),
"H63": ("Which captains have flown with at least 11 different first officers?",
        "Self-join [[crew_assignments]] on [[crew_assignments.flight_id]]: captain rows with first-officer rows, both completed; COUNT(DISTINCT first officer) per captain [[crew_members.employee_number]]; keep >= 11; order by count descending, employee number.",
        "Which commanders have the broadest pairing history, with 11 or more different first officers?",
        "Captains with many partners?"),
"H64": ("Which airports have worse average arrival delays than the network as a whole?",
        "Per destination [[airports.iata_code]], AVG(([[flights.actual_arrival]] - [[flights.scheduled_arrival]]) in minutes) over completed [[flights]], rounded to 1; keep airports above the average over all completed flights; worst first.",
        "Which inbound stations underperform the network average on arrival punctuality?",
        "Worst arrival airports?"),
"H65": ("Which five planes fly the most hours per day they're in use?",
        "Per [[aircraft.tail_number]], SUM of completed block hours ([[flights.actual_arrival]] - [[flights.actual_departure]]) divided by COUNT(DISTINCT date([[flights.actual_departure]])), rounded to 2; top 5.",
        "Which five airframes achieve the highest daily utilisation on the days they operate?",
        "Most utilised planes?"),
"H66": ("When both customs clearances go through, how many hours pass between export and import clearance, by import country?",
        "Self-join [[customs_declarations]] on [[customs_declarations.shipment_id]]: cleared export with cleared import; per import [[customs_declarations.customs_country]] COUNT(*) and AVG hours between the two [[customs_declarations.cleared_at]] values, rounded to 1; countries with at least 100; slowest first.",
        "What is the end-to-end customs cycle time, export clearance to import clearance, per destination jurisdiction?",
        "Customs gap by country?"),
"H67": ("For each service level, how long does it take from booking to handing the cargo over, on average and at worst?",
        "Join [[shipments]] to [[tracking_events]] with [[tracking_events.event_code]] = 'DLV'; per [[shipments.service_level]] COUNT(*), AVG and MAX of [[tracking_events.event_time]] - [[shipments.booking_date]] in days, rounded to 2.",
        "What is the booking-to-handover lead time per product tier, average and maximum?",
        "Door-to-door time?"),
"H68": ("For each insurer, how many days after an incident do claims get filed, and what share of claims gets paid?",
        "Join [[insurance_claims]] to [[incidents]]; per [[insurance_claims.insurer_name]] COUNT(*), AVG([[insurance_claims.filed_date]] - [[incidents.reported_at]]) in days rounded to 1, and the share with [[insurance_claims.status]] = 'paid' in percent rounded to 1.",
        "By insurer, how quickly are claims lodged after the incident, and what is the payout rate?",
        "Insurer performance?"),
"H69": ("In each sales region, who are the top two customers by number of shipments (ties count together)?",
        "Per [[customers.sales_region]], DENSE_RANK customers by COUNT of non-cancelled [[shipments]] descending; return region, [[customers.name]], count and rank for ranks 1-2; order by region, rank, name.",
        "Who are the two leading accounts by shipment count in each sales region?",
        "Top customers per region?"),
"H70": ("Which day of the week has the worst departure delays?",
        "Group completed [[flights]] by strftime('%w', [[flights.scheduled_departure]]) as an integer; COUNT(*) and AVG departure delay in minutes rounded to 1; order by weekday.",
        "How does departure punctuality vary by day of the week?",
        "Delays by weekday?"),
"H71": ("For each airline, how many completed flights carried cargo for three or more different customers?",
        "Find [[flight_cargo.flight_id]] values whose legs belong to at least 3 distinct [[shipments.customer_id]]; count those completed [[flights]] per [[airlines.name]]; most first.",
        "How many operated sectors per carrier were consolidated loads serving three or more customers?",
        "Shared flights?"),
"H72": ("If we split customers into five equal groups by revenue, how much does each group bring in and what share is that?",
        "NTILE(5) over customers ordered by SUM([[invoices.amount_usd]]) (via [[shipments]]) descending, ties by customer id; per quintile COUNT(*), SUM rounded to 2 and share of total in percent rounded to 1.",
        "Show revenue concentration by customer quintile: accounts, billed USD and share.",
        "Revenue by customer group?"),
"H73": ("Which airports send out temperature-controlled shipments without having a cold-chain warehouse, and how many?",
        "Join [[shipments]] to [[airports]] on [[shipments.origin_airport_id]]; count rows with [[shipments.is_temperature_controlled]] = 1 at airports with no [[warehouses]] row of [[warehouses.warehouse_type]] = 'cold_chain'; most first.",
        "Where are we originating temperature-sensitive cargo without dedicated cold-chain infrastructure?",
        "Cold chain gaps?"),
"H74": ("How many flights were cancelled because of weather in each month of 2025, including months with none?",
        "Generate months 2025-01 to 2025-12 with a recursive CTE, LEFT JOIN [[flights]] with [[flights.cancellation_reason]] = 'weather' by month of [[flights.scheduled_departure]] and COUNT, giving 0 for empty months.",
        "Give a complete 12-month view of weather-driven cancellations, showing zero months too.",
        "Weather cancellations by month?"),
"H75": ("Which planes flew on three or more days in a row, and what's their longest streak?",
        "Per [[aircraft.tail_number]], find the longest run of consecutive dates of completed [[flights.actual_departure]] (gaps and islands: date minus ROW_NUMBER); keep runs of at least 3; order by run descending, tail number.",
        "Which airframes had the longest unbroken streaks of operating days?",
        "Longest flying streaks?"),
"H76": ("Which customers have an average invoice at least 1.5 times the average for their customer type?",
        "Per customer, AVG([[invoices.amount_usd]]) (via [[shipments]]); compare with AVG of these per [[customers.customer_type]] (window); return [[customers.name]], type and both averages rounded to 2 where the customer is >= 1.5 times the type average; order by type, name.",
        "Which accounts have an average ticket far above their segment norm (1.5x or more)?",
        "Big spenders for their type?"),
"H77": ("For resolved incidents, how many days did they take to close by severity, and what share closed within 30 days?",
        "For [[incidents]] with [[incidents.resolved]] = 1, per [[incidents.severity]] COUNT(*), AVG days from [[incidents.reported_at]] to [[incidents.resolved_at]] rounded to 1, and the share resolved within 30 days in percent rounded to 1.",
        "What is the incident resolution cycle time per severity level, and the 30-day closure rate?",
        "How fast are incidents fixed?"),
"H78": ("For each commodity, which invoiced shipment earned the most per chargeable kilo?",
        "Join [[invoices]] to [[shipments]]; per [[shipments.commodity_category]] the [[shipments.awb_number]] with the highest [[invoices.amount_usd]] / [[shipments.chargeable_weight_kg]] (ties: smaller [[shipments.shipment_id]]), rounded to 2.",
        "Which shipment delivered the best yield per chargeable kg in each commodity vertical?",
        "Best yield per category?"),
"H79": ("In each month of Q4 2025, what share of completed flights did each airline operate?",
        "For completed [[flights]] with [[flights.actual_departure]] from 2025-10-01 to 2025-12-31, count per month and [[airlines.name]] and add 100 * count / SUM(count) OVER (PARTITION BY month) rounded to 1; order by month, count descending, airline.",
        "What was each carrier's monthly share of operated flights during Q4 2025?",
        "Airline share last quarter?"),
"H80": ("For two-leg shipments, how often does the second leg go on a different airline, by first-leg airline?",
        "Self-join [[flight_cargo]] on [[flight_cargo.shipment_id]] (leg 1 and leg 2), map each leg to its airline via [[flights]] and [[aircraft]]; count shipments where the airlines differ, per leg-1 [[airlines.name]]; most first.",
        "How many connecting shipments did each carrier hand over to another airline for the onward leg (interline)?",
        "Interline transfers?"),
})
