"""LA TRANSCENDANCE — fusion des trois cerveaux en une sur-intelligence.

Trois visions du même match :
  · L'HISTORIEN  — Elo (mémoire totale depuis 1872) → Dixon-Coles
  · L'ANATOMISTE — attaque/défense par équipe, demi-vie 4 ans (la classe)
  · LE FIÉVREUX  — attaque/défense par équipe, demi-vie 15 mois (la forme)

Fusion log-linéaire des distributions de scores :  M ∝ Π Mᵢ^wᵢ  (cellule à
cellule, renormalisée). Les poids w sont appris en rejouant les grands
tournois du passé SANS voir le futur, et validés en leave-one-out.
"""

import numpy as np

from laplace.data import played
from laplace.predict import Oracle, resolve

# (étiquette, nom dans les données, début, fin)
TOURNAMENTS = [
    ("CDM 2010", "FIFA World Cup", "2010-06-11", "2010-07-12"),
    ("CDM 2014", "FIFA World Cup", "2014-06-12", "2014-07-14"),
    ("CDM 2018", "FIFA World Cup", "2018-06-14", "2018-07-16"),
    ("CDM 2022", "FIFA World Cup", "2022-11-20", "2022-12-19"),
    ("Asie 2024", "AFC Asian Cup", "2024-01-12", "2024-02-11"),
    ("Euro 2024", "UEFA Euro", "2024-06-14", "2024-07-15"),
    ("Copa 2024", "Copa América", "2024-06-20", "2024-07-15"),
    ("Gold Cup 2025", "Gold Cup", "2025-06-14", "2025-07-07"),
    ("CAN 2025", "African Cup of Nations", "2025-12-21", "2026-01-19"),
]

MAX_GOALS = 10


class EnsembleOracle:
    """Même interface que Oracle, mais trois cerveaux fusionnés."""

    def __init__(self, brains, weights, elo_ratings):
        self.brains = brains          # objets avec .score_matrix(a, b, h)
        self.weights = np.asarray(weights, dtype=float)
        self.ratings = elo_ratings    # Elo : pour l'affichage et les tirs au but

    def score_matrix(self, team_a, team_b, home_ind=0, max_goals=MAX_GOALS):
        logm = np.zeros((max_goals + 1, max_goals + 1))
        for brain, w in zip(self.brains, self.weights):
            if w <= 0:
                continue
            m = brain.score_matrix(team_a, team_b, home_ind, max_goals)
            logm += w * np.log(np.clip(m, 1e-14, 1.0))
        m = np.exp(logm - logm.max())
        return m / m.sum()

    def lambdas(self, team_a, team_b, home_ind=0):
        m = self.score_matrix(team_a, team_b, home_ind)
        g = np.arange(m.shape[0])
        return float(m.sum(axis=1) @ g), float(m.sum(axis=0) @ g)

    def match(self, team_a, team_b, home_ind=0, max_goals=MAX_GOALS):
        a = resolve(team_a, self.ratings)
        b = resolve(team_b, self.ratings)
        m = self.score_matrix(a, b, home_ind, max_goals)
        la, lb = self.lambdas(a, b, home_ind)
        flat = [(int(i), int(j), float(m[i, j])) for i in range(m.shape[0]) for j in range(m.shape[1])]
        flat.sort(key=lambda t: -t[2])
        return {
            "team_a": a,
            "team_b": b,
            "elo_a": self.ratings.get(a, float("nan")),
            "elo_b": self.ratings.get(b, float("nan")),
            "lambda_a": la,
            "lambda_b": lb,
            "p_win": float(np.tril(m, -1).sum()),
            "p_draw": float(np.trace(m)),
            "p_loss": float(np.triu(m, 1).sum()),
            "top_scores": flat[:6],
            "matrix": m,
        }


class _EloBrain:
    """Adaptateur : le cerveau Elo v1 avec interface par noms d'équipes."""

    def __init__(self, oracle):
        self.oracle = oracle

    def score_matrix(self, a, b, h=0, max_goals=MAX_GOALS):
        return self.oracle.score_matrix(a, b, h, max_goals)


