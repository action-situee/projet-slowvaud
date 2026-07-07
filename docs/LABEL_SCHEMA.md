# Schema de labels pour les infrastructures cyclables

Ce schema est un point de depart pour transformer OSM et les donnees locales en labels faibles. Il ne remplace pas une validation visuelle.

## Classes

| Classe | Description | Sources probables | Prudence |
|---|---|---|---|
| `piste_cyclable_dediee` | Infrastructure cyclable separee ou dediee | OSM `highway=cycleway`, SITG `TYPE_AMENAGEMENT=Piste` | Geometrie parfois lateralisee ou decalee |
| `piste_cyclable_associee_chaussee` | Piste declaree comme attribut d'une route | OSM `cycleway=track`, `cycleway:left/right=track` | Necessite souvent une lateralisation |
| `bande_cyclable` | Marquage sur chaussee | OSM `cycleway=lane`, SITG `TYPE_AMENAGEMENT=Bande` | Visibilite depend de l'orthophoto et de l'etat du marquage |
| `voie_partagee_marquee` | Marquage partage ou voie bus/velo | OSM `shared_lane`, `share_busway` | Classe heterogene |
| `itineraire_ou_acces_velo_designe` | Acces velo signale sans amenagement visible garanti | OSM `bicycle=designated` | A ne pas utiliser comme label positif direct sans controle |
| `contexte_cyclable_osm` | Objet utile mais ambigu | OSM divers | Contexte uniquement |

## Champs recommandes

| Champ | Role |
|---|---|
| `label_id` | Identifiant stable du label |
| `agglo_key` | Agglomeration cible |
| `source_name` | OSM, SITG, viageo, autre |
| `source_feature_id` | Identifiant source si disponible |
| `label_class` | Classe harmonisee |
| `geometry` | Geometrie harmonisee en `EPSG:2056` pour les traitements locaux |
| `confidence` | `high`, `medium`, `low` |
| `source_date` | Date de publication ou de telechargement |
| `license_note` | Rappel de licence/source |

## Regle de prudence

Les labels OSM ou administratifs doivent etre consideres comme des aides a l'annotation. Pour l'apprentissage supervise, constituer un lot controle manuellement et conserver un champ `confidence`.
