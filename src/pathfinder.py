"""Pathfinding algorithms for the Fly-in Drones simulation."""
from .graph import Graph
from .models import Drone
from typing import cast
import heapq


class TimePlanner:
    """Space-time plannificator based on Djikstra."""

    def __init__(self, graph: Graph, horizon: int) -> None:
        """Initialize the pathfinder with a graph and a limit."""
        self.graph = graph
        self.horizon = horizon

        self.zone_use: dict[tuple[str, int], int] = {}
        self.link_use: dict[tuple[str, str, int], int] = {}

    @staticmethod
    def _lkey(a: str, b: str, turn: int) -> tuple[str, str, int]:
        """Normalise a conection keys."""
        first, second = sorted((a, b))
        return (first, second, turn)

    def _zone_free(self, zone: str, turn: int) -> bool:
        """Verify if a zone have space left."""
        if zone == self.graph.start or zone == self.graph.end:
            return True
        used = self.zone_use.get((zone, turn), 0)
        return used < self.graph.zone_capacity(zone)

    def _link_free(self, a: str, b: str, turn: int) -> bool:
        """Vérify if a conection still have room during the turn."""
        key = self._lkey(a, b, turn)
        used = self.link_use.get(key, 0)
        return used < self.graph.link_capacity(a, b)

    def _moves(self, zone: str, t: int) -> list[tuple[str, int]]:
        """Calculate all available move for a drone on a zone."""
        result: list[tuple[str, int]] = []

        if self._zone_free(zone, t + 1):
            result.append((zone, t + 1))

        for nxt in self.graph.find_neighbor(zone):
            if self.graph.is_blocked(nxt):
                continue

            cost = self.graph.get_cost(nxt)
            arrive_turn = t + cost

            links_ok = all(self._link_free(zone, nxt, t + k) for k in range(1,
                           cost + 1))

            if links_ok and self._zone_free(nxt, arrive_turn):
                result.append((nxt, arrive_turn))

        return result

    def plan(self, drone_id: int) -> Drone:
        """Find the shortest path on a space-time for a drone."""
        start = self.graph.start
        end = self.graph.end
        heap: list[tuple[int, int, str]] = [(0, 0, start)]

        parent: dict[tuple[str, int], tuple[str, int] | None] = {(start, 0):
                                                                 None}

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
            raise RuntimeError(f"Drone {drone_id} is blocked.")

        labels: list[tuple[int, str]] = []
        node = goal

        while parent[node] is not None:
            prev = cast(tuple[str, int], parent[node])
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
        """Initialize zone & link usage for graph."""
        self.graph.zone_use = self.zone_use
        self.graph.link_use = self.link_use
