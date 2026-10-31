#!/usr/bin/env python3
"""Single source of truth for questions + Gold SQL (NORMAL schema). Writes questions/questions_normal.json (stable IDs).

The same questions are used for all three schema variants; scripts/build_variants.py translates the Gold SQL into
questions_mixed.json and questions_cryptic.json and checks that every translation returns the identical result.
Q01-Q25 use the original 12 tables; Q26-Q45 use the tables and columns added in schema version 2.
"""
import json, os

AS_OF = "2025-12-20"
Q = []
def add(qid, difficulty, concepts, question, spec, sql):
    # stored on one line (whitespace collapsed) so the JSON holds no \n; no Gold SQL has multi-space string literals
    Q.append(dict(id=qid, difficulty=difficulty, concepts=concepts, question=question, answer_spec=spec, gold_sql=" ".join(sql.split())))

# ------------------------------------------------------------------ EASY
add("Q01", "easy", ["COUNT", "WHERE"],
    "How many airports are flagged as cargo hubs?",
    "One row, one column `hub_count` (integer).",
    "SELECT COUNT(*) AS hub_count FROM airports WHERE is_cargo_hub = 1;")
add("Q02", "easy", ["filtering", "ORDER BY"],
    "List the tail number and year of manufacture of every active aircraft built in 2015 or later, newest first; break ties by tail number alphabetically.",
    "Columns: tail_number, year_manufactured. Ordered by year_manufactured DESC, tail_number ASC.",
    """SELECT tail_number, year_manufactured FROM aircraft
WHERE status = 'active' AND year_manufactured >= 2015
ORDER BY year_manufactured DESC, tail_number ASC;""")
add("Q03", "easy", ["COUNT", "WHERE"],
    "How many flights were cancelled?",
    "One row, one column `cancelled_flights`.",
    "SELECT COUNT(*) AS cancelled_flights FROM flights WHERE status = 'cancelled';")
add("Q04", "easy", ["projection", "ORDER BY"],
    "List every aircraft model with its maximum payload in kg, from the highest payload to the lowest.",
    "Columns: model, max_payload_kg. Ordered by max_payload_kg DESC.",
    "SELECT model, max_payload_kg FROM aircraft_types ORDER BY max_payload_kg DESC;")
add("Q05", "easy", ["SUM", "WHERE"],
    "What is the total declared value in USD of delivered pharmaceutical shipments?",
    "One row, one column `total_declared_value_usd` rounded to 2 decimals. 'Pharmaceutical' = commodity_category 'pharmaceuticals'.",
    """SELECT ROUND(SUM(declared_value_usd), 2) AS total_declared_value_usd
FROM shipments WHERE status = 'delivered' AND commodity_category = 'pharmaceuticals';""")
add("Q06", "easy", ["filtering", "ORDER BY"],
    "List the name and country of all customers with 45-day payment terms, alphabetically by name and then by country.",
    "Columns: name, country. Customers sharing a name in different countries both appear.",
    "SELECT name, country FROM customers WHERE payment_terms_days = 45 ORDER BY name, country;")
add("Q07", "easy", ["GROUP BY", "COUNT"],
    "How many shipments are there in each status?",
    "Columns: status, shipment_count. Ordered by status alphabetically.",
    "SELECT status, COUNT(*) AS shipment_count FROM shipments GROUP BY status ORDER BY status;")
add("Q08", "easy", ["NOT EXISTS", "anti-join"],
    "Which aircraft (tail numbers) have never been assigned to any flight? Sort alphabetically.",
    "Column: tail_number. Includes aircraft of every status.",
    """SELECT a.tail_number FROM aircraft a
WHERE NOT EXISTS (SELECT 1 FROM flights f WHERE f.aircraft_id = a.aircraft_id)
ORDER BY a.tail_number;""")

