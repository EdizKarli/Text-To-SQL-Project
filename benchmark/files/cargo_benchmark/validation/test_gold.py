#!/usr/bin/env python3
"""Gold SQL validation: (1) executability/shape, (2) independent Python recomputation on the main DB,
(3) deliberately constructed tiny datasets exposing edge cases (ties, NULLs, join multiplication, anti-joins).
Runs on the NORMAL schema; the variants are checked against these results by validation/test_variants.py.
Usage: python validation/test_gold.py [--db databases/cargo_normal.db]"""
import argparse, collections, json, os, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = {q["id"]: q for q in json.load(open(os.path.join(ROOT, "questions", "questions_normal.json"), encoding="utf-8"))}
fails = []

def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail if not ok else ''}")
    if not ok: fails.append(label)

def run(con, qid):
    return con.execute(QUESTIONS[qid]["gold_sql"]).fetchall()

# ------------------------------------------------------------------ 1. executability + sanity
def layer1(con):
    print("== 1. Executability and result sanity ==")
    for qid, q in QUESTIONS.items():
        cur = con.execute(q["gold_sql"]); rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        spec = q["answer_spec"]
        missing = [c for c in cols if c not in spec]       # every output column must be named in the answer spec
        check(f"{qid} runs, non-empty, columns match spec", bool(rows) and not missing, f"rows={len(rows)} missing_in_spec={missing}")
        check(f"{qid} not all-NULL", any(v is not None for r in rows for v in r))

