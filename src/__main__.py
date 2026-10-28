"""Entry point for the Fly-in Drones simulation."""
from .parser import get_network, arg_parse
from pydantic import ValidationError
from .pathfinder import TimePlanner
from .simulation import Simulation
from .display import ColorPalette, Display
from .models import Network
from .graph import Graph


def main() -> None:
    """Run the Fly-in Drones simulation."""
    arg = arg_parse()
    network: Network = get_network(str(arg.get("file")))
    graph = Graph(network)

    planner = TimePlanner(graph, 100)
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
