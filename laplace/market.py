"""LE VOLEUR DE CERVEAUX — capture les cotes du marché mondial et les fusionne.

Les cotes des bookmakers agrègent des millions de parieurs, les compos, les
blessures, les rumeurs de vestiaire. Ce module les capture (The Odds API),
retire la marge du bookmaker, les confronte au démon, et signale les FAILLES :
les matchs où le démon et le marché divergent fortement.

Activation (à faire par le commandant, voir README) :
  1. Réseau de l'environnement ouvert à api.the-odds-api.com
  2. Clé gratuite -> variable d'environnement ODDS_API_KEY
"""

import json
import os
import urllib.error
import urllib.request

BASE = "https://api.the-odds-api.com/v4"

UNLOCK_HELP = """\
🔒 Le Voleur de Cerveaux est en cage. Pour l'activer :
   1. Réglages de l'environnement Claude Code (web) → Network access →
      'All domains' (ou ajouter api.the-odds-api.com)
      Doc : https://code.claude.com/docs/en/claude-code-on-the-web
   2. Clé gratuite sur https://the-odds-api.com → variable ODDS_API_KEY
"""

# Noms The Odds API -> noms du jeu de données
_ALIASES = {
    "USA": "United States",
    "South Korea": "South Korea",
    "Korea Republic": "South Korea",
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Cabo Verde": "Cape Verde",
    "Côte d'Ivoire": "Ivory Coast",
    "Congo DR": "DR Congo",
}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "laplace-demon/2.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def fetch_market():
    """Cotes 1-N-2 du Mondial, dé-margées en probabilités par bookmaker moyen."""
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        raise PermissionError(UNLOCK_HELP)
    try:
        sports = _get(f"{BASE}/sports/?apiKey={key}")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        raise PermissionError(UNLOCK_HELP + f"\n   (réseau : {e})") from e

    wc_keys = [s["key"] for s in sports if "world_cup" in s["key"] and "winner" not in s["key"]]
    if not wc_keys:
        raise LookupError("Aucun marché Coupe du Monde ouvert chez The Odds API pour l'instant.")

    out = []
    for sk in wc_keys:
        events = _get(f"{BASE}/sports/{sk}/odds/?apiKey={key}&regions=eu&markets=h2h&oddsFormat=decimal")
        for ev in events:
            home = _ALIASES.get(ev["home_team"], ev["home_team"])
            away = _ALIASES.get(ev["away_team"], ev["away_team"])
            probs = []
            for bk in ev.get("bookmakers", []):
                for mk in bk.get("markets", []):
                    if mk["key"] != "h2h":
                        continue
                    o = {oc["name"]: oc["price"] for oc in mk["outcomes"]}
                    if len(o) == 3 and all(v > 1.0 for v in o.values()):
                        inv = {k: 1.0 / v for k, v in o.items()}
                        s = sum(inv.values())
                        draw_key = next((k for k in o if k.lower() == "draw"), None)
                        if draw_key and ev["home_team"] in o and ev["away_team"] in o:
                            probs.append((
                                inv[ev["home_team"]] / s,
                                inv[draw_key] / s,
                                inv[ev["away_team"]] / s,
                            ))
            if probs:
                n = len(probs)
                out.append({
                    "home": home,
                    "away": away,
                    "start": ev.get("commence_time", ""),
                    "n_bookmakers": n,
                    "p_market": tuple(sum(p[i] for p in probs) / n for i in range(3)),
                })
    return out


def fuse(p_demon, p_market, w_market=0.7):
    """Fusion log-linéaire marché/démon (le marché domine, cf. littérature)."""
    import numpy as np

    pd_ = np.clip(np.asarray(p_demon, float), 1e-9, 1)
    pm = np.clip(np.asarray(p_market, float), 1e-9, 1)
    f = pm**w_market * pd_ ** (1 - w_market)
    return tuple(f / f.sum())


def edges(oracle, threshold=0.08):
    """Les failles : là où le démon défie le marché mondial."""
    rows = []
    for ev in fetch_market():
        try:
            p = oracle.match(ev["home"], ev["away"], 0)
        except ValueError:
            continue
        p_demon = (p["p_win"], p["p_draw"], p["p_loss"])
        gaps = [p_demon[i] - ev["p_market"][i] for i in range(3)]
        i_max = max(range(3), key=lambda i: abs(gaps[i]))
        rows.append({
            **ev,
            "p_demon": p_demon,
            "p_fused": fuse(p_demon, ev["p_market"]),
            "gap": gaps[i_max],
            "gap_on": ["1", "N", "2"][i_max],
            "is_edge": abs(gaps[i_max]) >= threshold,
        })
    return sorted(rows, key=lambda r: -abs(r["gap"]))
