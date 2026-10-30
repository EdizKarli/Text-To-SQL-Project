#!/usr/bin/env python3
"""Deterministic seed-data generator for the Air Cargo Flights benchmark.

Usage:  python data/generate_data.py [output.sql]      (default: data/seed.sql)

Everything is driven by fixed seeds, so the output is byte-identical on every run.
All customers, airlines, aircraft, crew and companies are fictional; airports/aircraft models are public facts.

Two phases:
  core       (seed 42)  the original 12 tables / 79 columns, unchanged from v1 so Q01-Q25 keep their answers
  extension  (seed 43)  the extra columns of those tables and the 8 new tables (schema version 2: 20 tables, 300 columns)
The output targets the NORMAL schema; scripts/build_variants.py derives the mixed and cryptic databases from it.
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
        return repr(round(v, 8))
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




# ===========================================================================
# EXTENSION PHASE (v2 schema: 20 tables / 300 columns)
# Everything below uses its own random stream X, so the core data above (and therefore the
# answers of the original 25 questions) is exactly the same as in the 12-table version.
# ===========================================================================
X = random.Random(SEED + 1)


def xw(options, weights):
    return X.choices(options, weights=weights, k=1)[0]


def xlog_uniform(lo, hi):
    return math.exp(X.uniform(math.log(lo), math.log(hi)))


def ts(dt):
    return dt.strftime(TS) if dt else None


def ds(d):
    return d.strftime(DS) if d else None


def r5(dt):
    return dt.replace(second=0, microsecond=0) - timedelta(minutes=dt.minute % 5)


def as_date(s):
    return datetime.strptime(s, DS)


fl_by_id = {f["id"]: f for f in flights}
ac_by_id = {a["id"]: a for a in aircraft}
ship_by_id = {s["id"]: s for s in ships}
airline_code_by_id = {a[0]: a[1] for a in AIRLINES}
US = "United States"

# --------------------------------------------------------------------------- airports (extra attributes)
# icao, region, timezone, elevation m, runways, longest runway m, cargo capacity t/yr, 24h customs, night curfew
AIRPORT_EXT = {
    "MEM": ("KMEM", "north_america", "America/Chicago", 104, 4, 3389, 4300000, 1, 0),
    "SDF": ("KSDF", "north_america", "America/New_York", 154, 3, 3624, 3000000, 0, 0),
    "ANC": ("PANC", "north_america", "America/Anchorage", 46, 3, 3780, 3500000, 0, 0),
    "LAX": ("KLAX", "north_america", "America/Los_Angeles", 38, 4, 3685, 2300000, 1, 0),
    "ORD": ("KORD", "north_america", "America/Chicago", 204, 8, 3962, 2000000, 1, 0),
    "MIA": ("KMIA", "north_america", "America/New_York", 2, 4, 3962, 2800000, 1, 0),
    "JFK": ("KJFK", "north_america", "America/New_York", 4, 4, 4423, 1500000, 1, 0),
    "FRA": ("EDDF", "europe", "Europe/Berlin", 111, 4, 4000, 2300000, 1, 1),
    "LEJ": ("EDDP", "europe", "Europe/Berlin", 142, 2, 3600, 1500000, 1, 0),
    "AMS": ("EHAM", "europe", "Europe/Amsterdam", -3, 6, 3800, 1700000, 1, 0),
    "IST": ("LTFM", "europe", "Europe/Istanbul", 99, 5, 4100, 2100000, 1, 0),
    "DXB": ("OMDB", "middle_east", "Asia/Dubai", 19, 2, 4447, 2500000, 1, 0),
    "DOH": ("OTHH", "middle_east", "Asia/Qatar", 4, 2, 4850, 2700000, 1, 0),
    "HKG": ("VHHH", "asia_pacific", "Asia/Hong_Kong", 9, 3, 3800, 5000000, 1, 0),
    "PVG": ("ZSPD", "asia_pacific", "Asia/Shanghai", 4, 5, 4000, 4100000, 1, 0),
    "ICN": ("RKSI", "asia_pacific", "Asia/Seoul", 7, 4, 4000, 3300000, 1, 0),
    "NRT": ("RJAA", "asia_pacific", "Asia/Tokyo", 43, 2, 4000, 2600000, 0, 1),
    "SIN": ("WSSS", "asia_pacific", "Asia/Singapore", 7, 3, 4000, 2200000, 1, 0),
}
for a in airports:
    (a["icao"], a["region"], a["tz"], a["elev"], a["rwys"], a["rwy_len"], a["cap_t"],
     a["customs24"], a["curfew"]) = AIRPORT_EXT[a["iata"]]

# --------------------------------------------------------------------------- airlines (extra attributes)
# icao, callsign, HQ city, founded, hub IATA, alliance, cargo-only, AOC number, web slug
AIRLINE_EXT = {
    "MC": ("MDC", "MERIDIAN", "Memphis", 1998, "MEM", "SkyFreight Alliance", 1, "US-MDCA-0412", "meridianaircargo"),
    "BF": ("BSF", "BOSPHORUS", "Istanbul", 2006, "IST", None, 0, "TR-AOC-0887", "bosphorusfreight"),
    "SK": ("SLK", "SILKLINE", "Hong Kong", 2001, "HKG", "SkyFreight Alliance", 1, "HK-AOC-0156", "silklinecargo"),
    "EA": ("EAF", "EURASIA", "Leipzig", 1994, "LEJ", "CargoLink", 1, "DE-AOC-2271", "eurasiaairfreight"),
    "GC": ("GCC", "CRESCENT", "Dubai", 2009, "DXB", "CargoLink", 0, "AE-AOC-0093", "gulfcrescentcargo"),
}
airlines_x = []
for aid, code, name, country in AIRLINES:
    icao, cs, hq, yr, hub, alli, cargo_only, aoc, slug = AIRLINE_EXT[code]
    airlines_x.append((aid, code, icao, name, cs, country, hq, yr, ap_by_iata[hub]["id"], alli, cargo_only, aoc,
                       f"https://www.{slug}.example", f"ops@{slug}.example"))
airline_slug = {code: AIRLINE_EXT[code][8] for code in AIRLINE_EXT}

# --------------------------------------------------------------------------- aircraft types (extra attributes)
# icao designator, engines, engine model, cruise km/h, MTOW kg, OEW kg, fuel capacity kg, burn kg/h, main-deck positions, wingspan m
TYPE_EXT = {
    "747-8F": ("B748", 4, "GEnx-2B67", 908, 447700, 197000, 193000, 10500, 34, 68.4),
    "777F": ("B77L", 2, "GE90-110B1", 896, 347800, 144400, 145500, 7500, 27, 64.8),
    "767-300F": ("B763", 2, "CF6-80C2", 851, 186900, 86000, 73000, 5200, 24, 47.6),
    "A330-200F": ("A332", 2, "Trent 772B", 871, 233000, 109000, 110000, 5800, 23, 60.3),
    "737-800BCF": ("B738", 2, "CFM56-7B", 842, 79000, 43000, 20900, 2500, 11, 35.8),
}
for t in types.values():
    (t["icao"], t["engines"], t["engine_model"], t["cruise"], t["mtow"], t["oew"], t["fuel_cap"], t["burn"],
     t["md_pos"], t["span"]) = TYPE_EXT[t["model"]]

# --------------------------------------------------------------------------- aircraft (extra attributes)
REG_COUNTRY = {"MC": US, "BF": "Turkey", "SK": "Hong Kong", "EA": "Germany", "GC": "United Arab Emirates"}
LESSORS = ["Aerolease Partners", "Northwind Aviation Capital", "Skybridge Leasing", "Harborline Aircraft Finance"]
used_msn = set()
for a in aircraft:
    while True:
        msn = str(X.randint(30000, 66999))
        if msn not in used_msn:
            used_msn.add(msn)
            break
    a["msn"] = msn
    dyear = a["year"] + (1 if a["year"] <= 2023 and X.random() < 0.3 else 0)
    a["delivery"] = datetime(dyear, X.randint(1, 12), X.randint(1, 28))
    a["ownership"] = "leased" if X.random() < 0.4 else "owned"
    a["lessor"] = X.choice(LESSORS) if a["ownership"] == "leased" else None
    a["lease_end"] = datetime(X.randint(2026, 2034), X.randint(1, 12), 1) if a["ownership"] == "leased" else None
    years = max(0.5, (datetime(2025, 1, 1) - a["delivery"]).days / 365.25)
    a["hours"] = int(years * X.uniform(2600, 4600))
    a["cycles"] = int(a["hours"] / X.uniform(3.5, 7.5))
    a["heavy"] = None
    if years >= 5:
        a["heavy"] = a["delivery"] + timedelta(days=int(365 * X.uniform(4.5, min(years - 0.2, 10))))
        if a["heavy"] > datetime(2024, 12, 15):
            a["heavy"] = datetime(2024, X.randint(1, 11), X.randint(1, 28))

# --------------------------------------------------------------------------- customers (extra attributes)
CITIES = {
    US: [("Chicago", "60601"), ("Houston", "77002"), ("Seattle", "98101"), ("Atlanta", "30303"), ("Newark", "07102")],
    "Germany": [("Hamburg", "20095"), ("Munich", "80331"), ("Stuttgart", "70173"), ("Cologne", "50667")],
    "China": [("Shenzhen", "518000"), ("Shanghai", "200000"), ("Guangzhou", "510000")],
    "Turkey": [("Istanbul", "34000"), ("Izmir", "35000"), ("Bursa", "16000")],
    "United Arab Emirates": [("Dubai", "00000"), ("Abu Dhabi", "00000")],
    "South Korea": [("Seoul", "04524"), ("Busan", "48058")],
    "Japan": [("Osaka", "530-0001"), ("Nagoya", "450-0002")],
    "Singapore": [("Singapore", "018956")],
    "Netherlands": [("Rotterdam", "3011 AA"), ("Eindhoven", "5611 AA")],
    "Canada": [("Toronto", "M5H 2N2"), ("Vancouver", "V6B 1A1")],
    "Brazil": [("Sao Paulo", "01000-000"), ("Campinas", "13010-000")],
    "India": [("Mumbai", "400001"), ("Bengaluru", "560001")],
    "United Kingdom": [("Manchester", "M1 1AE"), ("Birmingham", "B1 1AA")],
}
PHONE_CC = {US: "1", "Canada": "1", "Germany": "49", "China": "86", "Turkey": "90", "United Arab Emirates": "971",
            "South Korea": "82", "Japan": "81", "Singapore": "65", "Netherlands": "31", "Brazil": "55", "India": "91",
            "United Kingdom": "44"}
SALES_REGION = {US: "north_america", "Canada": "north_america", "Brazil": "south_america", "Germany": "europe",
                "Netherlands": "europe", "United Kingdom": "europe", "Turkey": "europe",
                "United Arab Emirates": "middle_east", "China": "asia_pacific", "South Korea": "asia_pacific",
                "Japan": "asia_pacific", "Singapore": "asia_pacific", "India": "asia_pacific"}
STREETS = ["Harbor Road", "Industrial Avenue", "Commerce Street", "Logistics Park Way", "Station Road",
           "Airport Boulevard", "Market Lane", "Riverside Drive"]
FIRST = ["Alex", "Maria", "Kenji", "Fatima", "Lukas", "Elif", "Daniel", "Sofia", "Omar", "Hannah", "Wei", "Priya",
         "Mateo", "Aylin", "Jonas", "Chloe", "Yusuf", "Mina", "Noah", "Leila", "Carlos", "Ingrid", "Tariq", "Emma",
         "Hiro", "Zeynep", "Marco", "Nadia", "Ethan", "Seo-yeon", "Felix", "Amira", "Lucas", "Mei", "Arjun", "Clara",
         "Kerem", "Isabel", "Ravi", "Laura"]
LAST = ["Novak", "Tanaka", "Schmidt", "Yilmaz", "Haddad", "Chen", "Johnson", "Kaya", "Fischer", "Park", "Silva",
        "Rahman", "Weber", "Demir", "Kim", "Rossi", "Ahmed", "Muller", "Lopez", "Sato", "Ozturk", "Brennan", "Ito",
        "Kowalski", "Nguyen", "Andersen", "Celik", "Moreau", "Patel", "Larsen"]
CREDIT = {"freight_forwarder": (250, 1500), "manufacturer": (200, 1000), "retailer": (100, 600), "shipper": (50, 400)}


def slug(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


ship_count = {c["id"]: 0 for c in customers}
for s in ships:
    if s["status"] != "cancelled":
        ship_count[s["cust"]] += 1
ranked = sorted(customers, key=lambda c: (-ship_count[c["id"]], c["id"]))
for k, c in enumerate(ranked):                     # loyalty tier follows shipment volume
    frac = k / len(ranked)
    c["tier"] = "platinum" if frac < 0.10 else "gold" if frac < 0.30 else "silver" if frac < 0.60 else "bronze"
for c in customers:
    c["code"] = f"CUS-{c['id']:04d}"
    c["city"], c["zip"] = X.choice(CITIES[c["country"]])
    c["addr"] = f"{X.randint(1, 480)} {X.choice(STREETS)}"
    fn, ln = X.choice(FIRST), X.choice(LAST)
    c["contact"] = f"{fn} {ln}"
    c["email"] = f"{slug(fn)}.{slug(ln)}@{slug(c['name'])}.example"
    c["phone"] = f"+{PHONE_CC[c['country']]} {X.randint(100, 999)} {X.randint(1000, 9999)}"
    c["web"] = f"https://www.{slug(c['name'])}.example" if X.random() < 0.85 else None
    c["sales_region"] = SALES_REGION[c["country"]]
    lo, hi = CREDIT[c["type"]]
    c["credit"] = float(X.randint(lo, hi) * 1000)
    c["known"] = 1 if X.random() < 0.75 else 0
cust_by_id = {c["id"]: c for c in customers}

# --------------------------------------------------------------------------- warehouses
OPERATORS = ["SwiftHandle Ground Services", "Apron Partners", "CargoGate Handling", "BlueDock Logistics",
             "TerraPort Services"]
WH_AREA = {"general": (8000, 40000), "cold_chain": (2000, 9000), "dangerous_goods": (800, 3000), "express": (3000, 12000)}
RENT_M2 = {"north_america": (0.9, 1.4), "europe": (1.0, 1.6), "middle_east": (0.7, 1.1), "asia_pacific": (0.9, 1.8)}
warehouses = []
for a in airports:
    kinds = ["general"]
    if a["hub"]:
        kinds += ["cold_chain", "express"] + (["dangerous_goods"] if X.random() < 0.7 else [])
    else:
        kinds += ["cold_chain" if X.random() < 0.6 else "express"]
    for n, kind in enumerate(kinds, start=1):
        lo, hi = WH_AREA[kind]
        area = int(round(X.uniform(lo, hi), -2))
        rooms = (X.randint(3, 12) if kind == "cold_chain" else
                 (0 if X.random() < 0.6 else X.randint(1, 2)) if kind == "general" else
                 (1 if X.random() < 0.3 else 0) if kind == "express" else 0)
        mint = (float(X.choice([-25, -20])) if kind == "cold_chain" else 2.0) if rooms else None
        rlo, rhi = RENT_M2[a["region"]]
        warehouses.append(dict(
            id=len(warehouses) + 1, code=f"{a['iata']}-W{n}", ap=a["id"], operator=X.choice(OPERATORS), type=kind,
            area=area, cap=int(area * X.uniform(0.08, 0.15)), rooms=rooms, mint=mint,
            doors=max(2, area // 1000 + X.randint(0, 6)),
            dg=1 if kind == "dangerous_goods" or (kind == "general" and X.random() < 0.3) else 0,
            bonded=1 if n == 1 else (1 if X.random() < 0.45 else 0),
            sec="high" if kind in ("express", "dangerous_goods") or X.random() < 0.4 else "standard",
            h24=1 if a["hub"] or X.random() < 0.7 else 0, opened=X.randint(1985, 2023),
            rent=round(area * X.uniform(rlo, rhi), 2)))
wh_by_airport = {}
for w in warehouses:
    wh_by_airport.setdefault(w["ap"], []).append(w)


def handling_warehouse(ap_id, s):
    """Pick the warehouse that handles shipment s at airport ap_id (deterministic preference order)."""
    whs = wh_by_airport[ap_id]
    by_type = {w["type"]: w for w in whs}
    if s["temp"] and "cold_chain" in by_type:
        return by_type["cold_chain"]
    if s["dg"] and "dangerous_goods" in by_type:
        return by_type["dangerous_goods"]
    if s["service"] == "express" and "express" in by_type:
        return by_type["express"]
    return by_type["general"]


def bonded_warehouse(ap_id, handling):
    if handling["bonded"]:
        return handling
    return next(w for w in wh_by_airport[ap_id] if w["bonded"])

# --------------------------------------------------------------------------- shipments (extra attributes)
AWB_PREFIX = {"MC": "901", "BF": "902", "SK": "903", "EA": "904", "GC": "905"}
CONS_PREFIX = ["Alder", "Bluefin", "Cedar", "Delta Point", "Elmstone", "Fairway", "Glacier", "Highland", "Indigo",
               "Jasper", "Kestrel", "Larkspur", "Maple Ridge", "Nimbus", "Oakmont", "Pacifica", "Quill", "Riverside",
               "Sable", "Thornbury"]
CONS_SUFFIX = ["Distribution", "Retail", "Medical", "Foods", "Components", "Wholesale", "Imports", "Assembly"]
DG_RULES = {"electronics": (0.15, ["9"]), "automotive_parts": (0.12, ["3", "9"]), "machinery": (0.08, ["8", "9"]),
            "pharmaceuticals": (0.08, ["2.2", "9"])}
DELIVERY_DAYS = {"express": (2, 4), "standard": (4, 7), "economy": (6, 12)}
used_awb = set()
for s in ships:
    code = airline_code_by_id[ac_by_id[s["legs"][0]["ac"]]["airline_id"]] if s["legs"] else X.choice(list(AWB_PREFIX))
    while True:
        serial = X.randint(1000000, 9999999)
        awb = f"{AWB_PREFIX[code]}-{serial:07d}{serial % 7}"          # last digit = serial mod 7 (IATA check digit)
        if awb not in used_awb:
            used_awb.add(awb)
            break
    s["awb"], s["carrier"] = awb, code
    s["ref"] = f"PO-{X.randint(10000, 99999)}" if X.random() < 0.7 else None
    s["consignee"] = f"{X.choice(CONS_PREFIX)} {X.choice(CONS_SUFFIX)}"
    lo, hi = DELIVERY_DAYS[s["service"]]
    s["req_date"] = as_date(s["booking"]) + timedelta(days=X.randint(lo, hi))
    s["chargeable"] = max(s["weight"], math.floor(s["volume"] * 167 * 10 + 0.5) / 10)   # half-up, like SQLite round()
    p, classes = DG_RULES.get(s["comm"], (0, None))
    s["dg"] = 1 if X.random() < p else 0
    s["dg_class"] = X.choice(classes) if s["dg"] else None
    s["temp"] = 1 if s["comm"] in ("pharmaceuticals", "perishables") else 0
    s["tmin"] = s["tmax"] = None
    if s["comm"] == "pharmaceuticals":
        s["tmin"], s["tmax"] = (2.0, 8.0) if X.random() < 0.7 else (15.0, 25.0)
    elif s["comm"] == "perishables":
        s["tmin"], s["tmax"] = xw([(0.0, 4.0), (-25.0, -18.0), (10.0, 14.0)], [0.6, 0.25, 0.15])

# --------------------------------------------------------------------------- flights (extra attributes)
DELAY_CODES = ["31", "41", "63", "71", "81", "89", "93"]
BAD_WX = ["snow", "fog", "thunderstorm"]
for f in flights:
    f["ftype"] = "charter" if X.random() < 0.12 else "scheduled"
    f["dstand"] = f"{X.choice('CFK')}{X.randint(1, 60)}"
    f["astand"] = f"{X.choice('CFK')}{X.randint(1, 60)}"
    f["alt"] = X.randrange(28000, 36000, 1000) if f["dist"] < 1500 else X.randrange(31000, 42000, 1000)
    f["wx"] = f["cxl"] = f["delay_code"] = f["tow"] = None
    if f["status"] == "cancelled":
        f["cxl"] = xw(["weather", "technical", "crew", "commercial", "atc"], [0.35, 0.3, 0.1, 0.15, 0.1])
        f["wx"] = X.choice(BAD_WX) if f["cxl"] == "weather" else xw(["clear", "cloudy", "rain"], [0.5, 0.35, 0.15])
    elif f["status"] == "completed":
        f["wx"] = xw(["clear", "cloudy", "rain", "snow", "fog", "thunderstorm"], [0.45, 0.30, 0.15, 0.04, 0.04, 0.02])
        if f["adep"] - f["sdep"] > timedelta(minutes=15):
            f["delay_code"] = "71" if f["wx"] in BAD_WX and X.random() < 0.7 else X.choice(DELAY_CODES)

# --------------------------------------------------------------------------- flight_cargo (ULD loading)
cargo_by_flight = {}
for c in cargo:
    cargo_by_flight.setdefault(c["flight"], []).append(c)
ship_uld = {}
for s in ships:
    if not s["legs"]:
        continue
    if s["comm"] == "documents" or s["weight"] < 60:
        kind = "BULK"
    elif s["volume"] < 3.5 and s["weight"] < 1500:
        kind = "RKN" if s["temp"] else "AKE"
    else:
        kind = "PMC" if X.random() < 0.7 else "PAG"
    num = None if kind == "BULK" else f"{kind}{X.randint(10000, 99999)}{s['carrier']}"
    seal = (f"SL{X.randint(100000, 999999)}" if kind != "BULK" and s["comm"] in ("electronics", "pharmaceuticals")
            and s["value"] > 50000 else None)
    ship_uld[s["id"]] = (kind, num, seal)
for fid, rows in cargo_by_flight.items():
    f = fl_by_id[fid]
    md_free = types[f["type_id"]]["md_pos"]
    main_n = lower_n = 0
    for seq, c in enumerate(sorted(rows, key=lambda r: r["id"]), start=1):
        kind, num, seal = ship_uld[c["ship"]]
        if kind in ("PMC", "PAG") and main_n >= md_free:          # main deck full -> loose-loaded in the bulk hold
            kind, num, seal = "BULK", None, None
        if kind in ("PMC", "PAG"):
            main_n += 1
            deck, pos = "main", f"MD{main_n:02d}"
        elif kind == "BULK":
            deck, pos = "lower", "BLK"
        else:
            lower_n += 1
            deck, pos = "lower", f"LD{lower_n:02d}"
        c.update(uld_type=kind, uld_number=num, seal=seal, deck=deck, pos=pos, seq=seq,
                 loaded=(f["adep"] - timedelta(minutes=X.randint(45, 240))) if c["status"] == "flown" else None)
cargo_kg = {fid: sum(c["s"]["weight"] for c in rows) for fid, rows in cargo_by_flight.items()}

# --------------------------------------------------------------------------- fuel uplifts + take-off weight (completed flights)
FUEL_PRICE = {"north_america": 0.68, "europe": 0.78, "middle_east": 0.62, "asia_pacific": 0.74}
SUPPLIERS = ["Skyline Fuels", "AeroPetro Services", "Horizon Aviation Fuels", "BlueJet Supply", "Northstar Aviation Energy"]
ap_suppliers = {a["id"]: X.sample(SUPPLIERS, 2) for a in airports}
fuel = []
for f in flights:
    if f["status"] != "completed":
        continue
    t, org = types[f["type_id"]], ap_by_id[f["org"]]
    block_h = (f["aarr"] - f["adep"]).total_seconds() / 3600
    trip = block_h * t["burn"] * X.uniform(0.93, 1.05)
    load = cargo_kg.get(f["id"], 0.0)
    uplift = int(min(trip * 1.05 + 0.75 * t["burn"], t["fuel_cap"], t["mtow"] - t["oew"] - load - 1))
    burned = int(min(trip, uplift * 0.97))
    density = round(X.uniform(0.785, 0.825), 3)
    litres = int(round(uplift / density))
    month = f["adep"].month
    price = round(FUEL_PRICE[org["region"]] * (1 + 0.06 * math.sin(month / 2.0)) * X.uniform(0.97, 1.03), 4)
    if org["country"] in ("Germany", "Netherlands"):
        saf = 2.0 if X.random() < 0.7 else round(X.uniform(2.0, 6.0), 1)
    else:
        saf = 0.0 if X.random() < 0.9 else round(X.uniform(0.5, 5.0), 1)
    fuel.append(dict(id=len(fuel) + 1, ticket=f"FT-{org['iata']}-{len(fuel) + 1:06d}", flight=f["id"], ap=org["id"],
                     supplier=X.choice(ap_suppliers[org["id"]]), ftype="Jet A" if org["country"] == US else "Jet A-1",
                     method=("hydrant" if X.random() < 0.85 else "truck") if org["hub"] else
                            ("truck" if X.random() < 0.7 else "hydrant"),
                     time=f["adep"] - timedelta(minutes=X.randint(35, 100)), kg=uplift, litres=litres,
                     density=density, price=price, cost=round(litres * price, 2), saf=saf, burned=burned,
                     co2=int(round(burned * 3.16))))
    f["tow"] = int(round(t["oew"] + load + uplift))

# --------------------------------------------------------------------------- crew members
crew = []
pools = {}                     # (airline_id, type_id, rank) -> [crew dicts]
lm_pools = {}                  # airline_id -> [loadmasters]
fleet_groups = {}
for a in aircraft:
    g = fleet_groups.setdefault((a["airline_id"], a["type_id"]), [0, 0])
    g[0 if a["status"] == "active" else 1] += 1
used_emp, used_lic = set(), set()


def new_crew(airline_id, rank, type_id):
    code = airline_code_by_id[airline_id]
    while True:
        emp = f"{code}-{X.randint(10000, 99999)}"
        if emp not in used_emp:
            used_emp.add(emp)
            break
    fn, ln = X.choice(FIRST), X.choice(LAST)
    cm = dict(id=len(crew) + 1, emp=emp, first=fn, last=ln, airline=airline_id,
              base=ap_by_iata[X.choice(HOMES[code])]["id"], rank=rank, type_id=type_id,
              hire=datetime(2005, 1, 1) + timedelta(days=X.randint(0, 7300)), active=1 if X.random() < 0.94 else 0,
              next_free=datetime(2000, 1, 1), last_release=None)
    cm["email"] = f"{slug(fn)}.{slug(ln)}.{cm['id']}@{airline_slug[code]}.example"
    if rank == "loadmaster":
        cm["lic"] = cm["lic_exp"] = cm["med_exp"] = None
        cm["hours"] = X.randint(1000, 12000)
    else:
        while True:
            lic = f"{REG_COUNTRY[code][:2].upper()}-{'ATPL' if rank == 'captain' else 'CPL'}-{X.randint(100000, 999999)}"
            if lic not in used_lic:
                used_lic.add(lic)
                break
        cm["lic"] = lic
        cm["lic_exp"] = (datetime(2025, X.randint(6, 11), X.randint(1, 28)) if X.random() < 0.05 else
                         datetime(X.randint(2026, 2028), X.randint(1, 12), X.randint(1, 28)))
        cm["med_exp"] = datetime(2026, X.randint(1, 12), X.randint(1, 28))
        cm["hours"] = X.randint(8000, 22000) if rank == "captain" else X.randint(1500, 9000)
    crew.append(cm)
    return cm


for (airline_id, type_id), (n_active, n_other) in sorted(fleet_groups.items()):
    n_cpt = 4 * n_active + 1 if n_active else 2
    n_fo = 5 * n_active + 1 if n_active else 2
    pools[(airline_id, type_id, "captain")] = [new_crew(airline_id, "captain", type_id) for _ in range(n_cpt)]
    pools[(airline_id, type_id, "first_officer")] = [new_crew(airline_id, "first_officer", type_id) for _ in range(n_fo)]
for airline_id, *_ in AIRLINES:
    n_ac = sum(1 for a in aircraft if a["airline_id"] == airline_id)
    lm_pools[airline_id] = [new_crew(airline_id, "loadmaster", None) for _ in range(3 + n_ac // 3)]
for airline_id, *_ in AIRLINES:                     # seniority = hire order within the airline
    for k, cm in enumerate(sorted((c for c in crew if c["airline"] == airline_id), key=lambda c: (c["hire"], c["id"])), 1):
        cm["seniority"] = k

# --------------------------------------------------------------------------- crew assignments
MIN_REST = timedelta(hours=12)
assignments = []


def pick(pool, report, dep_day):
    ok = [c for c in pool if c["active"] and c["next_free"] <= report and (c["lic_exp"] is None or c["lic_exp"] >= dep_day)]
    return X.choice(ok) if ok else None


for f in sorted((f for f in flights if f["status"] != "cancelled"), key=lambda f: (f["sdep"], f["id"])):
    ac = ac_by_id[f["ac"]]
    report = f["sdep"] - timedelta(minutes=90)
    release = (f["aarr"] if f["status"] == "completed" else f["sarr"]) + timedelta(minutes=30)
    dep_day = datetime(f["sdep"].year, f["sdep"].month, f["sdep"].day)
    roles = [("captain", pools[(ac["airline_id"], ac["type_id"], "captain")]),
             ("first_officer", pools[(ac["airline_id"], ac["type_id"], "first_officer")])]
    if f["sarr"] - f["sdep"] > timedelta(hours=9):
        roles.append(("relief_pilot", pools[(ac["airline_id"], ac["type_id"], "first_officer")]))
    if X.random() < 0.4:
        roles.append(("loadmaster", lm_pools[ac["airline_id"]]))
    pf = X.choice(["captain", "first_officer"])
    for role, pool in roles:
        cm = pick(pool, report, dep_day)
        if cm is None:
            assert role == "loadmaster", f"no {role} available for flight {f['id']}"
            continue
        rest = int((report - cm["last_release"]).total_seconds() // 60) if cm["last_release"] else None
        hotel = 1 if f["dst"] != cm["base"] else 0
        duty_h = (release - report).total_seconds() / 3600
        assignments.append(dict(
            id=len(assignments) + 1, flight=f["id"], crew=cm["id"], role=role, pf=1 if role == pf else 0,
            report=report, release=release,
            block=int((f["aarr"] - f["adep"]).total_seconds() // 60) if f["status"] == "completed" else None,
            rest=rest, per_diem=round(3.5 * duty_h + (45.0 if hotel else 0.0), 2), hotel=hotel,
            status="completed" if f["status"] == "completed" else "rostered"))
        cm["next_free"], cm["last_release"] = release + MIN_REST, release

# --------------------------------------------------------------------------- maintenance records
MRO = {"north_america": ["Hangar Nine Services", "AeroFix MRO"], "europe": ["Elbe Aero Technics", "AeroFix MRO"],
       "middle_east": ["Gulf Aero Engineering", "Desert Wing MRO"], "asia_pacific": ["Pacific Wing Maintenance", "Harbour Aero Works"]}
OWN_MRO = {"MC": "Meridian Technics", "BF": "Bosphorus Technic", "SK": "Silkline Engineering", "EA": "Eurasia Technik",
           "GC": "Crescent Engineering"}
ATA = [21, 24, 27, 29, 32, 36, 49, 52, 71, 72, 73, 79]
LABOR_RATE = {"north_america": 95, "europe": 105, "middle_east": 70, "asia_pacific": 80}
PARTS = {"line": (200, 3000), "A_check": (5000, 40000), "B_check": (20000, 120000), "unscheduled": (1500, 250000)}
TECHS = {"line": (2, 4), "A_check": (6, 12), "B_check": (10, 18), "unscheduled": (3, 8), "C_check": (25, 40)}
DEFERRED = {"line": 2, "A_check": 5, "B_check": 8, "unscheduled": 1, "C_check": 12}
maint = []


def add_maint(ac, ap_id, kind, start, end):
    reg = ap_by_id[ap_id]["region"]
    code = airline_code_by_id[ac["airline_id"]]
    status = "in_progress" if end is None else "completed" if end <= AS_OF else "planned" if start >= AS_OF else "in_progress"
    if status == "in_progress":
        end = None
    m = dict(id=len(maint) + 1, ac=ac["id"], ap=ap_id, kind=kind, start=start, end=end, status=status,
             ata=X.choice(ATA) if kind == "unscheduled" else None,
             mro=OWN_MRO[code] if kind in ("line", "unscheduled") and X.random() < 0.6 else X.choice(MRO[reg]),
             aog=1 if kind == "unscheduled" and X.random() < 0.8 else 0,
             hours=None, parts=None, labor=None, deferred=0, due=None)
    if status == "completed":
        dur_h = (end - start).total_seconds() / 3600
        m["hours"] = round(dur_h * X.randint(*TECHS[kind]) * X.uniform(0.7, 0.95), 1)
        m["labor"] = round(m["hours"] * LABOR_RATE[reg] * X.uniform(0.9, 1.1), 2)
        lo, hi = PARTS[kind]
        m["parts"] = round(xlog_uniform(lo, hi) if kind == "unscheduled" else X.uniform(lo, hi), 2)
        m["deferred"] = X.randint(0, DEFERRED[kind])
    if kind in ("A_check", "B_check") and end is not None:
        m["due"] = end + timedelta(days=90 if kind == "A_check" else 240)
    maint.append(m)


for ac in aircraft:
    if ac["status"] != "active":
        continue
    seq = sorted((f for f in flights if f["ac"] == ac["id"] and f["status"] != "cancelled"), key=lambda f: f["sdep"])
    for prev, nxt in zip(seq, seq[1:]):
        arr = prev["aarr"] if prev["status"] == "completed" else prev["sarr"]
        gap_h = (nxt["sdep"] - arr).total_seconds() / 3600
        start = r5(arr + timedelta(minutes=X.randint(120, 300)))
        latest_end = nxt["sdep"] - timedelta(hours=3)
        r = X.random()
        if gap_h >= 30 and r < 0.18:
            if gap_h >= 60 and X.random() < 0.15:
                kind, dur = "B_check", X.randint(30, 48)
            elif gap_h >= 40 and X.random() < 0.45:
                kind, dur = "A_check", X.randint(14, 26)
            else:
                kind, dur = "line", X.randint(3, 8)
        elif gap_h >= 12 and r < 0.215:
            kind, dur = "unscheduled", X.randint(4, 18)
        else:
            continue
        end = start + timedelta(hours=dur, minutes=X.choice([0, 15, 30, 45]))
        if end <= latest_end:
            add_maint(ac, prev["dst"], kind, start, end)
for ac in aircraft:                                  # the grounded aircraft is in a heavy check right now
    if ac["status"] == "maintenance":
        add_maint(ac, ac["home"], "C_check", datetime(2025, 11, 3, 8, 0), None)
maint.sort(key=lambda m: (m["start"], m["ac"]))
for k, m in enumerate(maint, start=1):
    m["id"] = k
    m["wo"] = f"WO-{m['start'].year}-{k:05d}"

# --------------------------------------------------------------------------- invoices + payments (extra attributes)
for inv in invoices:
    s = ship_by_id[inv["ship"]]
    a = inv["amount"]
    inv["number"] = f"INV-{inv['issued'].year}-{inv['id']:06d}"
    inv["terms"] = cust_by_id[s["cust"]]["terms"]
    inv["fuel"] = round(a * X.uniform(0.12, 0.18), 2)
    inv["security"] = round(min(max(10.0, s["weight"] * 0.11), a * 0.12), 2)
    inv["handling"] = round(min(max(20.0, s["weight"] * 0.07), a * 0.12), 2)
    inv["dg"] = round(a * 0.08, 2) if s["dg"] else 0.0
    inv["discount"] = round(a * X.uniform(0.02, 0.06), 2) if cust_by_id[s["cust"]]["tier"] in ("gold", "platinum") else 0.0
    inv["freight"] = round(a - inv["fuel"] - inv["security"] - inv["handling"] - inv["dg"] + inv["discount"], 2)
    inv["sent_via"] = xw(["email", "portal", "edi"], [0.5, 0.3, 0.2])

CURRENCY = {US: "USD", "Canada": "CAD", "Germany": "EUR", "Netherlands": "EUR", "China": "CNY", "Turkey": "TRY",
            "United Arab Emirates": "AED", "South Korea": "KRW", "Japan": "JPY", "Singapore": "SGD", "Brazil": "BRL",
            "India": "INR", "United Kingdom": "GBP"}
FX = {"USD": 1.0, "EUR": 1.08, "CAD": 0.73, "CNY": 0.139, "TRY": 0.029, "AED": 0.2723, "KRW": 0.00072,
      "JPY": 0.0066, "SGD": 0.74, "BRL": 0.18, "INR": 0.0118, "GBP": 1.27}


def fx_rate(cur, d):
    if cur in ("USD", "AED"):                        # AED is pegged
        return FX[cur]
    if cur == "TRY":
        return round(0.031 - 0.0004 * d.month, 8)
    return round(FX[cur] * (1 + 0.02 * math.sin(d.month + len(cur) * 7)), 8)


for p in payments:
    cust = cust_by_id[p["cust"]]
    cur = CURRENCY[cust["country"]] if p["method"] != "credit_card" and X.random() < 0.65 else "USD"
    rate = fx_rate(cur, p["date"])
    p["ref"] = f"PAY-{p['date'].strftime('%Y%m%d')}-{p['id']:05d}"
    p["cur"], p["rate"], p["orig"] = cur, rate, round(p["amount"] / rate, 2)
    p["bank"] = (round(X.uniform(15, 45), 2) if p["method"] == "wire_transfer" else
                 round(X.uniform(0, 1.5), 2) if p["method"] == "ach" else round(p["amount"] * 0.025, 2))
    recent = (AS_OF.date() - p["date"]).days < 5
    p["reconciled"] = (0 if X.random() < 0.7 else 1) if recent else (1 if X.random() < 0.97 else 0)

# --------------------------------------------------------------------------- customs declarations
EU = ("Germany", "Netherlands")
HS = {"electronics": [("847130", "portable computers"), ("851762", "network equipment"), ("854231", "integrated circuits")],
      "pharmaceuticals": [("300490", "packaged medicaments"), ("300215", "immunological products")],
      "perishables": [("030214", "fresh salmon"), ("060311", "fresh cut roses"), ("080510", "fresh oranges")],
      "automotive_parts": [("870899", "motor vehicle parts"), ("840991", "engine parts")],
      "apparel": [("610910", "cotton t-shirts"), ("620342", "cotton trousers")],
      "machinery": [("842959", "excavating machinery"), ("848180", "industrial valves")],
      "documents": [("490199", "printed documents")]}
DUTY = {"electronics": (0.0, 2.5), "pharmaceuticals": (0.0, 0.0), "perishables": (4.0, 12.0),
        "automotive_parts": (2.5, 4.5), "apparel": (8.0, 16.0), "machinery": (1.5, 4.0), "documents": (0.0, 0.0)}
VAT = {US: 0, "Germany": 19, "Netherlands": 21, "Turkey": 20, "United Arab Emirates": 5, "Qatar": 0, "Hong Kong": 0,
       "China": 13, "South Korea": 10, "Japan": 10, "Singapore": 9}
BROKERS = ["Customs Bridge Brokers", "Clearway Customs", "Borderline Trade Services", "TariffPro Agents", "Gateway Clearance"]


def territory(country):
    return "EU" if country in EU else country


def duty_rate(country, comm):
    lo, hi = DUTY[comm]
    if hi == 0 or country in ("Hong Kong", "Singapore"):
        return 0.0
    if country in ("United Arab Emirates", "Qatar"):
        return 5.0
    return round(X.uniform(lo, hi), 1)


customs = []
import_cleared = {}


def add_decl(s, kind, ap_id, wh, submitted, cleared, status, insp, result, rate):
    country = ap_by_id[ap_id]["country"]
    value = s["value"]
    duty = round(value * rate / 100, 2) if kind == "import" else 0.0
    vat = round((value + duty) * VAT[country] / 100, 2) if kind == "import" else 0.0
    customs.append(dict(id=len(customs) + 1, ship=s["id"], wh=wh["id"], kind=kind, country=country, hs=s["hs"][0],
                        desc=s["hs"][1], value=value, rate=rate if kind == "import" else 0.0, duty=duty, vat=vat,
                        broker=X.choice(BROKERS), insp=insp, result=result, submitted=submitted, cleared=cleared,
                        status=status, iata=ap_by_id[ap_id]["iata"]))


for s in ships:
    s["hs"] = X.choice(HS[s["comm"]])
    if not s["legs"]:
        continue
    o_c, d_c = ap_by_id[s["org"]]["country"], ap_by_id[s["dst"]]["country"]
    if territory(o_c) == territory(d_c):
        continue                                      # domestic / intra-EU: no customs
    leg1 = s["legs"][0]
    dep_time = leg1["adep"] if leg1["status"] == "completed" else leg1["sdep"]
    submitted = r5(dep_time - timedelta(hours=X.randint(8, 48)))
    submitted = max(submitted, as_date(s["booking"]) + timedelta(hours=8, minutes=X.randint(0, 120)))
    if submitted < AS_OF:
        wh = bonded_warehouse(s["org"], handling_warehouse(s["org"], s))
        insp = 1 if X.random() < 0.08 else 0
        if leg1["status"] == "completed":
            cleared = min(submitted + timedelta(minutes=X.randint(30, 600)), dep_time - timedelta(minutes=45))
            if cleared <= submitted:
                submitted = cleared - timedelta(minutes=60)
            add_decl(s, "export", s["org"], wh, submitted, cleared, "cleared", insp, "passed" if insp else None, 0.0)
        else:
            cleared = submitted + timedelta(minutes=X.randint(30, 900))
            if insp and X.random() < 0.5 and cleared <= AS_OF:
                add_decl(s, "export", s["org"], wh, submitted, None, "held", 1, "discrepancy", 0.0)
            elif cleared <= AS_OF:
                add_decl(s, "export", s["org"], wh, submitted, cleared, "cleared", insp, "passed" if insp else None, 0.0)
            else:
                add_decl(s, "export", s["org"], wh, submitted, None, "pending", insp, None, 0.0)
    if s["status"] == "delivered":
        arr = s["legs"][-1]["aarr"]
        submitted = arr + timedelta(minutes=X.randint(15, 60))
        if submitted >= AS_OF:
            import_cleared[s["id"]] = None           # import not lodged yet -> consignee cannot be notified
            continue
        insp = 1 if X.random() < 0.10 else 0
        cleared = submitted + timedelta(minutes=X.randint(20, 180) + (X.randint(60, 120) if insp else 0))
        wh = bonded_warehouse(s["dst"], handling_warehouse(s["dst"], s))
        rate = duty_rate(d_c, s["comm"])
        if insp and X.random() < 0.25:                # inspection found a discrepancy: goods held, no delivery
            add_decl(s, "import", s["dst"], wh, submitted, None, "held", 1, "discrepancy", rate)
            import_cleared[s["id"]] = None
        elif cleared <= AS_OF:
            add_decl(s, "import", s["dst"], wh, submitted, cleared, "cleared", insp, "passed" if insp else None, rate)
            import_cleared[s["id"]] = cleared
        else:
            add_decl(s, "import", s["dst"], wh, submitted, None, "pending", insp, None, rate)
            import_cleared[s["id"]] = None
for d in customs:
    d["number"] = f"{'EX' if d['kind'] == 'export' else 'IM'}-{d['iata']}-{d['id']:06d}"

# --------------------------------------------------------------------------- incidents (extra attributes)
ROOT = {"damage": (["handling", "packaging"], [0.6, 0.4]), "delay": (["weather", "equipment", "handling"], [0.4, 0.3, 0.3]),
        "missing_documents": (["documentation"], [1]), "temperature_excursion": (["equipment", "handling"], [0.6, 0.4]),
        "loss": (["handling", "unknown"], [0.5, 0.5])}
REPORTER = {"damage": (["ground_handler", "customer"], [0.6, 0.4]), "delay": (["ground_handler", "customer"], [0.5, 0.5]),
            "missing_documents": (["customs", "ground_handler"], [0.6, 0.4]),
            "temperature_excursion": (["ground_handler", "crew"], [0.7, 0.3]), "loss": (["customer", "ground_handler"], [0.6, 0.4])}
ACTION = {"damage": ["repacked", "compensated"], "delay": ["rerouted", "no_action"], "missing_documents": ["documents_supplied"],
          "temperature_excursion": ["compensated", "no_action"], "loss": ["compensated"]}
cargo_by_id = {c["id"]: c for c in cargo}
excursion_legs = set()
for i in incidents:
    c = cargo_by_id[i["cargo"]]
    s, f = c["s"], c["f"]
    i["ap"] = f["dst"]
    i["wh"] = handling_warehouse(f["dst"], s)["id"] if X.random() < 0.7 else None
    i["root"] = xw(*ROOT[i["type"]])
    i["by"] = xw(*REPORTER[i["type"]])
    i["pieces"] = (X.randint(1, min(s["pieces"], 5)) if i["type"] == "damage" else X.randint(1, s["pieces"])
                   if i["type"] == "loss" else s["pieces"] if i["type"] == "temperature_excursion" else None)
    i["delay"] = X.randint(90, 2880) if i["type"] == "delay" else None
    i["action"] = i["resolved_at"] = None
    if i["resolved"]:
        rep = datetime.strptime(i["at"], TS)
        i["resolved_at"] = rep + timedelta(days=X.randint(1, (AS_OF - rep).days - 1), hours=X.randint(0, 20))
        i["action"] = X.choice(ACTION[i["type"]])
    if i["type"] == "temperature_excursion":
        excursion_legs.add(c["id"])

# --------------------------------------------------------------------------- insurance claims
INSURERS = ["Atlas Marine & Cargo", "Beacon Transit Insurance", "Cirrus Underwriters"]
REJECT = ["inadequate_packaging", "late_notification", "excluded_cause", "insufficient_documentation"]
policy = {}
for c in customers:
    ins = X.choice(INSURERS)
    policy[c["id"]] = dict(insurer=ins, number=f"POL-{c['id']:04d}-{ins[:3].upper()}",
                           coverage="all_risk" if X.random() < 0.7 else "named_perils",
                           deductible=float(X.choice([500, 1000, 2500])))
claims = []
for i in incidents:
    if i["claim"] is None:
        continue
    s = cargo_by_id[i["cargo"]]["s"]
    filed = datetime.strptime(i["at"][:10], DS) + timedelta(days=X.randint(1, 10))
    if filed > AS_OF:
        continue                                      # claim not yet filed
    pol = policy[s["cust"]]
    age = (AS_OF - filed).days
    status, decision, settle, approved, reason = "filed", None, None, None, None
    if 7 <= age < 40:
        status = "under_review"
    elif age >= 40:
        decision = filed + timedelta(days=X.randint(10, min(age, 75)))
        if X.random() < (0.30 if pol["coverage"] == "named_perils" else 0.12):
            status, reason = "rejected", X.choice(REJECT)
        else:
            approved = round(max(0.0, i["claim"] - pol["deductible"]) * X.uniform(0.7, 1.0), 2)
            settle = decision + timedelta(days=X.randint(5, 30))
            status = "paid" if settle <= AS_OF else "approved"
            if status == "approved":
                settle = None
    claims.append(dict(id=len(claims) + 1, number=f"CLM-2025-{len(claims) + 1:05d}", inc=i["id"], cust=s["cust"],
                       policy=pol["number"], insurer=pol["insurer"], coverage=pol["coverage"], filed=filed,
                       claimed=i["claim"], deductible=pol["deductible"], approved=approved, status=status,
                       decision=decision, reason=reason, settle=settle,
                       adjuster=f"{X.choice(FIRST)} {X.choice(LAST)}"))

# --------------------------------------------------------------------------- tracking events
events = []


def scanner(ap_id):
    return f"SCN-{ap_by_id[ap_id]['iata']}-{X.randint(100, 999)}"


def reading(s, out_of_range=False):
    if not s["temp"]:
        return None
    if out_of_range:
        return round(s["tmax"] + X.uniform(1.5, 6.0), 1)
    return round(X.uniform(s["tmin"] + 0.3, s["tmax"] - 0.3), 1)


def ev(s, code, time, ap, flight=None, wh=None, by="system", weight=None, temp=None):
    if time > AS_OF:
        return False
    events.append(dict(ship=s["id"], flight=flight, ap=ap, wh=wh, code=code, time=time, pieces=s["pieces"],
                       weight=weight, temp=temp, by=by, scanner=scanner(ap) if by == "ground_handler" else None))
    return True


leg_cargo = {(c["ship"], c["leg"]): c for c in cargo}
for s in ships:
    booking0 = as_date(s["booking"])
    bkd = booking0 + timedelta(minutes=X.randint(360, 1200))
    if s["legs"]:
        leg1 = s["legs"][0]
        dep1 = leg1["adep"] if leg1["status"] == "completed" else leg1["sdep"]
        bkd = min(bkd, dep1 - timedelta(minutes=360))
    bkd = min(bkd, AS_OF)
    ev(s, "BKD", bkd, s["org"], by=xw(["customer_portal", "system"], [0.6, 0.4]))
    if not s["legs"]:
        ev(s, "CAN", min(bkd + timedelta(minutes=X.randint(60, 5760)), AS_OF), s["org"],
           by=xw(["customer_portal", "system"], [0.6, 0.4]))
        continue
    wh_o = handling_warehouse(s["org"], s)
    lo = bkd + timedelta(minutes=30)
    hi = dep1 - timedelta(minutes=250)
    rcs = lo + timedelta(minutes=X.randint(0, max(0, int((hi - lo).total_seconds() // 60))))
    ev(s, "RCS", min(rcs, hi), s["org"], wh=wh_o["id"], by="ground_handler",
       weight=round(s["weight"] * X.uniform(0.99, 1.01), 1), temp=reading(s))
    for n, f in enumerate(s["legs"], start=1):
        if f["status"] != "completed":
            break
        ev(s, "DEP", f["adep"], f["org"], flight=f["id"])
        ev(s, "ARR", f["aarr"], f["dst"], flight=f["id"],
           temp=reading(s, out_of_range=leg_cargo[(s["id"], n)]["id"] in excursion_legs))
    if s["status"] == "delivered":
        arr = s["legs"][-1]["aarr"]
        wh_d = handling_warehouse(s["dst"], s)
        rcf = arr + timedelta(minutes=X.randint(45, 150))
        if not ev(s, "RCF", rcf, s["dst"], wh=wh_d["id"], by="ground_handler", temp=reading(s)):
            continue
        if s["id"] in import_cleared and import_cleared[s["id"]] is None:
            continue                                  # still waiting for import clearance
        nfd = max(rcf, import_cleared.get(s["id"]) or rcf) + timedelta(minutes=X.randint(10, 60))
        if not ev(s, "NFD", nfd, s["dst"], wh=wh_d["id"], by="ground_handler"):
            continue
        ev(s, "DLV", nfd + timedelta(minutes=X.randint(30, 150)), s["dst"], wh=wh_d["id"], by="ground_handler",
           temp=reading(s))
for k, e in enumerate(events, start=1):
    e["id"] = k


# --------------------------------------------------------------------------- write SQL
def emit(out, table, cols, rows, chunk=250):
    rows = list(rows)
    for k in range(0, len(rows), chunk):
        part = rows[k:k + chunk]
        out.write(f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n")
        out.write(",\n".join("(" + ", ".join(sql_val(v) for v in r) + ")" for r in part))
        out.write(";\n")
    out.write("\n")


def main(path):
    with open(path, "w", encoding="utf-8", newline="\n") as out:
        out.write("-- Seed data for the Air Cargo Flights benchmark, NORMAL schema "
                  "(generated by data/generate_data.py, seed=%d)\n" % SEED)
        out.write("-- Do not edit by hand: regenerate instead.\nPRAGMA foreign_keys = ON;\nBEGIN;\n\n")
        emit(out, "benchmark_meta", ["meta_key", "meta_value"],
             [("as_of_timestamp", AS_OF.strftime(TS)), ("generator_seed", str(SEED)), ("engine", "SQLite 3.25+"),
              ("note", "All names are fictional; no real personal or confidential data."),
              ("schema_version", "2 (20 tables, 300 columns)")])
        emit(out, "airports", ["airport_id", "iata_code", "icao_code", "name", "city", "country", "region", "timezone",
                               "latitude", "longitude", "elevation_m", "runway_count", "longest_runway_m", "is_cargo_hub",
                               "annual_cargo_capacity_t", "has_24h_customs", "night_curfew"],
             [(a["id"], a["iata"], a["icao"], a["name"], a["city"], a["country"], a["region"], a["tz"], a["lat"], a["lon"],
               a["elev"], a["rwys"], a["rwy_len"], a["hub"], a["cap_t"], a["customs24"], a["curfew"]) for a in airports])
        emit(out, "airlines", ["airline_id", "iata_code", "icao_code", "name", "callsign", "country", "headquarters_city",
                               "founded_year", "home_hub_airport_id", "alliance", "is_cargo_only", "aoc_number", "website",
                               "contact_email"], airlines_x)
        emit(out, "aircraft_types", ["type_id", "model", "icao_type_designator", "manufacturer", "engine_count",
                                     "engine_model", "max_payload_kg", "max_volume_m3", "max_range_km", "cruise_speed_kmh",
                                     "max_takeoff_weight_kg", "operating_empty_weight_kg", "fuel_capacity_kg",
                                     "fuel_burn_kg_per_hour", "main_deck_positions", "wingspan_m"],
             [(t["id"], t["model"], t["icao"], t["mfr"], t["engines"], t["engine_model"], t["payload"], t["volume"],
               t["range"], t["cruise"], t["mtow"], t["oew"], t["fuel_cap"], t["burn"], t["md_pos"], t["span"])
              for t in types.values()])
        emit(out, "aircraft", ["aircraft_id", "tail_number", "serial_number", "type_id", "airline_id", "home_airport_id",
                               "registration_country", "year_manufactured", "delivery_date", "ownership", "lessor_name",
                               "lease_end_date", "total_flight_hours", "total_cycles", "last_heavy_check_date", "status"],
             [(a["id"], a["tail"], a["msn"], a["type_id"], a["airline_id"], a["home"], REG_COUNTRY[a["code"]], a["year"],
               ds(a["delivery"]), a["ownership"], a["lessor"], ds(a["lease_end"]), a["hours"], a["cycles"], ds(a["heavy"]),
               a["status"]) for a in aircraft])
        emit(out, "customers", ["customer_id", "account_code", "name", "customer_type", "country", "city", "address_line",
                                "postal_code", "contact_name", "contact_email", "contact_phone", "website", "sales_region",
                                "credit_limit_usd", "payment_terms_days", "is_known_shipper", "loyalty_tier",
                                "created_date"],
             [(c["id"], c["code"], c["name"], c["type"], c["country"], c["city"], c["addr"], c["zip"], c["contact"],
               c["email"], c["phone"], c["web"], c["sales_region"], c["credit"], c["terms"], c["known"], c["tier"],
               c["created"]) for c in customers])
        emit(out, "warehouses", ["warehouse_id", "warehouse_code", "airport_id", "operator_name", "warehouse_type",
                                 "floor_area_m2", "capacity_tonnes", "cold_room_count", "min_temperature_c",
                                 "dock_door_count", "has_dg_area", "is_bonded", "security_level", "operates_24h",
                                 "opened_year", "monthly_rent_usd"],
             [(w["id"], w["code"], w["ap"], w["operator"], w["type"], w["area"], w["cap"], w["rooms"], w["mint"],
               w["doors"], w["dg"], w["bonded"], w["sec"], w["h24"], w["opened"], w["rent"]) for w in warehouses])
        emit(out, "crew_members", ["crew_member_id", "employee_number", "first_name", "last_name", "email", "airline_id",
                                   "base_airport_id", "crew_rank", "type_rating_id", "license_number",
                                   "license_expiry_date", "medical_expiry_date", "hire_date", "seniority_number",
                                   "total_flight_hours", "is_active"],
             [(c["id"], c["emp"], c["first"], c["last"], c["email"], c["airline"], c["base"], c["rank"], c["type_id"],
               c["lic"], ds(c["lic_exp"]), ds(c["med_exp"]), ds(c["hire"]), c["seniority"], c["hours"], c["active"])
              for c in crew])
        emit(out, "flights", ["flight_id", "flight_number", "flight_type", "aircraft_id", "origin_airport_id",
                              "destination_airport_id", "scheduled_departure", "scheduled_arrival", "actual_departure",
                              "actual_arrival", "departure_stand", "arrival_stand", "distance_km",
                              "planned_cruise_altitude_ft", "takeoff_weight_kg", "weather_at_departure", "delay_code",
                              "cancellation_reason", "status"],
             [(f["id"], f["fn"], f["ftype"], f["ac"], f["org"], f["dst"], ts(f["sdep"]), ts(f["sarr"]), ts(f["adep"]),
               ts(f["aarr"]), f["dstand"], f["astand"], f["dist"], f["alt"], f["tow"], f["wx"], f["delay_code"], f["cxl"],
               f["status"]) for f in flights])
        emit(out, "crew_assignments", ["assignment_id", "flight_id", "crew_member_id", "duty_role", "is_pilot_flying",
                                       "report_time", "release_time", "block_minutes_credited", "rest_minutes_before",
                                       "per_diem_usd", "hotel_required", "assignment_status"],
             [(a["id"], a["flight"], a["crew"], a["role"], a["pf"], ts(a["report"]), ts(a["release"]), a["block"],
               a["rest"], a["per_diem"], a["hotel"], a["status"]) for a in assignments])
        emit(out, "maintenance_records", ["maintenance_id", "work_order_number", "aircraft_id", "airport_id", "check_type",
                                          "ata_chapter", "mro_provider", "start_time", "end_time", "labor_hours",
                                          "parts_cost_usd", "labor_cost_usd", "deferred_items_count", "is_aog",
                                          "next_due_date", "status"],
             [(m["id"], m["wo"], m["ac"], m["ap"], m["kind"], m["ata"], m["mro"], ts(m["start"]), ts(m["end"]), m["hours"],
               m["parts"], m["labor"], m["deferred"], m["aog"], ds(m["due"]), m["status"]) for m in maint])
        emit(out, "fuel_uplifts", ["fuel_uplift_id", "fuel_ticket_number", "flight_id", "airport_id", "supplier_name",
                                   "fuel_type", "delivery_method", "uplift_time", "quantity_kg", "quantity_litres",
                                   "density_kg_per_l", "price_usd_per_litre", "total_cost_usd", "saf_blend_pct",
                                   "fuel_burned_kg", "co2_emissions_kg"],
             [(u["id"], u["ticket"], u["flight"], u["ap"], u["supplier"], u["ftype"], u["method"], ts(u["time"]), u["kg"],
               u["litres"], u["density"], u["price"], u["cost"], u["saf"], u["burned"], u["co2"]) for u in fuel])
        emit(out, "shipments", ["shipment_id", "awb_number", "customer_id", "customer_reference", "consignee_name",
                                "origin_airport_id", "destination_airport_id", "booking_date", "requested_delivery_date",
                                "service_level", "commodity_category", "pieces", "total_weight_kg", "total_volume_m3",
                                "chargeable_weight_kg", "declared_value_usd", "is_dangerous_goods", "dg_class",
                                "is_temperature_controlled", "min_temperature_c", "max_temperature_c", "status"],
             [(s["id"], s["awb"], s["cust"], s["ref"], s["consignee"], s["org"], s["dst"], s["booking"], ds(s["req_date"]),
               s["service"], s["comm"], s["pieces"], s["weight"], s["volume"], s["chargeable"], s["value"], s["dg"],
               s["dg_class"], s["temp"], s["tmin"], s["tmax"], s["status"]) for s in ships])
        emit(out, "flight_cargo", ["flight_cargo_id", "shipment_id", "flight_id", "leg_number", "uld_type", "uld_number",
                                   "deck", "position_code", "load_sequence", "seal_number", "loaded_at", "leg_status"],
             [(c["id"], c["ship"], c["flight"], c["leg"], c["uld_type"], c["uld_number"], c["deck"], c["pos"], c["seq"],
               c["seal"], ts(c["loaded"]), c["status"]) for c in cargo])
        emit(out, "invoices", ["invoice_id", "invoice_number", "shipment_id", "issued_date", "due_date",
                               "payment_terms_days", "freight_charge_usd", "fuel_surcharge_usd", "security_fee_usd",
                               "handling_fee_usd", "dg_surcharge_usd", "discount_usd", "amount_usd", "sent_via", "status"],
             [(i["id"], i["number"], i["ship"], i["issued"].strftime(DS), i["due"].strftime(DS), i["terms"], i["freight"],
               i["fuel"], i["security"], i["handling"], i["dg"], i["discount"], i["amount"], i["sent_via"], i["status"])
              for i in invoices])
        emit(out, "payments", ["payment_id", "payment_reference", "invoice_id", "customer_id", "payment_date",
                               "amount_usd", "original_currency", "original_amount", "exchange_rate_to_usd", "method",
                               "bank_charges_usd", "is_reconciled"],
             [(p["id"], p["ref"], p["inv"], p["cust"], p["date"].strftime(DS), p["amount"], p["cur"], p["orig"], p["rate"],
               p["method"], p["bank"], p["reconciled"]) for p in payments])
        emit(out, "incidents", ["incident_id", "flight_cargo_id", "airport_id", "warehouse_id", "incident_type", "severity",
                                "root_cause", "reported_by", "reported_at", "pieces_affected", "delay_minutes",
                                "claim_amount_usd", "corrective_action", "resolved", "resolved_at"],
             [(i["id"], i["cargo"], i["ap"], i["wh"], i["type"], i["sev"], i["root"], i["by"], i["at"], i["pieces"],
               i["delay"], i["claim"], i["action"], i["resolved"], ts(i["resolved_at"])) for i in incidents])
        emit(out, "insurance_claims", ["claim_id", "claim_number", "incident_id", "customer_id", "policy_number",
                                       "insurer_name", "coverage_type", "filed_date", "claimed_amount_usd",
                                       "deductible_usd", "approved_amount_usd", "status", "decision_date",
                                       "rejection_reason", "settlement_date", "adjuster_name"],
             [(c["id"], c["number"], c["inc"], c["cust"], c["policy"], c["insurer"], c["coverage"], ds(c["filed"]),
               c["claimed"], c["deductible"], c["approved"], c["status"], ds(c["decision"]), c["reason"], ds(c["settle"]),
               c["adjuster"]) for c in claims])
        emit(out, "customs_declarations", ["declaration_id", "declaration_number", "shipment_id", "warehouse_id",
                                           "declaration_type", "customs_country", "hs_code", "goods_description",
                                           "customs_value_usd", "duty_rate_pct", "duty_amount_usd", "vat_amount_usd",
                                           "broker_name", "inspection_required", "inspection_result", "submitted_at",
                                           "cleared_at", "status"],
             [(d["id"], d["number"], d["ship"], d["wh"], d["kind"], d["country"], d["hs"], d["desc"], d["value"], d["rate"],
               d["duty"], d["vat"], d["broker"], d["insp"], d["result"], ts(d["submitted"]), ts(d["cleared"]), d["status"])
              for d in customs])
        emit(out, "tracking_events", ["event_id", "shipment_id", "flight_id", "airport_id", "warehouse_id", "event_code",
                                      "event_time", "pieces", "weight_kg", "temperature_c", "recorded_by", "scanner_id"],
             [(e["id"], e["ship"], e["flight"], e["ap"], e["wh"], e["code"], ts(e["time"]), e["pieces"], e["weight"],
               e["temp"], e["by"], e["scanner"]) for e in events])
        out.write("COMMIT;\n")


if __name__ == "__main__":
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql")
    main(sys.argv[1] if len(sys.argv) > 1 else default)