# ------------------------------------------------------------------ 2. independent recomputation
def layer2(con):
    print("\n== 2. Independent recomputation in Python ==")
    # Q10
    ac_air = dict(con.execute("SELECT aircraft_id, airline_id FROM aircraft"))
    cnt = collections.Counter()
    for ac, in con.execute("SELECT aircraft_id FROM flights WHERE status='completed'"):
        cnt[ac_air[ac]] += 1
    names = dict(con.execute("SELECT airline_id, name FROM airlines"))
    exp = sorted(((names[a], cnt[a]) for a in names), key=lambda x: (-x[1], x[0]))
    check("Q10 matches Python", run(con, "Q10") == exp)
    # Q15
    inv = con.execute("SELECT i.invoice_id, s.customer_id, i.amount_usd FROM invoices i JOIN shipments s USING(shipment_id)").fetchall()
    paid = collections.defaultdict(float)
    for iid, amt in con.execute("SELECT invoice_id, amount_usd FROM payments"): paid[iid] += amt
    agg = collections.defaultdict(lambda: [0.0, 0.0])
    for iid, cid, amt in inv:
        agg[cid][0] += amt; agg[cid][1] += paid[iid]
    exp = [(c, round(a, 2), round(p, 2), round(a - p, 2)) for c, (a, p) in agg.items() if round(a - p, 2) > 0]
    exp.sort(key=lambda r: (-r[3], r[0])); exp = exp[:10]
    got = run(con, "Q15")
    check("Q15 matches Python (tolerance 0.02)", len(got) == len(exp) and all(g[0] == e[0] and all(abs(x - y) < 0.02 for x, y in zip(g[1:], e[1:])) for g, e in zip(got, exp)))
    # Q19
    ap = dict(con.execute("SELECT airport_id, iata_code FROM airports"))
    pair = collections.Counter((ap[o], ap[d]) for o, d in con.execute("SELECT origin_airport_id, destination_airport_id FROM flights WHERE status='completed'"))
    best = {}
    for (o, d), n in sorted(pair.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1])):
        best.setdefault(o, (o, d, n))
    check("Q19 matches Python", run(con, "Q19") == sorted(best.values()))
    # Q24
    legs, incs = collections.Counter(), collections.Counter()
    cat = {}
    for fcid, c, st in con.execute("SELECT fc.flight_cargo_id, s.commodity_category, fc.leg_status FROM flight_cargo fc JOIN shipments s USING(shipment_id)"):
        cat[fcid] = c
        if st == "flown": legs[c] += 1
    for (fcid,) in con.execute("SELECT flight_cargo_id FROM incidents"): incs[cat[fcid]] += 1
    exp = sorted(((c, legs[c], incs[c], round(incs[c] / legs[c], 4)) for c in legs), key=lambda r: (-r[3], r[0]))
    check("Q24 matches Python", run(con, "Q24") == exp)
    # Q25
    flights = collections.Counter((ap[o], ap[d]) for o, d in con.execute("SELECT origin_airport_id, destination_airport_id FROM flights WHERE status='completed'"))
    exp = sorted((a, b, n, flights[(b, a)]) for (a, b), n in flights.items() if a < b and flights[(b, a)] > 0)
    check("Q25 matches Python", run(con, "Q25") == exp)
    # Q18 total equals sum over flown legs (conservation check)
    total = sum(r[1] for r in run(con, "Q18"))
    direct = con.execute("SELECT SUM(s.total_weight_kg) FROM flight_cargo fc JOIN shipments s USING(shipment_id) JOIN flights f USING(flight_id) WHERE f.status='completed'").fetchone()[0]
    check("Q18 monthly totals add up to all flown kg", abs(total - direct) < 1.0)
    # Q36
    agg = collections.defaultdict(lambda: [0, 0.0])
    for ins, st, amt in con.execute("SELECT insurer_name, status, approved_amount_usd FROM insurance_claims"):
        agg[ins][0] += 1
        if st in ("approved", "paid"): agg[ins][1] += amt
    check("Q36 matches Python", run(con, "Q36") == [(k, n, round(a, 2)) for k, (n, a) in sorted(agg.items())])
    # Q40 (fuel counted once per flight, cargo weight summed per flight)
    kg = collections.defaultdict(float)
    for fid, w in con.execute("SELECT fc.flight_id, s.total_weight_kg FROM flight_cargo fc JOIN shipments s USING(shipment_id)"): kg[fid] += w
    num, den = collections.defaultdict(float), collections.defaultdict(float)
    for fid, model, dist, burned in con.execute("""SELECT f.flight_id, t.model, f.distance_km, u.fuel_burned_kg FROM flights f
            JOIN fuel_uplifts u USING(flight_id) JOIN aircraft a USING(aircraft_id) JOIN aircraft_types t USING(type_id)
            WHERE f.status = 'completed'"""):
        if fid in kg:
            num[model] += burned; den[model] += kg[fid] / 1000 * dist
    exp = sorted(((m, round(num[m] * 1000 / den[m], 1)) for m in num), key=lambda r: (r[1], r[0]))
    check("Q40 matches Python", run(con, "Q40") == exp, f"{run(con, 'Q40')} vs {exp}")
    # Q41
    cnt = collections.defaultdict(lambda: [0, 0])
    for lvl, req, t in con.execute("""SELECT s.service_level, s.requested_delivery_date, e.event_time FROM shipments s
            JOIN tracking_events e ON e.shipment_id = s.shipment_id AND e.event_code = 'DLV'"""):
        cnt[lvl][0] += 1; cnt[lvl][1] += t[:10] > req
    check("Q41 matches Python", run(con, "Q41") == [(k, n, l, round(100 * l / n, 1)) for k, (n, l) in sorted(cnt.items())])
    # Q44
    inc = collections.defaultdict(lambda: [0, 0, 0.0])
    claims = {i: (st, a) for i, st, a in con.execute("SELECT incident_id, status, approved_amount_usd FROM insurance_claims")}
    for iid, rc in con.execute("SELECT incident_id, root_cause FROM incidents"):
        inc[rc][0] += 1
        if iid in claims:
            inc[rc][1] += 1
            if claims[iid][0] in ("approved", "paid"): inc[rc][2] += claims[iid][1]
    got = run(con, "Q44")
    exp = [(k, a, b, round(c, 2)) for k, (a, b, c) in sorted(inc.items())]
    check("Q44 matches Python (tolerance 0.02)", len(got) == len(exp) and all(g[:3] == e[:3] and abs(g[3] - e[3]) < 0.02 for g, e in zip(got, exp)))

