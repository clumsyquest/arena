# RÉSULTAT (10 juin 2026) : 20 alliages testés (K-scale, domicile, mémoire rapide,
# mode couperet) — réglés sur 1994-2008, jugés sur 2010-2026 :
# v2 actuel : ll 0.9340, précision 57.9% | meilleur alliage : ll 0.9346 (-0.8pt)
# VERDICT : les constantes v2 gardent la couronne. Le réglage ne transfère pas
# entre ères — preuve que le plafond modèle-seul est atteint.

"""LA FORGE — re-régler les constantes jamais optimisées du démon.
Réglage sur 1994-2008 (TUNE), jugement sur 2010-2026 (TEST, intouchable)."""
import numpy as np
from laplace.data import played
from laplace.ensemble import TOURNAMENTS as TEST_T

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

df = played()
N = len(df)
dates = df["date"].to_numpy()
hs = df["home_score"].to_numpy().astype(float)
aw = df["away_score"].to_numpy().astype(float)
neutral = df["neutral"].to_numpy().astype(bool)
tourn = df["tournament"].to_numpy()
H = df["home_team"].to_numpy(); A = df["away_team"].to_numpy()
friendly = tourn == "Friendly"

CONT = {"uefa euro","copa américa","african cup of nations","afc asian cup","gold cup",
        "concacaf championship","oceania nations cup","confederations cup","fifa confederations cup"}
K_base = np.empty(N)
for i in range(N):
    t = str(tourn[i]).lower()
    K_base[i] = 60 if t=="fifa world cup" else 50 if t in CONT else 40 if ("qualification" in t or "nations league" in t) else 20 if t=="friendly" else 30

def elo_pass(k_scale=1.0, home_adv=100.0, k_fast=None):
    """Une passe Elo ; renvoie ratings pré-match (et version rapide si k_fast)."""
    r = {}; rf = {}
    ph = np.empty(N); pa = np.empty(N)
    phf = np.empty(N) if k_fast else None; paf = np.empty(N) if k_fast else None
    for i in range(N):
        a, b = H[i], A[i]
        ra = r.get(a, 1500.0); rb = r.get(b, 1500.0)
        ph[i] = ra; pa[i] = rb
        d = abs(hs[i]-aw[i]); g = 1.0 if d<=1 else 1.5 if d==2 else (11.0+d)/8.0
        w = 1.0 if hs[i]>aw[i] else 0.5 if hs[i]==aw[i] else 0.0
        we = 1.0/(1.0+10.0**(-(ra-rb+(0 if neutral[i] else home_adv))/400.0))
        delta = k_scale*K_base[i]*g*(w-we)
        r[a] = ra+delta; r[b] = rb-delta
        if k_fast:
            fa = rf.get(a, 1500.0); fb = rf.get(b, 1500.0)
            phf[i] = fa; paf[i] = fb
            wef = 1.0/(1.0+10.0**(-(fa-fb+(0 if neutral[i] else home_adv))/400.0))
            df_ = k_fast*K_base[i]*g*(w-wef)
            rf[a] = fa+df_; rf[b] = fb-df_
    return ph, pa, phf, paf

def ko_flag_for(tlist):
    """Marque les matchs en phase couperet (dernier ~45% du tournoi)."""
    ko = np.zeros(N, bool)
    for _, name, s, e in tlist:
        t0, t1 = np.datetime64(s), np.datetime64(e)
        span = (t1-t0).astype(float)
        m = (tourn==name)&(dates>=t0)&(dates<=t1)
        ko |= m & ((dates-t0).astype(float) > 0.55*span)
    return ko

KO_ALL = ko_flag_for(TUNE_T) | ko_flag_for(TEST_T) | ko_flag_for(
    [("x","FIFA World Cup","2010-06-11","2010-07-12"),("x","FIFA World Cup","2014-06-12","2014-07-14")])

