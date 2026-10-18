from .pathfinder import Graph
import heapq
from .display import Display
from typing import Any


class Drone:
    """Représente un drone avec son trajet planifié."""
    def __init__(self,
                 id: int,
                 labels: list[tuple[int, str]],
                 arrival: int) -> None:

        self._id: str = "D" + str(id)
        self._path: list[tuple[int, str]] = labels
        self._arrival: int = arrival
        self._arrived: bool = False
        self._nb_moves: int = len(self._path)

    def move(self) -> tuple[int, str]:
        if self._path:
            move = heapq.heappop(self._path)
            if not self._path:
                self._arrived = True
            return move
        else:
            raise IndexError("Drone has reached it's destination")


class TimePlanner:
    """Planificateur temporel basé sur Dijkstra pour gérer le routage drone par drone."""

    def __init__(self, graph: Graph, horizon: int) -> None:
        self.graph = graph
        self.horizon = horizon

        self.zone_use: dict[tuple[str, int], int] = {}
        self.link_use: dict[tuple[str, str, int], int] = {}

    @staticmethod
    def _lkey(a: str, b: str, turn: int) -> tuple[str, str, int]:
        """Normalise la clé d'une connexion (car a-b est identique à b-a)."""
        first, second = sorted((a, b))
        return (first, second, turn)

    def _zone_free(self, zone: str, turn: int) -> bool:
        """Vérifie si une zone peut accueillir un drone supplémentaire à la fin du tour."""
        if zone == self.graph.start or zone == self.graph.end:
            return True
        used = self.zone_use.get((zone, turn), 0)
        return used < self.graph.zone_capacity(zone)

    def _link_free(self, a: str, b: str, turn: int) -> bool:
        """Vérifie si une connexion respecte sa capacité maximale pendant le tour."""
        key = self._lkey(a, b, turn)
        used = self.link_use.get(key, 0)
        return used < self.graph.link_capacity(a, b)

    def _moves(self, zone: str, t: int) -> list[tuple[str, int]]:
        """Calcule tous les déplacements valides (suivants) depuis la position (zone, t)."""
        result: list[tuple[str, int]] = []

        if self._zone_free(zone, t + 1):
            result.append((zone, t + 1))

        for nxt in self.graph.find_neighbor(zone):
            if self.graph.is_blocked(nxt):
                continue

            cost = self.graph.get_cost(nxt)
            arrive_turn = t + cost

            links_ok = all(self._link_free(zone, nxt, t + k) for k in range(1, cost + 1))

            if links_ok and self._zone_free(nxt, arrive_turn):
                result.append((nxt, arrive_turn))

        return result

    def plan(self, drone_id: int) -> Drone:
        """Trouve le chemin le plus court dans l'espace-temps (zone, tour) pour un drone."""
        start = self.graph.start
        end = self.graph.end

        heap: list[tuple[int, int, str]] = [(0, 0, start)]

        parent: dict[tuple[str, int], tuple[str, int] | None] = {(start, 0): None}

        goal: tuple[str, int] | None = None

        while heap:
            t, moves, zone = heapq.heappop(heap)

            if zone == end:
                goal = (zone, t)
                break

            if t >= self.horizon:
                continue

            for nxt, arrive_turn in self._moves(zone, t):
                state = (nxt, arrive_turn)
                if state not in parent:
                    parent[state] = (zone, t)
                    extra = 0 if nxt == zone else 1
                    heapq.heappush(heap, (arrive_turn, moves + extra, nxt))

        if goal is None:
            raise RuntimeError(f"Drone {drone_id} blocked.")

        labels: list[tuple[int, str]] = []
        node = goal

        while parent[node] is not None:
            prev = parent[node]
            (zone_prev, turn_prev), (zone_dest, turn_dest) = prev, node

            self.zone_use[(zone_dest, turn_dest)] = (
                self.zone_use.get((zone_dest, turn_dest), 0) + 1
            )

            if zone_prev != zone_dest:
                for turn in range(turn_prev + 1, turn_dest + 1):
                    key = self._lkey(zone_prev, zone_dest, turn)
                    self.link_use[key] = self.link_use.get(key, 0) + 1

                if turn_dest - turn_prev == 2:
                    labels.append((turn_prev + 1, f"{zone_prev}-{zone_dest}"))

                labels.append((turn_dest, zone_dest))

            node = prev

        labels.sort()

        return Drone(drone_id, labels, goal[1])

    def init_usage(self) -> None:
        self.graph.zone_use = self.zone_use
        self.graph.link_use = self.link_use


class Simulation:
    def __init__(self,
                 planner: TimePlanner,
                 display: Display,
                 arg: dict[str, Any]
                 ) -> None:

        self._planner = planner
        self._drones: list[Drone] = self.schedule()
        self._max_turn: int = max([drone._arrival for drone in self._drones])
        self.lines: list[str] = []
        self._display = display
        self._display._graph = self._planner.graph
        self._output_file: Any = arg.get("output")

    def schedule(self) -> list[Drone]:
        """Planifie tous les drones les uns après les autres en partageant le même planificateur."""
        drones = [self._planner.plan(drone_id) for drone_id in range(1, self._planner.graph.nb_drones + 1)]
        self._planner.graph._drones = drones
        return drones

    def run(self) -> None:
        for i in range(1, self._max_turn + 1):
            line: str = ""
            for drone in self._drones:
                if drone._arrived:
                    continue
                if drone._path[0][0] == i:
                    zone: str = drone.move()[1]
                    line += f"{drone._id}-{zone} "
            self.lines.append(line.strip())

        self.output()

    def output(self) -> None:
        self._planner.init_usage()
        self._display._output_file = self._output_file
        self._display.print_banner()

        with open(self._output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(self.lines))

        while True:
            inp = input()
            if inp.lower() == "l":
                print("\n")
                for line in self.lines:
                    print(line)
                input()
                self._display.stats(self.lines)
            elif inp.lower() == "v":
                self._display.play(self.lines)
            elif inp.lower() == "q":
                break
