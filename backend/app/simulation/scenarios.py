"""Deterministic demo scenarios (docs/DEMO.md, KB file 21).

The killer scenario: 50 reports → 17 incidents → 6 zones → 2 P1 / 3 P2 / 1 P3,
then +30 reports escalate zone 4 to P1 (medical-critical + elderly + rising water).

Structure: zones with centroids around a district; incidents = clusters of
reports (duplicates from the same incident, distinct devices). Generation is
seeded (SIMULATION_SEED=42) → identical replay every run (NFR-097).
"""
import random
import math
from dataclasses import dataclass, field

SIM_DISTRICT = {"name": "Mumbai Flood Sim", "type": "FLOOD", "mode": "DEGRADED",
                "center": {"lat": 19.0760, "lon": 72.8777}}

# Zone: id, center, radius_m, profile list (one entry per incident), reports range
ZONES = [
    {"id": "Z1", "lat": 19.0760, "lon": 72.8777, "radius_m": 400,
     "profiles": ["critical", "critical", "high_water", "high_water"]},
    {"id": "Z2", "lat": 19.0880, "lon": 72.8650, "radius_m": 350,
     "profiles": ["moderate_vuln", "moderate_vuln", "moderate_vuln"]},
    {"id": "Z3", "lat": 19.0650, "lon": 72.8900, "radius_m": 350,
     "profiles": ["critical", "high_water", "high_water"]},
    {"id": "Z4", "lat": 19.0980, "lon": 72.8700, "radius_m": 400,
     "profiles": ["moderate_vuln", "moderate_vuln", "moderate_vuln"]},
    {"id": "Z5", "lat": 19.0520, "lon": 72.8620, "radius_m": 300,
     "profiles": ["moderate_vuln", "moderate_vuln"]},
    {"id": "Z6", "lat": 19.0700, "lon": 72.9050, "radius_m": 300,
     "profiles": ["low", "low"]},
]
# 4+3+3+3+2+2 = 17 incidents ✓  → 6 zones ✓  → 2 P1 (Z1,Z3) 3 P2 (Z2,Z4,Z5) 1 P3 (Z6)

TEMPLATES: dict[str, list[str]] = {
    "high_water": [
        "Paani kamar tak aa gaya hai, {vuln} chhat par phans gaye, madad bhejo",
        "Water rising fast, we are trapped on rooftop, {vuln} with us cannot move",
        "paani bahut tej badh raha hai, {vuln} phas gaye hain, jaldi aao",
        "Flood water up to our chest, stuck on top floor, {vuln}, please help",
    ],
    "critical": [
        "KHOON BAH RAHA HAI, {vuln} BEHOSH HO GAYE HAIN, PAANI CHHAT TAK, JALDI MADAD",
        "Grandmother bleeding heavily and unconscious, water up to roof, 4 of us trapped, urgent",
        "Dadi ko dil ka daura pada, bachcha bemar hai, paani bahut badh gaya, phans gaye hain",
        "bhari khoon bah raha hai, be-hosh log hain, water rising, need rescue boats NOW",
    ],
    "moderate_vuln": [
        "paani ghar me ghus raha hai, {vuln}, kuch samajh nahi aa raha",
        "Water entering our house, {vuln}, need assistance soon",
        "flood water knee deep outside, {vuln}, scared, please check on us",
    ],
    "low": [
        "paani ghar me ghus raha hai, hum log ghar me hi hain, bas jankari de rahe hain",
        "water entering our house slowly, we are inside, just informing, no urgent need",
    ],
    "escalate": [
        "PAANI KAMAR TAK AUR TEJ BARH RAHA HAI, DADI AUR BACHCHE BEEMAR HAIN, KHOON BAH RAHA HAI, 5 LOG PHANSE HAIN",
        "Water rising to chest level now, grandmother bleeding and baby with fever, 5 of us trapped on rooftop",
        "situation critical, paani chhati tak, maa ko dil ka daura pada, bachcha bhi hai, jaldi bhejo boat",
    ],
}

