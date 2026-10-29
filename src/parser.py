"""Map file parser for the Fly-in Drones simulation."""
from argparse import Namespace, ArgumentParser
from pydantic import ValidationError
from typing import Any
from .models import Network, Zone, Connection, Hub
from .models import EndHub, StartHub, Metadata



class Parser:
    """Map file parser for the Fly-in Drones simulation."""
    def __init__(self) -> None:
        """Initialize the parser."""
        self._arguments: dict[str, Any] = self.arg_parse()
        self._file_path: Any = self._arguments.get("file")
        self._output_file: Any = self._arguments.get("output")

    def data_parser(self, network: list[str]) -> Network:
        """Receive the graph data and return a Network."""
        nb_drones: int = 1
        start_hub: Zone
        end_hub: Zone
        hub: list[Zone] = []
        connection: list[Connection] = []

        for i, zone in enumerate(network, 1):
            try:
                if zone.startswith("nb_drones:"):
                    _, number = zone.split(":", 1)
                    nb_drones = int(number.strip())
                elif zone.startswith("start_hub:"):
                    start_hub = self.arg_split(zone)
                elif zone.startswith("end_hub:"):
                    end_hub = self.arg_split(zone)
                elif zone.startswith("hub:"):
                    hub.append(self.arg_split(zone))
                elif zone.startswith("connection:"):
                    connection.append(self.connection_parser(zone))
                else:
                    raise ValueError(f"Not a valid zone type:"
                                    f" {zone} (line {i})")
            
            except ValidationError as error:
                raise ValueError(f"{error.errors()[0]["msg"]} (line {i})")
            except Exception as error:
                raise ValueError(f"{error} (line {i})")

        return (Network(
            nb_drones=nb_drones,
            start_hub=start_hub,
            end_hub=end_hub,
            hub=hub,
            connection=connection
        ))


    def arg_split(self, zone_str: str) -> Zone:
        """Parse a zone line and return the corresponding Zone model."""
        zone_part, _, meta = zone_str.strip().partition("[")

        metadata = (
            self.metadata_parser(meta) if meta else Metadata()
        )

        zone_list = zone_part.strip().split()
        if len(zone_list) < 4:
            raise ValueError(f"Incomplete zone line")

        zone_class = zone_list[0].rstrip(":")
        name = zone_list[1]
        try:
            x = int(zone_list[2])
            y = int(zone_list[3])
        except ValueError as error:
            raise ValueError(f"Invalid coordinates")

        if zone_class == "start_hub":
            return StartHub(
                zone_class=zone_class,
                name=name,
                x=x,
                y=y,
                metadata=metadata,
            )
        elif zone_class == "end_hub":
            return EndHub(
                zone_class=zone_class,
                name=name,
                x=x,
                y=y,
                metadata=metadata,
            )
        elif zone_class == "hub":
            return Hub(
                zone_class=zone_class,
                name=name,
                x=x,
                y=y,
                metadata=metadata,
            )
        else:
            raise ValueError(f"unknown zone class '{zone_class}'")

    def connection_parser(self, connection_str: str) -> Connection:
        """Parse the connection line and return a Connection instance."""
        connection_list, _, metadata = connection_str.strip().partition('[')

        if metadata:
            meta_dict = dict(item.split("=") for item in
                            metadata.strip('[]').split()
                            )
            for key in meta_dict.keys():
                if not key == "max_link_capacity":
                    raise ValueError(f"Invalid Connection's metadata: {key}")

        else:
            meta_dict = {"max_link_capacity": "1"}

        _, zone = connection_list.split()

        zone_1, zone_2 = zone.split('-', 1)

        return (Connection(
                        zone_1=zone_1,
                        zone_2=zone_2,
                        max_link_capacity=int(meta_dict["max_link_capacity"])
                        ))

    def metadata_parser(self, metadata: str) -> Metadata:
        """Parse a metadata raw string and return a Metadata instance."""
        allowed_keys = ("color", "zone", "max_drones")

        meta_dict = dict(item.split("=") for item in
                        metadata.strip('[]').strip().split())
        for key, value in meta_dict.items():
            if key not in allowed_keys:
                raise ValueError(f"Invalid metadata key: {key}")
            if not value:
                raise ValueError(f"Invalid metadata value")

        return Metadata(
            color=meta_dict["color"]
            if meta_dict.get("color") is not None else "",
            zone=meta_dict["zone"]
            if meta_dict.get("zone") is not None else "normal",
            max_drones=int(meta_dict["max_drones"])
            if meta_dict.get("max_drones") is not None else 1,
        )
       


    def get_network(self) -> Network:
        """Read the map file and start the parsing."""
        _network: list[str] = []

        starthub: int = 0
        nb_drone: int = 0
        endhub: int = 0

        with open(self._file_path, "r") as file:
            for line in file:
                if line.startswith("start_hub"):
                    starthub += 1
                elif line.startswith("end_hub"):
                    endhub += 1
                elif line.startswith("nb_drones:"):
                    nb_drone += 1
                if not line.strip().startswith("#") and line.strip():
                    _network.append(line.strip())
            if not _network[0].startswith("nb_drones:"):
                raise ValueError("First line should be nb_drones")
            if starthub > 1 or endhub > 1:
                raise ValueError("Start_hub/end_hub must be at most 1\n"
                                 f"starthub: {starthub}, endhub: {endhub}")
            if nb_drone > 1:
                raise ValueError("The number of drones must be stated one time.")

        return self.data_parser(_network)

    @staticmethod
    def arg_parse() -> dict[str, Any]:
        """Parse command-line arguments."""
        parser: ArgumentParser = ArgumentParser()

        parser.add_argument("map_file", help="Network file")

        parser.add_argument("--output", help="output file", default="output.txt")

        args: Namespace = parser.parse_args()

        arg = {"file": args.map_file, "output": args.output}

        return arg
