"""Interface de commandement du Démon de Laplace.

    python -m laplace simulate          # le tournoi entier, 20 000 univers
    python -m laplace match France Brésil
    python -m laplace today             # les prophéties du jour
    python -m laplace groups            # destin de chaque groupe
    python -m laplace ratings           # classement Elo mondial
    python -m laplace backtest          # la preuve par le passé
    python -m laplace update            # données fraîches
"""

import argparse
import sys
from datetime import date as _date

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

FLAGS = {
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czech Republic": "🇨🇿",
    "Canada": "🇨🇦", "Bosnia and Herzegovina": "🇧🇦", "Qatar": "🇶🇦", "Switzerland": "🇨🇭",
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "United States": "🇺🇸", "Paraguay": "🇵🇾", "Australia": "🇦🇺", "Turkey": "🇹🇷",
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Ivory Coast": "🇨🇮", "Ecuador": "🇪🇨",
    "Netherlands": "🇳🇱", "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳",
    "Belgium": "🇧🇪", "Egypt": "🇪🇬", "Iran": "🇮🇷", "New Zealand": "🇳🇿",
    "Spain": "🇪🇸", "Cape Verde": "🇨🇻", "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾",
    "France": "🇫🇷", "Senegal": "🇸🇳", "Iraq": "🇮🇶", "Norway": "🇳🇴",
    "Argentina": "🇦🇷", "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴",
    "Portugal": "🇵🇹", "DR Congo": "🇨🇩", "Uzbekistan": "🇺🇿", "Colombia": "🇨🇴",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Croatia": "🇭🇷", "Ghana": "🇬🇭", "Panama": "🇵🇦",
    "Italy": "🇮🇹", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "Denmark": "🇩🇰", "Nigeria": "🇳🇬",
    "Chile": "🇨🇱", "Peru": "🇵🇪", "Russia": "🇷🇺", "Ukraine": "🇺🇦",
    "Poland": "🇵🇱", "Serbia": "🇷🇸", "Greece": "🇬🇷", "Cameroon": "🇨🇲",
    "Mali": "🇲🇱", "Venezuela": "🇻🇪", "Costa Rica": "🇨🇷", "Hungary": "🇭🇺",
    "Slovakia": "🇸🇰", "Romania": "🇷🇴", "Israel": "🇮🇱", "Finland": "🇫🇮",
}


def flag(team):
    return FLAGS.get(team, "⚽")


def bar(p, width=22, color=GREEN):
    full = int(round(p * width))
    return f"{color}{'█' * full}{DIM}{'░' * (width - full)}{RESET}"


def pct(p, hot=0.15):
    s = f"{100 * p:5.1f}%"
    if p >= hot:
        return f"{BOLD}{GREEN}{s}{RESET}"
    if p >= hot / 3:
        return f"{YELLOW}{s}{RESET}"
    return f"{DIM}{s}{RESET}"


BANNER = f"""{MAGENTA}{BOLD}
   ╔══════════════════════════════════════════════════════════╗
   ║          🔮  L E   D É M O N   D E   L A P L A C E  ⚽    ║
   ║     « L'avenir, comme le passé, présent à mes yeux »      ║
   ╚══════════════════════════════════════════════════════════╝{RESET}"""


def _oracle(verbose=True, engine="v2"):
    if verbose:
        print(f"{DIM}⚙  Le démon relit toute l'histoire du football (1872 → aujourd'hui)...{RESET}")
    if engine == "v1":
        from laplace import build_oracle

        return build_oracle(verbose=verbose)
    from laplace.ensemble import build_ensemble

    return build_ensemble(verbose=verbose)


def cmd_update(args):
    from laplace.data import update

    print(f"{DIM}⬇  Téléchargement des données fraîches...{RESET}")
    path = update()
    from laplace.data import played

    df = played()
    print(f"{GREEN}✓{RESET} {len(df)} matchs joués en mémoire, dernier : {df['date'].max().date()}")


def cmd_ratings(args):
    oracle = _oracle()
    from laplace.elo import top

    print(BANNER)
    print(f"\n{BOLD}   CLASSEMENT ELO MONDIAL — recalculé depuis 1872{RESET}\n")
    rows = top(oracle.ratings, args.top)
    best = rows[0][1]
    for i, (team, r) in enumerate(rows, 1):
        b = bar((r - 1500) / (best - 1500), 26, CYAN)
        print(f"   {i:>3}. {flag(team)} {team:<22} {r:7.0f}  {b}")
    print()


