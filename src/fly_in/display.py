"""Terminal display and rendering for the Fly-in Drones simulation."""
from .graph import Graph
import random
import sys


class ColorPalette:
    """Turns any color word into a 256-color ANSI escape code."""

    RESET = "\033[0m"

    _KNOWN: dict[str, int] = {
        "black": 16, "white": 15, "gray": 244, "grey": 244,
        "silver": 250, "red": 196, "darkred": 124, "maroon": 88,
        "orange": 208, "gold": 220, "yellow": 226, "lime": 46,
        "green": 34, "darkgreen": 22, "olive": 100, "teal": 30,
        "cyan": 51, "turquoise": 44, "blue": 33, "navy": 18,
        "skyblue": 117, "purple": 93, "violet": 129, "magenta": 201,
        "pink": 213, "brown": 94, "beige": 223
    }

    _FALLBACK: tuple[int, ...] = (
        33, 39, 45, 70, 76, 99, 129, 135, 141, 166, 172, 178,
        184, 204, 208, 213, 214, 220)

    def __init__(self, enabled: bool | None = None) -> None:
        """Instanciate a ColorPalette."""
        self._enabled: bool = (
            sys.stdout.isatty() if enabled is None else enabled)

        self._cache: dict[str, int] = {}

    def _pick(self, name: str) -> int:
        """Pick a stable color number for an unknown color name."""
        if name not in self._cache:
            rng = random.Random(name)
            self._cache[name] = rng.choice(self._FALLBACK)
        return self._cache[name]

    def code(self, color: str | None) -> str:
        """Return the escape code for `color` ('' if none applies)."""
        if not self._enabled or color is None:
            return ""
        name = color.strip().lower()
        if name in ("", "none"):
            return ""
        number = self._KNOWN.get(name)
        if number is None:
            number = self._pick(name)
        return f"\033[38;5;{number}m"

    def paint(self, text: str, color: str | None) -> str:
        """Wrap `text` in its color, or return it unchanged."""
        code = self.code(color)
        return f"{code}{text}{self.RESET}" if code else text


