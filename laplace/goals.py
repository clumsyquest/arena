"""LE CERVEAU — modèle de buts Dixon-Coles entraîné sur l'histoire récente.

Transforme un écart de force Elo en distribution complète des scores exacts :
    log λ = α + β·(Elo_A − Elo_B)/400 + γ·[joue à domicile] + δ·[adversaire à domicile]
ajusté par maximum de vraisemblance (Poisson, IRLS), puis corrigé pour la
dépendance des petits scores (0-0, 1-0, 0-1, 1-1) par le ρ de Dixon-Coles.
"""

from dataclasses import dataclass
from math import exp, lgamma

import numpy as np

WINDOW_YEARS = 16   # fenêtre d'entraînement
HALF_LIFE = 4.0     # demi-vie de pondération (années) : le récent pèse plus
FRIENDLY_W = 0.5    # les amicaux comptent moitié moins
MAX_GOALS = 10      # taille de la grille de scores


@dataclass
class GoalModel:
    alpha: float
    beta: float
    gamma: float   # boost de celui qui joue à domicile
    delta: float   # malus de celui qui se déplace chez l'autre
    rho: float     # corrélation Dixon-Coles des petits scores

    def lambdas(self, ra, rb, home_ind=0):
        """Buts attendus (λ_A, λ_B). home_ind: +1 A reçoit, -1 B reçoit, 0 neutre."""
        d = (ra - rb) / 400.0
        la = self.alpha + self.beta * d
        lb = self.alpha - self.beta * d
        if home_ind == 1:
            la += self.gamma
            lb += self.delta
        elif home_ind == -1:
            lb += self.gamma
            la += self.delta
        return exp(la), exp(lb)

    def score_matrix(self, ra, rb, home_ind=0, max_goals=MAX_GOALS):
        """Matrice P(score = i-j), corrigée Dixon-Coles, normalisée."""
        la, lb = self.lambdas(ra, rb, home_ind)
        gx = np.arange(max_goals + 1)
        pa = np.exp(-la) * la**gx / _factorials[: max_goals + 1]
        pb = np.exp(-lb) * lb**gx / _factorials[: max_goals + 1]
        m = np.outer(pa, pb)
        r = self.rho
        m[0, 0] *= max(1.0 - la * lb * r, 1e-10)
        m[0, 1] *= max(1.0 + la * r, 1e-10)
        m[1, 0] *= max(1.0 + lb * r, 1e-10)
        m[1, 1] *= max(1.0 - r, 1e-10)
        return m / m.sum()


_factorials = np.array([exp(lgamma(k + 1)) for k in range(MAX_GOALS + 1)])


def fit_goal_model(matches, pre_home, pre_away, verbose=False):
    """Ajuste (α, β, γ, δ) par IRLS puis ρ par balayage de vraisemblance."""
    dates = matches["date"]
    as_of = dates.max()
    recent = dates >= as_of - np.timedelta64(int(WINDOW_YEARS * 365.25), "D")
    idx = np.flatnonzero(recent.to_numpy())

    hs = matches["home_score"].to_numpy()[idx].astype(float)
    aw = matches["away_score"].to_numpy()[idx].astype(float)
    neutral = matches["neutral"].to_numpy()[idx].astype(bool)
    friendly = (matches["tournament"].to_numpy()[idx] == "Friendly")
    ra, rb = pre_home[idx], pre_away[idx]

    age_years = (as_of - dates.iloc[idx]).dt.days.to_numpy() / 365.25
    w = 0.5 ** (age_years / HALF_LIFE) * np.where(friendly, FRIENDLY_W, 1.0)

    # Deux observations par match : les buts de chaque camp.
    d = (ra - rb) / 400.0
    home_flag = (~neutral).astype(float)
    X = np.vstack(
        [
            np.column_stack([np.ones_like(d), d, home_flag, np.zeros_like(d)]),
            np.column_stack([np.ones_like(d), -d, np.zeros_like(d), home_flag]),
        ]
    )
    y = np.concatenate([hs, aw])
    ww = np.concatenate([w, w])

    beta = np.zeros(4)
    for _ in range(25):  # IRLS / Newton-Raphson
        lam = np.exp(np.clip(X @ beta, -8, 5))
        grad = X.T @ (ww * (y - lam))
        hess = X.T @ (X * (ww * lam)[:, None])
        step = np.linalg.solve(hess, grad)
        beta += step
        if np.abs(step).max() < 1e-10:
            break
    alpha, b, gamma, delta = beta

    # ρ de Dixon-Coles : balayage sur la vraisemblance des scores observés.
    la = np.exp(np.clip(alpha + b * d + gamma * home_flag, -8, 5))
    lb = np.exp(np.clip(alpha - b * d + delta * home_flag, -8, 5))
    best_rho, best_ll = 0.0, -np.inf
    is00 = (hs == 0) & (aw == 0)
    is01 = (hs == 0) & (aw == 1)
    is10 = (hs == 1) & (aw == 0)
    is11 = (hs == 1) & (aw == 1)
    for rho in np.arange(-0.25, 0.10, 0.005):
        tau = np.ones_like(la)
        tau[is00] = np.maximum(1 - la[is00] * lb[is00] * rho, 1e-10)
        tau[is01] = np.maximum(1 + la[is01] * rho, 1e-10)
        tau[is10] = np.maximum(1 + lb[is10] * rho, 1e-10)
        tau[is11] = np.maximum(1 - rho, 1e-10)
        ll = float(np.sum(w * np.log(tau)))
        if ll > best_ll:
            best_ll, best_rho = ll, float(rho)

    model = GoalModel(float(alpha), float(b), float(gamma), float(delta), best_rho)
    if verbose:
        print(
            f"[cerveau] {len(idx)} matchs d'entraînement | "
            f"α={alpha:.3f} β={b:.3f} γ={gamma:.3f} δ={delta:.3f} ρ={best_rho:.3f}"
        )
    return model