def _print_match(p):
    a, b = p["team_a"], p["team_b"]
    print(f"\n   {BOLD}{flag(a)} {a}  🆚  {flag(b)} {b}{RESET}")
    print(
        f"   {DIM}Elo {p['elo_a']:.0f} vs {p['elo_b']:.0f} · "
        f"buts attendus {p['lambda_a']:.2f} — {p['lambda_b']:.2f}{RESET}"
    )
    rows = [
        (f"{a} gagne", p["p_win"], GREEN),
        ("Match nul", p["p_draw"], YELLOW),
        (f"{b} gagne", p["p_loss"], RED),
    ]
    for label, prob, color in rows:
        print(f"   {label:<24} {bar(prob, 24, color)} {BOLD}{100 * prob:5.1f}%{RESET}")
    scores = " · ".join(
        f"{BOLD}{i}-{j}{RESET} {DIM}({100 * q:.1f}%){RESET}" for i, j, q in p["top_scores"][:5]
    )
    print(f"   Scores les plus probables : {scores}")


def cmd_match(args):
    oracle = _oracle(engine=args.engine)
    home_ind = {"a": 1, "b": -1, "neutral": 0}[args.home]
    p = oracle.match(args.team_a, args.team_b, home_ind)
    print(BANNER)
    venue = {1: f"chez {p['team_a']}", -1: f"chez {p['team_b']}", 0: "terrain neutre"}[home_ind]
    print(f"\n   {MAGENTA}PROPHÉTIE{RESET} {DIM}({venue}){RESET}")
    _print_match(p)
    print()


def cmd_today(args):
    from laplace.data import fixtures

    oracle = _oracle(engine=args.engine)
    day = args.date or str(_date.today())
    fx = fixtures(start=day, end=day)
    print(BANNER)
    print(f"\n   {BOLD}PROPHÉTIES DU {day}{RESET}")
    if fx.empty:
        print(f"   {DIM}Aucun match de Coupe du Monde ce jour-là.{RESET}")
        print(f"   {DIM}(pense à `python -m laplace update` pendant le tournoi){RESET}\n")
        return
    for row in fx.itertuples():
        # Dans le CSV, l'équipe hôte est toujours listée en premier (neutral=False).
        h = 0 if row.neutral else 1
        p = oracle.match(row.home_team, row.away_team, h)
        _print_match(p)
        print(f"   {DIM}📍 {row.city} ({row.country}){RESET}")
    print()


def cmd_groups(args):
    oracle = _oracle(engine=args.engine)
    from laplace.simulate import Simulator
    from laplace.worldcup import GROUPS

    print(BANNER)
    print(f"\n{DIM}⚙  {args.n} univers parallèles en cours de simulation...{RESET}")
    sim = Simulator(oracle, seed=args.seed)
    df = sim.run(args.n)
    d = df.set_index("team")
    print(f"\n{BOLD}   DESTIN DES 12 GROUPES{RESET}  {DIM}(P 1er · P 2e · P qualifié · pts attendus){RESET}")
    for g, teams in GROUPS.items():
        print(f"\n   {BOLD}{CYAN}Groupe {g}{RESET}")
        for t in sorted(teams, key=lambda t: -d.loc[t, "exp_pts"]):
            r = d.loc[t]
            print(
                f"     {flag(t)} {t:<24} {pct(r['p_group_win'], 0.5)}  "
                f"{pct(r['p_runner_up'], 0.5)}  {pct(r['p_r32'], 0.6)}  "
                f"{DIM}{r['exp_pts']:.1f} pts{RESET}"
            )
    print()


