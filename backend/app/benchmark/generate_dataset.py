"""Synthetic labelled report generator (docs/BENCHMARK.md).

Deterministic (seed 42): 10,000 multilingual reports with ground-truth labels.
Profiles map 1:1 to labels, so ground truth is known by construction — but
reports carry natural variation (typos, short forms, Hinglish) so extraction
is non-trivial. 20% duplicates, 8% fake, 5% safe are injected per plan.

Usage: python -m app.benchmark.generate_dataset --n 10000 --out reports.jsonl
"""
import argparse
import json
import random
import string

SEED = 42

# profile → ground truth
PROFILES = {
    "critical_flood": {"disaster": "FLOOD", "severity": "CRITICAL",
                       "attrs": {"trapped": True, "water_rising": True, "medical_critical": True},
                       "victims": (2, 8)},
    "high_trapped": {"disaster": "FLOOD", "severity": "HIGH",
                     "attrs": {"trapped": True, "water_rising": True}, "victims": (1, 4)},
    "vulnerable_elderly": {"disaster": "FLOOD", "severity": "HIGH",
                           "attrs": {"elderly": True, "trapped": True}, "victims": (1, 3)},
    "child_alone": {"disaster": "FLOOD", "severity": "HIGH",
                    "attrs": {"child": True, "trapped": True}, "victims": (1, 2)},
    "mobility": {"disaster": "FLOOD", "severity": "HIGH",
                 "attrs": {"mobility_issue": True, "water_rising": True}, "victims": (1, 3)},
    "pregnant": {"disaster": "FLOOD", "severity": "MEDIUM",
                 "attrs": {"pregnant": True}, "victims": (1, 2)},
    "moderate_water": {"disaster": "FLOOD", "severity": "MEDIUM",
                       "attrs": {"water_rising": True}, "victims": (1, 5)},
    "low_water": {"disaster": "FLOOD", "severity": "LOW", "attrs": {}, "victims": (1, 2)},
    "quake_collapse": {"disaster": "EARTHQUAKE", "severity": "CRITICAL",
                       "attrs": {"trapped": True, "medical_critical": True}, "victims": (2, 10)},
    "quake_trapped": {"disaster": "EARTHQUAKE", "severity": "HIGH",
                      "attrs": {"trapped": True}, "victims": (1, 5)},
    "quake_moderate": {"disaster": "EARTHQUAKE", "severity": "MEDIUM", "attrs": {}, "victims": (1, 3)},
    "cyclone_moderate": {"disaster": "CYCLONE", "severity": "MEDIUM",
                         "attrs": {"access_issue": True}, "victims": (1, 4)},
}

