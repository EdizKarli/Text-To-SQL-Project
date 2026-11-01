#!/usr/bin/env python3
"""Gold SQL validation for the 120 base questions (each shared by 4 phrasings).

(1) executability and shape: every Gold query runs, returns rows, is not all-NULL; the 4 phrasings of a base
    question share exactly one Gold query; LIMIT queries have no tie at the cut-off (else the answer is arbitrary);
(2) independent recomputation in Python of a sample of moderate/hard answers on the main database;
(3) deliberately constructed tiny datasets exposing edge cases (ties, zero-count LEFT JOIN, anti-joins,
    join multiplication, relational division, NULL handling).
Runs on the NORMAL schema; validation/test_variants.py checks the mixed/cryptic Gold queries against these results.
Usage: python validation/test_gold.py [--db databases/cargo_normal.db]"""
import argparse, collections, json, os, re, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL = json.load(open(os.path.join(ROOT, "questions", "questions_normal.json"), encoding="utf-8"))
GOLD = {}
for q in ALL:
    GOLD.setdefault(q["base_id"], set()).add(q["gold_sql"])
fails = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail if not ok else ''}")
    if not ok:
        fails.append(label)


def run(con, base_id):
    return con.execute(next(iter(GOLD[base_id]))).fetchall()


# ------------------------------------------------------------------ 1. executability + sanity
def layer1(con):
    print("== 1. Executability, sanity and tie safety ==")
    per_diff = collections.Counter(b[0] for b in GOLD)
    check(f"{len(ALL)} questions = {len(GOLD)} base questions x 4 styles, same number of bases per difficulty",
          len(ALL) == 4 * len(GOLD) and len(set(per_diff.values())) == 1
          and all(len([q for q in ALL if q["base_id"] == b]) == 4 for b in GOLD))
    check("the 4 phrasings of each base question share one Gold query", all(len(s) == 1 for s in GOLD.values()))
    for b in sorted(GOLD):
        sql = next(iter(GOLD[b]))
        rows = con.execute(sql).fetchall()
        ok = bool(rows) and any(v is not None for r in rows for v in r)
        tie = ""
        m = re.search(r"LIMIT (\d+)\s*;?\s*$", sql)
        if m:
            n = int(m.group(1))
            full = con.execute(sql[:m.start()]).fetchall()
            if len(full) > n and full[n - 1][-1] == full[n][-1]:
                ok, tie = False, f"tie at LIMIT {n}: {full[n - 1]} / {full[n]}"
        check(f"{b} runs, non-empty, not all-NULL, no tie at cut-off", ok, f"rows={len(rows)} {tie}")


