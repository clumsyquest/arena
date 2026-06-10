"""Classement Elo mondial, recalculé depuis 1872 (méthodologie eloratings.net).

Chaque match de l'histoire ajuste la force des deux équipes : pondéré par
l'importance de la compétition, l'écart de buts et l'avantage du terrain.
"""

import numpy as np

START_RATING = 1500.0
HOME_ADV = 100.0  # bonus Elo du terrain (hors terrain neutre)

# Grandes phases finales continentales -> K = 50
_CONTINENTAL = {
    "uefa euro",
    "copa américa",
    "african cup of nations",
    "afc asian cup",
    "gold cup",
    "concacaf championship",
    "oceania nations cup",
    "confederations cup",
    "fifa confederations cup",
}


def k_factor(tournament):
    """Poids du match selon l'enjeu (échelle eloratings.net)."""
    t = str(tournament).lower()
    if t == "fifa world cup":
        return 60.0
    if t in _CONTINENTAL:
        return 50.0
    if "qualification" in t or "nations league" in t:
        return 40.0
    if t == "friendly":
        return 20.0
    return 30.0


def compute_elo(matches, return_history=False):
    """Rejoue toute l'histoire du football et renvoie les ratings finaux.

    Si return_history, renvoie aussi les ratings PRÉ-match de chaque ligne
    (nécessaires pour entraîner le modèle de buts sans fuite du futur).
    """
    ratings = {}
    n = len(matches)
    pre_home = np.empty(n) if return_history else None
    pre_away = np.empty(n) if return_history else None

    cols = zip(
        matches["home_team"].to_numpy(),
        matches["away_team"].to_numpy(),
        matches["home_score"].to_numpy(),
        matches["away_score"].to_numpy(),
        matches["tournament"].to_numpy(),
        matches["neutral"].to_numpy(),
    )
    for i, (home, away, hs, aw, tourn, neutral) in enumerate(cols):
        ra = ratings.get(home, START_RATING)
        rb = ratings.get(away, START_RATING)
        if return_history:
            pre_home[i] = ra
            pre_away[i] = rb

        dr = ra - rb + (0.0 if neutral else HOME_ADV)
        expected = 1.0 / (1.0 + 10.0 ** (-dr / 400.0))
        actual = 1.0 if hs > aw else (0.5 if hs == aw else 0.0)

        diff = abs(hs - aw)
        g = 1.0 if diff <= 1 else (1.5 if diff == 2 else (11.0 + diff) / 8.0)

        delta = k_factor(tourn) * g * (actual - expected)
        ratings[home] = ra + delta
        ratings[away] = rb - delta

    if return_history:
        return ratings, pre_home, pre_away
    return ratings


def top(ratings, n=20):
    """Les n équipes les mieux classées."""
    return sorted(ratings.items(), key=lambda kv: -kv[1])[:n]
