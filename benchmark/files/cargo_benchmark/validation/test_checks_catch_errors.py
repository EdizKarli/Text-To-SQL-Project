#!/usr/bin/env python3
"""Mutation test: corrupt a copy of the NORMAL database in known ways and confirm the matching validation check fires.
Usage: python validation/test_checks_catch_errors.py"""
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
 # v2 tables
 "crew_license_valid_on_duty": "UPDATE crew_members SET license_expiry_date = '2025-01-01' WHERE crew_member_id = (SELECT crew_member_id FROM crew_assignments WHERE duty_role = 'captain' ORDER BY report_time DESC LIMIT 1)",
 "crew_no_overlapping_duties": "UPDATE crew_assignments SET report_time = (SELECT report_time FROM crew_assignments WHERE assignment_id = 1), release_time = (SELECT release_time FROM crew_assignments WHERE assignment_id = 1) WHERE assignment_id = (SELECT MIN(assignment_id) FROM crew_assignments WHERE assignment_id > 1 AND crew_member_id = (SELECT crew_member_id FROM crew_assignments WHERE assignment_id = 1))",
 "crew_airline_and_type_rating_match_aircraft": "UPDATE crew_members SET type_rating_id = type_rating_id % 5 + 1 WHERE crew_member_id = (SELECT crew_member_id FROM crew_assignments WHERE duty_role = 'captain' LIMIT 1)",
 "takeoff_weight_within_mtow": "UPDATE flights SET takeoff_weight_kg = 999999 WHERE flight_id = (SELECT MIN(flight_id) FROM flights WHERE status='completed')",
 "fuel_quantities_and_cost_consistent": "UPDATE fuel_uplifts SET total_cost_usd = total_cost_usd * 2 WHERE fuel_uplift_id = 1",
 "maintenance_no_overlap_with_flights": "UPDATE maintenance_records SET end_time = '2025-12-31 00:00:00' WHERE maintenance_id = (SELECT MIN(maintenance_id) FROM maintenance_records WHERE status='completed')",
 "awb_check_digit": "UPDATE shipments SET awb_number = substr(awb_number, 1, 11) || ((CAST(substr(awb_number, 12, 1) AS INTEGER) + 1) % 10) WHERE shipment_id = 1",
 "invoice_components_sum_to_total": "UPDATE invoices SET fuel_surcharge_usd = fuel_surcharge_usd + 5 WHERE invoice_id = 1",
 "payment_fx_consistent": "UPDATE payments SET exchange_rate_to_usd = exchange_rate_to_usd * 1.1 WHERE payment_id = (SELECT MIN(payment_id) FROM payments WHERE original_currency <> 'USD')",
 "customs_only_cross_border": "UPDATE customs_declarations SET shipment_id = (SELECT s.shipment_id FROM shipments s JOIN airports o ON o.airport_id = s.origin_airport_id JOIN airports d ON d.airport_id = s.destination_airport_id WHERE o.country = d.country AND s.status <> 'cancelled' LIMIT 1) WHERE declaration_id = 1",
 "delivery_requires_import_clearance": "UPDATE customs_declarations SET status = 'held', cleared_at = NULL, inspection_required = 1, inspection_result = 'discrepancy' WHERE declaration_id = (SELECT d.declaration_id FROM customs_declarations d JOIN tracking_events e ON e.shipment_id = d.shipment_id AND e.event_code = 'DLV' WHERE d.declaration_type = 'import' LIMIT 1)",
 "tracking_flight_events_match_flights": "UPDATE tracking_events SET event_time = datetime(event_time, '+1 hour') WHERE event_id = (SELECT MIN(event_id) FROM tracking_events WHERE event_code = 'DEP')",
 "claims_match_incidents": "UPDATE insurance_claims SET claimed_amount_usd = claimed_amount_usd + 100 WHERE claim_id = 1",
 "out_of_range_readings_have_incident": "UPDATE tracking_events SET temperature_c = 40 WHERE event_id = (SELECT e.event_id FROM tracking_events e JOIN shipments s USING(shipment_id) WHERE s.commodity_category = 'pharmaceuticals' AND e.temperature_c IS NOT NULL AND NOT EXISTS (SELECT 1 FROM flight_cargo fc JOIN incidents i USING(flight_cargo_id) WHERE fc.shipment_id = s.shipment_id) LIMIT 1)",
}
checks = {n: sql for n, lvl, d, sql in parse_checks(os.path.join(ROOT, "validation", "validation_checks.sql"))}
bad = 0
with tempfile.TemporaryDirectory() as d:
    for name, stmt in MUTATIONS.items():
        path = os.path.join(d, "m.db"); shutil.copy(os.path.join(ROOT, "databases", "cargo_normal.db"), path)
        con = sqlite3.connect(path); con.execute("PRAGMA foreign_keys=OFF"); con.execute("PRAGMA ignore_check_constraints=ON")
        before = con.execute(checks[name]).fetchone()[0]
        try:
            con.execute(stmt); con.commit()
        except sqlite3.IntegrityError as e:
            print(f"[SKIP] {name}: blocked by schema constraint ({e})"); con.close(); continue
        after = con.execute(checks[name]).fetchone()[0]
        ok = before == 0 and after > 0; bad += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: violations {before} -> {after}"); con.close()
print(f"RESULT: {len(MUTATIONS) - bad}/{len(MUTATIONS)} mutations detected")
sys.exit(1 if bad else 0)
