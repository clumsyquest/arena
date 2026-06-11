# 🗡️ LE PEDIGREE DU DÉMON — sa précision globale, prouvée

> Protocole : **marche avant stricte, mode vivant** — pour chaque match,
> le démon n'a vu que les matchs antérieurs ; modèles ajustés avant chaque
> tournoi, Elo mis à jour match après match. Rejouable : `python -m laplace pedigree`.

## LE CHIFFRE GLOBAL : 473 matchs de grands tournois (2010-2026)

- **log-loss 0.9305** (hasard : 1.0986 · marché mondial : ~0.93-0.95)
- **précision 57.1%** sur 3 issues (hasard : 33.3% · marché : ~57%)
- **Brier 0.5488** (hasard : 0.6667)

## Par tournoi

| Tournoi | n | log-loss | précision |
|---|---|---|---|
| CDM 2010 | 64 | 0.9640 | 51.6% |
| CDM 2014 | 64 | 0.9074 | 60.9% |
| CDM 2018 | 64 | 0.9598 | 57.8% |
| CDM 2022 | 64 | 1.0646 | 51.6% |
| Asie 2024 | 51 | 0.8798 | 56.9% |
| Euro 2024 | 51 | 1.0262 | 51.0% |
| Copa 2024 | 32 | 0.8594 | 56.2% |
| Gold Cup 2025 | 31 | 0.8050 | 67.7% |
| CAN 2025 | 52 | 0.7910 | 65.4% |

## Calibration — quand le démon annonce X%, ça arrive X% du temps

| Annoncé (tranche) | Annoncé (moyen) | Arrivé | n probas |
|---|---|---|---|
| 0-10% | 6.6% | 7.3% | 82 |
| 10-20% | 15.5% | 12.6% | 253 |
| 20-30% | 25.2% | 25.6% | 524 |
| 30-40% | 35.1% | 35.2% | 145 |
| 40-50% | 45.2% | 45.0% | 120 |
| 50-60% | 55.1% | 55.5% | 119 |
| 60-70% | 65.2% | 70.7% | 92 |
| 70-100% | 78.2% | 77.4% | 84 |

## Le baromètre de confiance — plus le démon est sûr, plus il a raison

| Confiance du pronostic | n | précision |
|---|---|---|
| 0–40% | 58 | 34.5% |
| 40–50% | 120 | 45.0% |
| 50–60% | 119 | 55.5% |
| 60–100% | 176 | 73.9% |

## Les preuves de courage

- **Le nul, jamais en pronostic n°1** : sur l'ensemble du pedigree, aucune affiche n'a eu le nul comme issue la plus probable (il plafonne vers ~33%). Le démon le dit en probabilités, pas en coups de poker — et sa tranche 20-30% est calibrée (cf. table).

Ses démonstrations les plus sûres (et réussies) :

- Asie 2024 · Hong Kong–Iran : pronostic 2 à 95% → ✅
- CDM 2014 · Brazil–Cameroon : pronostic 1 à 94% → ✅
- CDM 2010 · Brazil–North Korea : pronostic 1 à 94% → ✅
- CAN 2025 · Morocco–Comoros : pronostic 1 à 91% → ✅
- CAN 2025 · Morocco–Tanzania : pronostic 1 à 91% → ✅

Et ses humiliations (gravées aussi — l'honnêteté n'élague pas) :

- CDM 2022 · Cameroon–Brazil : pronostic 2 à 88% → ❌ (issue : 1)
- CDM 2014 · Brazil–Mexico : pronostic 1 à 85% → ❌ (issue : N)
- CDM 2010 · England–Algeria : pronostic 1 à 85% → ❌ (issue : N)
- Asie 2024 · South Korea–Malaysia : pronostic 1 à 84% → ❌ (issue : N)
- CDM 2022 · Argentina–Saudi Arabia : pronostic 1 à 84% → ❌ (issue : 2)

La log-loss 2026 en cours s'ajoute à ce pedigree à chaque `laplace verdict` :
le chiffre global vit avec le tournoi.