def cmd_simulate(args):
    oracle = _oracle(engine=args.engine)
    from laplace.simulate import Simulator

    print(BANNER)
    print(f"\n{DIM}⚙  Le démon fait jouer la Coupe du Monde dans {args.n} univers parallèles...{RESET}")
    sim = Simulator(oracle, seed=args.seed)
    if sim.fixed:
        print(f"{DIM}⚡ Démon vivant : {len(sim.fixed)} résultats réels déjà gravés, "
              f"seul le futur restant est simulé.{RESET}")
    df = sim.run(args.n, progress=args.n // 4 if args.n >= 4000 else None)

    podium = df.head(3)
    print(f"\n{BOLD}   🏆 PROPHÉTIE FINALE — COUPE DU MONDE 2026{RESET}")
    medals = ["🥇", "🥈", "🥉"]
    for m, (_, r) in zip(medals, podium.iterrows()):
        print(f"        {m} {flag(r['team'])} {BOLD}{r['team']}{RESET} — {BOLD}{100 * r['p_champion']:.1f}%{RESET} de chances de soulever le trophée")

    header = f"{'16es':>7}{'8es':>7}{'¼':>8}{'½':>8}{'Fin.':>8}{'🏆':>7}"
    print(f"\n   {BOLD}{'#':>2}  {'Équipe':<25}{'Grp':<4}{'Elo':<6}{header}{RESET}")
    shown = df[df["p_champion"] >= args.cutoff] if args.cutoff else df
    for i, r in shown.iterrows():
        cells = " ".join([
            pct(r["p_r32"], 0.9),
            pct(r["p_r16"], 0.6),
            pct(r["p_qf"], 0.35),
            pct(r["p_sf"], 0.2),
            pct(r["p_final"], 0.12),
            pct(r["p_champion"], 0.08),
        ])
        line = (
            f"   {i + 1:>2}  {flag(r['team'])} {r['team']:<22} {r['group']:<3}"
            f"{r['elo']:<6.0f}{cells}"
        )
        print(line + "  " + bar(min(r["p_champion"] / max(df["p_champion"].iloc[0], 1e-9), 1.0), 14, MAGENTA))
    if args.cutoff:
        print(f"   {DIM}... équipes sous {100 * args.cutoff:.1f}% de titre masquées (--cutoff 0 pour tout voir){RESET}")

    print(f"\n   {BOLD}LES FINALES LES PLUS PROBABLES{RESET}")
    for (a, b), p in sim.finals[:5]:
        print(f"     {flag(a)} {a}  🆚  {flag(b)} {b}   {BOLD}{100 * p:4.1f}%{RESET} des univers")

    elo_rank = {t: i + 1 for i, (t, _) in enumerate(
        sorted(((r["team"], r["elo"]) for _, r in df.iterrows()), key=lambda x: -x[1])
    )}
    dark = max(
        (r for _, r in df.iterrows() if elo_rank[r["team"]] > 10),
        key=lambda r: r["p_sf"],
    )
    print(f"\n   🐎 {BOLD}Outsider du démon{RESET} : {flag(dark['team'])} {dark['team']} "
          f"(Elo n°{elo_rank[dark['team']]} seulement, mais {100 * dark['p_sf']:.1f}% de demi-finale)")

    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"\n   {GREEN}✓{RESET} Prophétie complète exportée : {args.csv}")
    print()


def cmd_backtest(args):
    from laplace.backtest import CUPS, backtest

    print(BANNER)
    print(f"\n{BOLD}   LE SERMENT D'HONNÊTETÉ — le démon jugé sur le passé{RESET}")
    print(f"{DIM}   (il ne voit que les matchs ANTÉRIEURS à chaque tournoi, puis prédit tout){RESET}\n")
    years = [args.cup] if args.cup else sorted(CUPS)
    for y in years:
        r = backtest(y)
        print(f"   {BOLD}{CYAN}Coupe du Monde {y}{RESET} — {r['n_matches']} matchs prédits")
        print(
            f"     log-loss {BOLD}{r['logloss']:.4f}{RESET} en mode vivant "
            f"{DIM}(figé : {r['logloss_frozen']:.4f} · hasard uniforme : {r['uniform_logloss']:.4f} "
            f"· taux de base : {r['base_logloss']:.4f}){RESET}"
        )
        print(
            f"     Brier {BOLD}{r['brier']:.4f}{RESET} {DIM}(hasard : {r['uniform_brier']:.4f}){RESET}"
            f" · bon pronostic {BOLD}{100 * r['accuracy']:.1f}%{RESET} des matchs"
        )
        t5 = " · ".join(f"{flag(t)} {t}" for t, _ in r["pre_top5"])
        print(f"     Top 5 Elo avant tournoi : {t5}")
        print(
            f"     Champion réel : {flag(r['champion'])} {BOLD}{r['champion']}{RESET}"
            f" — n°{r['champion_elo_rank']} de son classement pré-tournoi\n"
        )


def cmd_market(args):
    from laplace.market import UNLOCK_HELP, edges

    print(BANNER)
    print(f"\n{BOLD}   LE VOLEUR DE CERVEAUX — démon vs marché mondial{RESET}\n")
    try:
        oracle = _oracle(engine=args.engine)
        rows = edges(oracle, threshold=args.threshold)
    except PermissionError as e:
        print(str(e))
        return
    except LookupError as e:
        print(f"   {YELLOW}{e}{RESET}")
        return
    if not rows:
        print(f"   {DIM}Aucun match coté trouvé.{RESET}")
        return
    for r in rows:
        a, b = r["home"], r["away"]
        pd_, pm, pf = r["p_demon"], r["p_market"], r["p_fused"]
        mark = f" {MAGENTA}{BOLD}⚡ FAILLE ({r['gap']:+.0%} sur {r['gap_on']}){RESET}" if r["is_edge"] else ""
        print(f"   {flag(a)} {a} – {flag(b)} {b}  {DIM}({r['sources']}){RESET}{mark}")
        print(f"     {BOLD}démon  {pd_[0]:5.0%} {pd_[1]:5.0%} {pd_[2]:5.0%}{RESET}   "
              f"marché {pm[0]:5.0%} {pm[1]:5.0%} {pm[2]:5.0%}   "
              f"{DIM}fusion {pf[0]:5.0%} {pf[1]:5.0%} {pf[2]:5.0%}{RESET}")
    if args.enroll:
        from laplace.market import enroll

        counts = enroll(rows)
        print(f"\n   ⚔  Concurrents inscrits au registre : "
              f"MARCHE +{counts['MARCHE']} · FUSION +{counts['FUSION']} affiches")
        print(f"   {DIM}Le sceau du démon reste 100% démon — `laplace verdict` départagera.{RESET}")
    print()


