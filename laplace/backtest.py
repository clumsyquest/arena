"""Le serment d'honnêteté : mesurer la superpuissance sur le passé.

On remonte le temps : le démon n'a le droit de voir QUE les matchs antérieurs
à chaque match prédit. Deux modes mesurés :
  · FIGÉ   — forces gelées à la veille du tournoi (l'ancienne école)
  · VIVANT — l'Elo se met à jour match après match PENDANT le tournoi
             (aucune fuite : la prédiction du match m n'utilise que les
             matchs antérieurs à m ; c'est le mode de production réel)
"""

import numpy as np

from laplace.data import played
from laplace.elo import compute_elo, top
from laplace.goals import fit_goal_model

CUPS = {
    2014: ("2014-06-12", "2014-07-14", "Germany"),
    2018: ("2018-06-14", "2018-07-16", "France"),
    2022: ("2022-11-20", "2022-12-19", "Argentina"),
}


def _probs(model, ra, rb, h):
    m = model.score_matrix(ra, rb, h)
    return [float(np.tril(m, -1).sum()), float(np.trace(m)), float(np.triu(m, 1).sum())]


def backtest(year):
    start, end, champion = CUPS[year]
    df = played()
    ratings_now, pre_h, pre_a = compute_elo(df, return_history=True)

    dates = df["date"].to_numpy()
    before = dates < np.datetime64(start)
    in_cup = (
        (df["tournament"] == "FIFA World Cup").to_numpy()
        & (dates >= np.datetime64(start))
        & (dates <= np.datetime64(end))
    )

    model = fit_goal_model(df[before], pre_h[before], pre_a[before])
    frozen = compute_elo(df[before])

    probs_live, probs_frozen, outcomes = [], [], []
    for i in np.flatnonzero(in_cup):
        row = df.iloc[i]
        h = 0 if row["neutral"] else 1
        probs_live.append(_probs(model, pre_h[i], pre_a[i], h))
        probs_frozen.append(_probs(model, frozen[row["home_team"]], frozen[row["away_team"]], h))
        hs, aw = row["home_score"], row["away_score"]
        outcomes.append(0 if hs > aw else (1 if hs == aw else 2))

    probs_live = np.array(probs_live)
    probs_frozen = np.array(probs_frozen)
    outcomes = np.array(outcomes)
    n = len(outcomes)

    def metrics(p):
        picked = p[np.arange(n), outcomes]
        logloss = float(-np.mean(np.log(np.clip(picked, 1e-12, 1))))
        brier = float(np.mean(np.sum((p - np.eye(3)[outcomes]) ** 2, axis=1)))
        acc = float(np.mean(np.argmax(p, axis=1) == outcomes))
        return logloss, brier, acc

    logloss, brier, accuracy = metrics(probs_live)
    logloss_frozen, _, _ = metrics(probs_frozen)

    # Référence « taux de base historiques » (calculés AVANT le tournoi).
    hist = df[before].tail(4000)
    rates = np.array([
        float((hist["home_score"] > hist["away_score"]).mean()),
        float((hist["home_score"] == hist["away_score"]).mean()),
        float((hist["home_score"] < hist["away_score"]).mean()),
    ])
    base_logloss = float(-np.mean(np.log(rates[outcomes])))

    pre_elo = top(frozen, 200)
    champ_rank = next(i + 1 for i, (t, _) in enumerate(pre_elo) if t == champion)

    return {
        "year": year,
        "n_matches": n,
        "logloss": logloss,
        "logloss_frozen": logloss_frozen,
        "brier": brier,
        "accuracy": accuracy,
        "uniform_logloss": float(np.log(3.0)),
        "uniform_brier": 2.0 / 3.0,
        "base_logloss": base_logloss,
        "champion": champion,
        "champion_elo_rank": champ_rank,
        "pre_top5": pre_elo[:5],
    }
