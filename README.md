# SlowVaud - orthophotos et infrastructures cyclables

Ce dépôt prépare un environnement de travail reproductible pour constituer des
données d'apprentissage autour des infrastructures cyclables, à partir
d'orthophotos SWISSIMAGE et de données de contexte vectorielles.

Périmètre initial : Lausanne, Berne, Genève, Bâle, Zurich.

Objectif immédiat :

1. obtenir des périmètres d'agglomération suisses exploitables ;
2. extraire les objets OSM liés aux pistes, bandes et aménagements cyclables ;
3. préparer les orthophotos SWISSIMAGE couvrant les agglomérations à deux
   niveaux de résolution ;
4. documenter et télécharger, quand c'est direct, les sources locales de contexte ;
5. garder un environnement indépendant, propre et réutilisable.

## Structure

```text
config/slowvaud_config.json       Configuration centrale
src/slowvaud/                     Fonctions réutilisables
scripts/                          Wrappers CLI
00_donnees_geodesie_slowvaud.ipynb
02_agglomerations_shapes.ipynb
01_orthophotos_osm_network.ipynb
03_context_sources.ipynb
data/
  raw/                            Données brutes téléchargées
  context/                        Données cantonales/communales de contexte
  manifests/                      Manifestes et registres
  processed/                      Données préparées
exports/                          Exports finaux
docs/                             Notes complémentaires
```

Les dossiers `data/` et `exports/` sont ignorés par Git, sauf leurs `.gitkeep`.
Le dépôt versionne le code, les notebooks, la configuration et la documentation,
pas les orthophotos ni les exports volumineux.

## Données téléchargées

Les données générées par les notebooks ne sont pas versionnées dans Git.

Une copie des données préparées peut être téléchargée depuis kDrive :
https://kdrive.situee.ch/app/share/1187668/43676546-af8a-49ba-869b-5709c4afc2a6

Après téléchargement, placer le contenu à la racine du dossier `data/` du dépôt.
La procédure détaillée est dans `docs/DATA_LOADING.md`.

Arborescence attendue :

```text
data/raw/
data/context/
data/manifests/
data/processed/
```

Contrôle après chargement :

```bash
python3 scripts/check_data_inventory.py --strict
```

ou :

```bash
make check-data
```

Les orthophotos 10 cm complètes sont très volumineuses. Le test réel de 100
tuiles Lausanne donne une moyenne de 65.3 MiB par tuile, soit environ 83 GiB
pour Lausanne et environ 750 GiB pour les cinq agglomérations. Le téléchargement
10 cm complet doit donc être lancé sur un volume adapté.

## Installation

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Commandes utiles :

```bash
make check
make init-data
make manifest
```

Voir aussi `docs/SETUP.md` pour les variantes d'installation et le remote Git.

## Démarrage rapide

Pour reprendre le projet avec les données préparées :