def cmd_adjust(args):
    from laplace import scout

    if args.list:
        adj = scout.load()
        if not adj:
            print(f"{DIM}Aucun ajustement d'éclaireur actif.{RESET}")
        for t, info in adj.items():
            print(f"   {flag(t)} {t:<22} {info['delta']:+.0f} Elo  {DIM}{info.get('reason', '')}{RESET}")
        return
    if args.clear:
        scout.clear(None if args.clear == "all" else args.clear)
        print(f"{GREEN}✓{RESET} Ajustements effacés.")
        return
    if args.team is None or args.delta is None:
        print(f"{RED}✗ usage : laplace adjust ÉQUIPE ±DELTA [--reason \"...\"]{RESET}")
        return
    from laplace.predict import resolve

    oracle = _oracle(verbose=False, engine="v1")
    team = resolve(args.team, oracle.ratings)
    scout.set_adjustment(team, args.delta, args.reason or "")
    print(f"{GREEN}✓{RESET} {flag(team)} {team} : {args.delta:+.0f} Elo "
          f"{DIM}({args.reason or 'sans motif'}) — appliqué à tous les cerveaux dès maintenant.{RESET}")


def _scout_paused():
    """Capture puis vide les ajustements de l'éclaireur (pour un build PUR)."""
    from laplace import scout

    snap = scout.load()
    scout.save({})
    return snap


def _seal_rows(oracle, fx, day):
    rows = []
    for row in fx.itertuples():
        h = 0 if row.neutral else 1
        p = oracle.match(row.home_team, row.away_team, h)
        pr = [p["p_win"], p["p_draw"], p["p_loss"]]
        pick = ["1", "N", "2"][max(range(3), key=lambda i: pr[i])]
        rows.append([day, p["team_a"], p["team_b"],
                     f"{pr[0]:.4f}", f"{pr[1]:.4f}", f"{pr[2]:.4f}", pick])
    return rows


def cmd_seal(args):
    import csv
    import os

    from laplace import scout
    from laplace.data import fixtures

    if args.tournament:
        _seal_tournament(args)
        return

    day = args.date or str(_date.today())
    fx = fixtures(start=day, end=day)
    if fx.empty:
        print(f"{YELLOW}Aucun match à sceller le {day}.{RESET}")
        return
    os.makedirs("prophecies", exist_ok=True)
    path = f"prophecies/SEAL_{day}.csv"
    if os.path.exists(path):
        print(f"{RED}✗ {path} existe déjà — un sceau ne se réécrit JAMAIS (loi n°4).{RESET}")
        return

    # Le sceau officiel est le démon PUR : le modèle seul, sans info terrain.
    snap = _scout_paused()
    try:
        oracle = _oracle(engine="v2")
    finally:
        scout.save(snap)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "team_a", "team_b", "p1", "pn", "p2", "pick"])
        w.writerows(_seal_rows(oracle, fx, day))
    print(f"{GREEN}🔏 Scellé : {path} — grave-le : git add prophecies && git commit{RESET}")

    # Le 5e duelliste : ÉCLAIREUR = démon + intelligence terrain (blessures...),
    # inscrit comme simple concurrent du registre. L'arène jugera si l'info
    # terrain vaut des points de log-loss.
    if snap:
        adj_oracle = _oracle(verbose=False, engine="v2")
        cpath = "prophecies/challenger_ECLAIREUR.csv"
        seen = set()
        if os.path.exists(cpath):
            with open(cpath) as f:
                seen = {(r["date"], r["team_a"], r["team_b"]) for r in csv.DictReader(f)}
        with open(cpath, "a", newline="") as f:
            w = csv.writer(f)
            if f.tell() == 0:
                w.writerow(["date", "team_a", "team_b", "p1", "pn", "p2", "pick"])
            new = [r for r in _seal_rows(adj_oracle, fx, day)
                   if (r[0], r[1], r[2]) not in seen]
            w.writerows(new)
        actifs = " · ".join(f"{t} {i['delta']:+.0f}" for t, i in snap.items())
        print(f"{GREEN}🔭 Éclaireur inscrit (+{len(new)} affiches){RESET} {DIM}[{actifs}]{RESET}")