# ------------------------------------------------------------------ MEDIUM
add("Q09", "medium", ["JOIN", "GROUP BY", "COUNT"],
    "How many completed flights departed from Frankfurt (FRA)?",
    "One row, one column `completed_fra_departures`.",
    """SELECT COUNT(*) AS completed_fra_departures
FROM flights f JOIN airports a ON a.airport_id = f.origin_airport_id
WHERE a.iata_code = 'FRA' AND f.status = 'completed';""")
add("Q10", "medium", ["LEFT JOIN", "GROUP BY", "conditional join"],
    "For each airline, how many completed flights did it operate? Include airlines with zero. Order by count descending, then airline name.",
    "Columns: airline_name, completed_flights. LEFT JOIN semantics: zero-count airlines must appear.",
    """SELECT al.name AS airline_name, COUNT(f.flight_id) AS completed_flights
FROM airlines al
LEFT JOIN aircraft ac ON ac.airline_id = al.airline_id
LEFT JOIN flights f ON f.aircraft_id = ac.aircraft_id AND f.status = 'completed'
GROUP BY al.airline_id, al.name
ORDER BY completed_flights DESC, airline_name;""")
add("Q11", "medium", ["JOIN", "SUM", "ORDER BY", "LIMIT"],
    "Who are the top 5 customers by total declared value of their non-cancelled shipments? Break ties by lower customer_id.",
    "Columns: customer_id, name, total_declared_value_usd (rounded to 2 decimals; sort by the rounded value). Cancelled shipments are excluded.",
    """SELECT c.customer_id, c.name, ROUND(SUM(s.declared_value_usd), 2) AS total_declared_value_usd
FROM customers c JOIN shipments s ON s.customer_id = c.customer_id
WHERE s.status <> 'cancelled'
GROUP BY c.customer_id, c.name
ORDER BY total_declared_value_usd DESC, c.customer_id ASC
LIMIT 5;""")
add("Q12", "medium", ["JOIN", "GROUP BY", "HAVING"],
    "Which destination airports (IATA codes) received more than 150 completed flights? Show the count, highest first, ties by IATA code.",
    "Columns: iata_code, completed_arrivals. Ordered by completed_arrivals DESC, iata_code ASC.",
    """SELECT a.iata_code, COUNT(*) AS completed_arrivals
FROM flights f JOIN airports a ON a.airport_id = f.destination_airport_id
WHERE f.status = 'completed'
GROUP BY a.airport_id, a.iata_code
HAVING COUNT(*) > 150
ORDER BY completed_arrivals DESC, a.iata_code ASC;""")
add("Q13", "medium", ["date arithmetic", "AVG", "HAVING"],
    "For each origin airport with at least 40 completed departures, what is the average departure delay in minutes (actual minus scheduled)? Round to 1 decimal; highest delay first, ties by IATA code.",
    "Columns: iata_code, avg_departure_delay_min. Early departures count as negative delay. Only completed flights.",
    """SELECT a.iata_code,
       ROUND(AVG((julianday(f.actual_departure) - julianday(f.scheduled_departure)) * 1440), 1) AS avg_departure_delay_min
FROM flights f JOIN airports a ON a.airport_id = f.origin_airport_id
WHERE f.status = 'completed'
GROUP BY a.airport_id, a.iata_code
HAVING COUNT(*) >= 40
ORDER BY avg_departure_delay_min DESC, a.iata_code ASC;""")
add("Q14", "medium", ["LEFT JOIN", "NOT EXISTS", "NULL handling"],
    "Which customers have never booked any shipment (of any status)? List customer_id and name ordered by customer_id.",
    "Columns: customer_id, name. Customers with only cancelled shipments are NOT included.",
    """SELECT c.customer_id, c.name FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.customer_id = c.customer_id)
ORDER BY c.customer_id;""")
add("Q15", "medium", ["subquery", "join multiplication", "SUM", "HAVING"],
    "For each customer with an outstanding balance, show total invoiced, total paid and outstanding (invoiced minus paid) in USD, largest outstanding first (ties by customer_id). Show only the top 10.",
    "Columns: customer_id, total_invoiced_usd, total_paid_usd, outstanding_usd (all rounded to 2 decimals). Invoices without payments count as paid 0. Outstanding > 0 only. Beware: joining invoices to payments directly repeats invoice amounts.",
    """WITH paid AS (
  SELECT invoice_id, SUM(amount_usd) AS paid_usd FROM payments GROUP BY invoice_id
)
SELECT s.customer_id,
       ROUND(SUM(i.amount_usd), 2) AS total_invoiced_usd,
       ROUND(SUM(COALESCE(p.paid_usd, 0)), 2) AS total_paid_usd,
       ROUND(SUM(i.amount_usd) - SUM(COALESCE(p.paid_usd, 0)), 2) AS outstanding_usd
FROM invoices i
JOIN shipments s ON s.shipment_id = i.shipment_id
LEFT JOIN paid p ON p.invoice_id = i.invoice_id
GROUP BY s.customer_id
HAVING ROUND(SUM(i.amount_usd) - SUM(COALESCE(p.paid_usd, 0)), 2) > 0
ORDER BY outstanding_usd DESC, s.customer_id ASC
LIMIT 10;""")
add("Q16", "medium", ["GROUP BY", "subquery"],
    "How many shipments needed more than one flight (a connection), broken down by service level? Order by service level.",
    "Columns: service_level, connecting_shipments. Service levels without connecting shipments are omitted.",
    """SELECT s.service_level, COUNT(*) AS connecting_shipments
FROM shipments s
WHERE (SELECT COUNT(*) FROM flight_cargo fc WHERE fc.shipment_id = s.shipment_id) > 1
GROUP BY s.service_level ORDER BY s.service_level;""")

