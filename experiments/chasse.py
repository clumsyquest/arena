# LA CHASSE AUX SURPRISES — VERDICT (11/06/2026, 3 rounds, 11 hypothèses) :
#
# ❌ Mortes au réglage (1994-2008) : H1 malédiction de l'ouverture,
#    H6 oser le nul, H7 favori rassasié, H8 biscotto, H11 élan du tombeur.
# ❌ Mortes à l'épreuve du feu (2010-2026) : H2 champion (+0.0016),
#    H5 chaos (+0.0003, séismes +0.10), H9 recalibration isotonique
#    (tune in-sample 0.9584 → test +0.0133 : surapprentissage d'époque).
# ⚡ Honorables mais non adoptées : H3/H3b David (séismes −0.02/−0.035,
#    global +0.0004/+0.0019 — le filet à séismes coûte plus qu'il ne rend).
# ✅ ADOPTÉE : H4 LE CARTOGRAPHE (biais inter-confédérations, κ=650 élu sur
#    tune). Test historien seul : ll −0.0009, précision +0.7 pt. Dans le
#    moteur v2 complet (pedigree) : 0.9336 → 0.9305 (−0.0031), Brier
#    0.5509 → 0.5488, CDM 2014 −0.0102, CDM 2018 −0.0102, CDM 2022 −0.0031.
#    → production laplace/confed.py (v3).
# Leçon des séismes : 16 issues à p≤15% sur 473 matchs ; même la meilleure
# hypothèse ciblée ne déplace Argentine–Arabie que de 3.9 → 4.2%. Le filet
# à séismes ne vit PAS dans l'historique des scores : il vit dans
# l'information nouvelle (blessures, compos, dérive des cotes) — d'où
# l'ÉCLAIREUR et le voleur de cerveaux, déjà au registre.
#
# Ordre du commandant (11/06/2026) : « pour faire un exploit il faut oser
# inventer, pousser là où les autres ne sont pas allés — sinon on rate les
# Argentine-Arabie comme tout le monde et on appelle ça normal. »
#
# Six hypothèses NON-STANDARD, réglées sur 1994-2008 (TUNE), jugées sur
# 2010-2026 (TEST, les 473 matchs du pedigree — jamais touchés au réglage).
# Juge spécial : LE FILET À SÉISMES — log-loss restreinte aux issues que le
# modèle de base jugeait quasi impossibles (p ≤ 15%), c.-à-d. exactement les
# Argentine–Arabie saoudite, les Allemagne–Corée, les Brésil 1-7.
#
#   H1 LA MALÉDICTION DE L'OUVERTURE — un grand favori dans SON premier match
#      du tournoi est plus fragile (Espagne 2010, Argentine 2022...).
#   H2 LA MALÉDICTION DU CHAMPION — le tenant du titre en phase de groupes
#      (France 2002, Italie 2010, Espagne 2014, Allemagne 2018...).
#   H3 LE COEFFICIENT DE DAVID — certaines équipes sur-performent
#      systématiquement contre plus fort qu'elles (mémoire EWMA des exploits).
#   H4 LE BIAIS DES CONFÉDÉRATIONS — l'Elo se trompe en bloc sur les
#      continents (AFC/CAF sous-cotées face à UEFA/CONMEBOL ?), corrigé en
#      marche avant par les résultats inter-confédérations des 8 ans passés.
#   H5 LA TEMPÉRATURE DU CHAOS — équipes volatiles (résultats imprévisibles)
#      → distribution aplatie ; équipes métronomes → aiguisée.
#   H6 OSER LE NUL — politique de pronostic : pick = N quand le match est
#      serré (le nul n'est JAMAIS pronostiqué par les modèles classiques).

import numpy as np

from laplace.data import played
from laplace.elo import compute_elo
from laplace.ensemble import TOURNAMENTS as TEST_T
from laplace.goals import fit_goal_model

TUNE_T = [
    ("CDM 1994", "FIFA World Cup", "1994-06-17", "1994-07-17"),
    ("Euro 1996", "UEFA Euro", "1996-06-08", "1996-07-01"),
    ("CDM 1998", "FIFA World Cup", "1998-06-10", "1998-07-12"),
    ("Euro 2000", "UEFA Euro", "2000-06-10", "2000-07-02"),
    ("CDM 2002", "FIFA World Cup", "2002-05-31", "2002-06-30"),
    ("Euro 2004", "UEFA Euro", "2004-06-12", "2004-07-04"),
    ("CDM 2006", "FIFA World Cup", "2006-06-09", "2006-07-09"),
    ("Euro 2008", "UEFA Euro", "2008-06-07", "2008-06-29"),
]

