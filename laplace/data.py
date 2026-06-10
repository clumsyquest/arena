"""LA MÉMOIRE — tous les matchs internationaux depuis 1872.

Source : https://github.com/martj42/international_results (domaine public,
mis à jour en continu, y compris le calendrier de la Coupe du Monde 2026).
"""

import os
import urllib.request

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RESULTS_CSV = os.path.join(DATA_DIR, "results.csv")
SHOOTOUTS_CSV = os.path.join(DATA_DIR, "shootouts.csv")

BASE_URL = "https://raw.githubusercontent.com/martj42/international_results/master"

_cache = {}


def update():
    """Re-télécharge les données fraîches (résultats + tirs au but)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    urllib.request.urlretrieve(f"{BASE_URL}/results.csv", RESULTS_CSV)
    urllib.request.urlretrieve(f"{BASE_URL}/shootouts.csv", SHOOTOUTS_CSV)
    _cache.clear()
    return RESULTS_CSV


def load(refresh=False):
    """Charge le jeu de données complet (matchs joués + calendrier à venir)."""
    if refresh or not os.path.exists(RESULTS_CSV):
        update()
    if "df" not in _cache:
        df = pd.read_csv(RESULTS_CSV)
        df["date"] = pd.to_datetime(df["date"])
        _cache["df"] = df
    return _cache["df"]


def played(before=None):
    """Matchs effectivement joués (scores connus), triés chronologiquement."""
    df = load()
    out = df.dropna(subset=["home_score", "away_score"]).copy()
    if before is not None:
        out = out[out["date"] < pd.Timestamp(before)]
    out["home_score"] = out["home_score"].astype(int)
    out["away_score"] = out["away_score"].astype(int)
    return out.sort_values("date").reset_index(drop=True)


def fixtures(start=None, end=None, tournament="FIFA World Cup"):
    """Matchs à venir (scores inconnus) — le calendrier réel du Mondial."""
    df = load()
    out = df[df["home_score"].isna()].copy()
    if tournament:
        out = out[out["tournament"] == tournament]
    if start is not None:
        out = out[out["date"] >= pd.Timestamp(start)]
    if end is not None:
        out = out[out["date"] <= pd.Timestamp(end)]
    return out.sort_values("date").reset_index(drop=True)