# ------------------------------------------------------------------ HARD
add("Q17", "hard", ["CTE", "JOIN", "AVG", "GROUP BY"],
    "For each aircraft model, what is the average payload load factor (percent of max payload used) across its completed flights that carried at least one shipment? Round to 1 decimal; highest first.",
    "Columns: model, avg_load_factor_pct. Load factor of a flight = SUM(total_weight_kg of shipments on it) / max_payload_kg * 100. Flights without cargo are excluded; each flight counts once.",
    """WITH load AS (
  SELECT fc.flight_id, SUM(s.total_weight_kg) AS kg
  FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
  GROUP BY fc.flight_id
)
SELECT t.model, ROUND(AVG(l.kg * 100.0 / t.max_payload_kg), 1) AS avg_load_factor_pct
FROM load l
JOIN flights f ON f.flight_id = l.flight_id AND f.status = 'completed'
JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id
GROUP BY t.type_id, t.model
ORDER BY avg_load_factor_pct DESC, t.model;""")
add("Q18", "hard", ["date functions", "JOIN", "SUM", "GROUP BY"],
    "For each month of 2025 (by actual departure date), how many kilograms of cargo were flown on completed flights? A shipment on two flights counts on each flight.",
    "Columns: month ('YYYY-MM'), total_kg_flown (rounded to 1 decimal). Only months with completed flights carrying cargo appear. Ordered by month.",
    """SELECT substr(f.actual_departure, 1, 7) AS month, ROUND(SUM(s.total_weight_kg), 1) AS total_kg_flown
FROM flight_cargo fc
JOIN flights f ON f.flight_id = fc.flight_id
JOIN shipments s ON s.shipment_id = fc.shipment_id
WHERE f.status = 'completed' AND substr(f.actual_departure, 1, 4) = '2025'
GROUP BY substr(f.actual_departure, 1, 7)
ORDER BY month;""")
add("Q19", "hard", ["window function", "ROW_NUMBER", "tie-breaking"],
    "For each origin airport, which destination was served by the most completed flights? If two destinations tie, choose the alphabetically smaller IATA code. Order the result by origin IATA code.",
    "Columns: origin_iata, destination_iata, completed_flights. One row per origin airport that has at least one completed departure.",
    """WITH r AS (
  SELECT o.iata_code AS origin_iata, d.iata_code AS destination_iata, COUNT(*) AS completed_flights,
         ROW_NUMBER() OVER (PARTITION BY o.airport_id ORDER BY COUNT(*) DESC, d.iata_code ASC) AS rn
  FROM flights f
  JOIN airports o ON o.airport_id = f.origin_airport_id
  JOIN airports d ON d.airport_id = f.destination_airport_id
  WHERE f.status = 'completed'
  GROUP BY o.airport_id, o.iata_code, d.airport_id, d.iata_code
)
SELECT origin_iata, destination_iata, completed_flights FROM r WHERE rn = 1 ORDER BY origin_iata;""")
add("Q20", "hard", ["JOIN", "date arithmetic", "ORDER BY", "LIMIT"],
    "Among delivered shipments, which 10 arrived the latest relative to the scheduled arrival of their final leg? Show hours late (actual minus scheduled arrival of the last leg), rounded to 1 decimal. Break ties by lower shipment_id.",
    "Columns: shipment_id, hours_late. Sort by the ROUNDED hours_late. Positive = late. Only the final leg (highest leg_number) is considered.",
    """SELECT s.shipment_id,
       ROUND((julianday(f.actual_arrival) - julianday(f.scheduled_arrival)) * 24, 1) AS hours_late
FROM shipments s
JOIN flight_cargo fc ON fc.shipment_id = s.shipment_id
 AND fc.leg_number = (SELECT MAX(x.leg_number) FROM flight_cargo x WHERE x.shipment_id = s.shipment_id)
JOIN flights f ON f.flight_id = fc.flight_id
WHERE s.status = 'delivered'
ORDER BY hours_late DESC, s.shipment_id ASC
LIMIT 10;""")
add("Q21", "hard", ["EXISTS", "NOT EXISTS", "multi-hop join"],
    "Which customers have at least one delivered shipment but have never had an incident reported on any of their shipments? Order by customer_id.",
    "Columns: customer_id, name. Incidents are linked to shipments through flight_cargo. Customers with no delivered shipment are excluded.",
    """SELECT c.customer_id, c.name FROM customers c
WHERE EXISTS (SELECT 1 FROM shipments s WHERE s.customer_id = c.customer_id AND s.status = 'delivered')
  AND NOT EXISTS (SELECT 1 FROM shipments s
                  JOIN flight_cargo fc ON fc.shipment_id = s.shipment_id
                  JOIN incidents i ON i.flight_cargo_id = fc.flight_cargo_id
                  WHERE s.customer_id = c.customer_id)
ORDER BY c.customer_id;""")
add("Q22", "hard", ["window function", "ROW_NUMBER", "CTE"],
    "For every customer that has at least one shipment, what is the booking date and ID of their most recent shipment (any status)? If several share the latest booking date, take the highest shipment_id. Order by customer_id.",
    "Columns: customer_id, latest_booking_date, shipment_id.",
    """WITH r AS (
  SELECT customer_id, booking_date, shipment_id,
         ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY booking_date DESC, shipment_id DESC) AS rn
  FROM shipments
)
SELECT customer_id, booking_date AS latest_booking_date, shipment_id FROM r WHERE rn = 1 ORDER BY customer_id;""")
add("Q23", "hard", ["date arithmetic", "JOIN", "business rule"],
    f"As of {AS_OF}, which invoices are overdue (due before {AS_OF} and not fully paid)? Show the 10 with the most days overdue: invoice_id, customer name, days overdue, outstanding amount. Break ties by lower invoice_id.",
    "Columns: invoice_id, customer_name, days_overdue (integer, as-of date minus due date), outstanding_usd (rounded to 2 decimals). Outstanding = amount minus payments received.",
    f"""WITH paid AS (SELECT invoice_id, SUM(amount_usd) AS paid_usd FROM payments GROUP BY invoice_id)
SELECT i.invoice_id, c.name AS customer_name,
       CAST(julianday('{AS_OF}') - julianday(i.due_date) AS INTEGER) AS days_overdue,
       ROUND(i.amount_usd - COALESCE(p.paid_usd, 0), 2) AS outstanding_usd
FROM invoices i
JOIN shipments s ON s.shipment_id = i.shipment_id
JOIN customers c ON c.customer_id = s.customer_id
LEFT JOIN paid p ON p.invoice_id = i.invoice_id
WHERE i.due_date < '{AS_OF}' AND i.status <> 'paid'
ORDER BY days_overdue DESC, i.invoice_id ASC
LIMIT 10;""")
add("Q24", "hard", ["subqueries", "join multiplication", "rates"],
    "For each commodity category, what is the incident rate: incidents per flown shipment leg (rounded to 4 decimals)? Include categories with zero incidents; highest rate first, ties by category.",
    "Columns: commodity_category, flown_legs, incidents, incident_rate. A flown leg = flight_cargo row with leg_status 'flown'. Do not let the incidents join inflate flown_legs.",
    """WITH legs AS (
  SELECT s.commodity_category, COUNT(*) AS flown_legs
  FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
  WHERE fc.leg_status = 'flown' GROUP BY s.commodity_category
), inc AS (
  SELECT s.commodity_category, COUNT(*) AS incidents
  FROM incidents i
  JOIN flight_cargo fc ON fc.flight_cargo_id = i.flight_cargo_id
  JOIN shipments s ON s.shipment_id = fc.shipment_id
  GROUP BY s.commodity_category
)
SELECT l.commodity_category, l.flown_legs, COALESCE(n.incidents, 0) AS incidents,
       ROUND(COALESCE(n.incidents, 0) * 1.0 / l.flown_legs, 4) AS incident_rate
FROM legs l LEFT JOIN inc n ON n.commodity_category = l.commodity_category
ORDER BY incident_rate DESC, l.commodity_category;""")
add("Q25", "hard", ["self-join", "CTE", "bidirectional"],
    "Which airport pairs have completed flights in both directions? List each pair once with the smaller IATA code first, the number of completed flights in each direction, ordered by pair.",
    "Columns: airport_a, airport_b, flights_a_to_b, flights_b_to_a, where airport_a < airport_b alphabetically. Ordered by airport_a, airport_b.",
    """WITH r AS (
  SELECT o.iata_code AS o, d.iata_code AS d, COUNT(*) AS n
  FROM flights f
  JOIN airports o ON o.airport_id = f.origin_airport_id
  JOIN airports d ON d.airport_id = f.destination_airport_id
  WHERE f.status = 'completed' GROUP BY o.iata_code, d.iata_code
)
SELECT x.o AS airport_a, x.d AS airport_b, x.n AS flights_a_to_b, y.n AS flights_b_to_a
FROM r x JOIN r y ON y.o = x.d AND y.d = x.o
WHERE x.o < x.d
ORDER BY airport_a, airport_b;""")