UEFA = """Albania Austria Belgium Bulgaria Croatia Denmark England France Georgia Germany
Greece Hungary Iceland Italy Latvia Netherlands Norway Poland Portugal Romania Russia
Scotland Serbia Slovakia Slovenia Spain Sweden Switzerland Turkey Ukraine Wales""".split()
UEFA += ["Bosnia and Herzegovina", "Czech Republic", "Republic of Ireland"]
CONMEBOL = "Argentina Bolivia Brazil Chile Colombia Ecuador Paraguay Peru Uruguay Venezuela".split()
CONCACAF = """Canada Curaçao Guadeloupe Guatemala Haiti Honduras Jamaica Mexico Panama
Suriname""".split() + ["Costa Rica", "Dominican Republic", "El Salvador",
                       "Trinidad and Tobago", "United States"]
CAF = """Algeria Angola Benin Botswana Cameroon Comoros Egypt Gabon Ghana Mali Morocco
Mozambique Nigeria Senegal Sudan Tanzania Togo Tunisia Uganda Zambia Zimbabwe""".split() + [
    "Burkina Faso", "DR Congo", "Equatorial Guinea", "Ivory Coast", "South Africa"]
AFC = """Australia Bahrain China Indonesia Iran Iraq Japan Jordan Kyrgyzstan Lebanon
Malaysia Oman Palestine Qatar Syria Tajikistan Thailand Uzbekistan Vietnam India""".split() + [
    "Hong Kong", "North Korea", "Saudi Arabia", "South Korea", "United Arab Emirates"]
OFC = ["New Zealand"]
CONF = {}
for teams, c in ((UEFA, "UEFA"), (CONMEBOL, "SUD"), (CONCACAF, "CCF"),
                 (CAF, "CAF"), (AFC, "AFC"), (OFC, "OFC")):
    for t in teams:
        CONF[t] = c

# Tenant du titre à l'entrée du tournoi (label -> équipe).
CHAMPS = {
    "CDM 1994": "Germany", "CDM 1998": "Brazil", "CDM 2002": "France",
    "CDM 2006": "Brazil", "CDM 2010": "Italy", "CDM 2014": "Spain",
    "CDM 2018": "Germany", "CDM 2022": "France",
    "Euro 1996": "Denmark", "Euro 2000": "Germany", "Euro 2004": "France",
    "Euro 2008": "Greece", "Euro 2024": "Italy",
    "Asie 2024": "Qatar", "Copa 2024": "Argentina",
    "Gold Cup 2025": "Mexico", "CAN 2025": "Ivory Coast",
}

print("⚙ préparation : Elo vivant + marches EWMA sur 49 400 matchs...")
df = played()
N = len(df)
_, pre_h, pre_a = compute_elo(df, return_history=True)
dates = df["date"].to_numpy()
hs = df["home_score"].to_numpy().astype(float)
aw = df["away_score"].to_numpy().astype(float)
neutral = df["neutral"].to_numpy().astype(bool)
tourn = df["tournament"].to_numpy()
H = df["home_team"].to_numpy()
A = df["away_team"].to_numpy()

# ---- marches avant-sûres : coefficient de David + volatilité ----
DAVID_GAP, LD, LV, VOL0 = 80.0, 0.95, 0.92, 0.23
david, vol = {}, {}
david_h = np.zeros(N); david_a = np.zeros(N)
vol_h = np.full(N, VOL0); vol_a = np.full(N, VOL0)
for i in range(N):
    a, b = H[i], A[i]
    david_h[i] = david.get(a, 0.0); david_a[i] = david.get(b, 0.0)
    vol_h[i] = vol.get(a, VOL0); vol_a[i] = vol.get(b, VOL0)
    ra, rb = pre_h[i], pre_a[i]
    we = 1.0 / (1.0 + 10.0 ** (-(ra - rb + (0.0 if neutral[i] else 100.0)) / 400.0))
    w = 1.0 if hs[i] > aw[i] else (0.5 if hs[i] == aw[i] else 0.0)
    s = w - we
    if rb - ra >= DAVID_GAP:
        david[a] = LD * david.get(a, 0.0) + (1 - LD) * s
    if ra - rb >= DAVID_GAP:
        david[b] = LD * david.get(b, 0.0) + (1 - LD) * (-s)
    vol[a] = LV * vol.get(a, VOL0) + (1 - LV) * s * s
    vol[b] = LV * vol.get(b, VOL0) + (1 - LV) * s * s

