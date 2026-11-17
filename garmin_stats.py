import json, os
from datetime import date
from garmin_personal_api import GarminPersonalApiClient, PersonalApiAuthenticator

heute = date.today()
start = heute.replace(day=1)

with PersonalApiAuthenticator() as auth:
    token = auth.obtain_token(os.environ["GARMIN_PERSONAL_API_KEY"])

LAUFEN = {"running", "trail_running", "treadmill_running"}
RAD = {"cycling", "road_biking", "mountain_biking", "gravel_cycling", "indoor_cycling"}

km = {"laufen": 0.0, "rad": 0.0}
with GarminPersonalApiClient(token.access_token) as client:
    offset = 0
    while True:
        seite = client.search_activities(
            start=offset, limit=100,
            start_date=start.isoformat(), end_date=heute.isoformat(),
        )
        if not seite:
            break
        for a in seite:
            typ = a["activityType"]["typeKey"]
            meter = a.get("distance") or 0
            if typ in LAUFEN:
                km["laufen"] += meter / 1000
            elif typ in RAD:
                km["rad"] += meter / 1000
        offset += 100

with open("stats.json", "w") as f:
    json.dump({
        "monat": heute.strftime("%m/%Y"),
        "laufen_km": round(km["laufen"], 1),
        "rad_km": round(km["rad"], 1),
        "aktualisiert": heute.isoformat(),
    }, f)
