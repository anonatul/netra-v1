"""Layer 1 rules unit tests — multilingual extraction."""
from app.extraction.rules import extract


def test_hinglish_flood_elderly_child_trapped():
    r = extract("Paani kamar tak aa gaya hai, dadi aur bachcha chhat par phans gaye")
    assert r["severity"] == "HIGH"
    assert r["disaster"] == "FLOOD"
    assert r["attributes"]["elderly"]["value"] is True
    assert r["attributes"]["child"]["value"] is True
    assert r["attributes"]["trapped"]["value"] is True
    assert r["attributes"]["water_rising"]["value"] is True
    assert r["safe"] is False


def test_english_earthquake():
    r = extract("Building collapsed after earthquake, people stuck inside")
    assert r["disaster"] == "EARTHQUAKE"
    assert r["severity"] == "HIGH"
    assert r["attributes"]["trapped"]["value"] is True


def test_english_flood_mobility():
    r = extract("Water rising fast, we are trapped on rooftop, grandmother with us cannot walk")
    assert r["disaster"] == "FLOOD"
    assert r["attributes"]["elderly"]["value"] is True
    assert r["attributes"]["mobility_issue"]["value"] is True


def test_safe_message_no_incident():
    r = extract("we are safe now, reached shelter, all family fine")
    assert r["safe"] is True
    assert not r["attributes"]


def test_fake_sos_flagged():
    r = extract("this is a prank, testing the app, not real emergency")
    assert r["fake"] is True


def test_victim_hint():
    r = extract("5 log chhat par phans gaye, paani badh raha hai")
    assert r["victim_hint"] == 5


def test_empty_text_unknown():
    r = extract("")
    assert r["severity"] == "UNKNOWN"
    assert r["disaster"] == "UNKNOWN"