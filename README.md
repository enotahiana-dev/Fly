_This project has been created as part of the 42 curriculum by erakotom._

# Fly-in

## Description
The project is about a simulation of a fleet of autonomous drones
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

- Python 3.12 or later
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
uv run python -m src <path_to_maps> <flag>
```

### Flag
```bash
--output
```
Specifies the file where the output will be saved.

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

Initially, I thought that running a DFS to enumerate all possible paths and then distributing them across drones would be feasible, but it proved more complex than expected. I therefore switched to Dijkstra on a time-expanded graph, where each state is (zone, turn) and staying in place is an edge with cost 1. Drones are planned sequentially, and each one reserves its cells in a reservation table that subsequent drones must respect. This approach is known as prioritized planning

### Approach

The planner is a space-time Dijkstra that plans drones sequentially (prioritized planning). Each drone is planned with the reservations of previous drones already in place.

### Reservations

Two tables track capacity over time:

    zone_use[(zone, turn)] — drones per zone per turn,

    link_use[(a, b, turn)] — drones per connection per turn.

The start and end zones are always free. Connection keys are normalized with _lkey(a, b, turn) so that a-b and b-a are the same connection.

### Move generation

For a drone in zone z at turn t:

    Wait — (z, t + 1), if z is free at t + 1.

    Move — (neighbor, t + cost), if the destination and every traversed connection are free for every intermediate turn.

A move is legal only if all capacities are respected at every turn of the move.

### Planning one drone

Dijkstra with a priority queue keyed by (arrival_turn, moves, zone). The parent dictionary stores predecessors for path reconstruction. The search stops at the first (end, t) popped, which is optimal.

### Output

Each drone receives a list of time-stamped labels (turn, destination). A destination is either a zone name or a connection name (for restricted-zone transit).

### Complexity
Notation: `V` zones, `E` connections, `T` number of turns explored (bounded
by a horizon), `N` drones.

| | Complexity |
|---|---|
| States per drone | `V * T` |
| Edges per drone | about `(V + 2E) * T` |
| Time for one drone | `O(T * (V + E) * log(V * T))` |
| Time for all drones | `O(N * T * (V + E) * log(V * T))` |

Details:
 
- Each state is pushed to the heap at most once (a state already in `parent`
  is skipped), which gives the `log(V * T)` factor.
- Checking a zone or a link is a dictionary access, so `O(1)`.
- In practice `T` is the arrival turn of the drone, not the horizon: the
  search stops as soon as the end zone is popped from the heap. The horizon
  only protects against an unreachable end zone.
- Movement costs are only 1 or 2 turns, so the heap could be replaced by one
  queue per turn, giving `O(T * (V + E))` per drone. This optimization is not
  implemented.


## Visual Representation

The visualization is a **colored terminal output**, controlled by
three keys:

| Key | Action |
|---|---|
| `v` | Colored visualization mode |
| `l` | Line-by-line output mode |
| `q` | Quit |

In colored mode, the display advances turn by turn and waits for
`Enter`, so the user can follow each step at their own pace.

Each round shows the turn number, the start and end hub state, zone names (colored) with it's state; drones in a zone( ▸ ),
drones in transit to restricted zones( ▸▸ ).

At the end, a summary is always printed: total drones, number of
turns, minimum/maximum/average turns per drone, etc,...

## Technical Choices

- **Python 3.12+** — pattern matching, union types, modern typing.
- **Pydantic** — declarative validation with clear error messages.
- **Time-expanded Dijkstra** — each state is `(zone, turn)`.
  Handles waiting, restricted zones, and reservations naturally.
- **Prioritized planning** — drones planned sequentially.
  No capacity violation by construction; simple to explain.
- **No graph library** — custom `Graph`, `Pathfinder`, and
  `TimePlanner`. Only `heapq` and `collections` from stdlib.
- **Colored terminal** — works over SSH, no dependency, self-paced.
  Strict output on `stdout`, visualization on `stderr`.

### Models
The parser validates the map file using **Pydantic models**. Each line of the map is parsed into a dedicated model:

| Model | Role |
|---|---|
| `Zone` | Base model for any zone (name, coordinates, metadata). |
| `Hub` | Regular hub zone. |
| `StartHub` | The unique start hub. |
| `EndHub` | The unique end hub. |
| `Metadata` | Represent a zone's metadata. |
| `Connection` | A bidirectional connection between two zones. |
| `Network` | The full map: nb_drones, start, end, hubs, connections. |
| `Drone` | Represent a drone with his path. |


## Resources
### Documentation

- [Dijkstra's algorithm](https://www.youtube.com/watch?v=_lHSawdgXpI&pp=ygUSZGlqa3N0cmEgYWxnb3JpdGht)
- [argparse](https://docs.python.org/3/library/argparse.html)
- [heapq](https://docs.python.org/3/library/heapq.html)
- [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code)

### AI Usage

AI was used to help with documentation, code review, and
algorithm explanations. It was not used to generate the core
logic of the project. All suggestions were reviewed and tested
before integration.
