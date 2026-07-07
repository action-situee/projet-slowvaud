# Chargement des données

Ce guide décrit la procédure minimale pour reprendre le projet sur un nouveau
poste ou le transmettre à une autre personne.

## 1. Installer l'environnement

Depuis la racine du dépôt :

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Contrôle rapide :

```bash
make check
```

## 2. Récupérer les données préparées

Les données ne sont pas versionnées dans Git. Une copie est disponible sur
kDrive :

https://kdrive.situee.ch/app/share/1187668/43676546-af8a-49ba-869b-5709c4afc2a6

Télécharger le contenu et le placer dans le dossier `data/` du dépôt, en
conservant cette arborescence :

```text
data/raw/
data/context/
data/manifests/
data/processed/
```

Ne pas placer les données à côté du dépôt ni dans `exports/`. Les notebooks et
scripts cherchent les fichiers sous `data/`.

## 3. Vérifier l'inventaire local

Après copie des données :

```bash
python3 scripts/check_data_inventory.py
```

Pour une vérification bloquante des éléments nécessaires au travail courant :

```bash
python3 scripts/check_data_inventory.py --strict
```

Équivalent avec `make` :

```bash
make check-data
```

La vérification stricte attend notamment :

- les périmètres VaCO dissous en `EPSG:2056` ;
- les extractions OSM en `EPSG:4326` ;
- la couche SITG Genève en `EPSG:4326` ;
- le manifeste STAC orthophotos ;
- les orthophotos SWISSIMAGE `2.0 m`.

## 4. État attendu des données

État local produit lors de la préparation du projet :

| Donnée | Emplacement | État |
|---|---|---|
| Périmètres VaCO bruts | `data/raw/agglomerations/vaco/` | 5 agglomérations |
| Périmètres VaCO dissous | `data/processed/agglomerations/vaco/` | 1 géométrie par agglomération |
| OSM cyclable | `data/raw/osm/` | 5 GeoJSON |
| Contexte SITG Genève | `data/context/geneve/` | 1 GeoJSON |
| Manifeste orthophotos | `data/manifests/orthophoto_stac_manifest.csv` | `2.0 m` et `0.1 m` |
| Orthophotos `2.0 m` | `data/raw/orthophotos/ch.swisstopo.swissimage-dop10/gsd_2_0/` | couverture complète |
| Orthophotos `0.1 m` | `data/raw/orthophotos/ch.swisstopo.swissimage-dop10/gsd_0_1/` | échantillon Lausanne de 100 tuiles |

Les orthophotos complètes en `0.1 m` ne sont pas téléchargées localement par
défaut. L'ordre de grandeur mesuré sur 100 tuiles Lausanne est de 65.3 MiB par
tuile, soit environ 83 GiB pour Lausanne et environ 750 GiB pour les cinq
agglomérations.

## 5. Régénérer les données depuis les sources

Ordre recommandé si les données ne sont pas récupérées depuis kDrive :

```bash
python3 scripts/fetch_agglomerations.py --source vaco
.venv/bin/jupyter nbconvert --to notebook --execute --inplace 02_agglomerations_shapes.ipynb
.venv/bin/jupyter nbconvert --to notebook --execute --inplace 01_orthophotos_osm_network.ipynb
.venv/bin/jupyter nbconvert --to notebook --execute --inplace 03_context_sources.ipynb
.venv/bin/jupyter nbconvert --to notebook --execute --inplace 00_donnees_geodesie_slowvaud.ipynb
```

Pour les orthophotos :

```bash
python3 fetch_orthophotos_stac.py --gsds 2.0 0.1 --estimate-sizes
python3 fetch_orthophotos_stac.py --gsds 2.0 --download --estimate-sizes
```

Le téléchargement complet en `0.1 m` doit être lancé uniquement sur un volume
adapté :

```bash
python3 fetch_orthophotos_stac.py --gsds 0.1 --download --estimate-sizes
```

## 6. Points d'attention

Les CRS sont contractuels :

- agglomérations : `EPSG:2056` ;
- orthophotos SWISSIMAGE STAC : `EPSG:2056` ;
- OSM et contexte SITG téléchargé en GeoJSON : `EPSG:4326`.

OSM et les couches locales sont des labels faibles. Avant entraînement supervisé,
il faut contrôler un échantillon visuellement et documenter les règles de
conversion vers les classes de labels.
