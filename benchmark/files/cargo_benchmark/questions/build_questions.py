#!/usr/bin/env python3
"""Single source of truth for questions + Gold SQL. Writes questions/questions.json (stable IDs)."""
import json, os

AS_OF = "2025-12-20"
Q = []
def add(qid, difficulty, concepts, question, spec, sql):
    Q.append(dict(id=qid, difficulty=difficulty, concepts=concepts, question=question, answer_spec=spec, gold_sql=sql.strip()))

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

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(Q, fh, indent=2, ensure_ascii=False)
    print(f"wrote {len(Q)} questions -> {out}")
