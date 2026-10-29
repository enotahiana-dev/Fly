"""Simulation engine for the Fly-in Drones project."""
from .display import Display
from typing import Any
from .pathfinder import TimePlanner
from .models import Drone


class Simulation:
    """Planify and run the drone simulation."""

    def __init__(self,
                 planner: TimePlanner,
                 display: Display,
                 output_file: str
                 ) -> None:
        """Initialize the simulation."""
        self._planner = planner
        self._drones: list[Drone] = self.schedule()
        self._max_turn: int = max([drone._arrival for drone in self._drones])
        self.lines: list[str] = []
        self._display = display
        self._display._graph = self._planner.graph
        self._output_file: Any = output_file

    def schedule(self) -> list[Drone]:
        """Planify all drones consecutively on the same planificator."""
        drones = [self._planner.plan(drone_id) for drone_id in range(1,
                  self._planner.graph.nb_drones + 1)]
        self._planner.graph._drones = drones
        return drones

    def run(self) -> None:
        """Launch the simulation."""
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
        """Save the file and handle the display and interactions."""
        self._planner.init_usage()
        self._display._output_file = self._output_file
        self._display.print_banner()

        with open(self._output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(self.lines))

        while True:
            inp = input("▸ ")
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
            else:
                self._display.print_command()