# ------------------------------------------------------------------ 2. independent recomputation
def layer2(con):
    print("\n== 2. Independent recomputation in Python ==")
    q = lambda s: con.execute(s).fetchall()
    # M01 fleet per airline incl. zero
    n = collections.Counter(a for (a,) in q("SELECT airline_id FROM aircraft"))
    exp = sorted(((nm, n[i]) for i, nm in q("SELECT airline_id, name FROM airlines")), key=lambda r: (-r[1], r[0]))
    check("M01 matches Python", run(con, "M01") == exp)
    # M22 days to pay per method
    inv = dict(q("SELECT invoice_id, issued_date FROM invoices"))
    import datetime as dt
    d = lambda s: dt.date.fromisoformat(s)
    agg = collections.defaultdict(list)
    for iid, m, pd in q("SELECT invoice_id, method, payment_date FROM payments"):
        agg[m].append((d(pd) - d(inv[iid])).days)
    check("M22 matches Python", run(con, "M22") == [(m, round(sum(v) / len(v), 1)) for m, v in sorted(agg.items())])
    # H06 revenue share > 4 %
    rev = collections.defaultdict(float)
    for cid, amt in q("SELECT s.customer_id, i.amount_usd FROM invoices i JOIN shipments s USING(shipment_id)"):
        rev[cid] += amt
    tot = sum(rev.values())
    names = dict(q("SELECT customer_id, name FROM customers"))
    exp = sorted(((names[c], round(r, 2), round(100 * r / tot, 2)) for c, r in rev.items() if 100 * r / tot > 4), key=lambda x: -x[2])
    got = run(con, "H06")
    check("H06 matches Python (tolerance 0.02)", len(got) == len(exp) and all(g[0] == e[0] and abs(g[1] - e[1]) < 0.02 and g[2] == e[2] for g, e in zip(got, exp)))
    # H08 half-full flights (volume summed per flight before comparing)
    vol = collections.defaultdict(float)
    for fid, v in q("SELECT fc.flight_id, s.total_volume_m3 FROM flight_cargo fc JOIN shipments s USING(shipment_id)"):
        vol[fid] += v
    cnt = collections.Counter()
    for fid, model, cap in q("""SELECT f.flight_id, t.model, t.max_volume_m3 FROM flights f JOIN aircraft a USING(aircraft_id)
                                JOIN aircraft_types t USING(type_id) WHERE f.status = 'completed'"""):
        if vol.get(fid, 0) > 0.5 * cap:
            cnt[model] += 1
    check("H08 matches Python", run(con, "H08") == sorted(cnt.items()))
    # H09 aircraft that visited every hub
    hubs = {i for (i,) in q("SELECT airport_id FROM airports WHERE is_cargo_hub = 1")}
    seen = collections.defaultdict(set)
    for tail, dst in q("SELECT a.tail_number, f.destination_airport_id FROM flights f JOIN aircraft a USING(aircraft_id) WHERE f.status = 'completed'"):
        seen[tail].add(dst)
    check("H09 matches Python", run(con, "H09") == sorted((t,) for t, s in seen.items() if hubs <= s))
    # H31 incidents + approved claims per customer (LEFT JOIN, zero when no claim)
    claims = {i: (st, a) for i, st, a in q("SELECT incident_id, status, approved_amount_usd FROM insurance_claims")}
    per = collections.defaultdict(lambda: [0, 0.0])
    for iid, cid in q("SELECT i.incident_id, s.customer_id FROM incidents i JOIN flight_cargo fc USING(flight_cargo_id) JOIN shipments s USING(shipment_id)"):
        per[cid][0] += 1
        st, a = claims.get(iid, (None, None))
        if st in ("approved", "paid"):
            per[cid][1] += a
    exp = sorted(((c, names[c], k, round(v, 2)) for c, (k, v) in per.items() if k >= 4), key=lambda r: (-r[2], r[0]))
    got = run(con, "H31")
    check("H31 matches Python (tolerance 0.02)", [g[:2] for g in got] == [(e[1], e[2]) for e in exp] and all(abs(g[2] - e[3]) < 0.02 for g, e in zip(got, exp)))
    # H38 cumulative share ends at 100 %
    check("H38 cumulative share reaches 100%", run(con, "H38")[-1][-1] == 100.0)
    # H03 running total equals total invoiced in 2025
    tot25 = q("SELECT ROUND(SUM(amount_usd), 2) FROM invoices WHERE issued_date LIKE '2025%'")[0][0]
    check("H03 running total ends at the 2025 total", abs(run(con, "H03")[-1][-1] - tot25) < 0.02)


