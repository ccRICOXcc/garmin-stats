import json, os
from datetime import date
from garmin_personal_api import GarminPersonalApiClient, PersonalApiAuthenticator

heute = date.today()
start = heute.replace(day=1)

# (key, Anzeigename, Emoji, Stichwörter im Typ, auszuschließen, Modus)
# Modus "km" = Distanz anzeigen, "zeit" = Dauer anzeigen
SPORTARTEN = [
    ("rad",        "Rad",         "🚴", ["cycling", "biking", "bike", "ride"], ["indoor", "virtual"], "km"),
    ("laufen",     "Laufen",      "🏃", ["running"],                           [],                    "km"),
    ("schwimmen",  "Schwimmen",   "🏊", ["swimming"],                          [],                    "km"),
    ("wandern",    "Wandern",     "🥾", ["hiking"],                            [],                    "km"),
    ("gehen",      "Gehen",       "🚶", ["walking"],                           [],                    "km"),
    ("kraft",      "Krafttraining", "🏋️", ["strength"],                        [],                    "zeit"),
    ("yoga",       "Yoga/Pilates", "🧘", ["yoga", "pilates"],                  [],                    "zeit"),
]

stats = {s[0]: {"meter": 0.0, "sekunden": 0.0, "anzahl": 0} for s in SPORTARTEN}
nicht_zugeordnet = {}

with PersonalApiAuthenticator() as auth:
    token = auth.obtain_token(os.environ["GARMIN_PERSONAL_API_KEY"])

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
            sekunden = a.get("duration") or 0
            for key, name, emoji, woerter, ausschluss, modus in SPORTARTEN:
                if any(w in typ for w in woerter) and not any(x in typ for x in ausschluss):
                    stats[key]["meter"] += meter
                    stats[key]["sekunden"] += sekunden
                    stats[key]["anzahl"] += 1
                    break
            else:
                nicht_zugeordnet[typ] = nicht_zugeordnet.get(typ, 0) + 1
        offset += 100

print("Nicht zugeordnete Typen:", nicht_zugeordnet)

ausgabe = {
    "monat": heute.strftime("%m/%Y"),
    "aktualisiert": heute.isoformat(),
    "sportarten": [
        {
            "key": key, "label": name, "emoji": emoji, "modus": modus,
            "km": round(stats[key]["meter"] / 1000, 1),
            "stunden": round(stats[key]["sekunden"] / 3600, 1),
            "anzahl": stats[key]["anzahl"],
        }
        for key, name, emoji, _, _, modus in SPORTARTEN
    ],
}
with open("stats.json", "w") as f:
    json.dump(ausgabe, f, ensure_ascii=False)