# ---- biais inter-confédérations, recalculé AVANT chaque tournoi (8 ans) ----
def confed_residuals(t0):
    lo = t0 - np.timedelta64(int(8 * 365.25), "D")
    res = {c: [0.0, 0] for c in ("UEFA", "SUD", "CCF", "CAF", "AFC", "OFC")}
    sel = np.flatnonzero((dates >= lo) & (dates < t0))
    for i in sel:
        ca, cb = CONF.get(H[i]), CONF.get(A[i])
        if not ca or not cb or ca == cb:
            continue
        ra, rb = pre_h[i], pre_a[i]
        we = 1.0 / (1.0 + 10.0 ** (-(ra - rb + (0.0 if neutral[i] else 100.0)) / 400.0))
        w = 1.0 if hs[i] > aw[i] else (0.5 if hs[i] == aw[i] else 0.0)
        s = w - we
        res[ca][0] += s; res[ca][1] += 1
        res[cb][0] -= s; res[cb][1] += 1
    return {c: (v[0] / v[1] if v[1] >= 30 else 0.0) for c, v in res.items()}

# ---- assemblage des matchs de tournoi (probas de base via moteur historien) ----
def build(tlist):
    out = []
    for label, name, s, e in tlist:
        t0, t1 = np.datetime64(s), np.datetime64(e)
        before = dates < t0
        model = fit_goal_model(df[before], pre_h[before], pre_a[before])
        cres = confed_residuals(t0)
        span = (t1 - t0).astype(float)
        in_cup = (tourn == name) & (dates >= t0) & (dates <= t1)
        seen = set()
        pts, mno, last_surp = {}, {}, {}
        for i in np.flatnonzero(in_cup):
            h = 0 if neutral[i] else 1
            m = model.score_matrix(pre_h[i], pre_a[i], h)
            p = np.array([np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum()])
            y = 0 if hs[i] > aw[i] else (1 if hs[i] == aw[i] else 2)
            we_i = 1.0 / (1.0 + 10.0 ** (-(pre_h[i] - pre_a[i]
                          + (0.0 if neutral[i] else 100.0)) / 400.0))
            w_i = 1.0 if y == 0 else (0.5 if y == 1 else 0.0)
            out.append({
                "label": label, "i": int(i), "model": model, "h": h,
                "home": H[i], "away": A[i], "y": y, "p": p / p.sum(),
                "eh": float(pre_h[i]), "ea": float(pre_a[i]),
                "opener_h": H[i] not in seen, "opener_a": A[i] not in seen,
                "group": (dates[i] - t0).astype(float) <= 0.55 * span,
                "champ_h": CHAMPS.get(label) == H[i], "champ_a": CHAMPS.get(label) == A[i],
                "conf_h": CONF.get(H[i]), "conf_a": CONF.get(A[i]),
                "david_h": david_h[i], "david_a": david_a[i],
                "vol_h": vol_h[i], "vol_a": vol_a[i],
                "cres": cres,
                # état du tournoi AVANT le match (points et n° de match de chacun)
                "pts_h": pts.get(H[i], 0), "pts_a": pts.get(A[i], 0),
                "mno_h": mno.get(H[i], 0) + 1, "mno_a": mno.get(A[i], 0) + 1,
                # surprise (w-we) du match précédent de chacun DANS ce tournoi
                "surp_h": last_surp.get(H[i], 0.0), "surp_a": last_surp.get(A[i], 0.0),
            })
            seen.add(H[i]); seen.add(A[i])
            mno[H[i]] = mno.get(H[i], 0) + 1; mno[A[i]] = mno.get(A[i], 0) + 1
            pts[H[i]] = pts.get(H[i], 0) + (3 if y == 0 else (1 if y == 1 else 0))
            pts[A[i]] = pts.get(A[i], 0) + (3 if y == 2 else (1 if y == 1 else 0))
            last_surp[H[i]] = w_i - we_i
            last_surp[A[i]] = we_i - w_i
    return out

