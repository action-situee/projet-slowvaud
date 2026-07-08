# SlowVaud - première brique orthophotos et labels cyclables

Ce dépôt prépare les premières pistes techniques pour lancer SlowVaud. Il ne
couvre pas encore l'ensemble du projet décrit dans la note SDSC : portails web,
flux de mobilité, données perçues, simulations et indicateurs complets ne sont
pas traités ici.

Le périmètre de ce dépôt est plus limité :

- récupérer des périmètres d'agglomération ;
- mobiliser un réseau routier de référence ;
- préparer des orthophotos SWISSIMAGE ;
- extraire un contexte cyclable OSM ;
- identifier des sources locales de comparaison ;
- poser un premier schéma de labels faibles pour les infrastructures cyclables.

Périmètre exploratoire : Lausanne, Berne, Genève, Bâle, Zurich.

## Démarrage rapide

```bash
git clone git@github.com:action-situee/projet-slowvaud.git
cd projet-slowvaud
make install
make check
```

Copier ensuite le paquet kDrive dans `data/`, puis vérifier :

```bash
make check-data
```

Le paquet kDrive est ici :

https://kdrive.situee.ch/app/share/1187668/43676546-af8a-49ba-869b-5709c4afc2a6

## Contenu utile

```text
config/slowvaud_config.json       Villes, sources, CRS, paramètres
src/slowvaud/                     Fonctions Python réutilisables
scripts/check_data_inventory.py   Vérification courte des données locales
fetch_orthophotos_stac.py         Préparation/téléchargement SWISSIMAGE
00_donnees_geodesie_slowvaud.ipynb
02_agglomerations_shapes.ipynb
01_orthophotos_osm_network.ipynb
03_context_sources.ipynb
docs/DATA_SOURCES.md              Sources de données et pointeurs géoportail
docs/METHOD_NOTES.md              Classes provisoires et prochaines étapes
```

Le dépôt Git ne contient pas les orthophotos ni les données lourdes. Les données
locales doivent être placées sous `data/`.

Arborescence minimale attendue :

```text
data/
  raw/          périmètres, OSM, orthophotos, swissTLM3D
  context/      sources locales, par exemple SITG Genève
  processed/    périmètres préparés
```

Le dossier `data/` doit rester simple au démarrage : données brutes, sources de
contexte, données préparées. Les fichiers techniques générés par certains
scripts ne sont pas nécessaires pour une première prise en main.

## Données transmises

Le paquet kDrive contient de quoi démarrer :

- périmètres VaCO pour Lausanne, Berne, Genève, Bâle, Zurich ;
- swissTLM3D comme réseau routier de base, avec une extraction par ville ;
- extractions OSM cyclables ;
- sources locales Genève/SITG et Lausanne/Viageo ;
- sample SWISSIMAGE `2.0 m` sur Lausanne ;
- sample SWISSIMAGE `0.1 m` sur Lausanne.

La couverture SWISSIMAGE `0.1 m` complète n'est pas incluse. Elle représente un
ordre de grandeur de 700 à 750 GiB pour les cinq agglomérations et doit rester
une étape explicite si elle devient nécessaire.

## Commandes

Les commandes `make` sont seulement des raccourcis.

| Commande | Rôle |
|---|---|
| `make install` | Crée `.venv/` et installe les dépendances. |
| `make check` | Vérifie que le code Python compile. |
| `make check-data` | Vérifie que les données minimales sont présentes. |
| `make init-data` | Crée ou affiche les dossiers attendus, si besoin. |

Il n'y a pas de `make manifest`. La préparation des orthophotos est volontairement
laissée dans des commandes explicites, car elle peut impliquer des volumes
importants.

## Premières actions recommandées

1. Vérifier que l'installation fonctionne avec `make check`.
2. Copier le paquet kDrive dans `data/`.
3. Vérifier l'état local avec `make check-data`.
4. Ouvrir les notebooks dans l'ordre `00`, `02`, `01`, `03`.
5. Vérifier le réseau routier de référence et son alignement avec les
   orthophotos.
6. Comparer visuellement quelques secteurs Lausanne/Genève entre orthophotos,
   réseau, OSM et sources locales.
7. Choisir deux ou trois classes de départ, par exemple bande cyclable, piste
   séparée, indéterminé.
8. Intégrer ensuite Zurich comme source externe prioritaire de comparaison.

## Planning indicatif

Planning repris du fichier `260224_gantt.xlsx`. Il sert de cadrage de lancement
et devra être ajusté au fur et à mesure des premiers tests.

| Phase / jalon | Tâche ou livrable | Début | Échéance | Durée | Responsable | Statut |
|---|---|---:|---:|---:|---|---|
| Phase 1 Data acquisition | Télécharger les données pour 5 villes : swissTLM3D, SWISSIMAGE, deux villes test et trois villes train | 01.07.26 | 31.07.26 | 30 | AS | Not Started |
| Phase 1 Data acquisition | Préparer la couche SIG de groundtruth | 01.07.26 | 31.07.26 | 30 | AS | Not Started |
| Phase 1 Data acquisition | Préparer les données pour tout le canton | 01.07.26 | 31.07.26 | 30 | AS | Not Started |
| MS1: Review Meeting | Jalon de revue |  | 31.07.26 |  |  | Milestone |
| Phase 2 Data prep | Préparation des données | 31.07.26 | 21.08.26 | 21 | Person 1 | Not Started |
| Phase 2 Data prep | Exploration des données | 21.08.26 | 04.09.26 | 14 | Person 1 | Not Started |
| Phase 2 Data prep | Revue de littérature et identification des modèles | 04.09.26 | 18.09.26 | 14 | Person 1 | Not Started |
| Phase 2 Data prep | Data augmentation | 18.09.26 | 02.10.26 | 14 | [À COMPLÉTER] | Not Started |
| MS2: Review Meeting | Jalon de revue |  | 02.10.26 |  |  | Milestone |
| Phase 3 Training | Tester plusieurs modèles | 02.10.26 | 01.12.26 | 60 | Person 2 | Not Started |
| Phase 3 Training | Benchmark et évaluation en parallèle | 17.11.26 | 01.12.26 | 14 | Person 1 | Not Started |
| Phase 3 Training | Refactoring et nettoyage du code | 01.12.26 | 15.12.26 | 14 | Person 1 | Not Started |
| Phase 3 Training | Tester la généralisation sur d'autres villes, par exemple Zurich | 15.12.26 | 29.12.26 | 14 | Person 2 | Not Started |
| MS2: Review Meeting | Jalon de revue |  | 29.12.26 |  |  | Milestone |
| Phase 4 Extending to the whole Canton | Lancer le modèle | 29.12.26 | 05.01.27 | 7 | Person 1 | Not Started |
| Phase 4 Extending to the whole Canton | Revoir les résultats | 05.01.27 | 12.01.27 | 7 | Person 1 | Not Started |
| Phase 4 Extending to the whole Canton | Documentation de reproductibilité | 12.01.27 | 19.01.27 | 7 | Person 2 | Not Started |
| Phase 4 Extending to the whole Canton | Transmission | 19.01.27 | 26.01.27 | 7 | Person 2 | Not Started |
| MS3: Final Meeting | Jalon final |  | 26.01.27 |  |  | [À COMPLÉTER] |

Durée totale indicative : 179 jours. À vérifier : le Gantt source contient deux
lignes nommées `MS2`.

## Documentation

- `docs/DATA_SOURCES.md` : sources disponibles, géoportails, tags OSM, limites.
- `docs/METHOD_NOTES.md` : classes provisoires, prudences et prochaines étapes.