def build_brains(as_of=None, verbose=False):
    """Construit les trois cerveaux, n'utilisant QUE les matchs avant as_of."""
    from laplace import build_oracle
    from laplace.teamdc import fit_teamdc

    df = played(before=as_of)
    historien = _EloBrain(build_oracle(as_of=as_of, verbose=verbose))
    anatomiste = fit_teamdc(df, half_life=4.0, window_years=12.0, verbose=verbose)
    fievreux = fit_teamdc(df, half_life=1.25, window_years=5.0, verbose=verbose)
    return [historien, anatomiste, fievreux], historien.oracle.ratings


def _outcome_probs(matrix):
    return np.array([
        float(np.tril(matrix, -1).sum()),
        float(np.trace(matrix)),
        float(np.triu(matrix, 1).sum()),
    ])


def _tournament_matches(label):
    df = played()
    for lab, name, start, end in TOURNAMENTS:
        if lab == label:
            sel = df[
                (df["tournament"] == name)
                & (df["date"] >= np.datetime64(start))
                & (df["date"] <= np.datetime64(end))
            ]
            return sel, start
    raise KeyError(label)


def collect_predictions(verbose=False):
    """Pour chaque tournoi : matrices des 3 cerveaux (entraînés avant) + issues."""
    bank = {}
    for label, _, _, _ in TOURNAMENTS:
        cup, start = _tournament_matches(label)
        brains, _ = build_brains(as_of=start)
        mats, outs = [], []
        for row in cup.itertuples():
            h = 0 if row.neutral else 1
            mats.append([b.score_matrix(row.home_team, row.away_team, h) for b in brains])
            outs.append(0 if row.home_score > row.away_score else (1 if row.home_score == row.away_score else 2))
        bank[label] = (mats, np.array(outs))
        if verbose:
            print(f"  [{label}] {len(outs)} matchs prédits par les 3 cerveaux")
    return bank


def _pooled_logloss(mats, outs, w):
    ll = 0.0
    for triple, y in zip(mats, outs):
        logm = sum(wi * np.log(np.clip(m, 1e-14, 1.0)) for m, wi in zip(triple, w))
        m = np.exp(logm - logm.max())
        m /= m.sum()
        p = _outcome_probs(m)[y]
        ll -= np.log(max(p, 1e-12))
    return ll / len(outs)


def _grid(step=0.05):
    ws = []
    k = round(1 / step)
    for i in range(k + 1):
        for j in range(k + 1 - i):
            ws.append((i * step, j * step, 1 - i * step - j * step))
    return ws


def optimise_weights(bank, exclude=None):
    """Poids minimisant la log-loss cumulée des tournois (hors `exclude`)."""
    labels = [l for l in bank if l != exclude]
    best_w, best = None, np.inf
    for w in _grid():
        tot, n = 0.0, 0
        for l in labels:
            mats, outs = bank[l]
            tot += _pooled_logloss(mats, outs, w) * len(outs)
            n += len(outs)
        if tot / n < best:
            best, best_w = tot / n, w
    return best_w, best


def proof(verbose=True):
    """Le duel : chaque cerveau seul vs la fusion (poids leave-one-out)."""
    if verbose:
        print("  Reconstruction des cerveaux avant chacun des 9 tournois...")
    bank = collect_predictions(verbose=verbose)
    rows = []
    for label in bank:
        mats, outs = bank[label]
        solo = [
            _pooled_logloss(mats, outs, [1, 0, 0]),
            _pooled_logloss(mats, outs, [0, 1, 0]),
            _pooled_logloss(mats, outs, [0, 0, 1]),
        ]
        w_loo, _ = optimise_weights(bank, exclude=label)
        fused = _pooled_logloss(mats, outs, w_loo)
        rows.append({
            "label": label,
            "n": len(outs),
            "historien": solo[0],
            "anatomiste": solo[1],
            "fievreux": solo[2],
            "fusion": fused,
            "w_loo": w_loo,
        })
    w_final, _ = optimise_weights(bank)
    return rows, w_final


def build_ensemble(as_of=None, weights=None, verbose=False):
    """L'oracle transcendé, prêt pour 2026."""
    brains, elo = build_brains(as_of=as_of, verbose=verbose)
    if weights is None:
        weights = DEFAULT_WEIGHTS
    return EnsembleOracle(brains, weights, elo)


# Poids appris sur les 9 tournois majeurs 2010-2026 (cf. `laplace proof`) :
# l'Historien domine, l'Anatomiste apporte la robustesse sur les éditions
# chaotiques (CDM 2022, Euro 2024), le Fiévreux est écarté par les données.
DEFAULT_WEIGHTS = (0.85, 0.15, 0.0)