```bash
git clone git@github.com:action-situee/projet-slowvaud.git
cd projet-slowvaud
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Télécharger ensuite les données depuis kDrive, les placer dans `data/`, puis
contrôler l'inventaire :

```bash
python3 scripts/check_data_inventory.py --strict
```

Les notebooks peuvent ensuite être ouverts dans l'ordre indiqué plus bas.

## Contrat CRS

Le projet explicite les CRS à chaque étape pour éviter les inférences implicites.

| Donnée | CRS |
|---|---|
| Agglomérations GeoAdmin brutes et dissoutes | `EPSG:2056` LV95 |
| Centres d'agglomération dans la configuration | `EPSG:4326` WGS84 |
| OSM extrait via Overpass/OSMnx | `EPSG:4326` WGS84 |
| SITG Genève téléchargé en GeoJSON | sortie `EPSG:4326`, source métier `EPSG:2056` |
| Orthophotos SWISSIMAGE STAC | `EPSG:2056` LV95, GeoTIFF/COG |

Les conversions WGS84/LV95 sont faites avec `pyproj`. Les requêtes STAC utilisent
une emprise WGS84 pour interroger l'API, puis les items sont filtrés par
intersection avec les périmètres VaCO dissous en LV95.

## Notebooks

Les notebooks sont volontairement simples. Chaque notebook a une cellule de
paramètres en haut. Les téléchargements échouent explicitement si un prérequis
manque.

Ordre recommandé :

1. `00_donnees_geodesie_slowvaud.ipynb` : contrôle de la configuration,
   manifeste orthophoto STAC et estimation des volumes.
2. `02_agglomerations_shapes.ipynb` : téléchargement GeoAdmin VaCO et dissolution
   des périmètres d'agglomération en LV95.
3. `01_orthophotos_osm_network.ipynb` : extraction OSM dans les périmètres
   dissous.
4. `03_context_sources.ipynb` : registre des sources locales et téléchargement
   des sources directes, actuellement SITG Genève.

## Sources

Agglomérations :

- source par défaut : GeoAdmin `ch.are.agglomerationsverkehr`, champ
  `agglo_name`, périmètres VaCO ;
- source alternative configurée : `ch.bfs.generalisierte-grenzen_agglomerationen_g1`
  pour des limites généralisées, moins adaptées à la découpe fine d'orthophotos.

Orthophotos :

- source de travail : STAC GeoAdmin `ch.swisstopo.swissimage-dop10` ;
- format : GeoTIFF/COG en `EPSG:2056` ;
- niveaux disponibles dans la collection : `0.1 m` et `2.0 m` ;
- méthode : intersection des items STAC avec les périmètres VaCO dissous ;
- prudence : la couverture complète à 10 cm est volumineuse. Générer et
  contrôler le manifeste avant de lancer le téléchargement.

OSM :

- `highway=cycleway` ;
- `cycleway=*`, `cycleway:left=*`, `cycleway:right=*`, `cycleway:both=*` ;
- `bicycle=designated`.

Sources locales de contexte :

- `geneve_sitg_amenagements_2roues` : téléchargement direct ArcGIS FeatureServer ;
- `lausanne_viageo_amenagement_cyclable` : source documentée, téléchargement
  manuel ou authentifié à finaliser ;
- Berne, Bâle, Zurich : sources locales encore à compléter.

## Commandes

Télécharger les agglomérations :

```bash
python3 scripts/fetch_agglomerations.py --source vaco
```

Créer un manifeste orthophoto STAC complet, avec estimation des tailles :

```bash
python3 fetch_orthophotos_stac.py --gsds 2.0 0.1 --estimate-sizes
```

Télécharger la couverture complète en 2 m :

```bash
python3 fetch_orthophotos_stac.py --gsds 2.0 --download --estimate-sizes
```

Télécharger la couverture complète en 10 cm, uniquement sur un volume disposant
de suffisamment d'espace :

```bash
python3 fetch_orthophotos_stac.py --gsds 0.1 --download --estimate-sizes
```

Télécharger les sources de contexte directes :

```bash
python3 scripts/fetch_context_sources.py --sources geneve_sitg_amenagements_2roues
```

## Prudence méthodologique

OSM et les couches administratives locales servent de labels faibles. Elles ne
constituent pas une vérité terrain exhaustive. Avant apprentissage supervisé, il
faut contrôler les catégories, les dates, les décalages géométriques, les effets
de latéralisation et la visibilité réelle dans les orthophotos.

Un schéma de labels initial est disponible dans `docs/LABEL_SCHEMA.md`.

## Documentation utile

- `docs/DATA_LOADING.md` : chargement, contrôle et régénération des données.
- `docs/SETUP.md` : installation locale.
- `docs/LABEL_SCHEMA.md` : classes de labels faibles pour les infrastructures
  cyclables.

## Git

Remote prévu :

```bash
https://github.com/action-situee/projet-slowvaud.git
```
