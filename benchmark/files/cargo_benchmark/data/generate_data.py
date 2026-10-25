#!/usr/bin/env python3
"""Deterministic seed-data generator for the Air Cargo Flights benchmark.

Usage:  python data/generate_data.py [output.sql]      (default: data/seed.sql)

Everything is driven by one fixed seed, so the output is byte-identical on every run.
All customers, airlines and aircraft are fictional; airports/aircraft models are public facts.
"""
import math
import os
import random
import sys
from datetime import datetime, timedelta

SEED = 42
AS_OF = datetime(2025, 12, 20)             # "today" inside the dataset
DATA_START = datetime(2025, 1, 1)
DATA_END = datetime(2025, 12, 31, 23, 59)
N_SHIPMENTS_WITH_LEGS = 3000
N_CANCELLED_SHIPMENTS = 110
N_CUSTOMERS = 63                           # the last 3 never ship (LEFT JOIN edge case)
TS, DS = "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"

rng = random.Random(SEED)

# --------------------------------------------------------------------------- static reference data
AIRLINES = [
    (1, "MC", "Meridian Air Cargo", "United States"),
    (2, "BF", "Bosphorus Freight", "Turkey"),
    (3, "SK", "Silkline Cargo", "Hong Kong"),
    (4, "EA", "Eurasia Air Freight", "Germany"),
    (5, "GC", "Gulf Crescent Cargo", "United Arab Emirates"),
]
HOMES = {"MC": ["MEM", "SDF", "ORD", "ANC", "MIA"], "BF": ["IST"], "SK": ["HKG", "PVG", "ICN"],
         "EA": ["LEJ", "FRA", "AMS"], "GC": ["DXB", "DOH"]}
TAIL_PREFIX = {"MC": "N", "BF": "TC-", "SK": "B-", "EA": "D-", "GC": "A6-"}

# iata, name, city, country, lat, lon, hub
AIRPORTS = [
    ("MEM", "Memphis International Airport", "Memphis", "United States", 35.0424, -89.9767, 1),
    ("SDF", "Louisville Muhammad Ali International Airport", "Louisville", "United States", 38.1744, -85.7360, 1),
    ("ANC", "Ted Stevens Anchorage International Airport", "Anchorage", "United States", 61.1743, -149.9983, 1),
    ("LAX", "Los Angeles International Airport", "Los Angeles", "United States", 33.9416, -118.4085, 0),
    ("ORD", "Chicago O'Hare International Airport", "Chicago", "United States", 41.9742, -87.9073, 0),
    ("MIA", "Miami International Airport", "Miami", "United States", 25.7959, -80.2870, 0),
    ("JFK", "John F. Kennedy International Airport", "New York", "United States", 40.6413, -73.7781, 0),
    ("FRA", "Frankfurt Airport", "Frankfurt", "Germany", 50.0379, 8.5622, 1),
    ("LEJ", "Leipzig/Halle Airport", "Leipzig", "Germany", 51.4324, 12.2416, 1),
    ("AMS", "Amsterdam Airport Schiphol", "Amsterdam", "Netherlands", 52.3105, 4.7683, 0),
    ("IST", "Istanbul Airport", "Istanbul", "Turkey", 41.2753, 28.7519, 1),
    ("DXB", "Dubai International Airport", "Dubai", "United Arab Emirates", 25.2532, 55.3657, 1),
    ("DOH", "Hamad International Airport", "Doha", "Qatar", 25.2731, 51.6081, 1),
    ("HKG", "Hong Kong International Airport", "Hong Kong", "Hong Kong", 22.3080, 113.9185, 1),
    ("PVG", "Shanghai Pudong International Airport", "Shanghai", "China", 31.1443, 121.8083, 0),
    ("ICN", "Incheon International Airport", "Incheon", "South Korea", 37.4602, 126.4407, 1),
    ("NRT", "Narita International Airport", "Tokyo", "Japan", 35.7720, 140.3929, 0),
    ("SIN", "Singapore Changi Airport", "Singapore", "Singapore", 1.3644, 103.9915, 0),
]
# model, manufacturer, payload kg, volume m3, range km (approximate, illustrative values)
TYPES = [
    (1, "747-8F", "Boeing", 134000, 854.0, 8000),
    (2, "777F", "Boeing", 102000, 653.0, 9000),
    (3, "767-300F", "Boeing", 52700, 438.0, 6000),
    (4, "A330-200F", "Airbus", 65000, 475.0, 7400),
    (5, "737-800BCF", "Boeing", 23000, 140.0, 3700),
]
MIN_YEAR = {"747-8F": 2011, "777F": 2009, "767-300F": 2000, "A330-200F": 2010, "737-800BCF": 2000}
# airline code, model, status
FLEET = (
    [("MC", m, "active") for m in ["747-8F", "777F", "777F", "767-300F", "767-300F", "737-800BCF"]]
    + [("BF", m, "active") for m in ["A330-200F", "A330-200F", "737-800BCF", "767-300F"]]
    + [("SK", m, "active") for m in ["747-8F", "777F", "777F", "A330-200F"]]
    + [("EA", m, "active") for m in ["767-300F", "767-300F", "737-800BCF", "A330-200F"]]
    + [("GC", m, "active") for m in ["747-8F", "777F"]]
    + [("GC", "A330-200F", "maintenance"), ("MC", "767-300F", "retired")]
)

