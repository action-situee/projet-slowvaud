# SlowVaud - orthophotos et infrastructures cyclables

Ce dépôt prépare un environnement de travail reproductible pour constituer des
données d'apprentissage autour des infrastructures cyclables, à partir
d'orthophotos SWISSIMAGE et de données de contexte vectorielles.

Périmètre initial : Lausanne, Berne, Genève, Bâle, Zurich.

Objectif immédiat :

1. obtenir des périmètres d'agglomération suisses exploitables ;
2. extraire les objets OSM liés aux pistes, bandes et aménagements cyclables ;
3. préparer des échantillons d'orthophotos à deux niveaux de résolution WMTS ;
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

Après téléchargement, placer le contenu à la racine du dossier `data/` du dépôt,
en conservant l'arborescence attendue :

```text
data/raw/
data/context/
data/manifests/
data/processed/
```

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

## Contrat CRS

Le projet explicite les CRS à chaque étape pour éviter les inférences implicites.

| Donnée | CRS |
|---|---|
| Agglomérations GeoAdmin brutes et dissoutes | `EPSG:2056` LV95 |
| Centres d'agglomération dans la configuration | `EPSG:4326` WGS84 |
| OSM extrait via Overpass/OSMnx | `EPSG:4326` WGS84 |
| SITG Genève téléchargé en GeoJSON | sortie `EPSG:4326`, source métier `EPSG:2056` |
| Manifestes orthophotos | emprise `EPSG:4326`, tuiles WMTS `EPSG:3857` |

Les conversions WGS84/LV95 sont faites avec `pyproj`. Les emprises WMTS sont
construites à partir d'un buffer métrique en LV95, puis converties vers WGS84
pour les indices de tuiles web.

## Notebooks

Les notebooks sont volontairement simples. Chaque notebook a une cellule de
paramètres en haut. Les téléchargements échouent explicitement si un prérequis
manque.

Ordre recommandé :

1. `00_donnees_geodesie_slowvaud.ipynb` : contrôle de la configuration,
   manifeste orthophoto et téléchargement des échantillons WMTS.
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

- source de prototypage : WMTS GeoAdmin `ch.swisstopo.swissimage` ;
- profils configurés : `swissimage_25cm_like` à zoom 19 et
  `swissimage_10cm_like` à zoom 20 ;
- limite : les tuiles WMTS sont des JPEG web. Pour l'entraînement final, il
  faudra privilégier des GeoTIFF/COG SWISSIMAGE, conserver le géoréférencement et
  découper les tuiles d'apprentissage avec transform affine et CRS explicites.

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

Créer un manifeste orthophoto sans téléchargement :

```bash
python3 fetch_orthophotos_wmts.py --profiles swissimage_25cm_like swissimage_10cm_like --max-tiles 10 --dry-run
```

Télécharger les échantillons WMTS listés :

```bash
python3 fetch_orthophotos_wmts.py --profiles swissimage_25cm_like swissimage_10cm_like --max-tiles 10 --download
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

## Git

Remote prévu :

```bash
https://github.com/action-situee/projet-slowvaud.git
```