# ---- juges ----
def judge(recs, tf=None, surprise_cut=0.15):
    ll = acc = 0.0
    ll_s = n_s = 0
    for r in recs:
        p = tf(r) if tf else r["p"]
        ll -= np.log(max(p[r["y"]], 1e-12))
        acc += int(np.argmax(p) == r["y"])
        if r["p"][r["y"]] <= surprise_cut:  # séisme au sens du modèle de BASE
            ll_s -= np.log(max(p[r["y"]], 1e-12)); n_s += 1
    n = len(recs)
    return ll / n, acc / n, (ll_s / n_s if n_s else float("nan")), n_s

U = np.ones(3) / 3.0

def h1(theta):
    def tf(r):
        p = r["p"]
        fav_h = p[0] >= p[2]
        if max(p[0], p[2]) >= 0.55 and (r["opener_h"] if fav_h else r["opener_a"]):
            return (1 - theta) * p + theta * U
        return p
    return tf

def h2(theta):
    def tf(r):
        p = r["p"]
        if r["group"] and (r["champ_h"] or r["champ_a"]):
            return (1 - theta) * p + theta * U
        return p
    return tf

def h3(lam):
    def tf(r):
        p = r["p"].copy()
        if r["ea"] - r["eh"] >= DAVID_GAP:      # home est David
            p[0] *= np.exp(lam * r["david_h"])
        elif r["eh"] - r["ea"] >= DAVID_GAP:    # away est David
            p[2] *= np.exp(lam * r["david_a"])
        return p / p.sum()
    return tf

def h4(kappa):
    def tf(r):
        b = r["cres"]
        da = kappa * b.get(r["conf_h"], 0.0) if r["conf_h"] else 0.0
        db = kappa * b.get(r["conf_a"], 0.0) if r["conf_a"] else 0.0
        if da == 0.0 and db == 0.0:
            return r["p"]
        m = r["model"].score_matrix(r["eh"] + da, r["ea"] + db, r["h"])
        p = np.array([np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum()])
        return p / p.sum()
    return tf

VBAR = 2 * VOL0
def h5(gamma):
    def tf(r):
        t = float(np.exp(gamma * (r["vol_h"] + r["vol_a"] - VBAR)))
        p = r["p"] ** (1.0 / max(t, 0.05))
        return p / p.sum()
    return tf

def h7(theta, need=6):
    """LE FAVORI RASSASIÉ — 3e match de groupe, favori déjà qualifié (≥ need
    pts) : il tourne, il coupe le moteur — Brésil 2022, France 2022, Portugal
    2024 sont tombés exactement là. Aplatissement ciblé."""
    def tf(r):
        p = r["p"]
        fav_h = p[0] >= p[2]
        if max(p[0], p[2]) < 0.55 or not r["group"]:
            return p
        mno = r["mno_h"] if fav_h else r["mno_a"]
        pts = r["pts_h"] if fav_h else r["pts_a"]
        if mno == 3 and pts >= need:
            return (1 - theta) * p + theta * U
        return p
    return tf

def h8(mu):
    """LE BISCOTTO — 3e match de groupe, les DEUX équipes ont ≥ 4 pts :
    le nul arrange tout le monde (Suède–Danemark 2004...)."""
    def tf(r):
        if (r["mno_h"] == 3 and r["mno_a"] == 3 and r["group"]
                and r["pts_h"] >= 4 and r["pts_a"] >= 4):
            p = r["p"].copy()
            p[1] *= np.exp(mu)
            return p / p.sum()
        return r["p"]
    return tf

def h3b(lam):
    """David, variante complète : l'exploit de l'outsider = victoire OU nul
    arrachés — on déplace la masse du favori vers les DEUX autres issues."""
    def tf(r):
        p = r["p"].copy()
        if r["ea"] - r["eh"] >= DAVID_GAP:
            b = np.exp(lam * r["david_h"])
            p[0] *= b; p[1] *= np.sqrt(b)
        elif r["eh"] - r["ea"] >= DAVID_GAP:
            b = np.exp(lam * r["david_a"])
            p[2] *= b; p[1] *= np.sqrt(b)
        return p / p.sum()
    return tf

def pick_acc(recs, delta):
    """H6 : pronostic = N quand le match est serré (politique de pick seule)."""
    ok = 0
    for r in recs:
        p = r["p"]
        pick = 1 if max(p[0], p[2]) - p[1] < delta else int(np.argmax(p))
        ok += int(pick == r["y"])
    return ok / len(recs)

