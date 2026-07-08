# Notes de méthode

Ces notes posent les premières règles de travail. Elles sont provisoires et
doivent être ajustées après inspection visuelle des données.

## Périmètre réel de cette première brique

Le dépôt prépare seulement la partie géodonnées et labels faibles :

- orthophotos ;
- périmètres d'agglomération ;
- réseau routier de référence ;
- contexte OSM ;
- sources locales de comparaison ;
- classes initiales pour les infrastructures cyclables.

Il ne couvre pas encore les portails web, les flux de mobilité, les données
perçues, les indicateurs complets de marchabilité/cyclabilité ni les simulations.

## Classes de départ

Commencer avec peu de classes :

| Classe | Description | Prudence |
|---|---|---|
| `bande_cyclable` | marquage cyclable sur chaussée | dépend fortement de la visibilité du marquage |
| `piste_cyclable_separee` | aménagement séparé de la circulation générale | géométrie parfois décalée du réseau routier |
| `absence_amenagement_visible` | aucun aménagement identifiable dans l'image | à définir avec des exemples négatifs clairs |
| `indetermine` | cas occulté, ambigu ou trop incertain | classe importante pour éviter les faux positifs |

Ne pas multiplier les classes avant d'avoir contrôlé un premier échantillon.

## Champs minimaux à conserver

| Champ | Rôle |
|---|---|
| `label_id` | identifiant stable |
| `agglo_key` | agglomération |
| `source_name` | OSM, SITG, viageo, Zurich, contrôle manuel |
| `source_feature_id` | identifiant source si disponible |
| `label_class` | classe harmonisée |
| `confidence` | `high`, `medium`, `low` |
| `review_status` | `a_verifier`, `verifie`, `rejete` |
| `geometry` | géométrie de travail en `EPSG:2056` |

## Règles de prudence

- OSM et les couches administratives sont des labels faibles.
- swissTLM3D est utile comme réseau de référence, mais ne qualifie pas à lui
  seul les aménagements cyclables visibles.
- Une source locale peut être ancienne, incomplète ou décalée.
- La date de l'orthophoto doit être comparée à la date de la source.
- Les infrastructures latéralisées demandent une règle spécifique.
- Les carrefours, ombres, arbres, véhicules et marquages effacés doivent pouvoir
  basculer vers `indetermine`.

## Première séquence de travail

1. Vérifier le paquet de données avec `make check-data`.
2. Ouvrir quelques tuiles Lausanne `0.1 m`.
3. Superposer le réseau routier de référence et vérifier son alignement.
4. Superposer OSM et, si possible, la source Lausanne/Viageo.
5. Répéter le contrôle avec Genève/SITG.
6. Noter les cas simples et les cas ambigus.
7. Ajuster les classes avant tout entraînement.
8. Ajouter Zurich comme source externe de comparaison.

## Décisions à prendre ensuite

- unité de travail : vignette, tronçon, objet ou combinaison ;
- taille des vignettes orthophoto ;
- règle de buffer autour du réseau ;
- classes finales ;
- mode de validation manuelle ;
- besoin réel ou non d'une couverture `0.1 m` complète.
