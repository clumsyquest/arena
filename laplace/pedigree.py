"""LE PEDIGREE — la précision GLOBALE du démon, rejouable et affichée.

Le protocole-tribunal (marche avant stricte, mode vivant — celui de la
production) rejoué sur les 9 grands tournois 2010-2026 :

  · Elo VIVANT : pour chaque match, les forces pré-match exactes (l'Elo a
    digéré tous les matchs antérieurs, y compris ceux du tournoi en cours,
    jamais le match prédit ni les suivants).
  · Modèle de buts + cerveau Anatomiste : ajustés sur les seuls matchs
    ANTÉRIEURS au tournoi, figés pendant (comme en vrai : on ne re-calibre
    pas les constantes en plein Mondial).
  · Fusion 85/15 (DEFAULT_WEIGHTS), grille de scores 0-10 — le moteur v2.

Chaque prédiction est écrite dans prophecies/PEDIGREE.csv : de ce registre
découlent la log-loss globale, la précision, le Brier et la CALIBRATION.
Tout est recomputable par quiconque : `python -m laplace pedigree`.
"""

import csv
import os

import numpy as np

from laplace.data import played
from laplace.elo import compute_elo
from laplace.ensemble import DEFAULT_WEIGHTS, TOURNAMENTS
from laplace.goals import fit_goal_model
from laplace.teamdc import fit_teamdc

PEDIGREE_CSV = os.path.join("prophecies", "PEDIGREE.csv")
MAX_GOALS = 10


def _outcome(m):
    return np.array([float(np.tril(m, -1).sum()), float(np.trace(m)),
                     float(np.triu(m, 1).sum())])


def replay(verbose=False):
    """Rejoue les 9 tournois en marche avant ; renvoie le registre par match."""
    df = played()
    _, pre_h, pre_a = compute_elo(df, return_history=True)
    dates = df["date"].to_numpy()
    w_hist, w_anat, _ = DEFAULT_WEIGHTS

    records = []
    for label, name, start, end in TOURNAMENTS:
        t0, t1 = np.datetime64(start), np.datetime64(end)
        before = dates < t0
        goal_model = fit_goal_model(df[before], pre_h[before], pre_a[before])
        anatomiste = fit_teamdc(df[before], half_life=4.0, window_years=12.0)
        in_cup = ((df["tournament"] == name).to_numpy()
                  & (dates >= t0) & (dates <= t1))
        n_t = 0
        for i in np.flatnonzero(in_cup):
            row = df.iloc[i]
            h = 0 if row["neutral"] else 1
            m_hist = goal_model.score_matrix(pre_h[i], pre_a[i], h, MAX_GOALS)
            try:
                m_anat = anatomiste.score_matrix(
                    row["home_team"], row["away_team"], h, MAX_GOALS)
            except (KeyError, ValueError):
                m_anat = None
            if m_anat is None:
                m = m_hist
            else:
                logm = (w_hist * np.log(np.clip(m_hist, 1e-14, 1.0))
                        + w_anat * np.log(np.clip(m_anat, 1e-14, 1.0)))
                m = np.exp(logm - logm.max())
                m /= m.sum()
            p = _outcome(m)
            y = (0 if row["home_score"] > row["away_score"]
                 else (1 if row["home_score"] == row["away_score"] else 2))
            records.append({
                "tournament": label,
                "date": str(row["date"].date()),
                "home": row["home_team"],
                "away": row["away_team"],
                "p1": p[0], "pn": p[1], "p2": p[2],
                "outcome": ["1", "N", "2"][y],
                "pick": ["1", "N", "2"][int(p.argmax())],
                "hit": int(p.argmax() == y),
                "logloss": float(-np.log(max(p[y], 1e-12))),
            })
            n_t += 1
        if verbose:
            sub = records[-n_t:]
            ll = float(np.mean([r["logloss"] for r in sub]))
            acc = float(np.mean([r["hit"] for r in sub]))
            print(f"  [{label}] {n_t} matchs · log-loss {ll:.4f} · précision {100 * acc:.1f}%")
    return records


def save(records, path=PEDIGREE_CSV):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader()
        for r in records:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v)
                        for k, v in r.items()})
    return path


def load(path=PEDIGREE_CSV):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        out = []
        for r in csv.DictReader(f):
            r["p1"], r["pn"], r["p2"] = float(r["p1"]), float(r["pn"]), float(r["p2"])
            r["hit"], r["logloss"] = int(r["hit"]), float(r["logloss"])
            out.append(r)
        return out


def metrics(records):
    """Log-loss / Brier / précision globales d'un registre de prédictions."""
    if not records:
        return None
    p = np.array([[r["p1"], r["pn"], r["p2"]] for r in records])
    y = np.array([{"1": 0, "N": 1, "2": 2}[r["outcome"]] for r in records])
    n = len(y)
    picked = p[np.arange(n), y]
    return {
        "n": n,
        "logloss": float(-np.mean(np.log(np.clip(picked, 1e-12, 1)))),
        "brier": float(np.mean(np.sum((p - np.eye(3)[y]) ** 2, axis=1))),
        "accuracy": float(np.mean(p.argmax(axis=1) == y)),
    }


def calibration(records, edges=(0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 1.01)):
    """Fiabilité : quand le démon dit X%, à quelle fréquence ça arrive ?

    Toutes les probabilités émises (3 par match) sont jugées, pas
    seulement le pronostic.
    """
    probs, happened = [], []
    for r in records:
        y = {"1": 0, "N": 1, "2": 2}[r["outcome"]]
        for k, pk in enumerate((r["p1"], r["pn"], r["p2"])):
            probs.append(pk)
            happened.append(int(k == y))
    probs, happened = np.array(probs), np.array(happened)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (probs >= lo) & (probs < hi)
        if sel.sum() == 0:
            continue
        rows.append({
            "bucket": f"{100 * lo:.0f}-{min(100 * hi, 100):.0f}%",
            "n": int(sel.sum()),
            "announced": float(probs[sel].mean()),
            "realized": float(happened[sel].mean()),
        })
    return rows


def by_tournament(records):
    out = []
    for label, _, _, _ in TOURNAMENTS:
        sub = [r for r in records if r["tournament"] == label]
        if sub:
            out.append({"label": label, **metrics(sub)})
    return out