# ------------------------------------------------------------------ EASY (v2 tables)
add("Q26", "easy", ["COUNT", "WHERE"],
    "How many warehouses are customs-bonded?",
    "One row, one column `bonded_warehouses`.",
    "SELECT COUNT(*) AS bonded_warehouses FROM warehouses WHERE is_bonded = 1;")
add("Q27", "easy", ["filtering", "dates", "ORDER BY"],
    f"Which pilots have a licence that expired before {AS_OF}? Show employee number, first name and last name, ordered by employee number.",
    "Columns: employee_number, first_name, last_name. Loadmasters hold no licence and never qualify. Ordered by employee_number.",
    f"""SELECT employee_number, first_name, last_name FROM crew_members
WHERE license_expiry_date < '{AS_OF}'
ORDER BY employee_number;""")
add("Q28", "easy", ["GROUP BY", "NULL filtering"],
    "How many dangerous-goods shipments are there in each dangerous-goods class? Order by class.",
    "Columns: dg_class, shipment_count. Shipments that are not dangerous goods (NULL class) are excluded. Ordered by dg_class.",
    """SELECT dg_class, COUNT(*) AS shipment_count FROM shipments
WHERE is_dangerous_goods = 1
GROUP BY dg_class ORDER BY dg_class;""")
add("Q29", "easy", ["filtering", "ORDER BY"],
    "List the account code and name of every platinum-tier customer, ordered by account code.",
    "Columns: account_code, name. Ordered by account_code.",
    "SELECT account_code, name FROM customers WHERE loyalty_tier = 'platinum' ORDER BY account_code;")
