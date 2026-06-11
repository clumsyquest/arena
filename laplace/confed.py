"""LE CARTOGRAPHE — correction du biais inter-confédérations de l'Elo.

Né de la chasse aux surprises (experiments/chasse.py, 11/06/2026) : l'Elo se
trompe EN BLOC sur les continents, parce que les confédérations se croisent
rarement (Coupes du Monde, amicaux). Le Cartographe mesure, en marche avant,
le résidu moyen (résultat réel − attendu Elo) de chaque confédération dans
ses matchs inter-confédérations des 8 dernières années, et le convertit en
points d'Elo (κ).

Verdict du tribunal (réglé 1994-2008, jugé 2010-2026, jamais l'inverse) :
  · n'agit QUE sur les matchs inter-confédérations (Euro/CAN/Asie : intacts) ;
  · sur les 4 Coupes du Monde du test : 3 améliorées, dont 2022 (−0.0089) ;
  · global 473 matchs : log-loss −0.0009, précision +0.7 pt (57.9 → 58.6%).
2026 (48 équipes, 6 confédérations) est le Mondial le plus inter-continental
de l'histoire : c'est exactement le terrain du Cartographe.
"""

import numpy as np

KAPPA = 650.0        # élu sur 1994-2008 (grille 100→900), jamais retouché sur le test
WINDOW_YEARS = 8.0
MIN_MATCHES = 30     # en-dessous : pas assez de preuves, correction nulle
HOME_ADV = 100.0

UEFA = """Albania Austria Belgium Bulgaria Croatia Denmark England France Georgia Germany
Greece Hungary Iceland Italy Latvia Netherlands Norway Poland Portugal Romania Russia
Scotland Serbia Slovakia Slovenia Spain Sweden Switzerland Turkey Ukraine Wales""".split()
UEFA += ["Bosnia and Herzegovina", "Czech Republic", "Republic of Ireland",
         "Northern Ireland", "Finland", "Israel", "Kosovo", "North Macedonia",
         "Montenegro", "Moldova", "Belarus", "Lithuania", "Estonia", "Cyprus",
         "Luxembourg", "Azerbaijan", "Armenia", "Kazakhstan"]
CONMEBOL = "Argentina Bolivia Brazil Chile Colombia Ecuador Paraguay Peru Uruguay Venezuela".split()
CONCACAF = """Canada Curaçao Guadeloupe Guatemala Haiti Honduras Jamaica Mexico Panama
Suriname Martinique Nicaragua Cuba Bermuda Grenada Belize""".split() + [
    "Costa Rica", "Dominican Republic", "El Salvador", "Trinidad and Tobago",
    "United States", "Puerto Rico", "Saint Kitts and Nevis", "Antigua and Barbuda"]
CAF = """Algeria Angola Benin Botswana Cameroon Comoros Egypt Gabon Ghana Mali Morocco
Mozambique Nigeria Senegal Sudan Tanzania Togo Tunisia Uganda Zambia Zimbabwe Kenya
Libya Ethiopia Gambia Guinea Namibia Malawi Mauritania Niger Rwanda Congo Madagascar""".split() + [
    "Burkina Faso", "DR Congo", "Equatorial Guinea", "Ivory Coast", "South Africa",
    "Cape Verde", "Guinea-Bissau", "Sierra Leone", "South Sudan", "Central African Republic"]
AFC = """Australia Bahrain China Indonesia Iran Iraq Japan Jordan Kyrgyzstan Lebanon
Malaysia Oman Palestine Qatar Syria Tajikistan Thailand Uzbekistan Vietnam India
Singapore Myanmar Turkmenistan Yemen Kuwait Afghanistan Bangladesh Philippines""".split() + [
    "Hong Kong", "North Korea", "Saudi Arabia", "South Korea", "United Arab Emirates",
    "Chinese Taipei", "Sri Lanka", "Nepal"]
OFC = ["New Zealand", "Tahiti", "New Caledonia", "Fiji", "Solomon Islands",
       "Vanuatu", "Papua New Guinea", "Samoa", "Tonga"]

CONF = {}
for _teams, _c in ((UEFA, "UEFA"), (CONMEBOL, "CONMEBOL"), (CONCACAF, "CONCACAF"),
                   (CAF, "CAF"), (AFC, "AFC"), (OFC, "OFC")):
    for _t in _teams:
        CONF[_t] = _c


def confed_bias(df, pre_h, pre_a, as_of=None, kappa=KAPPA, window_years=WINDOW_YEARS):
    """Décalage d'Elo par confédération, mesuré en marche avant.

    df : matchs joués (triés), pre_h/pre_a : Elo pré-match alignés sur df.
    as_of : borne haute exclue (None = aujourd'hui). Ne regarde QUE le passé.
    """
    dates = df["date"].to_numpy()
    hi = dates.max() if as_of is None else np.datetime64(as_of)
    lo = hi - np.timedelta64(int(window_years * 365.25), "D")
    H = df["home_team"].to_numpy()
    A = df["away_team"].to_numpy()
    hs = df["home_score"].to_numpy().astype(float)
    aw = df["away_score"].to_numpy().astype(float)
    neutral = df["neutral"].to_numpy().astype(bool)

    res = {}
    for i in np.flatnonzero((dates >= lo) & (dates < hi)):
        ca, cb = CONF.get(H[i]), CONF.get(A[i])
        if not ca or not cb or ca == cb:
            continue
        we = 1.0 / (1.0 + 10.0 ** (-(pre_h[i] - pre_a[i]
                    + (0.0 if neutral[i] else HOME_ADV)) / 400.0))
        w = 1.0 if hs[i] > aw[i] else (0.5 if hs[i] == aw[i] else 0.0)
        s = w - we
        ra = res.setdefault(ca, [0.0, 0])
        rb = res.setdefault(cb, [0.0, 0])
        ra[0] += s; ra[1] += 1
        rb[0] -= s; rb[1] += 1
    return {c: kappa * v[0] / v[1] for c, v in res.items() if v[1] >= MIN_MATCHES}


def apply_to_ratings(ratings, bias):
    """Décale chaque équipe selon sa confédération (équipes inconnues : 0)."""
    for t in ratings:
        c = CONF.get(t)
        if c in bias:
            ratings[t] += bias[c]
