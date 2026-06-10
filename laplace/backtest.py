"""Le serment d'honnêteté : mesurer la superpuissance sur le passé.

On remonte le temps : le démon n'a le droit de voir QUE les matchs antérieurs
à chaque Coupe du Monde, puis il prédit tous les matchs du tournoi. On compare
ses probabilités à la réalité (log-loss, score de Brier, précision).
"""

import numpy as np

from laplace import build_oracle
from laplace.data import played
from laplace.elo import top

CUPS = {
    2014: ("2014-06-12", "2014-07-14", "Germany"),
    2018: ("2018-06-14", "2018-07-16", "France"),
    2022: ("2022-11-20", "2022-12-19", "Argentina"),
}


def backtest(year):
    start, end, champion = CUPS[year]
    df = played()
    cup = df[
        (df["tournament"] == "FIFA World Cup")
        & (df["date"] >= np.datetime64(start))
        & (df["date"] <= np.datetime64(end))
    ]
    oracle = build_oracle(as_of=start)

    probs, outcomes = [], []
    for row in cup.itertuples():
        h = 0 if row.neutral else 1
        p = oracle.match(row.home_team, row.away_team, h)
        probs.append([p["p_win"], p["p_draw"], p["p_loss"]])
        outcomes.append(
            0 if row.home_score > row.away_score else (1 if row.home_score == row.away_score else 2)
        )
    probs = np.array(probs)
    outcomes = np.array(outcomes)
    n = len(outcomes)

    picked = probs[np.arange(n), outcomes]
    logloss = float(-np.mean(np.log(np.clip(picked, 1e-12, 1))))
    onehot = np.eye(3)[outcomes]
    brier = float(np.mean(np.sum((probs - onehot) ** 2, axis=1)))
    accuracy = float(np.mean(np.argmax(probs, axis=1) == outcomes))

    # Référence naïve : probabilités uniformes (1/3, 1/3, 1/3).
    uniform_logloss = float(np.log(3.0))
    uniform_brier = 2.0 / 3.0

    # Référence « taux de base historiques » (calculés AVANT le tournoi).
    hist = df[df["date"] < np.datetime64(start)].tail(4000)
    rates = np.array([
        float((hist["home_score"] > hist["away_score"]).mean()),
        float((hist["home_score"] == hist["away_score"]).mean()),
        float((hist["home_score"] < hist["away_score"]).mean()),
    ])
    base_logloss = float(-np.mean(np.log(rates[outcomes])))

    pre_elo = top(oracle.ratings, 200)
    champ_rank = next(i + 1 for i, (t, _) in enumerate(pre_elo) if t == champion)

    return {
        "year": year,
        "n_matches": n,
        "logloss": logloss,
        "brier": brier,
        "accuracy": accuracy,
        "uniform_logloss": uniform_logloss,
        "uniform_brier": uniform_brier,
        "base_logloss": base_logloss,
        "champion": champion,
        "champion_elo_rank": champ_rank,
        "pre_top5": pre_elo[:5],
    }
