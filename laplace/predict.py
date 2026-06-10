"""L'Oracle — interroge le démon sur n'importe quelle affiche."""

import difflib

import numpy as np

# Noms alternatifs -> noms officiels du jeu de données
ALIASES = {
    "usa": "United States",
    "etats-unis": "United States",
    "états-unis": "United States",
    "korea": "South Korea",
    "coree du sud": "South Korea",
    "corée du sud": "South Korea",
    "korea republic": "South Korea",
    "czechia": "Czech Republic",
    "tchequie": "Czech Republic",
    "tchéquie": "Czech Republic",
    "turkiye": "Turkey",
    "türkiye": "Turkey",
    "turquie": "Turkey",
    "cabo verde": "Cape Verde",
    "cap-vert": "Cape Verde",
    "cap vert": "Cape Verde",
    "cote d'ivoire": "Ivory Coast",
    "côte d'ivoire": "Ivory Coast",
    "congo dr": "DR Congo",
    "rd congo": "DR Congo",
    "holland": "Netherlands",
    "pays-bas": "Netherlands",
    "bosnia": "Bosnia and Herzegovina",
    "bosnie": "Bosnia and Herzegovina",
    "allemagne": "Germany",
    "espagne": "Spain",
    "angleterre": "England",
    "bresil": "Brazil",
    "brésil": "Brazil",
    "argentine": "Argentina",
    "belgique": "Belgium",
    "maroc": "Morocco",
    "algerie": "Algeria",
    "algérie": "Algeria",
    "senegal": "Senegal",
    "sénégal": "Senegal",
    "japon": "Japan",
    "mexique": "Mexico",
    "ecosse": "Scotland",
    "écosse": "Scotland",
    "norvege": "Norway",
    "norvège": "Norway",
    "suede": "Sweden",
    "suède": "Sweden",
    "suisse": "Switzerland",
    "autriche": "Austria",
    "croatie": "Croatia",
    "egypte": "Egypt",
    "égypte": "Egypt",
    "arabie saoudite": "Saudi Arabia",
    "tunisie": "Tunisia",
    "afrique du sud": "South Africa",
    "nouvelle-zelande": "New Zealand",
    "nouvelle-zélande": "New Zealand",
    "ouzbekistan": "Uzbekistan",
    "ouzbékistan": "Uzbekistan",
    "jordanie": "Jordan",
    "irak": "Iraq",
    "haiti": "Haiti",
    "haïti": "Haiti",
    "equateur": "Ecuador",
    "équateur": "Ecuador",
    "colombie": "Colombia",
    "uruguay": "Uruguay",
    "paraguay": "Paraguay",
    "panama": "Panama",
    "ghana": "Ghana",
    "qatar": "Qatar",
    "iran": "Iran",
    "australie": "Australia",
    "canada": "Canada",
    "portugal": "Portugal",
    "curacao": "Curaçao",
}


def resolve(name, known):
    """Résout un nom d'équipe (insensible à la casse, alias FR/EN, suggestions)."""
    if name in known:
        return name
    low = name.strip().lower()
    if low in ALIASES and ALIASES[low] in known:
        return ALIASES[low]
    for k in known:
        if k.lower() == low:
            return k
    close = difflib.get_close_matches(name, list(known), n=3, cutoff=0.6)
    hint = f" Vouliez-vous dire : {', '.join(close)} ?" if close else ""
    raise ValueError(f"Équipe inconnue : « {name} ».{hint}")


class Oracle:
    """Combine ratings Elo et modèle de buts pour prophétiser un match."""

    def __init__(self, ratings, model):
        self.ratings = ratings
        self.model = model

    def rating(self, team):
        return self.ratings[resolve(team, self.ratings)]

    def match(self, team_a, team_b, home_ind=0, max_goals=10):
        """Prophétie complète : probabilités 1-N-2, buts attendus, scores probables."""
        a = resolve(team_a, self.ratings)
        b = resolve(team_b, self.ratings)
        ra, rb = self.ratings[a], self.ratings[b]
        m = self.model.score_matrix(ra, rb, home_ind, max_goals)
        la, lb = self.model.lambdas(ra, rb, home_ind)

        p_win = float(np.tril(m, -1).sum())   # lignes = buts de A
        p_draw = float(np.trace(m))
        p_loss = float(np.triu(m, 1).sum())

        flat = [(int(i), int(j), float(m[i, j])) for i in range(m.shape[0]) for j in range(m.shape[1])]
        flat.sort(key=lambda t: -t[2])

        return {
            "team_a": a,
            "team_b": b,
            "elo_a": ra,
            "elo_b": rb,
            "lambda_a": la,
            "lambda_b": lb,
            "p_win": p_win,
            "p_draw": p_draw,
            "p_loss": p_loss,
            "top_scores": flat[:6],
            "matrix": m,
        }
