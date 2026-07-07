# Installation locale

## Environnement virtuel

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

Alternative avec `make` :

```bash
make install
```

Le dossier `.venv/` est ignore par Git.

Python 3.12 est recommande pour maximiser la compatibilite avec `geopandas`, `rasterio` et `osmnx`.

## Controle rapide

```bash
make check
make init-data
make manifest
```

## Donnees volumineuses

Les donnees brutes, orthophotos, exports raster et manifestes generes ne sont pas versionnes. Seuls les dossiers vides de structure sont conserves via `.gitkeep`.

## Remote Git

Le depot local doit pointer vers :

```bash
git remote add origin git@github.com:action-situee/projet-slowvaud.git
```

ou, en HTTPS :

```bash
git remote add origin https://github.com/action-situee/projet-slowvaud.git
```