# commodity: pick-weight, kg range, density kg/m3 range, value USD/kg range, price factor
COMMODITIES = {
    "electronics":      (0.22, (100, 8000),   (120, 220), (80, 400), 1.1),
    "pharmaceuticals":  (0.12, (50, 3000),    (100, 200), (150, 800), 1.5),
    "perishables":      (0.15, (500, 15000),  (150, 300), (5, 25),   1.2),
    "automotive_parts": (0.15, (500, 20000),  (150, 350), (10, 60),  0.9),
    "apparel":          (0.13, (200, 6000),   (80, 160),  (15, 70),  0.9),
    "machinery":        (0.13, (1000, 30000), (200, 450), (8, 40),   0.8),
    "documents":        (0.10, (1, 40),       (90, 160),  (20, 100), 2.0),
}
SERVICE = {"express": (0.20, 1.6), "standard": (0.55, 1.0), "economy": (0.25, 0.65)}
BASE_RATE_PER_KG = 2.8

NAME_PREFIX = ["Apex", "Brightwave", "Cobalt", "Dunmore", "Evergreen", "Falcon", "Granite", "Harbor", "Ironbridge",
               "Juniper", "Keystone", "Lumen", "Meridian Hill", "Northgate", "Orchid", "Pinnacle", "Quartz",
               "Redwood", "Sterling", "Tidewater", "Umbra", "Vantage", "Willow", "Xenon", "Yarrow", "Zenith",
               "Atlas", "Beacon", "Crestline", "Driftwood", "Emberly", "Foxglove"]
NAME_SUFFIX = ["Logistics", "Trading", "Freight Services", "Pharma", "Electronics", "Motors", "Textiles",
               "Industries", "Foods", "Supply Co"]
CUST_COUNTRIES = ["United States", "Germany", "China", "Turkey", "United Arab Emirates", "South Korea", "Japan",
                  "Singapore", "Netherlands", "Canada", "Brazil", "India", "United Kingdom"]
CUST_TYPES = ["shipper", "freight_forwarder", "retailer", "manufacturer"]