class Display:
    """Colored terminal rendering of the simulation."""

    def __init__(self,
                 palette: ColorPalette | None = None) -> None:
        """Initialize the display with a graph and color settings."""
        self._graph: Graph
        self._palette = palette if palette is not None else ColorPalette()
        self._dot: str = ""
        self._output_file: str = ""
        self.init_form()

    def paint(self, zone: str) -> str:
        """Return the zone name wrapped in its color, if any."""
        if '-' in zone:
            _a, _b = zone.split('-')
            a = self._palette.paint(_a, self._graph.get_zone_color(_a))
            b = self._palette.paint(_b, self._graph.get_zone_color(_b))
            return '-'.join([a, b])
        return self._palette.paint(zone, self._graph.get_zone_color(zone))

    def line_output(self, line: str, turn: int) -> str:
        """Format one line(turn) and return."""
        lines: list[str] = line.split(' ')
        drones: dict[str, str] = {}
        for lin in lines:
            drone, zone = lin.split('-', 1)
            _prop = self.usage_format(turn, zone)
            drones[drone] = self._palette.paint(
                f"{zone}{_prop}",
                self._graph.get_zone_color(zone))

        _line: list[str] = []
        _arrow: str = self._palette.paint("▸", "lime")

        for drone, zone in drones.items():
            if "-" in zone:
                _line.append(f"{drone} {_arrow}{_arrow} {zone}")
            else:
                _line.append(f"{drone} {_arrow} {zone}")

        lin = self._palette.paint(" ◆ ", "lime").join(_line)

        return lin

    def show_turn(self, turn: int, line: str
                  ) -> None:
        """Print one turn."""
        if self._graph.end in line:
            self._dot = self.g_dot
        else:
            self._dot = self.r_dot
        start: str = "    \033[3mStart: \033[0m"
        end: str = "    \033[3mEnd: \033[0m"
        usage_s = self.usage_format(turn, self._graph.start)
        usage_e = self.usage_format(turn, self._graph.end).strip("()")

        print(f" {self._dot} ", f"{self._palette.paint(f" TURN {turn}:",
              "gray")}")

        print(f"{start}{usage_s}")
        print(f"{end}{usage_e}", "\n")

        print("    ", self.line_output(line, turn))

    def play(self, lines: list[str]) -> None:
        """Step through the turns, one key press at a time."""
        print("\n \n")
        print(f"{self._palette.paint(" • TURN 0:", "gray")}")
        print(f"    \033[3mStart: \033[0m{self.usage_format(0,
              self._graph.start)}")

        print(f"    \033[3mEnd: \033[0m{self.usage_format(0,
              self._graph.end).strip("()")}", "\n")
        input()
        for turn, line in enumerate(lines, start=1):
            self.show_turn(turn, line)
            print()
            input()
        print("\033[38;5;4;3m • Drones are successfully delivered ✓ \033[0m")
        self.stats(lines)

    def usage_format(self, turn: int, zone: str) -> str:
        """Return the usage into a (usage/capacity) format."""
        usage: int = 0
        if zone == self._graph.end:
            for z, t in self._graph.zone_use.keys():
                if z == self._graph.end and t <= turn:
                    usage += self._graph.zone_use.get((z, t), 0)
            max_drones = self._graph.zone_capacity(zone)
            return f"({usage}/{max_drones})"

        elif zone == self._graph.start:
            if turn == 0:
                return (f"{self._graph.zone_capacity(zone)}/"
                        f"{self._graph.zone_capacity(zone)}")
            usage = self._graph.zone_use.get((zone, turn), 0)
            max_drones = self._graph.zone_capacity(zone)
            return f"{usage}/{max_drones}"

        elif '-' in zone:
            a, b = zone.split('-', 1)
            usage = self._graph.get_link_use(a, b, turn)
            max_drones = self._graph.link_capacity(a, b)

        else:
            usage = self._graph.zone_use.get((zone, turn), 0)
            max_drones = self._graph.zone_capacity(zone)
        return f"({usage}/{max_drones})"

    def stats(self, lines: list[str]) -> None:
        """Print the statistics of the simulation."""
        print(f"\033[3;34m{("_") * 47}\033[0m\n")
        print("\033[38;5;4;3mSTATS:\033[0m")
        print()

        print(f" - Total drones: {self._graph.nb_drones}")

        print(f" - Total turns: {len(lines)}")
        print(f" - Min turns: {self._graph.get_turns()["min"]}")
        print(f" - Max turns: {self._graph.get_turns()["max"]}\n")

        print(f"File saved in: {self._output_file}")

        print()
        print(f"\033[3;34m{("_") * 47}\033[0m\n")

    def init_form(self) -> None:
        """Initialize a dot with different color."""
        self.r_dot: str = self._palette.paint('•', "red")
        self.g_dot: str = self._palette.paint('•', "green")

    def print_banner(self) -> None:
        """Print the banner introduction."""
        c1 = "\033[38;2;80;220;120m"
        c2 = "\033[38;2;80;150;255m"
        c3 = "\033[38;2;255;215;80m"
        c4 = "\033[38;2;220;100;220m"
        c5 = "\033[38;5;244m"
        r = "\033[0m"
        b = "\033[1m"

        lines = [
            f"{c1}  ______ _                 _                {r}",
            f"{c1} |  ____| |               (_)                 {r}",
            f"{c2} | |__  | |_   _           _ _ __    {r}",
            f"{c2} |  __| | | | | |  _____  | | '_ \\ {r}",
            f"{c3} | |    | | |_| | |_   _| | | | | |  {r}",
            f"{c3} |_|    |_|\\___,|         |_|_| |_| {r}",
            f"{c3}             _/ |                              {r}",
            f"{c4}            |___/                               {r}",
            "",
            f"{b}{c1}                  Command and PRESS Enter{r}",
            f"{b}{c5}'v' for visualisation{r}",
            f"{b}{c5}'l' for line per turn{r}",
            f"{b}{c5}'q' to quit{r}",


        ]
        for line in lines:
            print(line)
        print()

    def print_command(self) -> None:
        """Print the available command for interaction."""
        c = "\033[38;5;244m"
        b = "\033[1m"
        res = "\033[0m"
        print(
              f"{b}{c}'v' for visualisation{res}",
              f"{b}{c}'l' for line per turn{res}",
              f"{b}{c}'q' to quit{res}")