VULN_SETS = [
    "dadi",
    "bachcha",
    "dadi aur bachcha",
    "meri maa jo chal nahi sakti",
    "grandmother and a small child",
    "elderly parents",
]


@dataclass
class SimBatch:
    label: str
    events: list[dict] = field(default_factory=list)


def _jitter(rng: random.Random, base_lat: float, base_lon: float, radius_m: float) -> tuple[float, float]:
    """Uniform offset within radius (meters → degrees approx)."""
    d = radius_m * (rng.random() ** 0.5)
    theta = rng.random() * 2 * 3.14159265
    dlat = d * 0.0000090  # meters → degrees lat
    dlon = d * 0.0000110  # meters → degrees lon (approx at ~19°N)
    return base_lat + dlat * (1 if rng.random() < 0.5 else -1), base_lon + dlon * (1 if rng.random() < 0.5 else -1)


def build_killer_scenario(seed: int = 42, t0: str = "2026-08-18T09:00:00Z") -> list[SimBatch]:
    """Build the deterministic killer scenario as ordered batches."""
    import datetime as dt

    rng = random.Random(seed)
    start = dt.datetime.fromisoformat(t0.replace("Z", "+00:00"))
    batches: list[SimBatch] = [SimBatch("step1_50_reports")]

    device_counter = [0]
    # 17 incidents, exactly 50 reports (3+2+3+4+2+3+3+4+2+3+4+3+2+3+2+4+3 = 50)
    REPORTS_PER_INCIDENT = [3, 2, 3, 4, 2, 3, 3, 4, 2, 3, 4, 3, 2, 3, 2, 4, 3]

    def next_device() -> str:
        device_counter[0] += 1
        return f"sim-dev-{device_counter[0]:04d}"

    # Step 1: 17 incidents × 2–4 reports = exactly 50 reports across 6 zones.
    # Incident seeds sit on a deterministic ring (angle from profile index) so
    # incidents stay distinct (~250m apart) while the zone radius merges them.
    incident_idx = 0
    for zone in ZONES:
        n_incidents = len(zone["profiles"])
        for i, profile in enumerate(zone["profiles"]):
            angle = i * (2 * 3.14159265 / n_incidents) + 0.3
            dist = zone["radius_m"] * 0.35
            seed_lat = zone["lat"] + math.cos(angle) * dist * 0.0000090
            seed_lon = zone["lon"] + math.sin(angle) * dist * 0.0000110
            n_reports = REPORTS_PER_INCIDENT[incident_idx]
            incident_idx += 1
            vuln = rng.choice(VULN_SETS) if profile != "low" else ""
            for r_idx in range(n_reports):
                text = rng.choice(TEMPLATES[profile]).format(vuln=vuln)
                offset = dt.timedelta(minutes=rng.randint(0, 25))
                batches[0].events.append({
                    "source_type": rng.choice(["SMS", "SMS", "ERSS"]),
                    "source_timestamp": (start + offset).isoformat(),
                    "text": text,
                    "lat": seed_lat + rng.uniform(-0.00015, 0.00015),
                    "lon": seed_lon + rng.uniform(-0.00015, 0.00015),
                    "accuracy_m": rng.choice([30, 50, 80]),
                    "source_identifier": next_device(),
                })

    # Step 2: +30 reports — Z4 escalates P2→P1 via a medical-critical burst.
    # Burst lands near Z4's center (within its zone, beyond incident radius) →
    # new critical incidents in Z4 → zone priority P1 (deterministic rules path).
    step2 = SimBatch("step2_30_reports_escalation")
    z4 = ZONES[3]
    for i in range(10):
        lat, lon = _jitter(rng, z4["lat"], z4["lon"], z4["radius_m"] * 0.2)
        offset = dt.timedelta(minutes=30 + i)
        step2.events.append({
            "source_type": "SMS",
            "source_timestamp": (start + offset).isoformat(),
            "text": rng.choice(TEMPLATES["escalate"]),
            "lat": lat,
            "lon": lon,
            "accuracy_m": 40,
            "source_identifier": next_device(),
        })
    # 20 corroborating reports land ON existing incident seeds (0.15 × zone
    # radius) → merge into existing incidents, boost independent sources,
    # without creating edge incidents that bridge zones.
    for zone in ZONES[:3] + ZONES[4:]:
        for _ in range(4):
            lat, lon = _jitter(rng, zone["lat"], zone["lon"], zone["radius_m"] * 0.15)
            offset = dt.timedelta(minutes=35 + rng.randint(0, 10))
            profile = zone["profiles"][0]
            step2.events.append({
                "source_type": "SMS",
                "source_timestamp": (start + offset).isoformat(),
                "text": rng.choice(TEMPLATES[profile]).format(vuln=rng.choice(VULN_SETS) if profile != "low" else ""),
                "lat": lat,
                "lon": lon,
                "accuracy_m": rng.choice([50, 100]),
                "source_identifier": next_device(),
            })
    batches.append(step2)
    return batches


