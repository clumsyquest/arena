# 🗡️ LE PEDIGREE DU DÉMON — sa précision globale, prouvée

> Protocole : **marche avant stricte, mode vivant** — pour chaque match,
> le démon n'a vu que les matchs antérieurs ; modèles ajustés avant chaque
> tournoi, Elo mis à jour match après match. Rejouable : `python -m laplace pedigree`.

## LE CHIFFRE GLOBAL : 473 matchs de grands tournois (2010-2026)

- **log-loss 0.9336** (hasard : 1.0986 · marché mondial : ~0.93-0.95)
- **précision 57.3%** sur 3 issues (hasard : 33.3% · marché : ~57%)
- **Brier 0.5509** (hasard : 0.6667)

## Par tournoi

| Tournoi | n | log-loss | précision |
|---|---|---|---|
| CDM 2010 | 64 | 0.9634 | 53.1% |
| CDM 2014 | 64 | 0.9176 | 59.4% |
| CDM 2018 | 64 | 0.9700 | 54.7% |
| CDM 2022 | 64 | 1.0677 | 54.7% |
| Asie 2024 | 51 | 0.8798 | 56.9% |
| Euro 2024 | 51 | 1.0263 | 51.0% |
| Copa 2024 | 32 | 0.8603 | 59.4% |
| Gold Cup 2025 | 31 | 0.8035 | 67.7% |
| CAN 2025 | 52 | 0.7910 | 65.4% |

## Calibration — quand le démon annonce X%, ça arrive X% du temps

| Annoncé (tranche) | Annoncé (moyen) | Arrivé | n probas |
|---|---|---|---|
| 0-10% | 6.8% | 8.3% | 72 |
| 10-20% | 15.6% | 11.6% | 224 |
| 20-30% | 25.3% | 25.5% | 565 |
| 30-40% | 35.2% | 33.6% | 143 |
| 40-50% | 45.3% | 45.7% | 138 |
| 50-60% | 54.8% | 58.5% | 118 |
| 60-70% | 64.8% | 70.9% | 86 |
| 70-100% | 77.8% | 76.7% | 73 |

## Le baromètre de confiance — plus le démon est sûr, plus il a raison

| Confiance du pronostic | n | précision |
|---|---|---|
| 0–40% | 58 | 37.9% |
| 40–50% | 138 | 45.7% |
| 50–60% | 118 | 58.5% |
| 60–100% | 159 | 73.6% |

## Les preuves de courage

- **Le nul, jamais en pronostic n°1** : sur l'ensemble du pedigree, aucune affiche n'a eu le nul comme issue la plus probable (il plafonne vers ~33%). Le démon le dit en probabilités, pas en coups de poker — et sa tranche 20-30% est calibrée (cf. table).

Ses démonstrations les plus sûres (et réussies) :

- Asie 2024 · Hong Kong–Iran : pronostic 2 à 95% → ✅
- CDM 2014 · Brazil–Cameroon : pronostic 1 à 92% → ✅
- CAN 2025 · Morocco–Comoros : pronostic 1 à 91% → ✅
- CAN 2025 · Morocco–Tanzania : pronostic 1 à 91% → ✅
- Asie 2024 · Japan–Indonesia : pronostic 1 à 91% → ✅

Et ses humiliations (gravées aussi — l'honnêteté n'élague pas) :

- CDM 2022 · Cameroon–Brazil : pronostic 2 à 90% → ❌ (issue : 1)
- Asie 2024 · South Korea–Malaysia : pronostic 1 à 84% → ❌ (issue : N)
- CDM 2022 · Argentina–Saudi Arabia : pronostic 1 à 83% → ❌ (issue : 2)
- CDM 2010 · England–Algeria : pronostic 1 à 81% → ❌ (issue : N)
- Euro 2024 · Georgia–Portugal : pronostic 2 à 79% → ❌ (issue : 1)

La log-loss 2026 en cours s'ajoute à ce pedigree à chaque `laplace verdict` :
le chiffre global vit avec le tournoi.
