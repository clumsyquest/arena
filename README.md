# 🔮 LE DÉMON DE LAPLACE ⚽

> « Une intelligence qui, à un instant donné, connaîtrait toutes les forces dont
> la nature est animée et la situation respective des êtres qui la composent
> [...] rien ne serait incertain pour elle, et l'avenir, comme le passé, serait
> présent à ses yeux. » — **Pierre-Simon de Laplace**, 1814

Laplace a imaginé un démon qui défie les lois de la nature en prédisant le
futur. Nous l'avons construit pour la **Coupe du Monde 2026**. Il ne connaît pas
la position de chaque atome — il connaît mieux : **chaque match international
depuis 1872** (49 400 et quelques), le vrai tirage des 12 groupes, le vrai
calendrier des 104 matchs, et les lois statistiques du but.

## La machine en trois étages

1. **LA MÉMOIRE** — l'intégralité des résultats internationaux depuis 1872
   (mise à jour quotidienne pendant le tournoi), y compris le calendrier réel
   du Mondial 2026.
2. **LE CERVEAU** — un classement Elo mondial recalculé match par match depuis
   1872 (pondéré par l'enjeu, l'écart de buts et le terrain), branché sur un
   modèle de buts **Dixon-Coles** ajusté par maximum de vraisemblance : pour
   n'importe quelle affiche, il produit la probabilité de **chaque score exact**.
3. **LE DÉMON** — un simulateur Monte-Carlo qui fait jouer la Coupe du Monde
   entière dans des dizaines de milliers d'univers parallèles : 72 matchs de
   groupes, vrais critères de départage FIFA, repêchage des 8 meilleurs
   troisièmes selon la table officielle, tableau final réel, prolongations,
   tirs au but, avantage du terrain pour les trois pays hôtes.

## Allumage

```bash
pip install -r requirements.txt
python -m laplace simulate            # la prophétie complète (20 000 univers)
```

## Les commandes du démon

| Commande | Pouvoir |
|---|---|
| `python -m laplace simulate -n 50000` | Simule le tournoi entier : probabilités de titre, finale, demies… |
| `python -m laplace today` | Les prophéties des matchs du jour (à lancer chaque matin ☕) |
| `python -m laplace match France Brésil` | Prophétie sur n'importe quelle affiche (alias FR/EN acceptés) |
| `python -m laplace groups` | Le destin des 12 groupes (P 1er, P 2e, P qualifié) |
| `python -m laplace ratings --top 30` | Le classement Elo mondial recalculé depuis 1872 |
| `python -m laplace backtest` | Le serment d'honnêteté : le démon jugé sur 2014, 2018, 2022 |
| `python -m laplace update` | Recharge les données fraîches (résultats de la veille inclus) |

### Le rituel quotidien pendant la Coupe du Monde

```bash
python -m laplace update && python -m laplace today
```

Les résultats de la veille sont intégrés, le classement Elo bouge, les
prophéties du soir tombent.

## LA TRANSCENDANCE (v2) ⚡

Le démon v1 a été soumis à l'épreuve du feu : **9 tournois majeurs (2010→2026,
473 matchs) rejoués en marche avant stricte**, et cinq voies d'évolution
testées en leave-one-out. Les données ont tranché :

| Candidat | Verdict | Log-loss (473 matchs) |
|---|---|---|
| L'Historien (Elo→Dixon-Coles, v1) | ✅ colonne vertébrale | 0.9372 |
| **Le mode VIVANT** (Elo mis à jour match après match, même en plein tournoi) | ✅ **adopté : gagne sur 7/9 tournois, zéro paramètre** | **0.9341** |
| L'Anatomiste (attaque/défense par équipe, demi-vie 4 ans) | ✅ 15% de la fusion (robustesse sur les éditions chaotiques : CDM 2022, Euro 2024) | 0.9572 seul |
| Le Fiévreux (forme récente, demi-vie 15 mois) | ❌ écarté par les données | 0.9727 |
| Le Juge (verdict direct W/N/L) | ❌ exécuté | 1.0168 |
| Calibrations température / boost de nuls | ❌ ne transfèrent pas en LOO | — |