TEMPLATES = {
    "en": {
        "critical_flood": ["Water up to our chest and rising, {vict} of us trapped, {med} bleeding badly, need rescue NOW",
                           "{med} unconscious, flood water reaching rooftop, {vict} people stuck, urgent help",
                           "Severe flooding, trapped on top floor, {med} needs hospital, water still rising"],
        "high_trapped": ["Water rising fast, trapped on rooftop with {vict} people, need boat",
                         "Flooded, stuck on terrace, water up to waist, {vict} of us here",
                         "Trapped inside, water entering, {vict} family members, please send help"],
        "vulnerable_elderly": ["Grandmother cannot walk and we are stuck in flood water, {vict} of us",
                               "Elderly parents on roof, flood water all around, {vict} people, help",
                               "My old mother with me, water rising, we are trapped, {vict} persons"],
        "child_alone": ["Baby with me, water in the house, we are stuck, please come",
                        "Small child and I trapped in flooded house, {vict} of us, urgent"],
        "mobility": ["Wheelchair user, water everywhere, cannot move, {vict} people here",
                     "Cannot walk, flood water rising fast, trapped in room, {vict} of us"],
        "pregnant": ["Pregnant wife with me, water entering house, need help soon",
                     "My wife is pregnant and water is rising, {vict} of us, please assist"],
        "moderate_water": ["Water entering our house slowly, {vict} people inside, a bit worried",
                           "Flood water knee deep outside, {vict} of us at home, monitoring"],
        "low_water": ["Some water on the street, we are fine, just informing",
                      "Water near our building, {vict} of us safe, no urgent need"],
        "quake_collapse": ["Building collapsed, {vict} people trapped under debris, {med} severely injured",
                           "Earthquake, building came down, {vict} stuck inside, {med} critical"],
        "quake_trapped": ["Earthquake, stuck in collapsed room, {vict} of us, help",
                          "Tremors, building partially collapsed, {vict} people inside"],
        "quake_moderate": ["Felt strong tremor, minor cracks in wall, {vict} of us, no injuries",
                           "Earthquake shake, everything ok here, {vict} of us at home"],
        "cyclone_moderate": ["Storm winds, road to our village blocked by fallen trees, {vict} of us",
                             "Cyclone damage, road blocked, {vict} people here, need access help"],
    },
    "hi": {
        "critical_flood": ["Paani chhati tak aur tej badh raha hai, {vict} log phanse hain, {med} khoon bah raha hai",
                           "{med} behosh ho gaya, paani chhat tak, {vict} log phas gaye, jaldi madad",
                           "Gambhir flood, chhat par phans gaye, {med} hospital chahiye, paani barh raha"],
        "high_trapped": ["Paani tej badh raha, {vict} log chhat par phans gaye, boat bhejo",
                         "Flood ho gaya, terrace par atke hain, kamar tak paani, {vict} log",
                         "Ghar me paani ghus gaya, {vict} pariwar ke log, madad karo"],
        "vulnerable_elderly": ["Dadi chal nahi sakti, paani me phas gaye, {vict} log hain",
                               "Bujurg maa-baap chhat par, charo taraf paani, {vict} log, bachao"],
        "child_alone": ["Bachcha mere saath hai, ghar me paani, phas gaye hain",
                        "Chhota bachcha aur main ghar me band, {vict} log, jaldi aao"],
        "mobility": ["Wheelchair wale, paani charo taraf, chal nahi sakte, {vict} log",
                     "Lukva (paralyzed) aadmi, paani barh raha, kamre me phansa, {vict} log"],
        "pregnant": ["Garbhvati wife mere saath, ghar me paani ghus raha, madad karo",
                     "Bibi pregnant hai, paani badh raha, {vict} log, please help"],
        "moderate_water": ["Ghar me paani ghus raha dheere dheere, {vict} log andar, thodi chinta hai",
                           "Ghutno tak paani bahar, {vict} log ghar par, dekh rahe hain"],
        "low_water": ["Sadak par thoda paani hai, hum log ghar me hi hain, bas jankari",
                      "Paani building ke paas hai, {vict} log safe hain, urgent nahi"],
        "quake_collapse": ["Imarat gir gayi, {vict} log maliye ke neeche, {med} be-hosh",
                           "Bhoomp, building toot gayi, {vict} log andar atke, {med} critical"],
        "quake_trapped": ["Bhoomp aaya, kamre me phas gaye, {vict} log, madad",
                          "Zameen hil rahi thi, building parti, {vict} log andar"],
        "quake_moderate": ["Tez jhatka laga, deewar me halki darar, {vict} log, koi nuksan nahi",
                           "Bhoomp ka jhatka, sab theek hai, {vict} log ghar par"],
        "cyclone_moderate": ["Toofan se sadak band ho gayi, ped gir gaye, {vict} log, raasta kholo",
                             "Chakrawat se gali band, {vict} log yahan, access chahiye"],
    },
}

LANG_RATIO = {"en": 0.4, "hi": 0.35, "hinglish": 0.25}
PROFILE_RATIO = {
    "critical_flood": 0.07, "high_trapped": 0.12, "vulnerable_elderly": 0.08, "child_alone": 0.05,
    "mobility": 0.04, "pregnant": 0.03, "moderate_water": 0.22, "low_water": 0.12,
    "quake_collapse": 0.05, "quake_trapped": 0.08, "quake_moderate": 0.08, "cyclone_moderate": 0.06,
}

HINGLISH_NOISE = {
    "critical_flood": "paani chest tak and rising, {vict} log trapped, {med} khoon bah raha, NOW bhejo help",
    "high_trapped": "water rising fast, chhat par trapped {vict} log, boat bhejo please",
    "vulnerable_elderly": "dadi cannot walk, hum flood me stuck, {vict} log, urgent",
    "child_alone": "bachcha and me trapped in flooded ghar, {vict} log, jaldi aao",
    "mobility": "wheelchair wale, cannot move, paani everywhere, {vict} log",
    "pregnant": "wife pregnant hai, paani ghar me entering, {vict} log, help please",
    "moderate_water": "paani slowly ghar me ghus raha, {vict} log andar, little worried",
    "low_water": "thoda paani road par, hum log fine, no urgent need",
    "quake_collapse": "building collapse ho gaya, {vict} log under debris, {med} critical",
    "quake_trapped": "bhoomp, stuck in room, {vict} log, madad karo",
    "quake_moderate": "tremor aaya, sab ok, {vict} log, no injury",
    "cyclone_moderate": "toofan se road blocked, {vict} log yahan, access chahiye",
}

