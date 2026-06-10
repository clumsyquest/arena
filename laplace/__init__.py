"""LE DÉMON DE LAPLACE — moteur de prédiction de football international.

« Une intelligence qui, à un instant donné, connaîtrait toutes les forces
dont la nature est animée [...] rien ne serait incertain pour elle, et
l'avenir, comme le passé, serait présent à ses yeux. »
                                        — Pierre-Simon de Laplace, 1814
"""

from laplace.data import load, played, update
from laplace.elo import compute_elo
from laplace.goals import fit_goal_model
from laplace.predict import Oracle, resolve

__version__ = "1.0.0"


def build_oracle(as_of=None, verbose=False):
    """Assemble le démon complet : données -> Elo -> modèle de buts -> Oracle."""
    df = played(before=as_of)
    ratings, pre_home, pre_away = compute_elo(df, return_history=True)
    if as_of is None:  # les ajustements de l'éclaireur ne valent que pour le présent
        from laplace.scout import apply_to_ratings

        apply_to_ratings(ratings)
    model = fit_goal_model(df, pre_home, pre_away, verbose=verbose)
    return Oracle(ratings, model)
