from pydantic import BaseModel, model_validator, Field
import webcolors  # type: ignore
from argparse import Namespace, ArgumentParser


class Metadata(BaseModel):
    color: str = Field(default="")
    zone: str = "normal"
    max_drones: int = Field(ge=1, default=1)

    @model_validator(mode="after")
    def model_validator(self) -> "Metadata":
        if self.zone not in ("normal", "blocked",
                             "restricted", "priority"):
            raise ValueError(f"Error zone type: {self.zone}")

        if self.color and not self.is_valid_color():
            raise ValueError(f"Invalid color: {self.color}")
        return self

    def is_valid_color(self) -> bool:
        if self.color.lower() == "rainbow":
            return True
        try:
            webcolors.name_to_hex(self.color)
            return True
        except ValueError:
            return False


class Zone(BaseModel):
    zone_class: str
    name: str
    x: int
    y: int
    metadata: Metadata

    @model_validator(mode="after")
    def validate_zone_fields(self) -> "Zone":
        valid_class = {"start_hub", "hub", "end_hub"}
        if self.zone_class not in valid_class:
            raise ValueError(f"Invalid class {self.zone_class}")
        if ' ' in self.name or '-' in self.name:
            raise ValueError(f"Invalid zone name {self.name}")
        return self


class Hub(Zone):

    @model_validator(mode="after")
    def model_validator(self) -> "Hub":
        if not self.zone_class.startswith("hub"):
            raise ValueError(f"Not a hub zone type: {self.zone_class}")
        return self


class StartHub(Zone):
    @model_validator(mode="after")
    def model_validator(self) -> "StartHub":
        if not self.zone_class == "start_hub":
            raise ValueError(f"Not a starthub zone type: {self.zone_class}")
        return self


class EndHub(Zone):
    @model_validator(mode="after")
    def model_validator(self) -> "EndHub":
        if not self.zone_class.startswith("end_hub"):
            raise ValueError(f"Not a endhub zone type: {self.zone_class}")
        return self


class Connection(BaseModel):
    zone_1: str
    zone_2: str
    max_link_capacity: int = Field(default=1, ge=1)


class Network(BaseModel):
    nb_drones: int = Field(gt=0)
    start_hub: Zone
    end_hub: Zone
    hub: list[Zone] = []
    connection: list[Connection]

    @model_validator(mode="after")
    def model_validator(self) -> "Network":
        zone_name = ([zone.name for zone in self.hub] +
                     [self.start_hub.name, self.end_hub.name])
        connection = []
        for con in self.connection:
            connection.append((con.zone_1, con.zone_2))
            connection.append((con.zone_2, con.zone_1))

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

        return self


def data_parser(network: list[str]) -> Network:
    nb_drones: int = 1
    start_hub: Zone
    end_hub: Zone
    hub: list[Zone] = []
    connection: list[Connection] = []

    for zone in network:
        if zone.startswith("nb_drones"):
            _, _, number = zone.partition(" ")
            nb_drones = int(number)
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


def connection_parser(zone_str: str) -> Connection:
    connection_list, _, metadata = zone_str.strip().partition('[')
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


def main_parser() -> Network:
    parser: ArgumentParser = ArgumentParser()

    parser.add_argument("file", help="Network file")

    parser.add_argument("--output", help="output file", default="output.txt")

    args: Namespace = parser.parse_args()

    _network: list[str] = []

    with open(args.file, "r") as file:
        for line in file:
            if not line.strip().startswith("#") and line.strip():
                _network.append(line.strip())
        if not _network[0].startswith("nb_drones:"):
            raise ValueError("First line should be nb_drones")

    return data_parser(_network)


# if __name__ == "__main__":
#     zone_str = "end_hub: restricted_tunnel1 4 0
# [zone=restricted color=grey max_drones=2]"
#     try:
#         zone = arg_split("start_hub: start 0 0 [color=green]")

#         connection = connection_parser("connection:
# gate2-gate3 [max_link_capacity=1]")
#         print(zone)

#         print(connection)

#     except Exception as e:
#         print("Unexpected error:", e)