add("Q30", "easy", ["SUM", "unit conversion"],
    "What is the total CO2 emitted by the burned fuel of all completed flights, in tonnes? Round to 1 decimal.",
    "One row, one column `total_co2_tonnes` = SUM(co2_emissions_kg) / 1000 over fuel uplifts (one per completed flight), rounded to 1 decimal.",
    "SELECT ROUND(SUM(co2_emissions_kg) / 1000.0, 1) AS total_co2_tonnes FROM fuel_uplifts;")
add("Q31", "easy", ["GROUP BY", "COUNT", "ORDER BY"],
    "How many flights were cancelled for each cancellation reason? Most frequent reason first, ties alphabetically.",
    "Columns: cancellation_reason, cancelled_flights. Ordered by cancelled_flights DESC, cancellation_reason ASC.",
    """SELECT cancellation_reason, COUNT(*) AS cancelled_flights FROM flights
WHERE status = 'cancelled'
GROUP BY cancellation_reason
ORDER BY cancelled_flights DESC, cancellation_reason ASC;""")

# ------------------------------------------------------------------ MEDIUM (v2 tables)
add("Q32", "medium", ["JOIN", "AVG", "GROUP BY"],
    "What is the average fuel price per litre at each departure airport? Show the IATA code and the average rounded to 4 decimals, most expensive first, ties by IATA code.",
    "Columns: iata_code, avg_price_usd_per_litre. Simple (unweighted) average over fuel uplifts. Ordered by avg_price_usd_per_litre DESC, iata_code ASC.",
    """SELECT a.iata_code, ROUND(AVG(u.price_usd_per_litre), 4) AS avg_price_usd_per_litre
FROM fuel_uplifts u JOIN airports a ON a.airport_id = u.airport_id
GROUP BY a.airport_id, a.iata_code
ORDER BY avg_price_usd_per_litre DESC, a.iata_code ASC;""")
add("Q33", "medium", ["GROUP BY", "SUM", "filtering"],
    "For each customs country, how much import duty and import VAT was charged on cleared import declarations? Show both totals and their sum, largest sum first.",
    "Columns: customs_country, total_duty_usd, total_vat_usd, total_taxes_usd (all rounded to 2 decimals; total = duty + VAT). Only declaration_type 'import' with status 'cleared'. Ordered by total_taxes_usd DESC, customs_country ASC.",
    """SELECT customs_country,
       ROUND(SUM(duty_amount_usd), 2) AS total_duty_usd,
       ROUND(SUM(vat_amount_usd), 2) AS total_vat_usd,
       ROUND(SUM(duty_amount_usd + vat_amount_usd), 2) AS total_taxes_usd
FROM customs_declarations
WHERE declaration_type = 'import' AND status = 'cleared'
GROUP BY customs_country
ORDER BY total_taxes_usd DESC, customs_country ASC;""")
add("Q34", "medium", ["JOIN", "GROUP BY", "multi-column grouping"],
    "How many active crew members does each airline have in each rank? Order by airline name, then rank.",
    "Columns: airline_name, crew_rank, active_crew. Only is_active = 1. Ordered by airline_name, crew_rank.",
    """SELECT al.name AS airline_name, m.crew_rank, COUNT(*) AS active_crew
FROM crew_members m JOIN airlines al ON al.airline_id = m.airline_id
WHERE m.is_active = 1
GROUP BY al.airline_id, al.name, m.crew_rank
ORDER BY airline_name, m.crew_rank;""")
add("Q35", "medium", ["JOIN", "SUM", "ORDER BY", "LIMIT"],
    "Which 5 aircraft had the highest total cost (parts plus labour) of completed maintenance? Show tail number and cost; ties by tail number.",
    "Columns: tail_number, total_maintenance_cost_usd (rounded to 2 decimals; sort by the rounded value). Only status 'completed'. Ordered by cost DESC, tail_number ASC.",
    """SELECT a.tail_number, ROUND(SUM(m.parts_cost_usd + m.labor_cost_usd), 2) AS total_maintenance_cost_usd
FROM maintenance_records m JOIN aircraft a ON a.aircraft_id = m.aircraft_id
WHERE m.status = 'completed'
GROUP BY a.aircraft_id, a.tail_number
ORDER BY total_maintenance_cost_usd DESC, a.tail_number ASC
LIMIT 5;""")
add("Q36", "medium", ["conditional aggregation", "COALESCE", "GROUP BY"],
    "For each insurer, how many claims were filed and what is the total approved amount of claims that were approved or paid? Order by insurer name.",
    "Columns: insurer_name, claims, total_approved_usd (rounded to 2 decimals; 0 when nothing approved). Every claim counts in `claims`; only status 'approved' or 'paid' count in the total.",
    """SELECT insurer_name, COUNT(*) AS claims,
       ROUND(COALESCE(SUM(CASE WHEN status IN ('approved', 'paid') THEN approved_amount_usd END), 0), 2) AS total_approved_usd
FROM insurance_claims
GROUP BY insurer_name ORDER BY insurer_name;""")
add("Q37", "medium", ["JOIN", "GROUP BY", "HAVING"],
    "Which warehouses received more than 150 shipments from shippers (RCS scans)? Show warehouse code, airport IATA code and the number of RCS scans, highest first, ties by warehouse code.",
    "Columns: warehouse_code, iata_code, rcs_scans. event_code 'RCS' = received from shipper. Ordered by rcs_scans DESC, warehouse_code ASC.",
    """SELECT w.warehouse_code, a.iata_code, COUNT(*) AS rcs_scans
FROM tracking_events e
JOIN warehouses w ON w.warehouse_id = e.warehouse_id
JOIN airports a ON a.airport_id = w.airport_id
WHERE e.event_code = 'RCS'
GROUP BY w.warehouse_id, w.warehouse_code, a.iata_code
HAVING COUNT(*) > 150
ORDER BY rcs_scans DESC, w.warehouse_code ASC;""")
add("Q38", "medium", ["multi-hop join", "ratio of sums", "GROUP BY"],
    "For each aircraft model, how many kilograms of fuel were burned per 100 km flown on completed flights? Round to 1 decimal, highest first.",
    "Columns: model, fuel_kg_per_100km = SUM(fuel_burned_kg) * 100 / SUM(distance_km) over completed flights of that model (ratio of sums, not average of ratios). Ordered by fuel_kg_per_100km DESC, model ASC.",
    """SELECT t.model, ROUND(SUM(u.fuel_burned_kg) * 100.0 / SUM(f.distance_km), 1) AS fuel_kg_per_100km
FROM fuel_uplifts u
JOIN flights f ON f.flight_id = u.flight_id
JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id
WHERE f.status = 'completed'
GROUP BY t.type_id, t.model
ORDER BY fuel_kg_per_100km DESC, t.model ASC;""")

