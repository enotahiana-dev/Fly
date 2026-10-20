*This project has been created as part of the 42 curriculum by <erakotom>.*

# Fly-in

## Description
Fly-in is a Python simulation of a fleet of autonomous drones
moving from a start hub to an end hub through a network of connected
zones.


The goal is to route all drones from the start to the end in the
**fewest possible simulation turns**, while respecting:

- zone capacity (`max_drones`),
- connection capacity (`max_link_capacity`),
- zone types (`normal`, `priority`, `restricted`, `blocked`),
- simultaneous movement and collision avoidance.

## Instructions

### Requirements

- Python 3.10 or later
- uv

### Installation
```bash
make install
```

Or manually:
```bash
uv sync
```

### Run
```bash
make run ARGS="<path_to_maps> <flag>"
```

Or manually:
```bash
uv run python -m src.fly_in <path_to_maps> <flag>
```

### Flag
```bash
--output
```
Specify where the turn-per-line output will be saved.

### Debug
```bash
make debug
```

### Lint
```bash
make lint
```
or
```bash
make lint-strict
```
for strict typing verification.


## Algorithm description

Dans la littérature, ta méthode complète ressemble à Cooperative A* (Silver, 2005) ou Space-Time A*. C’est la famille des problèmes MAPF (Multi-Agent Path Finding) : trouver des chemins pour plusieurs agents sans collision.

La seule différence avec Cooperative A* est que ton code utilise Dijkstra et non A*. A* ajoute une heuristique (une estimation de la distance restante) pour chercher plus vite. Toi, tu n’en as pas, donc c’est bien Dijkstra.

Ce que tu peux dire en peer-review

« Je fais un Dijkstra sur un graphe étendu dans le temps, où un état est (zone, tour) et où rester sur place est une arête de coût 1. Les drones sont planifiés l’un après l’autre, et chacun réserve ses cases dans une table de réservations que les suivants doivent respecter. C’est de la planification prioritaire, une approche gloutonne issue du MAPF. »