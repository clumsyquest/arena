"""LE DEUXIÈME CERVEAU — Dixon-Coles complet : attaque & défense par équipe.

Là où l'Elo résume chaque nation à UN nombre, ce modèle apprend pour chacune
une force d'attaque et une force de défense distinctes :

    log λ_domicile = μ + home + att_A − def_B
    log λ_extérieur = μ        + att_B − def_A

ajustées par maximum de vraisemblance Poisson pondéré (récence + enjeu),
régularisation L2 (les petites nations sont tirées vers la moyenne), montée
de gradient Adam, puis correction Dixon-Coles ρ des petits scores.

Deux instances aux horizons différents forment des cerveaux complémentaires :
la CLASSE (demi-vie 4 ans) et la FORME (demi-vie 15 mois).
"""

from math import exp, lgamma

import numpy as np

MAX_GOALS = 10
_factorials = np.array([exp(lgamma(k + 1)) for k in range(MAX_GOALS + 1)])


class TeamDCModel:
    """Modèle à paramètres par équipe, interrogeable par noms d'équipes."""

    def __init__(self, mu, home, att, deff, rho):
        self.mu = mu
        self.home = home
        self.att = att      # dict équipe -> attaque
        self.deff = deff    # dict équipe -> défense
        self.rho = rho

    def lambdas(self, a, b, home_ind=0):
        att_a, def_a = self.att.get(a, 0.0), self.deff.get(a, 0.0)
        att_b, def_b = self.att.get(b, 0.0), self.deff.get(b, 0.0)
        la = self.mu + att_a - def_b + (self.home if home_ind == 1 else 0.0)
        lb = self.mu + att_b - def_a + (self.home if home_ind == -1 else 0.0)
        return exp(min(la, 4.0)), exp(min(lb, 4.0))

    def score_matrix(self, a, b, home_ind=0, max_goals=MAX_GOALS):
        la, lb = self.lambdas(a, b, home_ind)
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


def fit_teamdc(matches, half_life=4.0, window_years=12.0, friendly_w=0.5,
               reg=4.0, iters=600, lr=0.08, verbose=False):
    """Ajuste μ, home, att/def par équipe (Adam) puis ρ (balayage)."""
    dates = matches["date"]
    as_of = dates.max()
    recent = dates >= as_of - np.timedelta64(int(window_years * 365.25), "D")
    idx = np.flatnonzero(recent.to_numpy())

    hs = matches["home_score"].to_numpy()[idx].astype(float)
    aw = matches["away_score"].to_numpy()[idx].astype(float)
    neutral = matches["neutral"].to_numpy()[idx].astype(bool)
    friendly = matches["tournament"].to_numpy()[idx] == "Friendly"
    home_t = matches["home_team"].to_numpy()[idx]
    away_t = matches["away_team"].to_numpy()[idx]

    age_years = (as_of - dates.iloc[idx]).dt.days.to_numpy() / 365.25
    w = 0.5 ** (age_years / half_life) * np.where(friendly, friendly_w, 1.0)

    teams = sorted(set(home_t) | set(away_t))
    tid = {t: i for i, t in enumerate(teams)}
    hi = np.array([tid[t] for t in home_t])
    ai = np.array([tid[t] for t in away_t])
    hflag = (~neutral).astype(float)
    n_teams = len(teams)

    # Paramètres : [μ, home, att(0..n), def(0..n)]
    mu, home = float(np.log(max(hs.mean(), 0.5))), 0.25
    att = np.zeros(n_teams)
    deff = np.zeros(n_teams)

    # Adam
    m_ = np.zeros(2 + 2 * n_teams)
    v_ = np.zeros(2 + 2 * n_teams)
    b1, b2, eps = 0.9, 0.999, 1e-8

    for it in range(1, iters + 1):
        lh = np.clip(mu + home * hflag + att[hi] - deff[ai], -6, 4)
        la = np.clip(mu + att[ai] - deff[hi], -6, 4)
        elh, ela = np.exp(lh), np.exp(la)
        rh = w * (hs - elh)   # résidus pondérés
        ra = w * (aw - ela)

        g_mu = rh.sum() + ra.sum()
        g_home = float((rh * hflag).sum())
        g_att = np.zeros(n_teams)
        g_def = np.zeros(n_teams)
        np.add.at(g_att, hi, rh)
        np.add.at(g_att, ai, ra)
        np.add.at(g_def, ai, -rh)
        np.add.at(g_def, hi, -ra)
        g_att -= reg * att
        g_def -= reg * deff

        g = np.concatenate([[g_mu, g_home], g_att, g_def])
        m_ = b1 * m_ + (1 - b1) * g
        v_ = b2 * v_ + (1 - b2) * g * g
        mhat = m_ / (1 - b1**it)
        vhat = v_ / (1 - b2**it)
        step = lr * mhat / (np.sqrt(vhat) + eps)
        mu += step[0]
        home += step[1]
        att += step[2 : 2 + n_teams]
        deff += step[2 + n_teams :]
        if np.abs(g).max() < 1e-3:
            break

    # ρ de Dixon-Coles sur les scores observés.
    lh = np.exp(np.clip(mu + home * hflag + att[hi] - deff[ai], -6, 4))
    la = np.exp(np.clip(mu + att[ai] - deff[hi], -6, 4))
    is00 = (hs == 0) & (aw == 0)
    is01 = (hs == 0) & (aw == 1)
    is10 = (hs == 1) & (aw == 0)
    is11 = (hs == 1) & (aw == 1)
    best_rho, best_ll = 0.0, -np.inf
    for rho in np.arange(-0.25, 0.10, 0.005):
        tau = np.ones_like(lh)
        tau[is00] = np.maximum(1 - lh[is00] * la[is00] * rho, 1e-10)
        tau[is01] = np.maximum(1 + lh[is01] * rho, 1e-10)
        tau[is10] = np.maximum(1 + la[is10] * rho, 1e-10)
        tau[is11] = np.maximum(1 - rho, 1e-10)
        ll = float(np.sum(w * np.log(tau)))
        if ll > best_ll:
            best_ll, best_rho = ll, float(rho)

    if verbose:
        order = np.argsort(-att)
        best = ", ".join(f"{teams[i]} ({att[i]:+.2f}/{deff[i]:+.2f})" for i in order[:5])
        print(f"[cerveau att/def] {len(idx)} matchs, {n_teams} équipes, {it} itérations | "
              f"μ={mu:.3f} home={home:.3f} ρ={best_rho:.3f} | top att : {best}")

    return TeamDCModel(
        float(mu), float(home),
        {t: float(att[tid[t]]) for t in teams},
        {t: float(deff[tid[t]]) for t in teams},
        best_rho,
    )