# --------------------------------------------------------------------------- helpers
def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def round5(dt):
    return dt.replace(minute=(dt.minute // 5) * 5, second=0, microsecond=0)


def wchoice(options, weights):
    return rng.choices(options, weights=weights, k=1)[0]


def log_uniform(lo, hi):
    return math.exp(rng.uniform(math.log(lo), math.log(hi)))


def sql_val(v):
    if v is None:
        return "NULL"
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    if isinstance(v, float):
        return repr(round(v, 4))
    return str(v)


# --------------------------------------------------------------------------- build reference tables
airports = [dict(id=i + 1, iata=a[0], name=a[1], city=a[2], country=a[3], lat=a[4], lon=a[5], hub=a[6])
            for i, a in enumerate(AIRPORTS)]
ap_by_iata = {a["iata"]: a for a in airports}
types = {t[0]: dict(id=t[0], model=t[1], mfr=t[2], payload=t[3], volume=t[4], range=t[5]) for t in TYPES}
type_by_model = {t["model"]: t for t in types.values()}
airline_by_code = {a[1]: a for a in AIRLINES}

aircraft, used_tails = [], {}
for i, (code, model, status) in enumerate(FLEET, start=1):
    while True:
        tail = f"{TAIL_PREFIX[code]}{rng.randint(100, 999)}{rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}"
        if tail not in used_tails:
            used_tails[tail] = True
            break
    aircraft.append(dict(id=i, tail=tail, type_id=type_by_model[model]["id"], airline_id=airline_by_code[code][0],
                         code=code, year=rng.randint(MIN_YEAR[model], 2024), status=status,
                         home=ap_by_iata[rng.choice(HOMES[code])]["id"]))
ap_by_id = {a["id"]: a for a in airports}

# customers
customers, seen_names = [], {}
while len(customers) < N_CUSTOMERS:
    name = f"{rng.choice(NAME_PREFIX)} {rng.choice(NAME_SUFFIX)}"
    if name in seen_names:
        continue
    seen_names[name] = True
    customers.append(dict(id=len(customers) + 1, name=name, country=rng.choice(CUST_COUNTRIES),
                          type=rng.choice(CUST_TYPES), terms=wchoice([15, 30, 45, 60], [0.1, 0.5, 0.25, 0.15]),
                          created=(datetime(2018, 1, 1) + timedelta(days=rng.randint(0, 2400))).strftime(DS)))
# edge case: two different customers sharing one name (different countries)
customers[7]["name"] = customers[1]["name"]
if customers[7]["country"] == customers[1]["country"]:
    customers[7]["country"] = "Canada" if customers[1]["country"] != "Canada" else "Brazil"

# --------------------------------------------------------------------------- flights
flights, used_fn = [], {}
for ac in [a for a in aircraft if a["status"] == "active"]:
    t = DATA_START + timedelta(hours=rng.randint(0, 96))
    cur, rng_km = ac["home"], types[ac["type_id"]]["range"]
    while True:
        dep = round5(t)
        cands = [a for a in airports if a["id"] != cur and haversine(ap_by_id[cur], a) <= rng_km]
        assert cands, "aircraft stranded"
        dest = wchoice(cands, [3 if a["hub"] else 1 for a in cands])
        dist = int(round(haversine(ap_by_id[cur], dest)))
        dur = timedelta(minutes=int(dist / 780 * 60 + 50))
        arr = dep + dur
        if dep < AS_OF and arr + timedelta(hours=10) > AS_OF:       # nothing may be airborne at the as-of moment
            dep = AS_OF + timedelta(hours=rng.randint(1, 12))
            arr = dep + dur
        if dep > DATA_END:
            break
        if dep >= AS_OF:
            status = "scheduled"
        else:
            status = "cancelled" if rng.random() < 0.04 else "completed"
        while True:
            fn = f"{ac['code']}{rng.randint(100, 999)}"
            if (fn, dep) not in used_fn:
                used_fn[(fn, dep)] = True
                break
        adep = aarr = None
        if status == "completed":
            r = rng.random()
            delay = rng.randint(-5, 15) if r < 0.70 else rng.randint(20, 240) if r < 0.95 else rng.randint(241, 480)
            adep = dep + timedelta(minutes=delay)
            aarr = adep + dur + timedelta(minutes=rng.randint(-20, 30))
        flights.append(dict(ac=ac["id"], type_id=ac["type_id"], fn=fn, org=cur, dst=dest["id"], sdep=dep, sarr=arr,
                            adep=adep, aarr=aarr, dist=dist, status=status))
        if status != "cancelled":
            cur = dest["id"]
        t = arr + timedelta(hours=rng.randint(24, 120))
flights.sort(key=lambda f: (f["sdep"], f["ac"]))
for i, f in enumerate(flights, start=1):
    f["id"] = i

# --------------------------------------------------------------------------- shipments
rem_w = {f["id"]: types[f["type_id"]]["payload"] for f in flights}
rem_v = {f["id"]: types[f["type_id"]]["volume"] for f in flights}
eligible = [f for f in flights if f["status"] != "cancelled" and f["sdep"] >= datetime(2025, 1, 11)]
by_origin = {}
for f in flights:
    if f["status"] != "cancelled":
        by_origin.setdefault(f["org"], []).append(f)

comm_names = list(COMMODITIES)
comm_weights = [COMMODITIES[c][0] for c in comm_names]
cust_ids = [c["id"] for c in customers[: N_CUSTOMERS - 3]]
cust_weights = [1 / (k + 1) ** 0.8 for k in range(len(cust_ids))]


def new_shipment_attrs():
    comm = wchoice(comm_names, comm_weights)
    _, (wlo, whi), (dlo, dhi), (vlo, vhi), _f = COMMODITIES[comm]
    weight = round(log_uniform(wlo, whi), 1)
    volume = max(0.01, round(weight / rng.uniform(dlo, dhi), 2))
    pieces = max(1, int(weight / rng.uniform(5, 400)))
    service = wchoice(list(SERVICE), [SERVICE[s][0] for s in SERVICE])
    return dict(cust=wchoice(cust_ids, cust_weights), comm=comm, weight=weight, volume=volume, pieces=pieces,
                service=service, value=round(weight * rng.uniform(vlo, vhi), 2))


ships, attempts = [], 0
while len(ships) < N_SHIPMENTS_WITH_LEGS and attempts < 100000:
    attempts += 1
    f1 = rng.choice(eligible)
    legs = [f1]
    if rng.random() < 0.30:
        opts = [g for g in by_origin.get(f1["dst"], [])
                if g["dst"] != f1["org"] and f1["sarr"] + timedelta(hours=12) <= g["sdep"] <= f1["sarr"] + timedelta(days=5)]
        if opts:
            legs.append(rng.choice(opts))
    s = new_shipment_attrs()
    if any(s["weight"] > rem_w[l["id"]] or s["volume"] > rem_v[l["id"]] for l in legs):
        continue
    for l in legs:
        rem_w[l["id"]] -= s["weight"]
        rem_v[l["id"]] -= s["volume"]
    booking = min((f1["sdep"] - timedelta(days=rng.randint(1, 10))).date(), AS_OF.date())
    flown = [l["status"] == "completed" for l in legs]
    status = "delivered" if all(flown) else "in_transit" if any(flown) else "booked"
    s.update(booking=booking.strftime(DS), org=f1["org"], dst=legs[-1]["dst"], legs=legs, status=status)
    ships.append(s)

for _ in range(N_CANCELLED_SHIPMENTS):
    s = new_shipment_attrs()
    o, d = rng.sample(airports, 2)
    s.update(booking=(datetime(2025, 1, 2) + timedelta(days=rng.randint(0, 351))).strftime(DS),
             org=o["id"], dst=d["id"], legs=[], status="cancelled")
    ships.append(s)

ships.sort(key=lambda s: s["booking"])           # stable: ties keep creation order
for i, s in enumerate(ships, start=1):
    s["id"] = i

# --------------------------------------------------------------------------- flight_cargo, invoices, payments, incidents
cargo, invoices, payments, incidents = [], [], [], []
cust_by_id = {c["id"]: c for c in customers}
for s in ships:
    for n, l in enumerate(s["legs"], start=1):
        cargo.append(dict(id=len(cargo) + 1, ship=s["id"], flight=l["id"], leg=n,
                          status="flown" if l["status"] == "completed" else "planned", s=s, f=l))

for s in ships:
    if s["status"] not in ("in_transit", "delivered"):
        continue
    issued = s["legs"][0]["adep"].date()
    terms = cust_by_id[s["cust"]]["terms"]
    amount = round(max(s["weight"] * BASE_RATE_PER_KG * SERVICE[s["service"]][1] * COMMODITIES[s["comm"]][4]
                       * rng.uniform(0.9, 1.1), 75.0), 2)
    inv = dict(id=len(invoices) + 1, ship=s["id"], issued=issued, due=issued + timedelta(days=terms), amount=amount)
    r = rng.random()
    plan = []                                    # (payment date, amount)
    first_date = issued + timedelta(days=rng.randint(3, terms + 25))
    if r < 0.70:
        if rng.random() < 0.25:
            part = round(amount * rng.uniform(0.3, 0.7), 2)
            plan = [(first_date, part), (first_date + timedelta(days=rng.randint(2, 20)), round(amount - part, 2))]
        else:
            plan = [(first_date, amount)]
    elif r < 0.78:
        plan = [(first_date, round(amount * rng.uniform(0.2, 0.8), 2))]
    paid = 0.0
    for d, a in plan:
        if datetime(d.year, d.month, d.day) > AS_OF or a <= 0:
            continue
        payments.append(dict(id=len(payments) + 1, inv=inv["id"], cust=s["cust"], date=d, amount=a,
                             method=wchoice(["wire_transfer", "ach", "credit_card"], [0.5, 0.3, 0.2])))
        paid = round(paid + a, 2)
    inv["status"] = "paid" if paid >= amount else "partially_paid" if paid > 0 else "unpaid"
    invoices.append(inv)

INC_TYPES = ["damage", "delay", "missing_documents", "temperature_excursion", "loss"]
for c in cargo:
    if c["status"] != "flown" or rng.random() >= 0.04:
        continue
    s, f = c["s"], c["f"]
    ok = INC_TYPES if s["comm"] in ("perishables", "pharmaceuticals") else [t for t in INC_TYPES if t != "temperature_excursion"]
    itype = wchoice(ok, [{"damage": 35, "delay": 25, "missing_documents": 20, "temperature_excursion": 15, "loss": 5}[t] for t in ok])
    reported = min(f["aarr"] + timedelta(hours=rng.randint(1, 72)), AS_OF)
    claim = None
    if itype == "damage":
        claim = round(s["value"] * rng.uniform(0.05, 0.6), 2)
    elif itype == "loss":
        claim = s["value"]
    elif itype == "temperature_excursion" and rng.random() < 0.6:
        claim = round(s["value"] * rng.uniform(0.1, 0.8), 2)
    resolved = int((AS_OF - reported).days >= 14 and rng.random() < 0.7)
    incidents.append(dict(id=len(incidents) + 1, cargo=c["id"], type=itype,
                          sev=wchoice(["low", "medium", "high"], [0.5, 0.35, 0.15]),
                          at=reported.strftime(TS), claim=claim, resolved=resolved))


# --------------------------------------------------------------------------- write SQL
def emit(out, table, cols, rows):
    for r in rows:
        out.write(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(sql_val(v) for v in r)});\n")
    out.write("\n")


def main(path):
    with open(path, "w", encoding="utf-8", newline="\n") as out:
        out.write("-- Seed data for the Air Cargo Flights benchmark (generated by data/generate_data.py, seed=%d)\n" % SEED)
        out.write("-- Do not edit by hand: regenerate instead.\nPRAGMA foreign_keys = ON;\nBEGIN;\n\n")
        emit(out, "benchmark_meta", ["meta_key", "meta_value"],
             [("as_of_timestamp", AS_OF.strftime(TS)), ("generator_seed", str(SEED)), ("engine", "SQLite 3.25+"),
              ("note", "All names are fictional; no real personal or confidential data.")])
        emit(out, "airlines", ["airline_id", "iata_code", "name", "country"], AIRLINES)
        emit(out, "airports", ["airport_id", "iata_code", "name", "city", "country", "latitude", "longitude", "is_cargo_hub"],
             [(a["id"], a["iata"], a["name"], a["city"], a["country"], a["lat"], a["lon"], a["hub"]) for a in airports])
        emit(out, "aircraft_types", ["type_id", "model", "manufacturer", "max_payload_kg", "max_volume_m3", "max_range_km"],
             [(t["id"], t["model"], t["mfr"], t["payload"], t["volume"], t["range"]) for t in types.values()])
        emit(out, "aircraft", ["aircraft_id", "tail_number", "type_id", "airline_id", "year_manufactured", "status"],
             [(a["id"], a["tail"], a["type_id"], a["airline_id"], a["year"], a["status"]) for a in aircraft])
        emit(out, "customers", ["customer_id", "name", "country", "customer_type", "payment_terms_days", "created_date"],
             [(c["id"], c["name"], c["country"], c["type"], c["terms"], c["created"]) for c in customers])
        emit(out, "flights", ["flight_id", "flight_number", "aircraft_id", "origin_airport_id", "destination_airport_id",
                              "scheduled_departure", "scheduled_arrival", "actual_departure", "actual_arrival",
                              "distance_km", "status"],
             [(f["id"], f["fn"], f["ac"], f["org"], f["dst"], f["sdep"].strftime(TS), f["sarr"].strftime(TS),
               f["adep"].strftime(TS) if f["adep"] else None, f["aarr"].strftime(TS) if f["aarr"] else None,
               f["dist"], f["status"]) for f in flights])
        emit(out, "shipments", ["shipment_id", "customer_id", "origin_airport_id", "destination_airport_id", "booking_date",
                                "service_level", "commodity_category", "pieces", "total_weight_kg", "total_volume_m3",
                                "declared_value_usd", "status"],
             [(s["id"], s["cust"], s["org"], s["dst"], s["booking"], s["service"], s["comm"], s["pieces"], s["weight"],
               s["volume"], s["value"], s["status"]) for s in ships])
        emit(out, "flight_cargo", ["flight_cargo_id", "shipment_id", "flight_id", "leg_number", "leg_status"],
             [(c["id"], c["ship"], c["flight"], c["leg"], c["status"]) for c in cargo])
        emit(out, "invoices", ["invoice_id", "shipment_id", "issued_date", "due_date", "amount_usd", "status"],
             [(i["id"], i["ship"], i["issued"].strftime(DS), i["due"].strftime(DS), i["amount"], i["status"]) for i in invoices])
        emit(out, "payments", ["payment_id", "invoice_id", "customer_id", "payment_date", "amount_usd", "method"],
             [(p["id"], p["inv"], p["cust"], p["date"].strftime(DS), p["amount"], p["method"]) for p in payments])
        emit(out, "incidents", ["incident_id", "flight_cargo_id", "incident_type", "severity", "reported_at",
                                "claim_amount_usd", "resolved"],
             [(i["id"], i["cargo"], i["type"], i["sev"], i["at"], i["claim"], i["resolved"]) for i in incidents])
        out.write("COMMIT;\n")


if __name__ == "__main__":
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql")
    main(sys.argv[1] if len(sys.argv) > 1 else default)
