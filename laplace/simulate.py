"""LE DÉMON — simulation Monte-Carlo de la Coupe du Monde 2026 entière.

Chaque univers parallèle joue les 104 matchs : 72 matchs de groupes, classement
avec les vrais critères (points, différence, buts, confrontation directe),
repêchage des 8 meilleurs troisièmes, tableau final officiel, prolongations
et tirs au but. On compte ensuite dans combien d'univers chaque équipe soulève
le trophée.
"""

import random
from bisect import bisect_right

import numpy as np
import pandas as pd

from laplace.worldcup import (
    FINAL,
    GROUPS,
    HOSTS,
    KO_VENUE_COUNTRY,
    QUARTERS,
    ROUND_OF_16,
    ROUND_OF_32,
    SEMIS,
    TEAM_GROUP,
    home_ind_for,
)

MAX_G_90 = 8   # grille de scores 0-8 (au-delà : négligeable)
MAX_G_ET = 5   # grille pour la prolongation


class Simulator:
    def __init__(self, oracle, seed=None, condition_on_reality=True):
        self.oracle = oracle
        self.rng = random.Random(seed)
        self._cum90 = {}
        self._cum_et = {}
        # Round-robin de chaque groupe ; les hôtes jouent toujours chez eux
        # (le calendrier réel place chacun de leurs matchs dans leur pays).
        self.group_games = {
            g: [
                (teams[i], teams[j],
                 1 if teams[i] in HOSTS else (-1 if teams[j] in HOSTS else 0))
                for i in range(4)
                for j in range(i + 1, 4)
            ]
            for g, teams in GROUPS.items()
        }
        # Le démon vivant : les matchs déjà joués sont gravés, on ne simule
        # que le futur restant.
        self.fixed = {}
        if condition_on_reality:
            from laplace.data import played

            df = played()
            wc = df[
                (df["tournament"] == "FIFA World Cup")
                & (df["date"] >= np.datetime64("2026-06-01"))
            ]
            for row in wc.itertuples():
                self.fixed[(row.home_team, row.away_team)] = (
                    int(row.home_score),
                    int(row.away_score),
                )

    def _actual(self, a, b):
        if (a, b) in self.fixed:
            return self.fixed[(a, b)]
        if (b, a) in self.fixed:
            gb, ga = self.fixed[(b, a)]
            return (ga, gb)
        return None

    # ---------- échantillonnage des scores ----------

    def _dist90(self, a, b, h):
        key = (a, b, h)
        if key not in self._cum90:
            m = self.oracle.score_matrix(a, b, h, MAX_G_90)
            self._cum90[key] = np.cumsum(m.ravel())
        return self._cum90[key]

    def _dist_et(self, a, b, h):
        key = (a, b, h)
        if key not in self._cum_et:
            la, lb = self.oracle.lambdas(a, b, h)
            la, lb = la / 3.0, lb / 3.0  # 30 minutes de jeu
            gx = np.arange(MAX_G_ET + 1)
            fact = np.array([1, 1, 2, 6, 24, 120], dtype=float)
            pa = np.exp(-la) * la**gx / fact
            pb = np.exp(-lb) * lb**gx / fact
            m = np.outer(pa, pb)
            self._cum_et[key] = np.cumsum((m / m.sum()).ravel())
        return self._cum_et[key]

    def play90(self, a, b, h):
        cum = self._dist90(a, b, h)
        k = bisect_right(cum, self.rng.random())
        return divmod(min(k, len(cum) - 1), MAX_G_90 + 1)

    def play_knockout(self, a, b, h):
        """Renvoie (vainqueur, perdant)."""
        ga, gb = self.play90(a, b, h)
        if ga == gb:
            cum = self._dist_et(a, b, h)
            k = bisect_right(cum, self.rng.random())
            ea, eb = divmod(min(k, len(cum) - 1), MAX_G_ET + 1)
            ga, gb = ga + ea, gb + eb
        if ga == gb:  # tirs au but : quasi pile-ou-face, léger avantage au plus fort
            dr = self.oracle.ratings[a] - self.oracle.ratings[b]
            p_a = 1.0 / (1.0 + 10.0 ** (-dr / 2000.0))
            return (a, b) if self.rng.random() < p_a else (b, a)
        return (a, b) if ga > gb else (b, a)

    # ---------- phase de groupes ----------

    def _rank_group(self, g, results):
        """Classement FIFA : pts, diff, buts, confrontation directe, tirage au sort."""
        stats = {t: [0, 0, 0] for t in GROUPS[g]}
        for (a, b), (ga, gb) in results.items():
            stats[a][1] += ga - gb
            stats[a][2] += ga
            stats[b][1] += gb - ga
            stats[b][2] += gb
            if ga > gb:
                stats[a][0] += 3
            elif gb > ga:
                stats[b][0] += 3
            else:
                stats[a][0] += 1
                stats[b][0] += 1

        def h2h_key(subset):
            sub = {t: [0, 0, 0] for t in subset}
            for (a, b), (ga, gb) in results.items():
                if a in sub and b in sub:
                    sub[a][1] += ga - gb
                    sub[a][2] += ga
                    sub[b][1] += gb - ga
                    sub[b][2] += gb
                    if ga > gb:
                        sub[a][0] += 3
                    elif gb > ga:
                        sub[b][0] += 3
                    else:
                        sub[a][0] += 1
                        sub[b][0] += 1
            return sub

        # Tri principal, puis départage des ex æquo par confrontation directe.
        order = sorted(GROUPS[g], key=lambda t: tuple(stats[t]), reverse=True)
        final = []
        i = 0
        while i < len(order):
            j = i
            while j < len(order) and stats[order[j]] == stats[order[i]]:
                j += 1
            tied = order[i:j]
            if len(tied) > 1:
                sub = h2h_key(tied)
                tied.sort(key=lambda t: (tuple(sub[t]), self.rng.random()), reverse=True)
            final.extend(tied)
            i = j
        return final, stats

    def _assign_thirds(self, third_groups):
        """Affecte les 8 meilleurs troisièmes aux 8 slots du tableau (table FIFA)."""
        slots = [(no, set(sb.split(":")[1])) for no, _, sb in ROUND_OF_32 if sb.startswith("3:")]
        slots.sort(key=lambda s: len(s[1] & third_groups))
        assign = {}

        def bt(i, remaining):
            if i == len(slots):
                return True
            no, allowed = slots[i]
            opts = list(allowed & remaining)
            self.rng.shuffle(opts)
            for gch in opts:
                assign[no] = gch
                if bt(i + 1, remaining - {gch}):
                    return True
            assign.pop(no, None)
            return False

        if not bt(0, set(third_groups)):
            # Ne devrait jamais arriver (la table FIFA couvre les 495 combinaisons).
            rest = list(third_groups)
            self.rng.shuffle(rest)
            for (no, _), gch in zip(slots, rest):
                assign[no] = gch
        return assign

    # ---------- le tournoi entier ----------

    def run(self, n=20000, progress=None):
        teams = list(TEAM_GROUP)
        # compteurs : [R32, R16, QF, SF, Finale, Champion, 1er de groupe, points, 2e de groupe]
        counts = {t: np.zeros(9) for t in teams}
        finals = {}  # affiche de finale -> occurrences

        for sim in range(n):
            seeds, thirds = {}, {}
            for g in GROUPS:
                res = {
                    (a, b): self._actual(a, b) or self.play90(a, b, h)
                    for a, b, h in self.group_games[g]
                }
                order, stats = self._rank_group(g, res)
                seeds["1" + g] = order[0]
                seeds["2" + g] = order[1]
                thirds[g] = (order[2], stats[order[2]])
                counts[order[0]][6] += 1
                counts[order[1]][8] += 1
                for t in GROUPS[g]:
                    counts[t][7] += stats[t][0]

            ranked = sorted(
                thirds.items(),
                key=lambda kv: (tuple(kv[1][1]), self.rng.random()),
                reverse=True,
            )
            best8 = {g for g, _ in ranked[:8]}
            third_slot = self._assign_thirds(best8)

            winners = {}
            for no, sa, sb in ROUND_OF_32:
                a = seeds[sa]
                b = thirds[third_slot[no]][0] if sb.startswith("3:") else seeds[sb]
                counts[a][0] += 1
                counts[b][0] += 1
                h = home_ind_for(a, b, KO_VENUE_COUNTRY[no])
                winners[no], _ = self.play_knockout(a, b, h)

            for stage_idx, round_ in ((1, ROUND_OF_16), (2, QUARTERS), (3, SEMIS)):
                for no, ma, mb in round_:
                    a, b = winners[ma], winners[mb]
                    counts[a][stage_idx] += 1
                    counts[b][stage_idx] += 1
                    h = home_ind_for(a, b, KO_VENUE_COUNTRY[no])
                    winners[no], _ = self.play_knockout(a, b, h)

            (no, ma, mb), = FINAL
            a, b = winners[ma], winners[mb]
            counts[a][4] += 1
            counts[b][4] += 1
            pair = tuple(sorted((a, b)))
            finals[pair] = finals.get(pair, 0) + 1
            h = home_ind_for(a, b, KO_VENUE_COUNTRY[no])
            champ, _ = self.play_knockout(a, b, h)
            counts[champ][5] += 1

            if progress and (sim + 1) % progress == 0:
                print(f"  ... {sim + 1}/{n} univers simulés", flush=True)

        rows = []
        for t in teams:
            c = counts[t]
            rows.append({
                "team": t,
                "group": TEAM_GROUP[t],
                "elo": self.oracle.ratings.get(t, float("nan")),
                "p_r32": c[0] / n,
                "p_r16": c[1] / n,
                "p_qf": c[2] / n,
                "p_sf": c[3] / n,
                "p_final": c[4] / n,
                "p_champion": c[5] / n,
                "p_group_win": c[6] / n,
                "p_runner_up": c[8] / n,
                "exp_pts": c[7] / n,
            })
        df = pd.DataFrame(rows).sort_values("p_champion", ascending=False)
        self.finals = sorted(
            ((p, c / n) for p, c in finals.items()), key=lambda x: -x[1]
        )
        return df.reset_index(drop=True)
