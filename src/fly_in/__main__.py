from .parser import get_network, Network, arg_parse
from pydantic import ValidationError
from .pathfinder import Graph
from .simulation import Simulation, TimePlanner
from .display import ColorPalette, Display


def main() -> None:
    arg = arg_parse()
    network: Network = get_network(str(arg.get("file")))
    graph = Graph(network)

    planner = TimePlanner(graph, 120)
    color_palette = ColorPalette()
    display = Display(color_palette)
    simu = Simulation(planner, display, arg)

    simu.run()


if __name__ == "__main__":
    try:
        main()
    except ValidationError as e:
        print("Error Validation: ", e.errors()[0]["msg"])
    except Exception as e:
        print("Error: ", e)
