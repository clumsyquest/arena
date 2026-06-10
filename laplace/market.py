"""LE VOLEUR DE CERVEAUX — capture les cotes du marché mondial et les fusionne.

Les cotes des bookmakers agrègent des millions de parieurs, les compos, les
blessures, les rumeurs de vestiaire. Ce module les capture, retire la marge
du bookmaker, les confronte au démon, et signale les FAILLES : les matchs où
le démon et le marché divergent fortement.

Sources, dans l'ordre :
  1. GRATUIT SANS CLÉ : ESPN + Sofascore (cotes publiques, agrégées)
  2. Optionnel : The Odds API si ODDS_API_KEY est définie (dizaines de books)

Nécessite une session dont l'environnement autorise le réseau (All domains).
"""

import json
import os
import time
import urllib.error
import urllib.request

BASE = "https://api.the-odds-api.com/v4"

UNLOCK_HELP = """\
🔒 Le Voleur de Cerveaux est en cage (réseau fermé).
   ⚠ La politique réseau ne s'applique qu'aux NOUVELLES sessions :
   si tu viens de passer l'environnement en 'All domains', il faut
   DÉMARRER UNE NOUVELLE SESSION pour que la porte s'ouvre vraiment.
   Doc : https://code.claude.com/docs/en/claude-code-on-the-web
   (Aucune clé requise : sources gratuites ESPN/Sofascore intégrées.)
"""

# Noms des sources -> noms du jeu de données
_ALIASES = {
    "USA": "United States",
    "Korea Republic": "South Korea",
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "Turkiye": "Turkey",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cabo Verde": "Cape Verde",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Congo DR": "DR Congo",
    "DR Congo": "DR Congo",
    "IR Iran": "Iran",
}


def _norm(name):
    return _ALIASES.get(name, name)


def _get(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _amer_to_dec(ml):
    ml = float(ml)
    return 1.0 + (ml / 100.0 if ml > 0 else 100.0 / abs(ml))


def _frac_to_dec(frac):
    num, den = str(frac).split("/")
    return 1.0 + float(num) / float(den)


def _devig(d1, dx, d2):
    inv = [1.0 / d1, 1.0 / dx, 1.0 / d2]
    s = sum(inv)
    return tuple(v / s for v in inv)


# ---------------------------------------------------------------- ESPN (gratuit)

def fetch_espn(date_from, date_to):
    """Cotes ESPN BET du Mondial (ligue fifa.world), sans clé."""
    d1, d2 = date_from.replace("-", ""), date_to.replace("-", "")
    data = _get(
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/"
        f"scoreboard?dates={d1}-{d2}"
    )
    out = []
    for ev in data.get("events", []):
        try:
            comp = ev["competitions"][0]
            teams = {c["homeAway"]: c["team"]["displayName"] for c in comp["competitors"]}
            for od in comp.get("odds", []):
                h = od.get("homeTeamOdds", {}).get("moneyLine")
                a = od.get("awayTeamOdds", {}).get("moneyLine")
                x = od.get("drawOdds", {}).get("moneyLine")
                if h and a and x:
                    out.append({
                        "home": _norm(teams["home"]),
                        "away": _norm(teams["away"]),
                        "start": ev.get("date", ""),
                        "source": "ESPN",
                        "p": _devig(_amer_to_dec(h), _amer_to_dec(x), _amer_to_dec(a)),
                    })
                    break
        except (KeyError, IndexError, ValueError, ZeroDivisionError):
            continue
    return out


# ----------------------------------------------------------- Sofascore (gratuit)

def fetch_sofascore(date, max_events=24, pause=0.4):
    """Cotes Sofascore du Mondial (uniqueTournament 16), sans clé."""
    data = _get(f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}")
    events = [
        e for e in data.get("events", [])
        if e.get("tournament", {}).get("uniqueTournament", {}).get("id") == 16
    ][:max_events]
    out = []
    for e in events:
        try:
            time.sleep(pause)
            odds = _get(f"https://api.sofascore.com/api/v1/event/{e['id']}/odds/1/all")
            ft = next(
                (m for m in odds.get("markets", [])
                 if m.get("marketName", "").lower() in ("full time", "1x2") and not m.get("isLive")),
                None,
            )
            if not ft:
                continue
            ch = {c["name"]: _frac_to_dec(c["fractionalValue"]) for c in ft["choices"]}
            if {"1", "X", "2"} <= set(ch):
                out.append({
                    "home": _norm(e["homeTeam"]["name"]),
                    "away": _norm(e["awayTeam"]["name"]),
                    "start": str(e.get("startTimestamp", "")),
                    "source": "Sofascore",
                    "p": _devig(ch["1"], ch["X"], ch["2"]),
                })
        except (KeyError, StopIteration, ValueError, ZeroDivisionError,
                urllib.error.URLError, urllib.error.HTTPError):
            continue
    return out


# -------------------------------------------------- The Odds API (clé optionnelle)

def fetch_oddsapi():
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        return []
    sports = _get(f"{BASE}/sports/?apiKey={key}")
    out = []
    for s in sports:
        if "world_cup" not in s["key"] or "winner" in s["key"]:
            continue
        for ev in _get(f"{BASE}/sports/{s['key']}/odds/?apiKey={key}&regions=eu&markets=h2h&oddsFormat=decimal"):
            probs = []
            for bk in ev.get("bookmakers", []):
                for mk in bk.get("markets", []):
                    if mk["key"] != "h2h":
                        continue
                    o = {oc["name"]: oc["price"] for oc in mk["outcomes"]}
                    draw = next((k for k in o if k.lower() == "draw"), None)
                    if draw and ev["home_team"] in o and ev["away_team"] in o:
                        probs.append(_devig(o[ev["home_team"]], o[draw], o[ev["away_team"]]))
            if probs:
                n = len(probs)
                out.append({
                    "home": _norm(ev["home_team"]),
                    "away": _norm(ev["away_team"]),
                    "start": ev.get("commence_time", ""),
                    "source": f"OddsAPI×{n}",
                    "p": tuple(sum(p[i] for p in probs) / n for i in range(3)),
                })
    return out


# ------------------------------------------------------------------- agrégation

def fetch_market(days_ahead=3):
    """Toutes les sources disponibles, moyennées par affiche."""
    from datetime import date, timedelta

    today = date.today()
    until = today + timedelta(days=days_ahead)
    quotes, errors = [], []
    for fn in (
        lambda: fetch_espn(str(today), str(until)),
        lambda: [q for d in range(days_ahead + 1)
                 for q in fetch_sofascore(str(today + timedelta(days=d)))],
        fetch_oddsapi,
    ):
        try:
            quotes.extend(fn())
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            errors.append(str(e))
    if not quotes:
        raise PermissionError(UNLOCK_HELP + ("\n   Détail : " + " | ".join(errors[:2]) if errors else ""))

    merged = {}
    for q in quotes:
        merged.setdefault((q["home"], q["away"]), []).append(q)
    out = []
    for (h, a), qs in merged.items():
        out.append({
            "home": h,
            "away": a,
            "start": qs[0]["start"],
            "n_bookmakers": len(qs),
            "sources": "+".join(sorted({q["source"] for q in qs})),
            "p_market": tuple(sum(q["p"][i] for q in qs) / len(qs) for i in range(3)),
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
