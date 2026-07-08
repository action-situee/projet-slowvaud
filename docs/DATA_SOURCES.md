# Sources de données

Ce document rassemble les sources utiles pour lancer les premières explorations.
Il ne constitue pas un inventaire complet du futur projet SlowVaud.

## Données déjà préparées

Le paquet kDrive contient :

| Donnée | État |
|---|---|
| Périmètres VaCO | Lausanne, Berne, Genève, Bâle, Zurich |
| Réseau routier | swissTLM3D 2026, source complète et extractions par ville |
| OSM cyclable | extraction pour les cinq agglomérations |
| SITG Genève | couche d'aménagements cyclables téléchargée |
| Viageo Lausanne | ZIP source et couche `velo_amenagement` exportée en GeoJSON |
| Zurich Open Data | couches WFS `radwege` et `radstreifen` téléchargées |
| SWISSIMAGE `2.0 m` | sample Lausanne uniquement |
| SWISSIMAGE `0.1 m` | sample Lausanne uniquement |

La couverture SWISSIMAGE `0.1 m` complète n'est pas transmise. Elle représente
environ 700 à 750 GiB pour les cinq agglomérations.

## Orthophotos

Source :

- GeoAdmin STAC `ch.swisstopo.swissimage-dop10`
- format : GeoTIFF/COG
- CRS : `EPSG:2056`
- résolutions utilisées : `2.0 m` et `0.1 m`

Usage immédiat :

- `2.0 m` : contrôle général, cadrage et exploration légère ;
- `0.1 m` : inspection visuelle fine et préparation des premiers labels.

## Périmètres

Source principale :

- GeoAdmin `ch.are.agglomerationsverkehr`
- champ : `agglo_name`
- usage : périmètres VaCO dissous par agglomération
- CRS de travail : `EPSG:2056`

Source alternative configurée mais non prioritaire :

- GeoAdmin `ch.bfs.generalisierte-grenzen_agglomerationen_g1`
- limite : géométries généralisées, moins adaptées à une découpe fine
  d'orthophotos.

## Réseau routier

swissTLM3D est une donnée de base utile pour structurer le réseau routier. Elle
doit servir à :

- localiser les axes routiers dans les orthophotos ;
- découper ou accrocher les prédictions à un réseau de référence ;
- passer d'une détection sur image à une restitution par tronçon.

Dans la logique SlowVaud, l'ordre de travail peut donc être :

1. reconnaître ou vérifier le réseau routier sur l'image ;
2. identifier ensuite les aménagements cyclables associés à ce réseau ;
3. agréger les résultats par tronçon avec un niveau de confiance.

Prudence : swissTLM3D est une base de réseau, pas une vérité terrain suffisante
pour qualifier les bandes, pistes ou marquages cyclables visibles. Il faut donc
la compléter avec les orthophotos, OSM et les sources locales.

## OSM

OSM sert de contexte et de label faible, pas de vérité terrain.

Tags extraits :

| Famille | Tags |
|---|---|
| Voies cyclables dédiées | `highway=cycleway` |
| Aménagements cyclables portés par une route | `cycleway=*`, `cycleway:left=*`, `cycleway:right=*`, `cycleway:both=*` |
| Accès vélo désigné | `bicycle=designated` |

Prudence :

- `cycleway=lane` peut indiquer une bande visible, mais dépend de la date et de
  l'état du marquage ;
- `cycleway=track` demande souvent une règle de latéralisation ;
- `bicycle=designated` ne doit pas être utilisé seul comme label positif ;
- les géométries OSM peuvent être décalées par rapport aux orthophotos.

## Sources locales de comparaison

| Ville | Pointeur | Source cible | Statut |
|---|---|---|---|
| Genève | https://map.sitg.ge.ch/app/?portalresources=OTC_AMENAG_2ROUES | SITG `OTC_AMENAG_2ROUES` | très bon candidat |
| Lausanne | https://map.lausanne.ch/?lang=fr&baselayer_ref=fonds_geo_osm_bdcad_couleur&baselayer_opacity=0&tree_group_layers_mobilite_grp=mobilite_velo_amenagement%2Cmobilite_velo_carrefour%2Cmobilite_velo_libre_service%2Cmobilite_velo_parking%2Cmobilite_velo_pompe&map_x=2538191&map_y=1152593&map_zoom=5&tree_groups=mobilite_grp | Viageo `Aménagement cyclable` | bon candidat, téléchargement à finaliser |
| Berne | https://map.bern.ch/geoportal/ | chercher `Velo`, `Velohauptrouten`, `Velostrassen`, `Veloinfrastruktur` | couche pertinente non confirmée |
| Bâle | https://map.geo.bs.ch/s/OWV5 | Velostadtplan ; `Alltagsvelorouten`, `Touristische Velorouten` | plutôt contexte qu'aménagement visible |
| Zurich | https://data.stadt-zuerich.ch/dataset?q=velo | `Veloinfrastruktur Radwege und Radstreifen`, `Fuss- und Velowegnetz` | source prioritaire à intégrer |

Avant d'utiliser une source comme label, documenter :

- date d'accès ;
- licence ;
- CRS ;
- champs utilisés ;
- règle de conversion vers les classes SlowVaud.

## Référence modèle et littérature

Papini, S. P. et Zani, D. (2025), "Mapping Cycling-Specific Infrastructure
Using Object Detection on Remotely Sensed Images", STRC 2025, ETH Zurich
Research Collection. DOI : https://doi.org/10.3929/ethz-b-000732131.

Cette référence est utile pour cadrer l'usage de SWISSIMAGE et YOLOv8. Elle ne
définit pas directement le schéma de données SlowVaud.

## Sources à ne pas retenir comme groundtruth cyclable

Ne pas utiliser comme vérité terrain d'aménagement cyclable visible :

- SuisseMobile ;

SuisseMobile peut avoir un intérêt de contexte, mais ne décrit pas directement
les bandes, pistes ou marquages à identifier dans les orthophotos. swissTLM3D,
en revanche, est à conserver comme donnée de base pour le réseau routier.
