"""Map file parser for the Fly-in Drones simulation."""
from argparse import Namespace, ArgumentParser
from typing import Any
from .models import Network, Zone, Connection, Hub
from .models import EndHub, StartHub, Metadata


def data_parser(network: list[str]) -> Network:
    """Receive the graph data and return a Network."""
    nb_drones: int = 1
    start_hub: Zone
    end_hub: Zone
    hub: list[Zone] = []
    connection: list[Connection] = []

    for zone in network:
        if zone.startswith("nb_drones"):
            _, number = zone.split(":", 1)
            nb_drones = int(number.strip())
        elif zone.startswith("start_hub"):
            start_hub = arg_split(zone)
        elif zone.startswith("end_hub"):
            end_hub = arg_split(zone)
        elif zone.startswith("hub"):
            hub.append(arg_split(zone))
        elif zone.startswith("connection"):
            connection.append(connection_parser(zone))
        else:
            raise ValueError(f"Not a valid zone type: {zone}")

    return (Network(
        nb_drones=nb_drones,
        start_hub=start_hub,
        end_hub=end_hub,
        hub=hub,
        connection=connection
    ))


def arg_split(zone_str: str) -> Zone:
    """Receive a zone line a return the zone instance."""
    zone_, _, meta = zone_str.strip().partition('[')

    if meta:
        metadata = metadata_parser(meta)
    else:
        metadata = Metadata()

    zone_list = zone_.strip().split()
    if zone_str.startswith("start_hub"):
        return (StartHub(
                        zone_class=zone_list[0].strip(':'),
                        name=zone_list[1].strip(),
                        x=int(zone_list[2].strip()),
                        y=int(zone_list[3].strip()),
                        metadata=metadata
                        ))
    elif zone_str.startswith("end_hub"):
        return (EndHub(
                      zone_class=zone_list[0].strip(':'),
                      name=zone_list[1].strip(),
                      x=int(zone_list[2].strip()),
                      y=int(zone_list[3].strip()),
                      metadata=metadata
                      ))
    elif zone_str.startswith("hub"):
        return (Hub(
                   zone_class=zone_list[0].strip(':'),
                   name=zone_list[1].strip(),
                   x=int(zone_list[2].strip()),
                   y=int(zone_list[3].strip()),
                   metadata=metadata
                   ))

    else:
        raise ValueError("Not valid zone: ", zone_str)


def connection_parser(connection_str: str) -> Connection:
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


def metadata_parser(metadata: str) -> Metadata:
    """Parse a metadata raw string and return a Metadata instance."""
    meta_dict = dict(item.split("=") for item in
                     metadata.strip('[]').strip().split())
    allowed_keys = ("color", "zone", "max_drones")

    for key in meta_dict.keys():
        if key not in allowed_keys:
            raise ValueError(f"Invalid metadata key: {key}")

    return Metadata(
        color=meta_dict["color"]
        if meta_dict.get("color") is not None else "",
        zone=meta_dict["zone"]
        if meta_dict.get("zone") is not None else "normal",
        max_drones=int(meta_dict["max_drones"])
        if meta_dict.get("max_drones") is not None else 1,
    )


def get_network(path: str) -> Network:
    """Read the map file and start the parsing."""
    _network: list[str] = []

    starthub: int = 0

    endhub: int = 0

    with open(path, "r") as file:
        for line in file:
            if line.startswith("start_hub"):
                starthub += 1
            elif line.startswith("end_hub"):
                endhub += 1
            if not line.strip().startswith("#") and line.strip():
                _network.append(line.strip())
        if not _network[0].startswith("nb_drones:"):
            raise ValueError("First line should be nb_drones")
        if starthub > 1 or endhub > 1:
            raise ValueError("Start_hub/end_hub must be at most 1")

    return data_parser(_network)


def arg_parse() -> dict[str, Any]:
    """Parse command-line arguments."""
    parser: ArgumentParser = ArgumentParser()

    parser.add_argument("map_file", help="Network file")

    parser.add_argument("--output", help="output file", default="output.txt")

    args: Namespace = parser.parse_args()

    arg = {"file": args.map_file, "output": args.output}

    return arg
