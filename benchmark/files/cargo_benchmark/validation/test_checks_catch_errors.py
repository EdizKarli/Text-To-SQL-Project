#!/usr/bin/env python3
"""Mutation test: corrupt a copy of the database in known ways and confirm the matching validation check fires."""
import os, re, shutil, sqlite3, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "validation"))
from run_validation import parse_checks

MUTATIONS = {   # check name -> corrupting statement
 "payment_customer_matches_shipment_customer": "UPDATE payments SET customer_id = customer_id % 60 + 1 WHERE payment_id = 1",
 "no_cargo_on_cancelled_flights": "UPDATE flight_cargo SET flight_id = (SELECT MIN(flight_id) FROM flights WHERE status='cancelled') WHERE flight_cargo_id = 1",
 "flight_payload_and_volume_not_exceeded": "UPDATE shipments SET total_weight_kg = 500000 WHERE shipment_id = (SELECT shipment_id FROM flight_cargo WHERE leg_status='flown' LIMIT 1)",
 "invoice_status_matches_payments": "UPDATE invoices SET status = 'unpaid' WHERE status = 'paid' AND invoice_id = (SELECT MIN(invoice_id) FROM invoices WHERE status='paid')",
 "shipment_status_matches_legs": "UPDATE shipments SET status = 'booked' WHERE status = 'delivered' AND shipment_id = (SELECT MIN(shipment_id) FROM shipments WHERE status='delivered')",
 "temperature_incident_commodity": "UPDATE shipments SET commodity_category='documents' WHERE shipment_id = (SELECT fc.shipment_id FROM incidents i JOIN flight_cargo fc USING(flight_cargo_id) WHERE i.incident_type='temperature_excursion' LIMIT 1)",
 "aircraft_no_overlapping_flights": "UPDATE flights SET scheduled_departure=(SELECT scheduled_departure FROM flights WHERE flight_id=(SELECT flight_id FROM flights WHERE aircraft_id=1 AND status<>'cancelled' ORDER BY scheduled_departure LIMIT 1 OFFSET 1)), scheduled_arrival=(SELECT scheduled_arrival FROM flights WHERE flight_id=(SELECT flight_id FROM flights WHERE aircraft_id=1 AND status<>'cancelled' ORDER BY scheduled_departure LIMIT 1 OFFSET 1)) WHERE flight_id=(SELECT flight_id FROM flights WHERE aircraft_id=1 AND status<>'cancelled' ORDER BY scheduled_departure LIMIT 1)",
 "legs_connect_in_space_and_time": "UPDATE flight_cargo SET flight_id = (SELECT MIN(flight_id) FROM flights WHERE status='completed') WHERE leg_number = 2 AND flight_cargo_id = (SELECT MIN(flight_cargo_id) FROM flight_cargo WHERE leg_number=2)",
}
checks = {n: sql for n, lvl, d, sql in parse_checks(os.path.join(ROOT, "validation", "validation_checks.sql"))}
bad = 0
with tempfile.TemporaryDirectory() as d:
    for name, stmt in MUTATIONS.items():
        path = os.path.join(d, "m.db"); shutil.copy(os.path.join(ROOT, "cargo_flights.db"), path)
        con = sqlite3.connect(path); con.execute("PRAGMA foreign_keys=OFF")
        before = con.execute(checks[name]).fetchone()[0]
        try:
            con.execute(stmt); con.commit()
        except sqlite3.IntegrityError as e:
            print(f"[SKIP] {name}: blocked by schema constraint ({e})"); con.close(); continue
        after = con.execute(checks[name]).fetchone()[0]
        ok = before == 0 and after > 0; bad += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: violations {before} -> {after}"); con.close()
sys.exit(1 if bad else 0)