def _seal_tournament(args):
    import csv
    import os

    from laplace import scout
    from laplace.data import played
    from laplace.simulate import Simulator

    day = args.date or str(_date.today())
    path = f"prophecies/TOURNAMENT_SEAL_{day}.csv"
    if os.path.exists(path):
        print(f"{RED}✗ {path} existe déjà — un sceau ne se réécrit JAMAIS (loi n°4).{RESET}")
        return
    os.makedirs("prophecies", exist_ok=True)

    snap = _scout_paused()
    try:
        oracle = _oracle(engine="v2")
    finally:
        scout.save(snap)
    sim = Simulator(oracle, seed=args.seed)
    print(f"{DIM}⚙  Sceau Total : {args.n} univers (graine {args.seed}, démon pur, "
          f"{len(sim.fixed)} résultats réels gravés)...{RESET}")
    df = sim.run(args.n, progress=args.n // 4)
    last = str(played()["date"].max().date())
    cols = ("p_group_win", "p_runner_up", "p_r32", "p_r16",
            "p_qf", "p_sf", "p_final", "p_champion")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sealed_on", "data_until", "n_universes", "seed",
                    "team", "group", "elo", *cols, "exp_pts"])
        for _, r in df.iterrows():
            w.writerow([day, last, args.n, args.seed, r["team"], r["group"],
                        f"{r['elo']:.1f}", *(f"{r[c]:.5f}" for c in cols),
                        f"{r['exp_pts']:.3f}"])
    print(f"{GREEN}🔏 Sceau Total : {path} — le destin des 48, gravé avant le réel.{RESET}")
    for m, (_, r) in zip(["🥇", "🥈", "🥉"], df.head(3).iterrows()):
        print(f"     {m} {flag(r['team'])} {r['team']} — {100 * r['p_champion']:.2f}%")


def _live_2026_records():
    """Les sceaux du DÉMON jugés par le réel (format du pedigree)."""
    import csv
    import glob

    import numpy as np

    from laplace.data import played
    from laplace.predict import resolve

    df = played()
    wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= np.datetime64("2026-06-01"))]
    results = {(r.home_team, r.away_team): (int(r.home_score), int(r.away_score))
               for r in wc.itertuples()}
    known = set(df["home_team"]) | set(df["away_team"])
    records = []
    for path in sorted(glob.glob("prophecies/SEAL_*.csv")):
        with open(path) as f:
            for row in csv.DictReader(f):
                try:
                    a = resolve(row["team_a"].strip(), known)
                    b = resolve(row["team_b"].strip(), known)
                except ValueError:
                    continue
                res = results.get((a, b)) or tuple(reversed(results.get((b, a), ()))) or None
                if not res:
                    continue
                y = 0 if res[0] > res[1] else (1 if res[0] == res[1] else 2)
                p = [float(row["p1"]), float(row["pn"]), float(row["p2"])]
                s = sum(p)
                p = [x / s for x in p]
                records.append({
                    "tournament": "CDM 2026 (vivant)",
                    "date": row["date"],
                    "home": a, "away": b,
                    "p1": p[0], "pn": p[1], "p2": p[2],
                    "outcome": ["1", "N", "2"][y],
                    "pick": ["1", "N", "2"][max(range(3), key=lambda i: p[i])],
                    "hit": int(max(range(3), key=lambda i: p[i]) == y),
                    "logloss": float(-__import__("numpy").log(max(p[y], 1e-12))),
                })
    return records


def _print_global_precision():
    """LE chiffre que le commandant veut voir : la précision globale, toujours."""
    from laplace.pedigree import load, metrics

    ped = load()
    live = _live_2026_records()
    if not ped and not live:
        return
    print(f"\n   {BOLD}{MAGENTA}PRÉCISION GLOBALE DU DÉMON{RESET} "
          f"{DIM}(log-loss : plus bas = plus fort ; hasard 1.0986 / 33%){RESET}")
    rows = []
    if ped:
        rows.append(("Pedigree 2010-2026 (marche avant)", metrics(ped)))
    if live:
        rows.append(("CDM 2026 en cours (sceaux jugés)", metrics(live)))
    if ped and live:
        rows.append(("GLOBAL — pedigree + 2026", metrics(ped + live)))
    for label, m in rows:
        print(f"     {label:<36} {m['n']:>4} matchs · "
              f"log-loss {BOLD}{m['logloss']:.4f}{RESET} · "
              f"précision {BOLD}{100 * m['accuracy']:.1f}%{RESET} · "
              f"Brier {m['brier']:.4f}")
    if not ped:
        print(f"     {DIM}(pedigree absent — `python -m laplace pedigree` pour le graver){RESET}")