# ---- H9 : recalibration isotonique (pool-adjacent-violators) ----
def pav_fit(points):
    """points = [(p_annoncée, arrivé 0/1)] -> fonction monotone p -> p'."""
    pts = sorted(points)
    x = np.array([p for p, _ in pts]); y = np.array([float(o) for _, o in pts], float)
    w = np.ones_like(y)
    # PAV : moyennes par blocs croissants
    vals, wts, lo = [], [], []
    for i in range(len(y)):
        vals.append(y[i]); wts.append(w[i]); lo.append(i)
        while len(vals) > 1 and vals[-2] >= vals[-1]:
            v = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / (wts[-2] + wts[-1])
            wts[-2] += wts[-1]; vals[-2] = v
            vals.pop(); wts.pop(); lo.pop()
    fitted = np.empty_like(y)
    starts = lo + [len(y)]
    for k in range(len(vals)):
        fitted[starts[k]:starts[k + 1]] = vals[k]
    # interpolation par la grille des x (clip aux bords + plancher anti-zéro)
    xs, idx = np.unique(x, return_index=True)
    ys = np.maximum(fitted[idx], 5e-3)
    def f(p):
        return float(np.interp(p, xs, ys, left=ys[0], right=ys[-1]))
    return f

def h9_make(recs):
    pts = []
    for r in recs:
        for k in range(3):
            pts.append((float(r["p"][k]), int(r["y"] == k)))
    f = pav_fit(pts)
    def tf(r):
        p = np.array([f(float(r["p"][k])) for k in range(3)])
        return p / p.sum()
    return tf

def h11(nu):
    """L'ÉLAN DU TOMBEUR — dans CE tournoi, une équipe qui vient de voler des
    points à plus fort qu'elle surfe sur l'exploit au match suivant."""
    def tf(r):
        p = r["p"].copy()
        p[0] *= np.exp(nu * max(r["surp_h"], 0.0))
        p[2] *= np.exp(nu * max(r["surp_a"], 0.0))
        return p / p.sum()
    return tf

print("⚙ probas de base : 8 tournois TUNE (1994-2008)...")
tune = build(TUNE_T)
print(f"  {len(tune)} matchs de réglage")
print("⚙ probas de base : 9 tournois TEST (2010-2026, scellés pendant le réglage)...")
test = build(TEST_T)
print(f"  {len(test)} matchs de jugement")

base_tune = judge(tune)
base_test = judge(test)
print(f"\nBASE  TUNE ll {base_tune[0]:.4f} acc {100*base_tune[1]:.1f}%  | "
      f"TEST ll {base_test[0]:.4f} acc {100*base_test[1]:.1f}% · "
      f"séismes (p≤15%) : {base_test[3]} matchs, ll {base_test[2]:.4f}")

GRIDS = {
    "H1 ouverture": (h1, [0.05, 0.1, 0.15, 0.2, 0.3, 0.4]),
    "H2 champion": (h2, [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]),
    "H3 David": (h3, [0.5, 1.0, 2.0, 3.0, 5.0, 8.0]),
    "H3b David+nul": (h3b, [0.5, 1.0, 2.0, 3.0, 5.0, 8.0]),
    "H4 confédérations": (h4, [100.0, 200.0, 300.0, 450.0, 650.0, 900.0]),
    "H5 chaos": (h5, [-1.0, -0.5, -0.25, 0.25, 0.5, 1.0]),
    "H7 favori rassasié": (h7, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]),
    "H8 biscotto": (h8, [0.15, 0.3, 0.5, 0.7, 1.0]),
    "H11 élan du tombeur": (h11, [0.2, 0.4, 0.7, 1.0, 1.5]),
}
print("\n=== RÉGLAGE (1994-2008) puis ÉPREUVE DU FEU (2010-2026) ===")
verdicts = {}
for name, (maker, grid) in GRIDS.items():
    best_t, best_ll = None, base_tune[0]
    for t in grid:
        ll, _, _, _ = judge(tune, maker(t))
        if ll < best_ll - 1e-5:
            best_ll, best_t = ll, t
    if best_t is None:
        print(f"  {name:<20} ❌ mort au réglage (aucun gain même sur TUNE)")
        verdicts[name] = None
        continue
    ll, acc, ll_s, n_s = judge(test, maker(best_t))
    d_ll = ll - base_test[0]; d_s = ll_s - base_test[2]
    flag = "✅" if (d_ll < -0.0005 and d_s < 0) else ("⚡" if d_s < -0.01 and d_ll < 0.002 else "❌")
    print(f"  {name:<20} θ*={best_t:<5} tune {best_ll:.4f} | TEST ll {ll:.4f} ({d_ll:+.4f}) "
          f"acc {100*acc:.1f}% · séismes {ll_s:.4f} ({d_s:+.4f}) {flag}")
    verdicts[name] = (best_t, d_ll, d_s)