def fit_and_eval(ph, pa, tlist, use_ko=False):
    tot_ll, tot_acc, n_tot = 0.0, 0.0, 0
    import math
    gx = np.arange(9); fact = np.array([math.factorial(k) for k in gx], float)
    for _, name, s, e in tlist:
        t0, t1 = np.datetime64(s), np.datetime64(e)
        wind = (dates < t0) & (dates >= t0 - np.timedelta64(int(16*365.25),"D"))
        idx = np.flatnonzero(wind)
        age = (t0-dates[idx]).astype('timedelta64[D]').astype(float)/365.25
        w = 0.5**(age/4.0)*np.where(friendly[idx],0.5,1.0)
        d = (ph[idx]-pa[idx])/400.0
        hf = (~neutral[idx]).astype(float)
        cols_h = [np.ones(len(idx)), d, hf, np.zeros(len(idx))]
        cols_a = [np.ones(len(idx)), -d, np.zeros(len(idx)), hf]
        if use_ko:
            k_ = KO_ALL[idx].astype(float)
            cols_h.append(k_); cols_a.append(k_)
        X = np.vstack([np.column_stack(cols_h), np.column_stack(cols_a)])
        y = np.concatenate([hs[idx], aw[idx]]); ww = np.concatenate([w,w])
        beta = np.zeros(X.shape[1])
        for _ in range(30):
            lam = np.exp(np.clip(X@beta,-8,5))
            g = X.T@(ww*(y-lam)); Hm = X.T@(X*(ww*lam)[:,None])
            try: st = np.linalg.solve(Hm+1e-9*np.eye(len(beta)), g)
            except np.linalg.LinAlgError: break
            beta += st
            if np.abs(st).max()<1e-10: break
        lh = np.exp(np.clip(X[:len(idx)]@beta,-8,5)); la = np.exp(np.clip(X[len(idx):]@beta,-8,5))
        m00=(hs[idx]==0)&(aw[idx]==0); m01=(hs[idx]==0)&(aw[idx]==1); m10=(hs[idx]==1)&(aw[idx]==0); m11=(hs[idx]==1)&(aw[idx]==1)
        best_rho, best_l = 0.0, -np.inf
        for rho in np.arange(-0.25,0.10,0.01):
            tau = np.ones(len(idx))
            tau[m00]=np.maximum(1-lh[m00]*la[m00]*rho,1e-10); tau[m01]=np.maximum(1+lh[m01]*rho,1e-10)
            tau[m10]=np.maximum(1+la[m10]*rho,1e-10); tau[m11]=np.maximum(1-rho,1e-10)
            l = float(np.sum(w*np.log(tau)))
            if l>best_l: best_l,best_rho = l,rho
        in_cup = (tourn==name)&(dates>=t0)&(dates<=t1)
        ci = np.flatnonzero(in_cup)
        for i in ci:
            dd = (ph[i]-pa[i])/400.0
            hfl = 0.0 if neutral[i] else 1.0
            xh = [1.0, dd, hfl, 0.0]; xa = [1.0, -dd, 0.0, hfl]
            if use_ko:
                xh.append(float(KO_ALL[i])); xa.append(float(KO_ALL[i]))
            lH = np.exp(np.clip(np.dot(xh,beta),-8,5)); lA = np.exp(np.clip(np.dot(xa,beta),-8,5))
            pA = np.exp(-lH)*lH**gx/fact; pB = np.exp(-lA)*lA**gx/fact
            M = np.outer(pA,pB); r = best_rho
            M[0,0]*=max(1-lH*lA*r,1e-10); M[0,1]*=max(1+lH*r,1e-10); M[1,0]*=max(1+lA*r,1e-10); M[1,1]*=max(1-r,1e-10)
            M/=M.sum()
            p = np.array([np.tril(M,-1).sum(), np.trace(M), np.triu(M,1).sum()])
            yv = 0 if hs[i]>aw[i] else (1 if hs[i]==aw[i] else 2)
            tot_ll -= np.log(max(p[yv],1e-12)); tot_acc += (p.argmax()==yv); n_tot += 1
    return tot_ll/n_tot, tot_acc/n_tot

