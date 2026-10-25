#!/usr/bin/env python3
"""Gold SQL validation: (1) executability/shape, (2) independent Python recomputation on the main DB,
(3) deliberately constructed tiny datasets exposing edge cases (ties, NULLs, join multiplication, anti-joins).
Usage: python validation/test_gold.py [--db cargo_flights.db]"""
import argparse, collections, json, os, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = {q["id"]: q for q in json.load(open(os.path.join(ROOT, "questions", "questions.json")))}
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

# ------------------------------------------------------------------ 3. tiny edge-case datasets
def fixture():
    con = sqlite3.connect(":memory:")
    con.executescript(open(os.path.join(ROOT, "schema", "schema.sql")).read())
    con.execute("PRAGMA foreign_keys = OFF")
    ins = lambda sql, rows: con.executemany(sql, rows)
    ins("INSERT INTO airports VALUES (?,?,?,?,?,?,?,?)", [(1, "AAA", "a", "a", "X", 0, 0, 0), (2, "BBB", "b", "b", "X", 1, 1, 0), (3, "CCC", "c", "c", "X", 2, 2, 0)])
    ins("INSERT INTO customers VALUES (?,?,?,?,?,?)", [(1, "A", "US", "shipper", 30, "2020-01-01"), (2, "B", "US", "shipper", 30, "2020-01-01"),
                                                        (3, "C", "US", "shipper", 30, "2020-01-01"), (4, "A", "CA", "shipper", 30, "2020-01-01")])
    fl = lambda i, o, d: (i, f"XX{i}", 1, o, d, "2025-02-01 10:00:00", "2025-02-01 14:00:00", "2025-02-01 10:05:00", "2025-02-01 14:05:00", 500, "completed")
    ins("INSERT INTO flights VALUES (?,?,?,?,?,?,?,?,?,?,?)", [fl(1, 1, 2), fl(2, 1, 2), fl(3, 1, 3), fl(4, 1, 3), fl(5, 2, 1)])   # AAA->BBB x2 ties AAA->CCC x2
    sh = lambda i, c, st, bk: (i, c, 1, 2, bk, "standard", "documents", 1, 10.0, 0.1, 100.0, st)
    ins("INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [sh(1, 1, "delivered", "2025-03-01"), sh(2, 1, "delivered", "2025-03-01"),
                                                                    sh(3, 2, "cancelled", "2025-02-01"), sh(4, 4, "delivered", "2025-01-15")])
    ins("INSERT INTO flight_cargo VALUES (?,?,?,?,?)", [(1, 1, 1, 1, "flown")])
    ins("INSERT INTO invoices VALUES (?,?,?,?,?,?)", [(1, 1, "2025-02-01", "2025-03-03", 100.0, "partially_paid"), (2, 2, "2025-02-01", "2025-03-03", 50.0, "unpaid")])
    ins("INSERT INTO payments VALUES (?,?,?,?,?,?)", [(1, 1, 1, "2025-02-10", 30.0, "ach"), (2, 1, 1, "2025-02-20", 20.0, "ach")])
    ins("INSERT INTO incidents VALUES (?,?,?,?,?,?,?)", [(1, 1, "delay", "low", "2025-02-02 00:00:00", None, 0)])
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

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--db", default=os.path.join(ROOT, "cargo_flights.db")); a = ap.parse_args()
    con = sqlite3.connect(a.db)
    layer1(con); layer2(con); layer3()
    print(f"\nRESULT: {'ALL GOLD CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    sys.exit(1 if fails else 0)