# ------------------------------------------------------------------ 3. tiny edge-case datasets
def fixture():
    """Tiny hand-made dataset. CHECK constraints are off so only the columns that matter need values."""
    con = sqlite3.connect(":memory:")
    con.executescript(open(os.path.join(ROOT, "schema", "schema.sql"), encoding="utf-8").read())
    con.execute("PRAGMA foreign_keys = OFF")
    con.execute("PRAGMA ignore_check_constraints = ON")
    info = {}

    def ins(table, rows):
        if table not in info:
            info[table] = [(r[1], r[2], r[3]) for r in con.execute(f"PRAGMA table_info({table})")]
        for row in rows:
            vals = [row[n] if n in row else ((0 if t in ("INTEGER", "REAL") else f"{table[:3]}-{n}-{id(row)}") if nn else None)
                    for n, t, nn in info[table]]
            con.execute(f"INSERT INTO {table} VALUES ({','.join('?' * len(vals))})", vals)

    ins("airports", [dict(airport_id=1, iata_code="AAA", is_cargo_hub=1), dict(airport_id=2, iata_code="BBB", is_cargo_hub=1),
                     dict(airport_id=3, iata_code="CCC", is_cargo_hub=0)])
    ins("airlines", [dict(airline_id=1, name="Air One"), dict(airline_id=2, name="Air Two"), dict(airline_id=3, name="Air Zero")])
    ins("aircraft_types", [dict(type_id=1, model="M1", max_volume_m3=100.0), dict(type_id=2, model="M2", max_volume_m3=100.0)])
    ins("aircraft", [dict(aircraft_id=1, tail_number="T2", type_id=1, airline_id=1, status="active"),
                     dict(aircraft_id=2, tail_number="T1", type_id=1, airline_id=1, status="active"),
                     dict(aircraft_id=3, tail_number="T3", type_id=2, airline_id=2, status="active")])
    fl = lambda i, ac, o, d, st="completed": dict(flight_id=i, flight_number=f"F{i}", aircraft_id=ac, origin_airport_id=o, destination_airport_id=d,
                                                  scheduled_departure=f"2025-03-{i:02d} 10:00:00", scheduled_arrival=f"2025-03-{i:02d} 14:00:00",
                                                  actual_departure=f"2025-03-{i:02d} 10:00:00", actual_arrival=f"2025-03-{i:02d} 14:00:00", status=st)
    # T2 and T1 both fly 2 completed flights (tie -> smaller tail T1); T1 visits both hubs, T2 only AAA; T3 visits both hubs
    ins("flights", [fl(1, 1, 3, 1), fl(2, 1, 3, 1), fl(3, 2, 3, 1), fl(4, 2, 3, 2), fl(5, 3, 3, 1), fl(6, 3, 1, 2), fl(7, 1, 1, 2, "cancelled")])
    ins("customers", [dict(customer_id=1, name="C1"), dict(customer_id=2, name="C2"), dict(customer_id=3, name="C3")])
    sh = lambda i, c, d, vol, st="delivered": dict(shipment_id=i, customer_id=c, origin_airport_id=3, destination_airport_id=d,
                                                   total_volume_m3=vol, total_weight_kg=10.0, status=st)
    # flight 5 carries 30 + 30 m3 (60 % of 100 -> half full only when summed); flight 6 carries 70 m3 once
    ins("shipments", [sh(1, 1, 1, 30.0), sh(2, 1, 2, 30.0), sh(3, 2, 1, 70.0), sh(4, 2, 2, 1.0, "cancelled")])
    ins("flight_cargo", [dict(flight_cargo_id=1, shipment_id=1, flight_id=5, leg_number=1, load_sequence=1, leg_status="flown"),
                         dict(flight_cargo_id=2, shipment_id=2, flight_id=5, leg_number=1, load_sequence=2, leg_status="flown"),
                         dict(flight_cargo_id=3, shipment_id=3, flight_id=6, leg_number=1, load_sequence=1, leg_status="flown")])
    ins("maintenance_records", [dict(maintenance_id=1, aircraft_id=1, check_type="line", status="completed", work_order_number="W1",
                                     parts_cost_usd=1.0, labor_cost_usd=1.0)])
    ins("invoices", [dict(invoice_id=1, shipment_id=1, issued_date="2025-10-01", amount_usd=100.0, status="unpaid"),
                     dict(invoice_id=2, shipment_id=3, issued_date="2025-10-01", amount_usd=100.0, status="partially_paid")])
    ins("payments", [dict(payment_id=1, invoice_id=2, customer_id=2, payment_date="2025-12-01", amount_usd=10.0, method="ach")])
    return con


def layer3():
    print("\n== 3. Edge-case fixtures ==")
    con = fixture()
    check("M01 LEFT JOIN keeps an airline with zero aircraft", run(con, "M01") == [("Air One", 2), ("Air Two", 1), ("Air Zero", 0)], str(run(con, "M01")))
    check("M15 anti-join: aircraft without maintenance records", run(con, "M15") == [("T1",), ("T3",)], str(run(con, "M15")))
    check("H01 tie on completed flights broken by smaller tail number; cancelled flight ignored",
          run(con, "H01") == [("Air One", "T1", 2), ("Air Two", "T3", 2)], str(run(con, "H01")))
    check("H08 volume summed per flight before comparing with 50% capacity", run(con, "H08") == [("M2", 2)], str(run(con, "H08")))
    check("H09 relational division: aircraft that reached every hub", run(con, "H09") == [("T1",), ("T3",)], str(run(con, "H09")))
    check("H22 customers with a recent payment are excluded; open invoices counted", run(con, "H22") == [("C1", 1)], str(run(con, "H22")))
    check("H33 cancelled shipments do not count towards covering every hub", run(con, "H33") == [(1, "C1")], str(run(con, "H33")))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--db", default=os.path.join(ROOT, "databases", "cargo_normal.db")); a = ap.parse_args()
    con = sqlite3.connect(a.db)
    layer1(con); layer2(con); layer3()
    print(f"\nRESULT: {'ALL GOLD CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    sys.exit(1 if fails else 0)
