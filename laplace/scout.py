"""L'ÉCLAIREUR — injection d'intelligence terrain dans le démon.

Le démon ne lit pas les news (blessures, compos, méforme d'un cadre) : cette
information vit hors de ses archives. L'éclaireur — humain aujourd'hui, agent
demain — la lui injecte en points d'Elo :

    python -m laplace adjust France -40 --reason "Mbappé forfait"

L'ajustement est appliqué à TOUS les cerveaux à la construction de l'oracle
(échelle : un titulaire majeur absent ≈ -30 à -50 Elo, un banc décimé ≈ -80).
"""

import json
import os

from laplace.data import DATA_DIR

PATH = os.path.join(DATA_DIR, "adjustments.json")

# Conversion Elo -> log-buts (β/400 du modèle de buts : ~0.0019 par point Elo).
BETA_PER_ELO = 0.0019


def load():
    if os.path.exists(PATH):
        with open(PATH) as f:
            return json.load(f)
    return {}


def save(adj):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PATH, "w") as f:
        json.dump(adj, f, ensure_ascii=False, indent=2)


def set_adjustment(team, delta, reason=""):
    adj = load()
    adj[team] = {"delta": float(delta), "reason": reason}
    save(adj)


def clear(team=None):
    if team is None:
        save({})
    else:
        adj = load()
        adj.pop(team, None)
        save(adj)


def apply_to_ratings(ratings):
    """Décale l'Elo des équipes ajustées (cerveau Historien)."""
    for team, info in load().items():
        if team in ratings:
            ratings[team] += info["delta"]


def apply_to_teamdc(model):
    """Équivalent sur les cerveaux attaque/défense : même effet sur les buts."""
    for team, info in load().items():
        if team in model.att:
            model.att[team] += info["delta"] * BETA_PER_ELO
            model.deff[team] += info["delta"] * BETA_PER_ELO