def cmd_pedigree(args):
    from laplace.pedigree import (PEDIGREE_CSV, by_tournament, calibration,
                                  metrics, replay, save)

    print(BANNER)
    print(f"\n{BOLD}   LE PEDIGREE — la précision globale, rejouée sous tes yeux{RESET}")
    print(f"{DIM}   (marche avant stricte : le démon ne voit jamais le futur du match prédit){RESET}\n")
    records = replay(verbose=True)
    path = save(records)
    m = metrics(records)
    print(f"\n   {BOLD}GLOBAL : {m['n']} matchs · log-loss {m['logloss']:.4f} · "
          f"précision {100 * m['accuracy']:.1f}% · Brier {m['brier']:.4f}{RESET}")
    print(f"   {DIM}hasard uniforme : 1.0986 / 33.3% · marché mondial : ~0.93-0.95 / ~57%{RESET}")
    print(f"\n   {BOLD}CALIBRATION{RESET} {DIM}(annoncé vs arrivé — l'honnêteté se mesure){RESET}")
    for b in calibration(records):
        print(f"     {b['bucket']:>8}  annoncé {100 * b['announced']:5.1f}%  "
              f"arrivé {100 * b['realized']:5.1f}%  {DIM}({b['n']} probas){RESET}")
    print(f"\n   {GREEN}✓{RESET} Registre gravé : {path} ({m['n']} lignes)")

    if args.md:
        _write_pedigree_md(records, m)
        print(f"   {GREEN}✓{RESET} Vitrine : prophecies/PEDIGREE.md")
    print()


def _write_pedigree_md(records, m):
    from laplace.pedigree import by_tournament, calibration

    lines = [
        "# 🗡️ LE PEDIGREE DU DÉMON — sa précision globale, prouvée",
        "",
        "> Protocole : **marche avant stricte, mode vivant** — pour chaque match,",
        "> le démon n'a vu que les matchs antérieurs ; modèles ajustés avant chaque",
        "> tournoi, Elo mis à jour match après match. Rejouable : `python -m laplace pedigree`.",
        "",
        f"## LE CHIFFRE GLOBAL : {m['n']} matchs de grands tournois (2010-2026)",
        "",
        f"- **log-loss {m['logloss']:.4f}** (hasard : 1.0986 · marché mondial : ~0.93-0.95)",
        f"- **précision {100 * m['accuracy']:.1f}%** sur 3 issues (hasard : 33.3% · marché : ~57%)",
        f"- **Brier {m['brier']:.4f}** (hasard : 0.6667)",
        "",
        "## Par tournoi",
        "",
        "| Tournoi | n | log-loss | précision |",
        "|---|---|---|---|",
    ]
    for t in by_tournament(records):
        lines.append(f"| {t['label']} | {t['n']} | {t['logloss']:.4f} | {100 * t['accuracy']:.1f}% |")
    lines += [
        "",
        "## Calibration — quand le démon annonce X%, ça arrive X% du temps",
        "",
        "| Annoncé (tranche) | Annoncé (moyen) | Arrivé | n probas |",
        "|---|---|---|---|",
    ]
    for b in calibration(records):
        lines.append(f"| {b['bucket']} | {100 * b['announced']:.1f}% | "
                     f"{100 * b['realized']:.1f}% | {b['n']} |")
    picks = [(max(r["p1"], r["pn"], r["p2"]), r) for r in records]
    tiers = [(0.0, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 1.01)]
    lines += [
        "",
        "## Le baromètre de confiance — plus le démon est sûr, plus il a raison",
        "",
        "| Confiance du pronostic | n | précision |",
        "|---|---|---|",
    ]
    for lo, hi in tiers:
        sub = [r for c, r in picks if lo <= c < hi]
        if sub:
            acc = sum(r["hit"] for r in sub) / len(sub)
            lines.append(f"| {100 * lo:.0f}–{min(100 * hi, 100):.0f}% | {len(sub)} | {100 * acc:.1f}% |")

    draws = [r for r in records if r["pick"] == "N"]
    draws_hit = [r for r in draws if r["hit"]]
    if draws:
        draw_line = (f"- **Nuls osés** : prédire un match nul est le pari le plus dur du "
                     f"football — le démon l'a tenté {len(draws)} fois, réussi "
                     f"{len(draws_hit)} ({100 * len(draws_hit) / len(draws):.0f}%).")
    else:
        draw_line = ("- **Le nul, jamais en pronostic n°1** : sur l'ensemble du pedigree, "
                     "aucune affiche n'a eu le nul comme issue la plus probable (il "
                     "plafonne vers ~33%). Le démon le dit en probabilités, pas en coups "
                     "de poker — et sa tranche 20-30% est calibrée (cf. table).")
    lines += [
        "",
        "## Les preuves de courage",
        "",
        draw_line,
        "",
        "Ses démonstrations les plus sûres (et réussies) :",
        "",
    ]
    for c, r in sorted(((c, r) for c, r in picks if r["hit"]), key=lambda x: -x[0])[:5]:
        lines.append(f"- {r['tournament']} · {r['home']}–{r['away']} : "
                     f"pronostic {r['pick']} à {100 * c:.0f}% → ✅")
    lines += ["", "Et ses humiliations (gravées aussi — l'honnêteté n'élague pas) :", ""]
    for c, r in sorted(((c, r) for c, r in picks if not r["hit"]), key=lambda x: -x[0])[:5]:
        lines.append(f"- {r['tournament']} · {r['home']}–{r['away']} : "
                     f"pronostic {r['pick']} à {100 * c:.0f}% → ❌ (issue : {r['outcome']})")
    lines += [
        "",
        "La log-loss 2026 en cours s'ajoute à ce pedigree à chaque `laplace verdict` :",
        "le chiffre global vit avec le tournoi.",
        "",
    ]
    with open("prophecies/PEDIGREE.md", "w") as f:
        f.write("\n".join(lines))


