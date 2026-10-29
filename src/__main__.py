"""Entry point for the Fly-in Drones simulation."""
from .parser import Parser
from pydantic import ValidationError
from .pathfinder import TimePlanner
from .simulation import Simulation
from .display import ColorPalette, Display
from .models import Network
from .graph import Graph


if __name__ == "__main__":
    try:
        parser = Parser()
        network: Network = parser.get_network()
        graph = Graph(network)
    
        planner = TimePlanner(graph, 100)
        color_palette = ColorPalette()
        display = Display(color_palette)
        simu = Simulation(planner, display, parser._output_file)
    
        simu.run()

    except ValidationError as error:
        print(error.errors()[0]["msg"])
    except Exception as error:
        print(f"An error has occurred:\n{error}")
