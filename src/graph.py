"""Graph for the Fly-in Drones simulation."""
from .models import Network, Drone


class Graph:
    """Represent a Graph and store different usefull variables and methods."""

    def __init__(self,
                 network: Network):
        """Initialize a Graph instance."""
        self._network = network
        self.connection = {
            tuple(sorted((con.zone_1, con.zone_2))): con.max_link_capacity
            for con in network.connection
        }

        self.start: str = network.start_hub.name
        self.end: str = network.end_hub.name
        self.nb_drones: int = network.nb_drones

        self.zones = {zone.name: zone for zone in network.hub}
        self.zones.update({network.start_hub.name: network.start_hub,
                           network.end_hub.name: network.end_hub})

        self.zones_type = {zone.name: zone.metadata.zone
                           for zone in network.hub}
        self.zones_type[self.start] = network.start_hub.metadata.zone
        self.zones_type[self.end] = network.end_hub.metadata.zone

        self.zone_color = {zone.name: zone.metadata.color
                           for zone in network.hub}
        self.zone_color.update({self.start: network.start_hub.metadata.color,
                                self.end: network.end_hub.metadata.color})

        self._drones: list[Drone] = []

        self.zone_use: dict[tuple[str, int], int] = {}
        self.link_use: dict[tuple[str, str, int], int] = {}

    def get_cost(self, zone_name: str) -> int:
        """Get the cost of a zone."""
        zone_type: str = self.zones_type.get(zone_name, "")
        if not zone_type:
            raise ValueError("Invalid zone_name", zone_name)
        if zone_type == "priority":
            return 1
        elif zone_type == "normal":
            return 1
        elif zone_type == "restricted":
            return 2
        elif zone_type == "blocked":
            return 0
        else:
            raise ValueError(f"Not a valid zone type: {zone_type}")

    def is_blocked(self, zone_name: str) -> bool:
        """Verify if a zone is blocked."""
        zone = self.get_cost(zone_name)
        return zone == 0

    def find_neighbor(self, zone_str: str) -> list[str]:
        """List all the neighbor available for the zone."""
        con_neighbor: set[tuple[str, str]] = {
            (con.zone_1, con.zone_2) for con in self._network.connection
            if zone_str in (con.zone_1, con.zone_2)
            }

        str_neighbor: list[str] = [nei for t in con_neighbor
                                   for nei in t if nei != zone_str]

        return str_neighbor

    def zone_capacity(self, zone: str) -> int:
        """Return the zone capacity."""
        _zone = self.zones.get(zone)

        if _zone is None:
            raise ValueError(f"Invalid zone: {zone}")
        return _zone.metadata.max_drones

    def link_capacity(self, a: str, b: str) -> int:
        """Return the link capacity(max_link_capacity)."""
        key = tuple(sorted((a, b)))
        capacity = self.connection.get(key)
        if capacity is None:
            raise ValueError(f"Invalid zones: {a, b}")
        return capacity

    def get_zone_color(self, zone: str) -> str:
        """Get the zone color."""
        color = self.zone_color.get(zone, "")
        return color

    def get_link_use(self, zone_a: str, zone_b: str, turn: int) -> int:
        """Get the usage of a link during a turn."""
        key = tuple(sorted((zone_a, zone_b)))
        usage = self.link_use.get((key[0], key[1], turn), None)

        if usage is None:
            raise ValueError(f"Invalid zones: {key[0], key[1]}")

        return usage

    def get_turns(self) -> dict[str, int]:
        """Return the min & max turn."""
        turns: dict[str, int] = {}
        minimum = min([drone._arrival for drone in self._drones])
        maximum = max([drone._arrival for drone in self._drones])

        turns["min"] = minimum
        turns["max"] = maximum

        return turns