def build_adversarial_packs(seed: int = 42, t0: str = "2026-08-18T09:00:00Z") -> dict[str, SimBatch]:
    """Adversarial packs (KB file 19 §3) — injected on demand."""
    import datetime as dt

    rng = random.Random(seed)
    start = dt.datetime.fromisoformat(t0.replace("Z", "+00:00"))
    packs: dict[str, SimBatch] = {}

    fake = SimBatch("500_fake_sos")
    for i in range(500):
        fake.events.append({
            "source_type": "SMS",
            "source_timestamp": (start + dt.timedelta(minutes=60 + i % 15)).isoformat(),
            "text": "MERA MOBILE TEST HO RAHA HAI, YE PRANK HAI, HAHA",
            "lat": 19.0760 + rng.uniform(-0.001, 0.001),
            "lon": 72.8777 + rng.uniform(-0.001, 0.001),
            "accuracy_m": 500,
            "source_identifier": "prank-phone-001",
        })
    packs["fake_sos"] = fake

    dupes = SimBatch("30_duplicates_one_device")
    for i in range(30):
        dupes.events.append({
            "source_type": "SMS",
            "source_timestamp": (start + dt.timedelta(minutes=70 + i)).isoformat(),
            "text": "PAANI CHHAT TAK AA GAYA HAI HUM PHANSE HAIN MADAD KARO",
            "lat": 19.0700,
            "lon": 72.9050,
            "accuracy_m": 50,
            "source_identifier": "same-device-042",
        })
    packs["duplicates"] = dupes

    stale = SimBatch("stale_reports")
    for i in range(20):
        stale.events.append({
            "source_type": "SMS",
            "source_timestamp": (start - dt.timedelta(hours=12 + i)).isoformat(),
            "text": rng.choice(TEMPLATES["high_water"]).format(vuln="dadi"),
            "lat": 19.0650 + rng.uniform(-0.002, 0.002),
            "lon": 72.8900 + rng.uniform(-0.002, 0.002),
            "accuracy_m": 100,
            "source_identifier": next_device(rng),
        })
    packs["stale"] = stale

    medical = SimBatch("medical_burst")
    for i in range(15):
        medical.events.append({
            "source_type": "ERSS",
            "source_timestamp": (start + dt.timedelta(minutes=80 + i)).isoformat(),
            "text": rng.choice([
                "Khoon bah raha hai, be-hosh ho gaye hain, 4 log injured",
                "Heart attack, unconscious man on 2nd floor, water rising",
                "bachcha behosh ho gaya, saans nahi aa rahi, jaldi ambulance",
            ]),
            "lat": 19.0760 + rng.uniform(-0.0015, 0.0015),
            "lon": 72.8777 + rng.uniform(-0.0015, 0.0015),
            "accuracy_m": 60,
            "source_identifier": f"erss-med-{i:03d}",
        })
    packs["medical"] = medical
    return packs


def next_device(rng: random.Random) -> str:
    return f"stale-dev-{rng.randint(1000, 9999)}"