# ------------------------------------------------------------------ HARD (v2 tables)
add("Q39", "hard", ["window function", "ROW_NUMBER", "multi-hop join", "tie-breaking"],
    "For each airline, which captain credited the most block hours in the captain role on completed flights? Show airline name, employee number and block hours (1 decimal). Ties go to the smaller employee number. Order by airline name.",
    "Columns: airline_name, employee_number, block_hours (= SUM(block_minutes_credited) / 60, rounded to 1 decimal). Only duty_role 'captain' and assignment_status 'completed'. One row per airline that has such assignments.",
    """WITH h AS (
  SELECT m.airline_id, m.employee_number, SUM(ca.block_minutes_credited) AS minutes
  FROM crew_assignments ca JOIN crew_members m ON m.crew_member_id = ca.crew_member_id
  WHERE ca.duty_role = 'captain' AND ca.assignment_status = 'completed'
  GROUP BY m.crew_member_id, m.airline_id, m.employee_number
), r AS (
  SELECT h.*, ROW_NUMBER() OVER (PARTITION BY airline_id ORDER BY minutes DESC, employee_number ASC) AS rn FROM h
)
SELECT al.name AS airline_name, r.employee_number, ROUND(r.minutes / 60.0, 1) AS block_hours
FROM r JOIN airlines al ON al.airline_id = r.airline_id
WHERE r.rn = 1
ORDER BY airline_name;""")
add("Q40", "hard", ["CTE", "join multiplication", "ratio of sums"],
    "For each aircraft model, what is the fuel efficiency in grams of fuel burned per tonne-kilometre of cargo, over completed flights that carried cargo? Round to 1 decimal; most efficient (lowest) first.",
    "Columns: model, grams_per_tonne_km = SUM(fuel_burned_kg) * 1000 / SUM(cargo_tonnes * distance_km), where cargo_tonnes of a flight = SUM(total_weight_kg of its shipments) / 1000. Flights without cargo are excluded. Beware: joining fuel uplifts to flight_cargo directly repeats each flight's fuel once per shipment. Ordered by grams_per_tonne_km ASC, model ASC.",
    """WITH load AS (
  SELECT fc.flight_id, SUM(s.total_weight_kg) / 1000.0 AS tonnes
  FROM flight_cargo fc JOIN shipments s ON s.shipment_id = fc.shipment_id
  GROUP BY fc.flight_id
)
SELECT t.model,
       ROUND(SUM(u.fuel_burned_kg) * 1000.0 / SUM(l.tonnes * f.distance_km), 1) AS grams_per_tonne_km
FROM load l
JOIN flights f ON f.flight_id = l.flight_id AND f.status = 'completed'
JOIN fuel_uplifts u ON u.flight_id = f.flight_id
JOIN aircraft a ON a.aircraft_id = f.aircraft_id
JOIN aircraft_types t ON t.type_id = a.type_id
GROUP BY t.type_id, t.model
ORDER BY grams_per_tonne_km ASC, t.model ASC;""")
add("Q41", "hard", ["JOIN", "conditional aggregation", "dates", "percentages"],
    "For each service level, what percentage of shipments handed to the consignee (DLV scan) were delivered after the requested delivery date? Round to 1 decimal; order by service level.",
    "Columns: service_level, delivered_shipments, late_shipments, late_pct. Late = date part of the DLV event_time > requested_delivery_date. Only shipments with a DLV event count. late_pct = 100 * late / delivered, rounded to 1 decimal.",
    """SELECT s.service_level, COUNT(*) AS delivered_shipments,
       SUM(CASE WHEN substr(e.event_time, 1, 10) > s.requested_delivery_date THEN 1 ELSE 0 END) AS late_shipments,
       ROUND(100.0 * SUM(CASE WHEN substr(e.event_time, 1, 10) > s.requested_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS late_pct
FROM shipments s JOIN tracking_events e ON e.shipment_id = s.shipment_id AND e.event_code = 'DLV'
GROUP BY s.service_level ORDER BY s.service_level;""")
add("Q42", "hard", ["date arithmetic", "AVG", "HAVING"],
    "For each customs country with at least 50 cleared import declarations, what is the average clearance time in hours (submission to clearance)? Round to 2 decimals; fastest first, ties by country.",
    "Columns: customs_country, cleared_imports, avg_clearance_hours. Only declaration_type 'import' and status 'cleared'. Ordered by avg_clearance_hours ASC, customs_country ASC.",
    """SELECT customs_country, COUNT(*) AS cleared_imports,
       ROUND(AVG((julianday(cleared_at) - julianday(submitted_at)) * 24), 2) AS avg_clearance_hours
FROM customs_declarations
WHERE declaration_type = 'import' AND status = 'cleared'
GROUP BY customs_country
HAVING COUNT(*) >= 50
ORDER BY avg_clearance_hours ASC, customs_country ASC;""")
add("Q43", "hard", ["JOIN", "range comparison across tables", "GROUP BY"],
    "Which temperature-controlled shipments had at least one probe reading outside their allowed temperature range? Show shipment ID, air waybill number, the number of out-of-range readings and the largest deviation from the range in degrees (1 decimal). Order by shipment ID.",
    "Columns: shipment_id, awb_number, out_of_range_readings, max_deviation_c. A reading is out of range when temperature_c < min_temperature_c or > max_temperature_c; deviation = distance to the nearest range limit. Readings that are NULL are ignored.",
    """SELECT s.shipment_id, s.awb_number, COUNT(*) AS out_of_range_readings,
       ROUND(MAX(CASE WHEN e.temperature_c > s.max_temperature_c THEN e.temperature_c - s.max_temperature_c
                      ELSE s.min_temperature_c - e.temperature_c END), 1) AS max_deviation_c
FROM tracking_events e JOIN shipments s ON s.shipment_id = e.shipment_id
WHERE s.is_temperature_controlled = 1
  AND (e.temperature_c < s.min_temperature_c OR e.temperature_c > s.max_temperature_c)
GROUP BY s.shipment_id, s.awb_number
ORDER BY s.shipment_id;""")
add("Q44", "hard", ["LEFT JOIN", "COALESCE", "conditional aggregation"],
    "For each incident root cause, how many incidents were there, how many of them led to an insurance claim, and what is the total approved claim amount (approved or paid claims)? Order by root cause.",
    "Columns: root_cause, incidents, claims, total_approved_usd (rounded to 2 decimals, 0 when none). Every root cause with at least one incident appears, even without claims. Ordered by root_cause.",
    """SELECT i.root_cause, COUNT(*) AS incidents, COUNT(c.claim_id) AS claims,
       ROUND(COALESCE(SUM(CASE WHEN c.status IN ('approved', 'paid') THEN c.approved_amount_usd END), 0), 2) AS total_approved_usd
FROM incidents i LEFT JOIN insurance_claims c ON c.incident_id = i.incident_id
GROUP BY i.root_cause ORDER BY i.root_cause;""")
add("Q45", "hard", ["NOT EXISTS", "LEFT JOIN", "multi-hop join"],
    f"Which shipments have landed at their final destination (status delivered) but, as of {AS_OF}, have not been handed over to the consignee (no DLV scan)? Show air waybill number, destination IATA code and the status of the import customs declaration (NULL if none). Order by air waybill number.",
    "Columns: awb_number, destination_iata, import_status. 'Handed over' = a tracking event with event_code 'DLV'. import_status comes from the shipment's declaration_type 'import' row, NULL when there is none.",
    """SELECT s.awb_number, a.iata_code AS destination_iata, d.status AS import_status
FROM shipments s
JOIN airports a ON a.airport_id = s.destination_airport_id
LEFT JOIN customs_declarations d ON d.shipment_id = s.shipment_id AND d.declaration_type = 'import'
WHERE s.status = 'delivered'
  AND NOT EXISTS (SELECT 1 FROM tracking_events e WHERE e.shipment_id = s.shipment_id AND e.event_code = 'DLV')
ORDER BY s.awb_number;""")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions_normal.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(Q, fh, indent=2, ensure_ascii=False)
    print(f"wrote {len(Q)} questions -> {out}")
