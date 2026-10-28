"""Core data models for the Fly-in Drones simulation."""
from pydantic import BaseModel, model_validator, Field
import heapq


class Metadata(BaseModel):
    """Represent a zone's metadata."""

    color: str = Field(default="")
    zone: str = "normal"
    max_drones: int = Field(ge=1, default=1)

    @model_validator(mode="after")
    def model_validator(self) -> "Metadata":
        """Check the metadata's value."""
        if self.zone not in ("normal", "blocked",
                             "restricted", "priority"):
            raise ValueError(f"Error zone type: {self.zone}")

        if self.color and not self.is_valid_color():
            raise ValueError(f"Invalid color: {self.color}")
        return self

    def is_valid_color(self) -> bool:
        """Return True if 'color' is only alphabetic."""
        return self.color.isalpha()


class Zone(BaseModel):
    """A node of the drone network."""

    zone_class: str
    name: str
    x: int
    y: int
    metadata: Metadata

    @model_validator(mode="after")
    def validate_zone_fields(self) -> "Zone":
        """Validate the class and name of the zone."""
        valid_class = {"start_hub", "hub", "end_hub"}
        if self.zone_class not in valid_class:
            raise ValueError(f"Invalid class {self.zone_class}")
        if ' ' in self.name or '-' in self.name:
            raise ValueError(f"Invalid zone name {self.name}")
        return self


class Hub(Zone):
    """A regular hub zone."""

    @model_validator(mode="after")
    def model_validator(self) -> "Hub":
        """Check that the zone is a hub."""
        if not self.zone_class.startswith("hub"):
            raise ValueError(f"Not a hub zone type: {self.zone_class}")
        return self


class StartHub(Zone):
    """The start hub zone."""

    @model_validator(mode="after")
    def model_validator(self) -> "StartHub":
        """Check that the zone is the start hub."""
        if not self.zone_class == "start_hub":
            raise ValueError(f"Not a starthub zone type: {self.zone_class}")
        return self


class EndHub(Zone):
    """The end hub zone."""

    @model_validator(mode="after")
    def model_validator(self) -> "EndHub":
        """Check that the zone is the end hub."""
        if not self.zone_class.startswith("end_hub"):
            raise ValueError(f"Not a endhub zone type: {self.zone_class}")
        return self


class Connection(BaseModel):
    """A bidirectional connection between two zones."""

    zone_1: str
    zone_2: str
    max_link_capacity: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def model_validator(self) -> "Connection":
        """Check that the two zones are different."""
        if self.zone_1 == self.zone_2:
            raise ValueError("The same zone cannot be connected: "
                             f"{self.zone_1} {self.zone_2}")
        return self


class Network(BaseModel):
    """The full drone network.

    Attributes:
        nb_drones: Number of drones to simulate.
        start_hub: The start zone.
        end_hub: The end zone.
        hub: List of regular zones.
        connection: List of connections.
    """

    nb_drones: int = Field(gt=0)
    start_hub: Zone
    end_hub: Zone
    hub: list[Zone] = []
    connection: list[Connection]

    @model_validator(mode="after")
    def model_validator(self) -> "Network":
        """Check global consistency of the network."""
        zone_name = ([zone.name for zone in self.hub] +
                     [self.start_hub.name, self.end_hub.name])
        connection = [frozenset((con.zone_1, con.zone_2)) for
                      con in self.connection]

        coordinates = ([(zone.x, zone.y) for zone in self.hub] +
                       [(self.start_hub.x, self.start_hub.y),
                       (self.end_hub.x, self.end_hub.y)])

        if len(zone_name) != len(set(zone_name)):
            raise ValueError("All zones must have different names!")
        if len(connection) != len(set(connection)):
            raise ValueError("All connections must be unique!")
        if len(coordinates) != len(set(coordinates)):
            raise ValueError("All coordinates must be unique!")

        for con in self.connection:
            if con.zone_1 not in zone_name or con.zone_2 not in zone_name:
                raise ValueError("Unknown zone for connection"
                                 f"'{con.zone_1}-{con.zone_2}'")

        self.start_hub.metadata.max_drones = self.nb_drones
        self.end_hub.metadata.max_drones = self.nb_drones

        return self


class Drone:
    """Represent a drone with his path."""

    def __init__(self,
                 id: int,
                 labels: list[tuple[int, str]],
                 arrival: int) -> None:
        """Initialize a Drone instance."""
        self._id: str = "D" + str(id)
        self._path: list[tuple[int, str]] = labels
        self.preserved_path: list[tuple[int, str]] = list(labels)
        self._arrival: int = arrival
        self._arrived: bool = False
        self._nb_moves: int = len(self._path)

    def move(self) -> tuple[int, str]:
        """Move the drone accross the given path."""
        if self._path:
            move = heapq.heappop(self._path)
            if not self._path:
                self._arrived = True
            return move
        else:
            raise IndexError("Drone has reached it's destination")