def cmd_verdict(args):
    import csv
    import glob

    import numpy as np

    from laplace.data import played
    from laplace.predict import resolve

    df = played()
    wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= np.datetime64("2026-06-01"))]
    results = {}
    for r in wc.itertuples():
        results[(r.home_team, r.away_team)] = (int(r.home_score), int(r.away_score))
    known = set(df["home_team"]) | set(df["away_team"])

    print(BANNER)
    print(f"\n{BOLD}   LE VERDICT — chaque système jugé par le réel{RESET}\n")
    files = sorted(glob.glob("prophecies/SEAL_*.csv")) + sorted(glob.glob("prophecies/challenger_*.csv"))
    if not files:
        print(f"   {DIM}Aucun sceau trouvé dans prophecies/.{RESET}")
        return
    systems = {}
    for path in files:
        name = "🔮 DÉMON" if "SEAL_" in path else "⚔️  " + path.split("challenger_")[1].rsplit(".", 1)[0]
        with open(path) as f:
            for row in csv.DictReader(f):
                systems.setdefault(name, []).append(row)

    for name, rows in systems.items():
        scored, pending, hits, lls = 0, 0, 0, []
        for row in rows:
            try:
                a = resolve(row["team_a"].strip(), known)
                b = resolve(row["team_b"].strip(), known)
            except ValueError:
                continue
            res = results.get((a, b)) or tuple(reversed(results.get((b, a), ()))) or None
            if not res:
                pending += 1
                continue
            y = 0 if res[0] > res[1] else (1 if res[0] == res[1] else 2)
            scored += 1
            probs = None
            if row.get("p1") and row.get("pn") and row.get("p2"):
                try:
                    probs = [float(row["p1"]), float(row["pn"]), float(row["p2"])]
                except ValueError:
                    probs = None
            if probs:
                s = sum(probs)
                probs = [p / s for p in probs]
                lls.append(-np.log(max(probs[y], 1e-12)))
                pick = max(range(3), key=lambda i: probs[i])
            else:
                pick = {"1": 0, "N": 1, "n": 1, "X": 1, "2": 2}.get(str(row.get("pick", "")).strip(), None)
                if pick is None:
                    pick = 0 if str(row.get("pick", "")).strip() == row["team_a"].strip() else 2
            hits += int(pick == y)
        line = f"   {BOLD}{name:<18}{RESET} {scored} jugés · {pending} en attente"
        if scored:
            line += f" · précision {BOLD}{100 * hits / scored:.1f}%{RESET}"
            if lls:
                line += f" · log-loss {BOLD}{float(np.mean(lls)):.4f}{RESET}"
        print(line)
    _print_global_precision()
    print(f"\n   {DIM}Inscrire un concurrent : prophecies/challenger_NOM.csv")
    print(f"   colonnes : date,team_a,team_b,p1,pn,p2,pick (probas ou pick seul){RESET}\n")


