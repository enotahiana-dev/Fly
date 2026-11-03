"""Graphical view of a Fly-in simulation."""
import pygame
import colorsys
import math
from .graph import Graph


class GraphicDisplay:
    """Animated view: zones, connections and numbered drones."""

    def __init__(self,
                 graph: Graph,
                 width: int = 1000, height: int = 640) -> None:
        """Precompute positions, scaling and drone colours."""
        pygame.init()
        self._window = pygame.display.set_mode((width, height))
        self._font = pygame.font.Font(None, 19)
        self._zones = graph.zones
        self._links = graph.links
        self._moves = graph.get_moves()
        self._speed = 1.5
        self._show_labels = False

        tracks: dict[str, dict[int, tuple[float, float]]] = {}
        for entry in self._moves:
            tracks.update(entry)

        self._last_turn = max(
            (max(t) for t in tracks.values() if t), default=0)
        self._timeline = {
            name: self._fill(track) for name, track in tracks.items()}
        self._names = sorted(self._timeline, key=self._number)
        self._colours = {
            name: self.drone_colour(i) for i, name in enumerate(self._names)}

        xs = [z.x for z in self._zones.values()]
        ys = [z.y for z in self._zones.values()]
        span_x = max(max(xs) - min(xs), 1.0)
        span_y = max(max(ys) - min(ys), 1.0)
        margin = 60
        inner_w, inner_h = width - 2 * margin, height - 2 * margin
        self._scale = min(inner_w / span_x, inner_h / span_y)
        self._off_x = margin + (inner_w - span_x * self._scale) / 2 \
            - min(xs) * self._scale
        self._off_y = margin + (inner_h - span_y * self._scale) / 2 \
            - min(ys) * self._scale

        pts = [self._screen((z.x, z.y)) for z in self._zones.values()]
        closest = min((math.dist(p, q) for i, p in enumerate(pts)
                       for q in pts[i + 1:]), default=100.0)
        self._node_r = max(10, min(26, int(closest * 0.33)))
        self._drone_r = max(6, int(self._node_r * 0.38))
        self._spacing = int(self._drone_r * 1.7)
        self._slots = self._build_slots()

        self._progress = 0.0
        self._playing = True

    @staticmethod
    def _number(name: str) -> int:
        """Return 12 for 'D12'."""
        digits = "".join(ch for ch in name if ch.isdigit())
        return int(digits) if digits else 0

    @staticmethod
    def zone_colour(word: str | None) -> tuple[int, int, int]:
        """Return the RGB of a colour word, or the default colour."""
        if word is None:
            return (110, 120, 150)
        try:
            c = pygame.Color(word.strip().lower())
        except ValueError:
            return (110, 120, 150)
        return (c.r, c.g, c.b)

    @staticmethod
    def drone_colour(index: int) -> tuple[int, int, int]:
        """Bright colour, well separated from the previous drone's."""
        r, g, b = colorsys.hsv_to_rgb(
            (index * 0.618033988749895) % 1.0, 0.65, 1.0)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _fill(self, track: dict[int, tuple[float, float]]
              ) -> list[tuple[float, float]]:
        """One position per turn, from the sparse {turn: position}."""
        if not track:
            return [(0.0, 0.0)] * (self._last_turn + 1)
        current = track[min(track)]
        points: list[tuple[float, float]] = []
        for turn in range(self._last_turn + 1):
            current = track.get(turn, current)
            points.append(current)
        return points

    def _screen(self, p: tuple[float, float]) -> tuple[float, float]:
        """Map coordinates -> pixels."""
        return (p[0] * self._scale + self._off_x,
                p[1] * self._scale + self._off_y)

    def _build_slots(self) -> list[dict[str, tuple[float, float]]]:
        """Per turn, spread the drones sharing a position on a grid."""
        slots: list[dict[str, tuple[float, float]]] = []
        for turn in range(self._last_turn + 1):
            groups: dict[tuple[float, float], list[str]] = {}
            for name in self._names:
                groups.setdefault(self._timeline[name][turn], []).append(name)
            frame: dict[str, tuple[float, float]] = {}
            for members in groups.values():
                cols = math.ceil(math.sqrt(len(members)))
                rows = math.ceil(len(members) / cols)
                for i, name in enumerate(members):
                    frame[name] = (
                        (i % cols - (cols - 1) / 2) * self._spacing,
                        (i // cols - (rows - 1) / 2) * self._spacing)
            slots.append(frame)
        return slots

    def _drone_pos(self, name: str) -> tuple[float, float]:
        """Pixel position of a drone at the current time."""
        i = min(int(self._progress), self._last_turn)
        j = min(i + 1, self._last_turn)
        f = self._progress - i
        f = f * f * (3 - 2 * f)
        x0, y0 = self._screen(self._timeline[name][i])
        x1, y1 = self._screen(self._timeline[name][j])
        ox0, oy0 = self._slots[i][name]
        ox1, oy1 = self._slots[j][name]
        return (x0 + (x1 - x0) * f + ox0 + (ox1 - ox0) * f,
                y0 + (y1 - y0) * f + oy0 + (oy1 - oy0) * f)

    def _draw(self) -> None:
        """Draw one frame."""
        self._window.fill((18, 20, 28))
        for a, b in self._links:
            za, zb = self._zones[a], self._zones[b]
            pygame.draw.line(self._window, (70, 76, 96),
                             self._screen((za.x, za.y)),
                             self._screen((zb.x, zb.y)), 2)
        for name, zone in self._zones.items():
            centre = self._screen((zone.x, zone.y))
            pygame.draw.circle(
                self._window, self.zone_colour(zone.metadata.color), centre,
                self._node_r, 4)
            if self._show_labels:
                text = self._font.render(name, True, (225, 228, 238))
                self._window.blit(text, text.get_rect(
                    center=(centre[0], centre[1] + self._node_r + 12)))
        for name in self._names:
            x, y = self._drone_pos(name)
            pygame.draw.circle(
                self._window, self._colours[name], (x, y), self._drone_r)
            label = self._font.render(
                str(self._number(name)), True, (15, 15, 20))
            self._window.blit(label, label.get_rect(center=(x, y)))
        width, height = self._window.get_size()
        help_text = self._font.render(
            "SPACE pause     R restart     L names     ESC quit",
            True, (95, 101, 122))
        self._window.blit(help_text, help_text.get_rect(
            center=(width // 2, height - 18)))

    def run(self) -> None:
        """Run the main core of the graphic display."""
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self._playing = not self._playing
                    elif event.key == pygame.K_r:
                        self._progress, self._playing = 0.0, True
                    elif event.key == pygame.K_l:
                        self._show_labels = not self._show_labels
            if self._playing:
                self._progress = min(
                    self._progress + self._speed * dt, float(self._last_turn))
            turn = min(int(self._progress + 0.5), self._last_turn)
            pygame.display.set_caption(
                f"Fly-in - turn {turn}/{self._last_turn}")
            self._draw()
            pygame.display.flip()
        pygame.quit()