# H6 : politique de pick (la log-loss ne bouge pas, seule la précision).
best_d, best_acc = 0.0, base_tune[1]
for d in [0.02, 0.04, 0.06, 0.08, 0.10, 0.12]:
    a = pick_acc(tune, d)
    if a > best_acc + 1e-9:
        best_acc, best_d = a, d
if best_d > 0:
    a_test = pick_acc(test, best_d)
    print(f"  {'H6 oser le nul':<20} δ*={best_d:<5} tune acc {100*best_acc:.1f}% | "
          f"TEST acc {100*a_test:.1f}% ({100*(a_test-base_test[1]):+.1f} pt) "
          f"{'✅' if a_test > base_test[1] else '❌'}")
else:
    print(f"  {'H6 oser le nul':<20} ❌ mort au réglage")

# ---- H9 : recalibration isotonique apprise sur TUNE, jugée sur TEST ----
h9 = h9_make(tune)
ll_t9, _, _, _ = judge(tune, h9)
ll9, acc9, ll_s9, _ = judge(test, h9)
print(f"  {'H9 recalibration':<20} (PAV)   tune {ll_t9:.4f}* | TEST ll {ll9:.4f} "
      f"({ll9 - base_test[0]:+.4f}) acc {100*acc9:.1f}% · séismes {ll_s9:.4f} "
      f"({ll_s9 - base_test[2]:+.4f}) "
      f"{'✅' if ll9 < base_test[0] and ll_s9 < base_test[2] else '❌'}  (* in-sample)")

# ---- LES ALLIAGES CIBLÉS : David répare les séismes, confédés le global ----
def compose(tfs):
    def stack_tf(r):
        base = np.log(np.clip(r["p"], 1e-12, 1.0))
        logp = base.copy()
        for tf in tfs:
            logp += np.log(np.clip(tf(r), 1e-12, 1.0)) - base
        p = np.exp(logp - logp.max())
        return p / p.sum()
    return stack_tf

named = {n: GRIDS[n][0](v[0]) for n, v in verdicts.items() if v}
named["H9 recalibration"] = h9
combos = [c for c in (
    ["H3b David+nul", "H4 confédérations"],
    ["H3 David", "H4 confédérations"],
    ["H9 recalibration", "H4 confédérations"],
    ["H9 recalibration", "H3b David+nul", "H4 confédérations"],
) if all(n in named for n in c)]
stack_tf = None
print()
for c in combos:
    tf = compose([named[n] for n in c])
    ll_t, _, _, _ = judge(tune, tf)
    ll, acc, ll_s, n_s = judge(test, tf)
    mark = "✅" if (ll < base_test[0] and ll_s < base_test[2]) else "❌"
    print(f"  ALLIAGE [{' + '.join(x.split()[0] for x in c)}]  tune {ll_t:.4f} | "
          f"TEST ll {ll:.4f} ({ll - base_test[0]:+.4f}) acc {100*acc:.1f}% · "
          f"séismes {ll_s:.4f} ({ll_s - base_test[2]:+.4f}) {mark}")
    if mark == "✅" and stack_tf is None:
        stack_tf = tf

# ---- le mur des séismes : les 10 plus gros chocs du TEST, avant/après ----
print("\n=== LE MUR DES SÉISMES (TEST) — proba de base de l'issue arrivée ===")
shocks = sorted(test, key=lambda r: r["p"][r["y"]])[:10]
live = [(n, GRIDS[n][0](v[0])) for n, v in verdicts.items() if v]
if stack_tf:
    live.append(("ALLIAGE total", stack_tf))
for r in shocks:
    after = " ".join(f"{n.split()[0]}:{100*tf(r)[r['y']]:.1f}%" for n, tf in live)
    print(f"  {r['label']:<14} {r['home']}–{r['away']} → {['1','N','2'][r['y']]} "
          f"(base {100*r['p'][r['y']]:.1f}%) {after}")