FAKE_TEXTS = [
    "THIS IS A PRANK CALL, NOTHING HAPPENED, HAHA",
    "ye to mazak tha, koi problem nahi hai",
    "testing the app, ignore this message",
    "just a joke, no emergency, sorry",
]
SAFE_TEXTS = [
    "we reached the shelter, all safe, thank you",
    "hum log safe hain, shelter pahunch gaye",
    "evacuated, everyone fine, no help needed",
    "bach gaye hum log, theek hain ab",
]


def _noise(rng: random.Random, text: str) -> str:
    """Add typos/short forms to ~20% of reports (realistic channel noise)."""
    if rng.random() > 0.2:
        return text
    words = text.split()
    if not words:
        return text
    idx = rng.randrange(len(words))
    word = words[idx]
    if len(word) <= 2:
        return text
    if rng.random() < 0.5:
        words[idx] = word[:-1]  # dropped last letter
    else:
        letter = rng.choice(string.ascii_lowercase)
        pos = rng.randrange(1, len(word))
        words[idx] = word[:pos] + letter + word[pos:]
    return " ".join(words)


def _victims(rng: random.Random, profile: dict, lang: str) -> str:
    lo, hi = profile["victims"]
    n = rng.randint(lo, hi)
    token = {"en": "people", "hi": "log", "hinglish": "log"}[lang]
    return f"{n} {token}"


def _medical(rng: random.Random, lang: str) -> str:
    return {"en": "one person", "hi": "ek aadmi", "hinglish": "ek aadmi"}[lang]


def generate(n: int = 10000, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    profiles = list(PROFILES)
    weights = [PROFILE_RATIO[p] for p in profiles]
    langs = list(LANG_RATIO)
    lang_weights = [LANG_RATIO[l] for l in langs]

    rows: list[dict] = []
    for i in range(n):
        kind = rng.random()
        if kind < 0.08:
            text = rng.choice(FAKE_TEXTS)
            rows.append({"id": i, "text": text, "lang": "en", "profile": "FAKE",
                         "disaster": "UNKNOWN", "severity": "UNKNOWN", "attrs": {}, "victims": None,
                         "safe": False, "fake": True})
            continue
        if kind < 0.13:
            text = rng.choice(SAFE_TEXTS)
            rows.append({"id": i, "text": text, "lang": "en", "profile": "SAFE",
                         "disaster": "UNKNOWN", "severity": "UNKNOWN", "attrs": {}, "victims": None,
                         "safe": True, "fake": False})
            continue

        profile = rng.choices(profiles, weights=weights)[0]
        lang = rng.choices(langs, weights=lang_weights)[0]
        meta = PROFILES[profile]
        if lang == "hinglish":
            text = HINGLISH_NOISE[profile]
        else:
            text = rng.choice(TEMPLATES[lang][profile])
        text = text.format(vict=_victims(rng, meta, lang), med=_medical(rng, lang))
        rows.append({
            "id": i, "text": _noise(rng, text), "lang": lang, "profile": profile,
            "disaster": meta["disaster"], "severity": meta["severity"],
            "attrs": dict(meta["attrs"]), "victims": rng.randint(*meta["victims"]),
            "safe": False, "fake": False,
        })

    # 20% duplicates: duplicate random rows with slight variation
    dupes = int(n * 0.2)
    for i in range(dupes):
        src = rows[rng.randrange(len(rows))]
        if src["fake"] or src["safe"]:
            continue
        dup = dict(src)
        dup["id"] = n + i
        dup["text"] = src["text"].replace("NOW", "NOW!!!").replace("help", "help please")
        rows.append(dup)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10000)
    parser.add_argument("--out", type=str, default="reports.jsonl")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    rows = generate(args.n, args.seed)
    with open(args.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    fake = sum(1 for r in rows if r["fake"])
    safe = sum(1 for r in rows if r["safe"])
    print(f"generated {len(rows)} reports -> {args.out} (fake={fake}, safe={safe})")


if __name__ == "__main__":
    main()