Le moteur v2 = **fusion log-linéaire Historien 85% + Anatomiste 15%, en mode
vivant**, et le simulateur **grave les résultats réels** au fur et à mesure du
tournoi : chaque matin, la prophétie est re-calculée conditionnée à tout ce qui
s'est réellement passé. (`--engine v1` reste disponible ; `python -m laplace
proof` rejoue le duel des cerveaux.)

## Le serment d'honnêteté 🗡️

Un vrai démon ne triche pas : on le renvoie dans le passé, il n'a le droit de
voir **que** les matchs antérieurs à chaque tournoi, puis il prédit tout.

| Coupe du Monde | Log-loss (vivant) | Log-loss (figé) | Hasard | Bon pronostic | Champion réel (rang Elo pré-tournoi) |
|---|---|---|---|---|---|
| 2014 | **0.905** | 0.943 | 1.099 | 60.9% | Allemagne (n°3) |
| 2018 | **0.971** | 0.977 | 1.099 | 56.2% | France (n°5) |
| 2022 | **1.080** | 1.056 | 1.099 | 54.7% | Argentine (n°2) |

Sur les trois dernières éditions, le champion réel figurait **toujours dans son
top 5 pré-tournoi**. (Pour situer : les bookmakers tournent autour de 0.95–1.05
de log-loss sur ces tournois. 2022 reste l'édition la plus folle de l'histoire.)

## La prophétie du 10 juin 2026 (veille du match d'ouverture, moteur v2)

50 000 univers simulés :

| # | Équipe | 🏆 Titre | Finale | Demies |
|---|---|---|---|---|
| 🥇 | 🇪🇸 Espagne | **22.9%** | 34.0% | 46.9% |
| 🥈 | 🇦🇷 Argentine | **18.4%** | 28.9% | 41.3% |
| 🥉 | 🇫🇷 France | **9.7%** | 17.5% | 31.4% |
| 4 | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre | 6.4% | 12.6% | 22.9% |
| 5 | 🇧🇷 Brésil | 6.2% | 12.1% | 23.4% |
| 6 | 🇨🇴 Colombie | 4.8% | 9.9% | 18.3% |
| 7 | 🇵🇹 Portugal | 3.9% | 8.3% | 16.0% |
| 8 | 🇪🇨 Équateur | 3.1% | 7.1% | 16.2% |

**Finale la plus probable** : Argentine – Espagne (8.7% des univers).
**Outsider du démon** : le Mexique (Elo n°13, mais 16.4% de demi-finale à domicile).

## Sous le capot

- **Elo** : méthodologie eloratings.net — K selon l'enjeu (Mondial 60, finales
  continentales 50, qualifications/Ligue des Nations 40, amicaux 20),
  multiplicateur d'écart de buts, +100 Elo de terrain hors matchs neutres.
- **Modèle de buts** : `log λ = α + β·ΔElo/400 + γ·domicile + δ·extérieur`,
  régression de Poisson (IRLS) sur 16 ans de matchs pondérés par récence
  (demi-vie 4 ans, amicaux ×0.5), correction Dixon-Coles (ρ) des petits scores.
- **Simulation** : tirage et calendrier officiels, avantage du terrain pour
  Mexique/USA/Canada chez eux, départage points → différence → buts →
  confrontation directe → sort, affectation des troisièmes par retour sur
  trace sur la table FIFA, prolongations (λ/3) puis tirs au but.

## Superpouvoirs à venir

- [x] ~~**Le démon vivant**~~ : Elo mis à jour match après match, prophéties
      conditionnées aux résultats réels (v2)
- [x] ~~**Les cerveaux multiples**~~ : fusion Historien + Anatomiste (v2)
- [ ] **L'agent éclaireur** : lecture des news (blessés, compos) pour ajuster
      les ratings la veille des matchs
- [ ] **Le vol de cerveau des bookmakers** : calibration sur les cotes du marché
- [ ] **L'œil atomique** : xG niveau joueur (valeur des effectifs, forme des clubs)
- [ ] **Le miroir** : tableau de bord web en direct pendant le tournoi

## Données & crédits

- Résultats : [martj42/international_results](https://github.com/martj42/international_results) (domaine public, CC0)
- Structure du tournoi : [openfootball/worldcup](https://github.com/openfootball/worldcup) (domaine public)
- Code : MIT. Prédire le futur reste un art probabiliste — le démon donne des
  probabilités, le ballon reste rond. 🎲⚽
