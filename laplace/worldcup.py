"""Coupe du Monde 2026 — le vrai format à 48 équipes.

Tirage officiel (5 déc. 2025) + barrages de mars 2026, calendrier réel,
règles d'appariement des meilleurs troisièmes pour les 16es de finale.
Source structure : openfootball/worldcup (domaine public).
"""

from laplace.data import fixtures

HOSTS = {"Mexico", "Canada", "United States"}

GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

TEAM_GROUP = {t: g for g, teams in GROUPS.items() for t in teams}

# 16es de finale : (n° de match, slot A, slot B).
# "1A"/"2A" = 1er/2e du groupe A ; "3:ABCDF" = un des meilleurs troisièmes
# issu de l'un de ces groupes (table officielle FIFA).
ROUND_OF_32 = [
    (73, "2A", "2B"),
    (74, "1E", "3:ABCDF"),
    (75, "1F", "2C"),
    (76, "1C", "2F"),
    (77, "1I", "3:CDFGH"),
    (78, "2E", "2I"),
    (79, "1A", "3:CEFHI"),
    (80, "1L", "3:EHIJK"),
    (81, "1D", "3:BEFIJ"),
    (82, "1G", "3:AEHIJ"),
    (83, "2K", "2L"),
    (84, "1H", "2J"),
    (85, "1B", "3:EFGIJ"),
    (86, "1J", "2H"),
    (87, "1K", "3:DEIJL"),
    (88, "2D", "2G"),
]

ROUND_OF_16 = [(89, 74, 77), (90, 73, 75), (91, 76, 78), (92, 79, 80),
               (93, 83, 84), (94, 81, 82), (95, 86, 88), (96, 85, 87)]
QUARTERS = [(97, 89, 90), (98, 93, 94), (99, 91, 92), (100, 95, 96)]
SEMIS = [(101, 97, 98), (102, 99, 100)]
FINAL = [(104, 101, 102)]

# Pays hôte de chaque match à élimination directe (avantage du terrain).
KO_VENUE_COUNTRY = {
    73: "United States", 74: "United States", 75: "Mexico", 76: "United States",
    77: "United States", 78: "United States", 79: "Mexico", 80: "United States",
    81: "United States", 82: "United States", 83: "Canada", 84: "United States",
    85: "Canada", 86: "United States", 87: "United States", 88: "United States",
    89: "United States", 90: "United States", 91: "United States", 92: "Mexico",
    93: "United States", 94: "United States", 95: "United States", 96: "Canada",
    97: "United States", 98: "United States", 99: "United States", 100: "United States",
    101: "United States", 102: "United States", 103: "United States", 104: "United States",
}

STAGES = ["Groupes", "16es", "8es", "Quarts", "Demies", "Finale", "CHAMPION"]


def home_ind_for(team_a, team_b, venue_country):
    """+1 si A joue dans son pays, -1 si B, 0 sinon (avantage du terrain hôte)."""
    if team_a == venue_country:
        return 1
    if team_b == venue_country:
        return -1
    return 0


def group_fixtures():
    """Les 72 matchs de groupes réels (équipes, date, lieu, terrain neutre ou non)."""
    fx = fixtures(start="2026-06-01", end="2026-06-30")
    out = []
    for row in fx.itertuples():
        a, b = row.home_team, row.away_team
        g = TEAM_GROUP.get(a)
        if g is None or TEAM_GROUP.get(b) != g:
            continue
        out.append({
            "group": g,
            "team_a": a,
            "team_b": b,
            "date": row.date,
            "city": row.city,
            "country": row.country,
            "home_ind": 0 if row.neutral else 1,
        })
    return out
