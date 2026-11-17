import json, os
from datetime import date
from garmin_personal_api import GarminPersonalApiClient, PersonalApiAuthenticator

heute = date.today()
monatsstart = heute.replace(day=1)
jahresstart = heute.replace(month=1, day=1)

# Falls du die Liste vorher angepasst hast (z. B. Rad Indoor), nimm deine Version
SPORTARTEN = [
    ("rad",        "Rad",           "🚴", ["cycling", "biking", "bike", "ride", "indoor_cycling"], [], "km"),
    ("laufen",     "Laufen",        "🏃", ["running"],                           [], "km"),
    ("schwimmen",  "Schwimmen",     "🏊", ["swimming"],                          [], "km"),
    ("wandern",    "Wandern",       "🥾", ["hiking"],                            [], "km"),
    ("gehen",      "Gehen",         "🚶", ["walking"],                           [], "km"),
    ("kraft",      "Krafttraining", "🏋️", ["strength"],                          [], "zeit"),
    ("yoga",       "Yoga/Pilates",  "🧘", ["yoga", "pilates"],                   [], "zeit"),
]


def sammle(client, von, bis):
    stats = {s[0]: {"meter": 0.0, "sekunden": 0.0, "anzahl": 0} for s in SPORTARTEN}
    offen = {}
    offset = 0
    while True:
        seite = client.search_activities(
            start=offset, limit=100,
            start_date=von.isoformat(), end_date=bis.isoformat(),
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
                offen[typ] = offen.get(typ, 0) + 1
        offset += 100
    return stats, offen


def baue_json(stats, zeitraum):
    return {
        "monat": zeitraum,
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


with PersonalApiAuthenticator() as auth:
    token = auth.obtain_token(os.environ["GARMIN_PERSONAL_API_KEY"])

with GarminPersonalApiClient(token.access_token) as client:
    monat, offen_m = sammle(client, monatsstart, heute)
    jahr, offen_j = sammle(client, jahresstart, heute)

print("Nicht zugeordnete Typen (Jahr):", offen_j)

with open("stats.json", "w") as f:
    json.dump(baue_json(monat, heute.strftime("%m/%Y")), f, ensure_ascii=False)

with open("stats_jahr.json", "w") as f:
    json.dump(baue_json(jahr, str(heute.year)), f, ensure_ascii=False)