# ------------------------------------------------------------------ 3. tiny edge-case datasets
def fixture():
    """Tiny hand-made dataset. CHECK constraints are switched off so that only the columns that matter for a
    question need values; every other NOT NULL column gets a neutral default."""
    con = sqlite3.connect(":memory:")
    con.executescript(open(os.path.join(ROOT, "schema", "schema.sql"), encoding="utf-8").read())
    con.execute("PRAGMA foreign_keys = OFF")
    con.execute("PRAGMA ignore_check_constraints = ON")
    info = {}

    def ins(table, rows):
        if table not in info:
            info[table] = [(r[1], r[2], r[3]) for r in con.execute(f"PRAGMA table_info({table})")]
        for row in rows:
            vals = []
            for name, typ, notnull in info[table]:
                if name in row:
                    vals.append(row[name])
                else:
                    vals.append((0 if typ in ("INTEGER", "REAL") else f"{table[:3]}{len(vals)}-{id(row)}") if notnull else None)
            con.execute(f"INSERT INTO {table} VALUES ({','.join('?' * len(vals))})", vals)

    ins("airports", [dict(airport_id=i, iata_code=c) for i, c in [(1, "AAA"), (2, "BBB"), (3, "CCC")]])
    ins("airlines", [dict(airline_id=1, name="Air One"), dict(airline_id=2, name="Air Two")])
    ins("aircraft_types", [dict(type_id=1, model="M1", max_payload_kg=1000), dict(type_id=2, model="M2", max_payload_kg=2000)])
    ins("aircraft", [dict(aircraft_id=1, tail_number="T1", type_id=1, airline_id=1), dict(aircraft_id=2, tail_number="T2", type_id=2, airline_id=2)])
    ins("customers", [dict(customer_id=i, name=n, country=c) for i, n, c in [(1, "A", "US"), (2, "B", "US"), (3, "C", "US"), (4, "A", "CA")]])
    fl = lambda i, o, d, ac=1, dist=500: dict(flight_id=i, flight_number=f"XX{i}", aircraft_id=ac, origin_airport_id=o, destination_airport_id=d,
                                              scheduled_departure="2025-02-01 10:00:00", scheduled_arrival="2025-02-01 14:00:00",
                                              actual_departure="2025-02-01 10:05:00", actual_arrival="2025-02-01 14:05:00",
                                              distance_km=dist, status="completed")
    ins("flights", [fl(1, 1, 2), fl(2, 1, 2), fl(3, 1, 3), fl(4, 1, 3), fl(5, 2, 1), fl(6, 2, 3, ac=2, dist=1000)])  # AAA->BBB x2 ties AAA->CCC x2
    sh = lambda i, c, st, bk, kg=10.0: dict(shipment_id=i, customer_id=c, origin_airport_id=1, destination_airport_id=2, booking_date=bk,
                                            service_level="standard", commodity_category="documents", pieces=1, total_weight_kg=kg,
                                            total_volume_m3=0.1, declared_value_usd=100.0, status=st)
    ins("shipments", [sh(1, 1, "delivered", "2025-03-01"), sh(2, 1, "delivered", "2025-03-01"), sh(3, 2, "cancelled", "2025-02-01"),
                      sh(4, 4, "delivered", "2025-01-15"), sh(5, 2, "in_transit", "2025-01-20", kg=500.0), sh(6, 2, "in_transit", "2025-01-20", kg=1500.0)])
    ins("flight_cargo", [dict(flight_cargo_id=1, shipment_id=1, flight_id=1, leg_number=1, load_sequence=1, leg_status="flown"),
                         dict(flight_cargo_id=2, shipment_id=5, flight_id=6, leg_number=1, load_sequence=1, leg_status="flown"),
                         dict(flight_cargo_id=3, shipment_id=6, flight_id=6, leg_number=1, load_sequence=2, leg_status="flown")])
    # Q40: flight 6 carries 2 shipments (2 t in total) over 1000 km and burned 1000 kg -> 500 g per tonne-km
    ins("fuel_uplifts", [dict(fuel_uplift_id=1, flight_id=6, fuel_burned_kg=1000), dict(fuel_uplift_id=2, flight_id=1, fuel_burned_kg=100)])
    ins("invoices", [dict(invoice_id=1, shipment_id=1, issued_date="2025-02-01", due_date="2025-03-03", amount_usd=100.0, status="partially_paid"),
                     dict(invoice_id=2, shipment_id=2, issued_date="2025-02-01", due_date="2025-03-03", amount_usd=50.0, status="unpaid")])
    ins("payments", [dict(payment_id=1, invoice_id=1, customer_id=1, payment_date="2025-02-10", amount_usd=30.0, method="ach"),
                     dict(payment_id=2, invoice_id=1, customer_id=1, payment_date="2025-02-20", amount_usd=20.0, method="ach")])
    ins("incidents", [dict(incident_id=1, flight_cargo_id=1, incident_type="delay", root_cause="weather", reported_at="2025-02-02 00:00:00", resolved=0),
                      dict(incident_id=2, flight_cargo_id=2, incident_type="damage", root_cause="handling", reported_at="2025-02-02 00:00:00", resolved=0)])
    ins("insurance_claims", [dict(claim_id=1, incident_id=2, customer_id=2, status="rejected", claimed_amount_usd=80.0)])
    # Q39: two captains of airline 1 tie on 120 block minutes -> the smaller employee number wins
    ins("crew_members", [dict(crew_member_id=1, employee_number="E-200", airline_id=1, crew_rank="captain", seniority_number=1),
                         dict(crew_member_id=2, employee_number="E-100", airline_id=1, crew_rank="captain", seniority_number=2),
                         dict(crew_member_id=3, employee_number="E-050", airline_id=1, crew_rank="first_officer", seniority_number=3)])
    ca = lambda i, f, c, role, mins: dict(assignment_id=i, flight_id=f, crew_member_id=c, duty_role=role, block_minutes_credited=mins,
                                          assignment_status="completed")
    ins("crew_assignments", [ca(1, 1, 1, "captain", 120), ca(2, 2, 2, "captain", 60), ca(3, 3, 2, "captain", 60), ca(4, 4, 3, "first_officer", 900)])
    # Q45: shipments 1, 2, 4 are delivered; only 1 has a DLV scan; 2 has a held import, 4 needs no customs (NULL)
    ins("tracking_events", [dict(event_id=1, shipment_id=1, event_code="DLV", event_time="2025-03-05 10:00:00", airport_id=2)])
    ins("customs_declarations", [dict(declaration_id=1, shipment_id=2, declaration_type="import", status="held")])
    con.execute("UPDATE shipments SET awb_number = 'AWB-' || shipment_id")
    return con