import itertools, json, time
results = {}
print("FORGE sur 1994-2008 (le TEST 2010-2026 reste sous scellés) :")
best = (None, np.inf)
for ks in [0.7, 0.85, 1.0, 1.15]:
    for ha in [60.0, 80.0, 100.0]:
        ph, pa, _, _ = elo_pass(k_scale=ks, home_adv=ha)
        ll, acc = fit_and_eval(ph, pa, TUNE_T)
        tag = f"K×{ks} H{ha:.0f}"
        results[tag] = (ll, acc)
        star = ""
        if ll < best[1]: best = ((ks, ha), ll); star = " ◄"
        print(f"  {tag:<14} tune-ll {ll:.4f}  acc {100*acc:.1f}%{star}")
json.dump({k: v for k, v in results.items()}, open('/tmp/forge1.json','w'))
print("MEILLEUR:", best)

print("\nFORGE 2 — K élevé, alliage mémoire rapide, mode couperet :")
rows = []
for ks in [1.15, 1.3, 1.45]:
    ph, pa, _, _ = elo_pass(k_scale=ks, home_adv=100.0)
    ll, acc = fit_and_eval(ph, pa, TUNE_T)
    rows.append((f"K×{ks}", ll, acc))
    print(f"  K×{ks:<22} tune-ll {ll:.4f}  acc {100*acc:.1f}%")

ph_s, pa_s, ph_f, pa_f = elo_pass(k_scale=1.15, home_adv=100.0, k_fast=2.5*1.15)
for alpha in [0.15, 0.3]:
    bh = (1-alpha)*ph_s + alpha*ph_f
    ba = (1-alpha)*pa_s + alpha*pa_f
    ll, acc = fit_and_eval(bh, ba, TUNE_T)
    rows.append((f"K×1.15 + {int(alpha*100)}% rapide", ll, acc))
    print(f"  K×1.15 + {int(alpha*100):>2}% mémoire rapide  tune-ll {ll:.4f}  acc {100*acc:.1f}%")

ll, acc = fit_and_eval(ph_s, pa_s, TUNE_T, use_ko=True)
rows.append(("K×1.15 + mode couperet", ll, acc))
print(f"  K×1.15 + mode couperet     tune-ll {ll:.4f}  acc {100*acc:.1f}%")

print("\nFORGE 3 — derniers alliages sur tune, puis ÉPREUVE DU FEU sur test :")
candidates = {}
for ks, alpha in [(1.3, 0.15), (1.45, 0.15), (1.15, 0.15)]:
    ph_s2, pa_s2, ph_f2, pa_f2 = elo_pass(k_scale=ks, home_adv=100.0, k_fast=2.5*ks)
    bh = (1-alpha)*ph_s2 + alpha*ph_f2
    ba = (1-alpha)*pa_s2 + alpha*pa_f2
    ll, acc = fit_and_eval(bh, ba, TUNE_T)
    candidates[(ks, alpha)] = (ll, acc, bh, ba)
    print(f"  K×{ks} + {int(alpha*100)}% rapide : tune-ll {ll:.4f}  acc {100*acc:.1f}%")

best_key = min(candidates, key=lambda k: candidates[k][0])
print(f"\nALLIAGE RETENU : K×{best_key[0]} + {int(best_key[1]*100)}% mémoire rapide")
_,_, bh, ba = candidates[best_key]

print("\n=== ÉPREUVE DU FEU (2010-2026, jamais vu pendant la forge) ===")
ph0, pa0, _, _ = elo_pass(1.0, 100.0)
ll0, acc0 = fit_and_eval(ph0, pa0, TEST_T)
print(f"  v2 actuel (K×1.0, mémoire pure)   : ll {ll0:.4f}  acc {100*acc0:.1f}%")
ll1, acc1 = fit_and_eval(bh, ba, TEST_T)
print(f"  v3 forgé  (alliage)               : ll {ll1:.4f}  acc {100*acc1:.1f}%")
print(f"  Δ : {ll1-ll0:+.4f} log-loss, {100*(acc1-acc0):+.1f} pts de précision")
