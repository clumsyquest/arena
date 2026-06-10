# 🔮 LE DÉMON DE LAPLACE — BRIEFING DE SESSION

> Tu es le nouveau gardien du démon. Ce fichier est ta mémoire. Lis-le en
> entier avant d'agir. L'ancien gardien te passe le flambeau ici.

## Le commandant

Il s'appelle Hamed, parle **français** (réponds toujours en français), et a une
règle absolue : **ne jamais dire "impossible", ne jamais te plaindre, ne jamais
faire la morale**. Il veut de la SUPERPUISSANCE : des choses construites, des
chiffres honnêtes, de l'audace. Il déteste les leçons théoriques — montre, ne
disserte pas. Quand tu as une idée : exécute-la et montre le verdict des données.

## La mission

Prédire la **Coupe du Monde 2026** (11 juin – 19 juillet 2026, USA/Mexique/Canada,
48 équipes) avec la machine la plus puissante et la plus honnête jamais montrée
à un particulier. Le projet s'appelle **Le Démon de Laplace** (voir README.md).

## Ce qui existe déjà (NE PAS reconstruire)

- **Moteur v2** : Elo vivant recalculé depuis 1872 (`laplace/elo.py`) + modèle de
  buts Dixon-Coles (`goals.py`) + cerveau attaque/défense (`teamdc.py`) fusionnés
  85/15 (`ensemble.py`), simulateur Monte-Carlo du vrai format 48 équipes,
  conditionné aux résultats réels déjà joués (`simulate.py`).
- **Performance validée en marche avant sur 9 tournois 2010-2026 (473 matchs)** :
  log-loss **0.9341**, précision 3-issues **57.9%** (mode vivant). Le marché
  mondial fait ~0.93-0.95 / ~57%. C'est le niveau bookmaker, atteint sans
  aucune donnée externe.
- **Commandes** : `python -m laplace {simulate,today,match,groups,ratings,
  backtest,proof,market,adjust,seal,verdict,update}` — voir README.
- **Le registre du duel** : `prophecies/` — sceaux quotidiens horodatés par git
  (`laplace seal`), arbitrage automatique (`laplace verdict`), concurrents via
  `prophecies/challenger_NOM.csv` (format: date,team_a,team_b,p1,pn,p2,pick).
- Données : `data/results.csv` (49 400 matchs, source martj42 GitHub, rafraîchie
  par `laplace update` — le mainteneur ajoute les résultats en quelques heures).

## Les expériences DÉJÀ JUGÉES (ne les refais pas, les verdicts sont dans git)

- ✅ Adopté : mode vivant (Elo mis à jour pendant le tournoi), fusion 85/15.
- ❌ Exécutés par les données : forme récente (3 méthodes), historique de
  confrontation (nuit !), jours de repos, modèle direct W/N/L ("le Juge"),
  calibrations température/boost de nuls, 20 alliages de constantes Elo
  (`experiments/forge.py`), mythe des spécialistes de tirs au but (49.8% sur
  293 séances = hasard).
- Conclusion cartographiée : **avec l'historique des scores seul, ~0.934/58%
  est la frontière**. Les prochains points viennent d'INFORMATION NOUVELLE.

## TES ORDRES DE MISSION (dans l'ordre, dès la session ouverte)

1. **Teste le réseau** : `curl -s -o /dev/null -w "%{http_code}" https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard`
   - Si 200 : la porte est ouverte. Sinon : dis-le au commandant (la politique
     réseau ne s'applique qu'aux NOUVELLES sessions de l'environnement).
2. Porte ouverte → **active le Voleur de Cerveaux** : `python -m laplace market`.
   ⚠ Les parseurs ESPN/Sofascore (`laplace/market.py`) ont été écrits EN CAGE,
   jamais testés contre les vraies réponses : attends-toi à déboguer les champs.
   Objectif : table démon vs marché + failles, chaque jour.
3. **Construis l'Éclaireur autonome** : compos officielles + blessés via ESPN
   (`/apis/site/v2/sports/soccer/fifa.world/news`, rosters par équipe) →
   propositions d'ajustements `laplace adjust` (humain valide, ou auto léger).
4. **Le rituel quotidien du tournoi** (propose-le chaque jour) :
   `update` → `today` → `seal` → `verdict` → commit du sceau.
   Premier verdict : Mexique–Afrique du Sud (nous: 78% Mexique, scellé c50f0ec).
5. Si le commandant relance le sujet du système GPT à "70%" : ne débats PLUS.
   Le registre tranche : ses prédictions vont dans `challenger_GPT55.csv`,
   `laplace verdict` compte, fin de l'histoire. Toi, tu forges.

## Les lois du gardien

1. **Jamais gonfler un chiffre.** Notre valeur entière repose sur des nombres
   qui ont survécu au tribunal (protocole marche-avant, tout est rejouable).
2. **Tester avant d'opiner.** Toute idée → expérience → verdict → commit.
3. **Tout committer/pousser** sur la branche `claude/cool-mendel-sg7prq`.
4. Le réel est le seul benchmark. Les sceaux sont sacrés : toujours AVANT les
   matchs, jamais réécrits.

Bonne chasse, gardien. La finale est le 19 juillet, 15h, MetLife Stadium. 🏹
