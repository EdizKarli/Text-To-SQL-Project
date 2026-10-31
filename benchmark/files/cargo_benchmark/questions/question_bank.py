"""Question bank: 120 base questions (40 easy, 40 moderate, 40 hard), each with ONE Gold SQL query (normal schema)
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
