"""Identifier mapping for the three schema variants.

normal  : the human-readable schema in schema/schema.sql (source of truth)
mixed   : SAP-style abbreviations, mostly German (kunnr, flug, abfl_ist, zoll_anm ...) mixed with English ones
cryptic : meaningless table names (t + 3 characters) and positional column names (c01, c02, ...)

Only identifiers change. Data values (e.g. 'completed', 'FRA') are identical in all three databases, so the
Gold result of every question is the same in every variant.
"""
import random

# table -> (mixed table name, {normal column: mixed column})
MIXED = {
    "benchmark_meta": ("bm_param", {"meta_key": "param_schl", "meta_value": "param_wert"}),
    "airports": ("flghf", {
        "airport_id": "fh_nr", "iata_code": "iata_cd", "icao_code": "icao_cd", "name": "bez", "city": "ort",
        "country": "land", "region": "reg", "timezone": "zeitz", "latitude": "breite", "longitude": "laenge",
        "elevation_m": "hoehe_m", "runway_count": "anz_slb", "longest_runway_m": "max_slb_m", "is_cargo_hub": "hub_kz",
        "annual_cargo_capacity_t": "kap_jahr_t", "has_24h_customs": "zoll_24h_kz", "night_curfew": "nachtflugverb_kz"}),
    "airlines": ("flges", {
        "airline_id": "flges_nr", "iata_code": "iata_cd", "icao_code": "icao_cd", "name": "bez", "callsign": "rufz",
        "country": "land", "headquarters_city": "sitz_ort", "founded_year": "gruend_jahr",
        "home_hub_airport_id": "hub_fh_nr", "alliance": "allianz", "is_cargo_only": "nur_fracht_kz",
        "aoc_number": "aoc_nr", "website": "web_adr", "contact_email": "kontakt_mail"}),
    "aircraft_types": ("lfz_typ", {
        "type_id": "typ_nr", "model": "mdl", "icao_type_designator": "icao_typ", "manufacturer": "herst",
        "engine_count": "anz_trw", "engine_model": "trw_mdl", "max_payload_kg": "max_nutzl_kg",
        "max_volume_m3": "max_vol_m3", "max_range_km": "max_reichw_km", "cruise_speed_kmh": "reise_geschw_kmh",
        "max_takeoff_weight_kg": "mtow_kg", "operating_empty_weight_kg": "leergew_kg",
        "fuel_capacity_kg": "tank_kap_kg", "fuel_burn_kg_per_hour": "verbr_kg_h", "main_deck_positions": "anz_hd_pos",
        "wingspan_m": "spannw_m"}),
    "aircraft": ("lfz", {
        "aircraft_id": "lfz_nr", "tail_number": "kennz", "serial_number": "msn", "type_id": "typ_nr",
        "airline_id": "flges_nr", "home_airport_id": "heimat_fh_nr", "registration_country": "zul_land",
        "year_manufactured": "baujahr", "delivery_date": "ausl_dat", "ownership": "eigt_art",
        "lessor_name": "leasgeb", "lease_end_date": "leas_ende_dat", "total_flight_hours": "ges_flugstd",
        "total_cycles": "ges_zyklen", "last_heavy_check_date": "letzt_c_chk_dat", "status": "stat"}),
    "customers": ("knd_stamm", {
        "customer_id": "kunnr", "account_code": "kto_cd", "name": "name1", "customer_type": "knd_typ",
        "country": "land", "city": "ort", "address_line": "strasse", "postal_code": "plz",
        "contact_name": "ansprechp", "contact_email": "ansp_mail", "contact_phone": "ansp_tel",
        "website": "web_adr", "sales_region": "vertr_reg", "credit_limit_usd": "kredlim_usd",
        "payment_terms_days": "zahlbed_tg", "is_known_shipper": "bek_versender_kz", "loyalty_tier": "treue_stufe",
        "created_date": "erdat"}),
    "warehouses": ("lgr", {
        "warehouse_id": "lgr_nr", "warehouse_code": "lgr_cd", "airport_id": "fh_nr", "operator_name": "betreiber",
        "warehouse_type": "lgr_typ", "floor_area_m2": "flaeche_m2", "capacity_tonnes": "kap_t",
        "cold_room_count": "anz_kuehlr", "min_temperature_c": "min_temp_c", "dock_door_count": "anz_tore",
        "has_dg_area": "gefgut_ber_kz", "is_bonded": "zolllager_kz", "security_level": "sich_stufe",
        "operates_24h": "betr_24h_kz", "opened_year": "eroeff_jahr", "monthly_rent_usd": "miete_mon_usd"}),
    "crew_members": ("bes_mitgl", {
        "crew_member_id": "pers_nr", "employee_number": "ma_nr", "first_name": "vorname", "last_name": "nachname",
        "email": "mail", "airline_id": "flges_nr", "base_airport_id": "basis_fh", "crew_rank": "dienstgrad",
        "type_rating_id": "musterber_typ", "license_number": "lizenz_nr", "license_expiry_date": "lizenz_ablauf",
        "medical_expiry_date": "med_ablauf", "hire_date": "eintr_dat", "seniority_number": "dienstalter_nr",
        "total_flight_hours": "ges_flugstd", "is_active": "aktiv_kz"}),
    "flights": ("flug", {
        "flight_id": "flug_id", "flight_number": "flugnr", "flight_type": "flug_art", "aircraft_id": "lfz_nr",
        "origin_airport_id": "abfl_fh", "destination_airport_id": "ziel_fh", "scheduled_departure": "abfl_plan",
        "scheduled_arrival": "ank_plan", "actual_departure": "abfl_ist", "actual_arrival": "ank_ist",
        "departure_stand": "abfl_pos", "arrival_stand": "ank_pos", "distance_km": "entf_km",
        "planned_cruise_altitude_ft": "reiseflughoehe_ft", "takeoff_weight_kg": "tow_kg",
        "weather_at_departure": "wetter_abfl", "delay_code": "versp_cd", "cancellation_reason": "storno_grund",
        "status": "stat"}),
    "crew_assignments": ("bes_eins", {
        "assignment_id": "eins_id", "flight_id": "flug_id", "crew_member_id": "pers_nr", "duty_role": "funktion",
        "is_pilot_flying": "pf_kz", "report_time": "meld_zeit", "release_time": "ende_zeit",
        "block_minutes_credited": "block_min", "rest_minutes_before": "ruhe_min_vor", "per_diem_usd": "spesen_usd",
        "hotel_required": "hotel_kz", "assignment_status": "eins_stat"}),
    "maintenance_records": ("wartg", {
        "maintenance_id": "wartg_id", "work_order_number": "auftr_nr", "aircraft_id": "lfz_nr", "airport_id": "fh_nr",
        "check_type": "chk_art", "ata_chapter": "ata_kap", "mro_provider": "mro_dienstl", "start_time": "beginn",
        "end_time": "ende", "labor_hours": "arb_std", "parts_cost_usd": "teile_kost_usd",
        "labor_cost_usd": "lohn_kost_usd", "deferred_items_count": "anz_zurueckgest", "is_aog": "aog_kz",
        "next_due_date": "naechst_faell", "status": "stat"}),
    "fuel_uplifts": ("betankg", {
        "fuel_uplift_id": "betank_id", "fuel_ticket_number": "beleg_nr", "flight_id": "flug_id", "airport_id": "fh_nr",
        "supplier_name": "lieferant", "fuel_type": "krst_art", "delivery_method": "liefer_art",
        "uplift_time": "betank_zeit", "quantity_kg": "menge_kg", "quantity_litres": "menge_l",
        "density_kg_per_l": "dichte", "price_usd_per_litre": "preis_usd_l", "total_cost_usd": "ges_kost_usd",
        "saf_blend_pct": "saf_ant_pct", "fuel_burned_kg": "verbr_kg", "co2_emissions_kg": "co2_kg"}),
    "shipments": ("sndg", {
        "shipment_id": "sndg_nr", "awb_number": "lbf_nr", "customer_id": "kunnr", "customer_reference": "knd_ref",
        "consignee_name": "empf_name", "origin_airport_id": "urspr_fh", "destination_airport_id": "ziel_fh",
        "booking_date": "buch_dat", "requested_delivery_date": "wunsch_lief_dat", "service_level": "serv_lvl",
        "commodity_category": "waren_kat", "pieces": "anz_stk", "total_weight_kg": "ges_gew_kg",
        "total_volume_m3": "ges_vol_m3", "chargeable_weight_kg": "fracht_gew_kg",
        "declared_value_usd": "dekl_wert_usd", "is_dangerous_goods": "gefgut_kz", "dg_class": "gefgut_kl",
        "is_temperature_controlled": "temp_kz", "min_temperature_c": "temp_min_c", "max_temperature_c": "temp_max_c",
        "status": "stat"}),
    "flight_cargo": ("flug_ladg", {
        "flight_cargo_id": "ladg_id", "shipment_id": "sndg_nr", "flight_id": "flug_id", "leg_number": "abschn_nr",
        "uld_type": "uld_typ", "uld_number": "uld_nr", "deck": "deck_cd", "position_code": "pos_cd",
        "load_sequence": "lade_folge", "seal_number": "plomben_nr", "loaded_at": "geladen_um",
        "leg_status": "abschn_stat"}),
    "invoices": ("rech_kopf", {
        "invoice_id": "rech_id", "invoice_number": "belnr", "shipment_id": "sndg_nr", "issued_date": "ausst_dat",
        "due_date": "faell_dat", "payment_terms_days": "zahlbed_tg", "freight_charge_usd": "fracht_usd",
        "fuel_surcharge_usd": "treibst_zuschl_usd", "security_fee_usd": "sich_geb_usd",
        "handling_fee_usd": "abfert_geb_usd", "dg_surcharge_usd": "gefgut_zuschl_usd", "discount_usd": "rabatt_usd",
        "amount_usd": "brutto_usd", "sent_via": "versand_weg", "status": "stat"}),
    "payments": ("zahlg", {
        "payment_id": "zahlg_id", "payment_reference": "zahl_ref", "invoice_id": "rech_id", "customer_id": "kunnr",
        "payment_date": "zahl_dat", "amount_usd": "betr_usd", "original_currency": "orig_waehr",
        "original_amount": "orig_betr", "exchange_rate_to_usd": "wkurs_usd", "method": "zahl_art",
        "bank_charges_usd": "bankgeb_usd", "is_reconciled": "abgestimmt_kz"}),
    "incidents": ("vorf", {
        "incident_id": "vorf_id", "flight_cargo_id": "ladg_id", "airport_id": "fh_nr", "warehouse_id": "lgr_nr",
        "incident_type": "vorf_art", "severity": "schwere", "root_cause": "ursache", "reported_by": "gemeldet_von",
        "reported_at": "meld_zeit", "pieces_affected": "betr_stk", "delay_minutes": "versp_min",
        "claim_amount_usd": "ford_betr_usd", "corrective_action": "korr_massn", "resolved": "erledigt_kz",
        "resolved_at": "erledigt_am"}),
    "insurance_claims": ("vers_schad", {
        "claim_id": "schad_id", "claim_number": "schad_nr", "incident_id": "vorf_id", "customer_id": "kunnr",
        "policy_number": "police_nr", "insurer_name": "versicherer", "coverage_type": "deckung_art",
        "filed_date": "meld_dat", "claimed_amount_usd": "ford_usd", "deductible_usd": "selbstbeh_usd",
        "approved_amount_usd": "genehm_usd", "status": "stat", "decision_date": "entsch_dat",
        "rejection_reason": "ablehn_grund", "settlement_date": "reg_dat", "adjuster_name": "sachbearb"}),
    "customs_declarations": ("zoll_anm", {
        "declaration_id": "anm_id", "declaration_number": "anm_nr", "shipment_id": "sndg_nr", "warehouse_id": "lgr_nr",
        "declaration_type": "anm_art", "customs_country": "zoll_land", "hs_code": "zolltarif_nr",
        "goods_description": "waren_bez", "customs_value_usd": "zollwert_usd", "duty_rate_pct": "zollsatz_pct",
        "duty_amount_usd": "zoll_betr_usd", "vat_amount_usd": "eust_usd", "broker_name": "zollagent",
        "inspection_required": "beschau_kz", "inspection_result": "beschau_erg", "submitted_at": "eingereicht",
        "cleared_at": "freigabe", "status": "stat"}),
    "tracking_events": ("sdg_verfolg", {
        "event_id": "ereig_id", "shipment_id": "sndg_nr", "flight_id": "flug_id", "airport_id": "fh_nr",
        "warehouse_id": "lgr_nr", "event_code": "ereig_cd", "event_time": "ereig_zeit", "pieces": "anz_stk",
        "weight_kg": "gew_kg", "temperature_c": "temp_c", "recorded_by": "erfasst_von", "scanner_id": "scanner_nr"}),
}


def cryptic_map(tables_in_order, columns_by_table, seed=491):
    """Cryptic names: tables get random 't' + 3-character codes, columns get c01..cNN (schema order)."""
    rng = random.Random(seed)
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    used, out = set(), {}
    for t in tables_in_order:
        while True:
            code = "t" + "".join(rng.choice(alphabet) for _ in range(3))
            if code not in used:
                used.add(code)
                break
        out[t] = (code, {c: f"c{k:02d}" for k, c in enumerate(columns_by_table[t], start=1)})
    return out


def index_name(variant, table_new, k):
    return {"mixed": f"ix_{table_new}_{k}", "cryptic": f"i{table_new[1:]}{k}"}[variant]
