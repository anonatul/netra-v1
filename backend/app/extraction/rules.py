"""Layer 1 — deterministic multilingual safety rules (docs/AI.md).

Always-on, zero-latency, auditable. Output: {attr: {"value": bool, "confidence": 1.0,
"model": "rules-v1", "source_terms": [...]}} plus severity + victim count hints.

Matching is lowercase substring on normalized text; Hinglish/romanized Hindi terms
are first-class citizens.
"""
import re

from app.config import settings

RULES_VERSION = settings.nlp_rules_version

SEVERITY_TERMS = {
    "CRITICAL": {
        "en": ["unconscious", "not breathing", "cardiac", "heart attack", "stroke", "severe bleeding",
               "bleeding heavily", "critical", "dying"],
        "hi": ["behosh", "be-hosh", "sans nahi", "saans nahi", "dil ka daura", "bhari khoon", "khoon bah raha",
               "khatre me", "mar rahe", "mar rahi"],
    },
    "HIGH": {
        "en": ["bleeding", "injured", "serious", "trapped", "stuck", "can't move", "cannot move",
               "broken", "fracture"],
        "hi": ["khoon", "ghaayal", "gambhir", "phans gaye", "phans gaya", "phas gaye", "harkat nahi",
               "hil nahi sakta", "hil nahi sakti", "tut gaya", "tut gai"],
    },
    "MEDIUM": {
        "en": ["water rising", "water entering", "flooded", "water inside", "chest deep", "knee deep"],
        "hi": ["paani badh", "paani ghus", "paani andar", "paani bhara", "chhati tak paani", "ghutno tak paani"],
    },
}

VULNERABILITY_TERMS = {
    "elderly": {
        "en": ["grandmother", "grandfather", "elderly", "old man", "old woman", "aged", "senior citizen"],
        "hi": ["dadi", "dada", "bujurg", "budhe", "budhi", "bade log"],
    },
    "child": {
        "en": ["baby", "infant", "child", "kid", "children", "toddler"],
        "hi": ["bachcha", "bachchi", "bachche", "shishu", "baba", "baby"],
    },
    "mobility_issue": {
        "en": ["cannot walk", "can't walk", "wheelchair", "disabled", "paralyzed", "bedridden"],
        "hi": ["chal nahi sakta", "chal nahi sakti", "wheelchair", "viklang", "lukva", "bed par"],
    },
    "pregnant": {
        "en": ["pregnant", "expecting"],
        "hi": ["garbhvati", "pet me bachcha", "pregnant"],
    },
}

DISASTER_TERMS = {
    "FLOOD": {
        "en": ["flood", "flooded", "water", "paani", "water level", "rains", "dam", "river"],
        "hi": ["baadh", "paani", "barish", "nadi", "dam"],
    },
    "EARTHQUAKE": {
        "en": ["earthquake", "tremor", "building collapsed", "building shaking", "aftershock"],
        "hi": ["bhookamp", "zameen hil", "imarat gir", "jhatka"],
    },
    "CYCLONE": {
        "en": ["cyclone", "storm", "winds", "tornado", "hurricane"],
        "hi": ["toofan", "chakrawat", "hawa tez", "andhi"],
    },
}

WATER_RISING_TERMS = {
    "en": ["water rising", "water level rising", "rising water", "water up to", "water reached",
           "chest deep", "knee deep", "waist deep", "kamar tak", "flooding fast"],
    "hi": ["paani badh", "paani upar", "paani kamar tak", "paani chhati tak", "paani ghutno tak",
           "paani barh", "paani bahut ho"],
}

TRAPPED_TERMS = {
    "en": ["trapped", "stuck", "can't get out", "cannot get out", "locked in", "rooftop", "terrace",
           "on the roof", "top floor", "marooned"],
    "hi": ["phans", "phas", "bahar nahi nikal", "chhat par", "terrace par", "upar wale floor",
           "nikal nahi pa rahe"],
}

ACCESS_TERMS = {
    "en": ["road blocked", "no road", "bridge broken", "bridge collapsed", "can't reach", "cut off",
           "isolated", "landslide"],
    "hi": ["sadak band", "raasta band", "pul tut", "pul gir", "nahi pahunch", "cut off", "alag ho"],
}

SAFE_TERMS = {
    "en": ["safe", "rescued", "reached shelter", "fine", "we are ok", "evacuated", "in shelter"],
    "hi": ["safe", "bach gaye", "bach gaya", "theek hoon", "theek hai", "shelter pahunch", "nikal gaye"],
}

FAKE_TERMS = {
    "en": ["prank", "joke", "testing", "test message", "not real"],
    "hi": ["mazak", "jhooth", "test", "khel"],
}


def _terms(*groups: dict[str, list[str]]) -> list[str]:
    out: list[str] = []
    for group in groups:
        for lang_terms in group.values():
            out.extend(lang_terms)
    return out


def _matches(text: str, terms: list[str]) -> list[str]:
    return [t for t in terms if t in text]


def extract(text: str) -> dict:
    """Run Layer 1 rules on raw text. Returns extraction dict (JSON-serializable)."""
    normalized = text.lower()

    attributes: dict[str, dict] = {}
    for attr, groups in [
        ("elderly", VULNERABILITY_TERMS["elderly"]),
        ("child", VULNERABILITY_TERMS["child"]),
        ("mobility_issue", VULNERABILITY_TERMS["mobility_issue"]),
        ("pregnant", VULNERABILITY_TERMS["pregnant"]),
        ("water_rising", WATER_RISING_TERMS),
        ("trapped", TRAPPED_TERMS),
        ("access_issue", ACCESS_TERMS),
    ]:
        hits = _matches(normalized, _terms(groups))
        if hits:
            attributes[attr] = {"value": True, "confidence": 1.0, "model": RULES_VERSION, "source_terms": hits[:5]}

    severity = "UNKNOWN"
    severity_hits: list[str] = []
    for level, groups in SEVERITY_TERMS.items():
        hits = _matches(normalized, _terms(groups))
        if hits:
            severity = level
            severity_hits = hits[:5]
            break
    if severity == "UNKNOWN" and (attributes.get("trapped") or attributes.get("water_rising")):
        severity = "MEDIUM"

    disaster = "UNKNOWN"
    for kind, groups in DISASTER_TERMS.items():
        if _matches(normalized, _terms(groups)):
            disaster = kind
            break

    safe = bool(_matches(normalized, _terms(SAFE_TERMS)))
    fake = bool(_matches(normalized, _terms(FAKE_TERMS)))

    victim_hint: int | None = None
    m = re.search(r"\b(\d{1,3})\s*(?:log|logo|people|persons|bacche|bachche|sadak|members)\b", normalized)
    if m:
        victim_hint = int(m.group(1))

    return {
        "severity": severity,
        "severity_hits": severity_hits,
        "disaster": disaster,
        "safe": safe,
        "fake": fake,
        "victim_hint": victim_hint,
        "attributes": attributes,
        "model": RULES_VERSION,
        "confidence": 1.0,
    }