def layer3():
    print("\n== 3. Edge-case fixtures ==")
    con = fixture()
    check("Q14 anti-join: customers with only cancelled shipments are NOT 'never booked'; no-shipment customer is", run(con, "Q14") == [(3, "C")])
    check("Q15 no join multiplication (2 payments on 1 invoice)", run(con, "Q15") == [(1, 150.0, 50.0, 100.0)], str(run(con, "Q15")))
    check("Q19 tie broken by alphabetically smaller IATA", run(con, "Q19") == [("AAA", "BBB", 2), ("BBB", "AAA", 1)], str(run(con, "Q19")))
    check("Q21 NOT EXISTS across multi-hop join (incident excludes customer 1; customer 2 has no delivered)", run(con, "Q21") == [(4, "A")], str(run(con, "Q21")))
    check("Q22 latest booking tie -> highest shipment_id", run(con, "Q22") == [(1, "2025-03-01", 2), (2, "2025-02-01", 3), (4, "2025-01-15", 4)], str(run(con, "Q22")))
    # naive formulation really differs on this fixture -> proves the fixture discriminates
    naive = con.execute("SELECT s.customer_id, ROUND(SUM(i.amount_usd),2) FROM invoices i JOIN shipments s USING(shipment_id) JOIN payments p USING(invoice_id) GROUP BY 1").fetchall()
    check("fixture discriminates: naive invoice-payment join inflates invoiced amount", naive != [(1, 150.0)], str(naive))
    check("Q39 captain tie broken by smaller employee number; first officers ignored", run(con, "Q39") == [("Air One", "E-100", 2.0)], str(run(con, "Q39")))
    check("Q40 fuel counted once per flight even with 2 shipments on board", run(con, "Q40") == [("M2", 500.0), ("M1", 20000.0)], str(run(con, "Q40")))
    naive40 = con.execute("""SELECT t.model, ROUND(SUM(u.fuel_burned_kg) * 1000.0 / SUM(s.total_weight_kg / 1000.0 * f.distance_km), 1)
        FROM flight_cargo fc JOIN shipments s USING(shipment_id) JOIN flights f USING(flight_id) JOIN fuel_uplifts u USING(flight_id)
        JOIN aircraft a USING(aircraft_id) JOIN aircraft_types t USING(type_id) GROUP BY t.model ORDER BY 2""").fetchall()
    check("fixture discriminates: naive fuel x cargo join doubles fuel", naive40 != run(con, "Q40"), str(naive40))
    check("Q44 root causes without claims still appear with 0", run(con, "Q44") == [("handling", 1, 1, 0.0), ("weather", 1, 0, 0.0)], str(run(con, "Q44")))
    check("Q45 NULL import status for shipments needing no customs", run(con, "Q45") == [("AWB-2", "BBB", "held"), ("AWB-4", "BBB", None)], str(run(con, "Q45")))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--db", default=os.path.join(ROOT, "databases", "cargo_normal.db")); a = ap.parse_args()
    con = sqlite3.connect(a.db)
    layer1(con); layer2(con); layer3()
    print(f"\nRESULT: {'ALL GOLD CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    sys.exit(1 if fails else 0)