def cmd_proof(args):
    from laplace.ensemble import optimise_weights, proof

    print(BANNER)
    print(f"\n{BOLD}   LA PREUVE — 3 cerveaux seuls vs FUSION, 9 tournois rejoués sans triche{RESET}")
    print(f"{DIM}   (log-loss, plus bas = plus fort ; hasard = 1.0986 ; poids fusion en leave-one-out){RESET}\n")
    rows, w_final = proof(verbose=True)
    print()
    print(f"   {BOLD}{'Tournoi':<15}{'n':>4}  {'Historien':>10} {'Anatomiste':>11} {'Fiévreux':>9} {'FUSION':>8}{RESET}")
    tot = {k: 0.0 for k in ("historien", "anatomiste", "fievreux", "fusion")}
    n_tot = 0
    for r in rows:
        print(f"   {r['label']:<15}{r['n']:>4}  {r['historien']:>10.4f} {r['anatomiste']:>11.4f} "
              f"{r['fievreux']:>9.4f} {BOLD}{r['fusion']:>8.4f}{RESET}")
        for k in tot:
            tot[k] += r[k] * r["n"]
        n_tot += r["n"]
    print(f"   {BOLD}{'TOTAL':<15}{n_tot:>4}  {tot['historien'] / n_tot:>10.4f} {tot['anatomiste'] / n_tot:>11.4f} "
          f"{tot['fievreux'] / n_tot:>9.4f} {tot['fusion'] / n_tot:>8.4f}{RESET}")
    print(f"\n   Poids retenus pour 2026 : {tuple(round(w, 2) for w in w_final)} "
          f"{DIM}(Historien · Anatomiste · Fiévreux){RESET}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="laplace",
        description="🔮 Le Démon de Laplace — prédiction de la Coupe du Monde 2026",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("update", help="télécharger les données fraîches").set_defaults(fn=cmd_update)

    p = sub.add_parser("ratings", help="classement Elo mondial")
    p.add_argument("--top", type=int, default=20)
    p.set_defaults(fn=cmd_ratings)

    p = sub.add_parser("match", help="prophétie sur une affiche")
    p.add_argument("team_a")
    p.add_argument("team_b")
    p.add_argument("--home", choices=["a", "b", "neutral"], default="neutral")
    p.add_argument("--engine", choices=["v1", "v2"], default="v2")
    p.set_defaults(fn=cmd_match)

    p = sub.add_parser("today", help="prophéties des matchs du jour")
    p.add_argument("--date", help="AAAA-MM-JJ (défaut : aujourd'hui)")
    p.add_argument("--engine", choices=["v1", "v2"], default="v2")
    p.set_defaults(fn=cmd_today)

    p = sub.add_parser("groups", help="destin des 12 groupes")
    p.add_argument("-n", type=int, default=10000)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--engine", choices=["v1", "v2"], default="v2")
    p.set_defaults(fn=cmd_groups)

    p = sub.add_parser("simulate", help="simuler le tournoi entier")
    p.add_argument("-n", type=int, default=20000, help="nombre d'univers parallèles")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--cutoff", type=float, default=0.002, help="masquer sous ce %% de titre")
    p.add_argument("--csv", help="exporter la prophétie complète en CSV")
    p.add_argument("--engine", choices=["v1", "v2"], default="v2")
    p.set_defaults(fn=cmd_simulate)

    p = sub.add_parser("proof", help="le duel des cerveaux sur 9 tournois (LOO)")
    p.set_defaults(fn=cmd_proof)

    p = sub.add_parser("seal", help="sceller les prophéties du jour (CSV horodaté git)")
    p.add_argument("--date", help="AAAA-MM-JJ (défaut : aujourd'hui)")
    p.add_argument("--tournament", action="store_true",
                   help="Sceau Total : destin complet des 48 équipes")
    p.add_argument("-n", type=int, default=100000, help="univers (Sceau Total)")
    p.add_argument("--seed", type=int, default=2026, help="graine reproductible")
    p.set_defaults(fn=cmd_seal)

    p = sub.add_parser("verdict", help="le réel juge tous les systèmes scellés")
    p.set_defaults(fn=cmd_verdict)

    p = sub.add_parser("pedigree", help="la précision GLOBALE rejouée (9 tournois, marche avant)")
    p.add_argument("--md", action="store_true", default=True,
                   help="écrire aussi la vitrine prophecies/PEDIGREE.md")
    p.set_defaults(fn=cmd_pedigree)

    p = sub.add_parser("market", help="voleur de cerveaux : démon vs cotes du marché")
    p.add_argument("--threshold", type=float, default=0.08, help="seuil de faille")
    p.add_argument("--engine", choices=["v1", "v2"], default="v2")
    p.add_argument("--enroll", action="store_true",
                   help="inscrire MARCHÉ et FUSION comme concurrents du registre")
    p.set_defaults(fn=cmd_market)

    p = sub.add_parser("adjust", help="éclaireur : injecter une info terrain (blessure...)")
    p.add_argument("team", nargs="?")
    p.add_argument("delta", nargs="?", type=float, help="points d'Elo, ex: -40")
    p.add_argument("--reason", help="motif (ex: 'Mbappé forfait')")
    p.add_argument("--list", action="store_true", help="voir les ajustements actifs")
    p.add_argument("--clear", help="effacer une équipe, ou 'all'")
    p.set_defaults(fn=cmd_adjust)

    p = sub.add_parser("backtest", help="prouver la puissance sur 2014/2018/2022")
    p.add_argument("--cup", type=int, choices=[2014, 2018, 2022], default=None)
    p.set_defaults(fn=cmd_backtest)

    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except ValueError as e:
        print(f"{RED}✗ {e}{RESET}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
