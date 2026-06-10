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


def _oracle(verbose=True):
    from laplace import build_oracle

    if verbose:
        print(f"{DIM}⚙  Le démon relit toute l'histoire du football (1872 → aujourd'hui)...{RESET}")
    return build_oracle(verbose=verbose)


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
    oracle = _oracle()
    home_ind = {"a": 1, "b": -1, "neutral": 0}[args.home]
    p = oracle.match(args.team_a, args.team_b, home_ind)
    print(BANNER)
    venue = {1: f"chez {p['team_a']}", -1: f"chez {p['team_b']}", 0: "terrain neutre"}[home_ind]
    print(f"\n   {MAGENTA}PROPHÉTIE{RESET} {DIM}({venue}){RESET}")
    _print_match(p)
    print()


def cmd_today(args):
    from laplace.data import fixtures

    oracle = _oracle()
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
    oracle = _oracle()
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
    oracle = _oracle()
    from laplace.simulate import Simulator

    print(BANNER)
    print(f"\n{DIM}⚙  Le démon fait jouer la Coupe du Monde dans {args.n} univers parallèles...{RESET}")
    sim = Simulator(oracle, seed=args.seed)
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
            f"     log-loss {BOLD}{r['logloss']:.4f}{RESET} "
            f"{DIM}(hasard uniforme : {r['uniform_logloss']:.4f} · taux de base : {r['base_logloss']:.4f}){RESET}"
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
    p.set_defaults(fn=cmd_match)

    p = sub.add_parser("today", help="prophéties des matchs du jour")
    p.add_argument("--date", help="AAAA-MM-JJ (défaut : aujourd'hui)")
    p.set_defaults(fn=cmd_today)

    p = sub.add_parser("groups", help="destin des 12 groupes")
    p.add_argument("-n", type=int, default=10000)
    p.add_argument("--seed", type=int, default=None)
    p.set_defaults(fn=cmd_groups)

    p = sub.add_parser("simulate", help="simuler le tournoi entier")
    p.add_argument("-n", type=int, default=20000, help="nombre d'univers parallèles")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--cutoff", type=float, default=0.002, help="masquer sous ce %% de titre")
    p.add_argument("--csv", help="exporter la prophétie complète en CSV")
    p.set_defaults(fn=cmd_simulate)

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
