import math
from collections import deque

import pygame

from physics import (accelerations, make_earth_moon, orbit_elements,
                     step_verlet, total_energy)

WIN_W, WIN_H = 1400, 860
RIGHT_W, BOTTOM_H = 400, 240
VIEW = pygame.Rect(0, 0, WIN_W - RIGHT_W, WIN_H - BOTTOM_H)
RIGHT = pygame.Rect(VIEW.right, 0, RIGHT_W, VIEW.height)
BOTTOM = pygame.Rect(0, VIEW.bottom, WIN_W, BOTTOM_H)

BASE_SCALE = 1.7e6
BAR_CHOICES_KM = [1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7]
DT = 1600.0
TRAIL_LEN = 2000
HIST_LEN = 700
PRESETS = {pygame.K_1: 1.0, pygame.K_2: 0.8, pygame.K_3: 1.45}

BG = (0, 0, 0)
PANEL = (18, 20, 26)
CARD = (26, 29, 37)
LINE = (60, 64, 76)
TEXT = (220, 224, 232)
DIM = (140, 146, 160)
VEL_COL = (80, 220, 120)
ACC_COL = (255, 110, 100)
BODY_STYLE = {"Earth": ((70, 130, 255), 8), "Moon": ((235, 235, 235), 4)}


class Simulation:
    def __init__(self, speed_factor=1.0):
        self.reset(speed_factor)

    def reset(self, speed_factor):
        self.factor = speed_factor
        self.bodies = make_earth_moon(speed_factor)
        self.t = 0.0
        self.e0 = total_energy(self.bodies)
        self.trails = [deque(maxlen=TRAIL_LEN) for _ in self.bodies]
        self.hist = deque(maxlen=HIST_LEN)
        self.record()

    def advance(self, n):
        for _ in range(n):
            step_verlet(self.bodies, DT)
            self.t += DT

    def drift(self):
        return (total_energy(self.bodies) - self.e0) / abs(self.e0)

    def record(self):
        el = orbit_elements(*self.bodies)
        self.hist.append((self.t, el["r"], el["speed"], self.drift()))
        for trail, b in zip(self.trails, self.bodies):
            trail.append((b.x, b.y))


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Orbit simulator")
        self.clock = pygame.time.Clock()
        names = "consolas,dejavusansmono,couriernew,monospace"
        self.font = pygame.font.SysFont(names, 15)
        self.small = pygame.font.SysFont(names, 13)
        self.sim = Simulation(1.0)
        self.scale = BASE_SCALE
        self.steps = 1
        self.paused = False
        self.running = True

    def to_screen(self, x, y):
        sx = VIEW.centerx + x / self.scale
        sy = VIEW.centery - y / self.scale
        return (int(max(-30000, min(30000, sx))), int(max(-30000, min(30000, sy))))

    def reset(self, factor):
        self.sim.reset(factor)
        self.scale = BASE_SCALE

    def fit_view(self):
        half_w, half_h = VIEW.w / 2 - 30, VIEW.h / 2 - 30
        need = max(max(abs(b.x) / half_w, abs(b.y) / half_h) for b in self.sim.bodies)
        self.scale = max(self.scale, need * 1.05)

    def text(self, s, pos, color=TEXT, font=None):
        surf = (font or self.font).render(s, True, color)
        self.screen.blit(surf, pos)
        return pos[1] + surf.get_height() + 2

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_UP:
                    self.steps = min(64, self.steps * 2)
                elif event.key == pygame.K_DOWN:
                    self.steps = max(1, self.steps // 2)
                elif event.key == pygame.K_r:
                    self.reset(self.sim.factor)
                elif event.key in PRESETS:
                    self.reset(PRESETS[event.key])

    def update(self):
        if not self.paused:
            self.sim.advance(self.steps)
            self.sim.record()
            self.fit_view()

    def arrow(self, color, origin, wx, wy, px_per_unit):
        dx, dy = wx * px_per_unit, -wy * px_per_unit
        length = math.hypot(dx, dy)
        if length < 3:
            return
        if length > 120:
            dx, dy = dx * 120 / length, dy * 120 / length
        end = (origin[0] + dx, origin[1] + dy)
        pygame.draw.line(self.screen, color, origin, end, 2)
        ang = math.atan2(dy, dx)
        head = [end] + [(end[0] - 9 * math.cos(ang + s * 0.4),
                         end[1] - 9 * math.sin(ang + s * 0.4)) for s in (1, -1)]
        pygame.draw.polygon(self.screen, color, head)

    def draw_view(self):
        pygame.draw.rect(self.screen, BG, VIEW)
        self.screen.set_clip(VIEW)
        cx, cy = VIEW.center
        pygame.draw.line(self.screen, LINE, (cx - 6, cy), (cx + 6, cy))
        pygame.draw.line(self.screen, LINE, (cx, cy - 6), (cx, cy + 6))
        bar_km = next((k for k in BAR_CHOICES_KM if k * 1e3 / self.scale >= 40), BAR_CHOICES_KM[-1])
        bar = bar_km * 1e3 / self.scale
        y = VIEW.bottom - 24
        pygame.draw.line(self.screen, DIM, (20, y), (20 + bar, y), 2)
        accs = accelerations(self.sim.bodies)
        for body, trail, (ax, ay) in zip(self.sim.bodies, self.sim.trails, accs):
            color, radius = BODY_STYLE[body.name]
            if len(trail) > 1:
                dim = tuple(int(c * 0.55) for c in color)
                pygame.draw.lines(self.screen, dim, False,
                                  [self.to_screen(px, py) for px, py in trail], 1)
            pos = self.to_screen(body.x, body.y)
            self.arrow(VEL_COL, pos, body.vx / 1e3, body.vy / 1e3, 45)
            self.arrow(ACC_COL, pos, ax * 1e3, ay * 1e3, 20)
            pygame.draw.circle(self.screen, color, pos, radius)
        self.screen.set_clip(None)
        self.text(f"{bar_km:,.0f} km", (20, y + 5), DIM, self.small)
        self.text("SPACE pause   UP/DOWN speed   R reset   1 circular  2 ellipse  3 escape",
                  (16, 12), DIM, self.small)
        self.text("green = velocity   red = acceleration", (16, 32), DIM, self.small)
        self.text("bodies not to scale", (VIEW.right - 170, VIEW.bottom - 24), DIM, self.small)

    def section(self, title, y):
        return self.text(title, (RIGHT.x + 16, y + 6), DIM, self.small) + 2

    def row(self, s, y, color=TEXT):
        return self.text(s, (RIGHT.x + 16, y), color)

    def draw_right(self):
        pygame.draw.rect(self.screen, PANEL, RIGHT)
        pygame.draw.line(self.screen, LINE, RIGHT.topleft, RIGHT.bottomleft)
        sim = self.sim
        fps = self.clock.get_fps() or 60.0
        y = self.section("TIME", 8)
        y = self.row(f"t      {sim.t / 86400:9.2f} days", y)
        y = self.row(f"dt     {DT:.0f} s  x{self.steps} steps/frame", y)
        y = self.row(f"speed  {DT * self.steps * fps / 86400:9.2f} days per second", y)
        if self.paused:
            y = self.row("PAUSED", y, ACC_COL)
        y = self.text("pos, vel, acc: from the Earth-Moon barycenter", (RIGHT.x + 16, y + 2), DIM, self.small)
        accs = accelerations(sim.bodies)
        for body, (ax, ay) in zip(sim.bodies, accs):
            color, _ = BODY_STYLE[body.name]
            y = self.section(body.name.upper(), y + 6)
            pygame.draw.rect(self.screen, color, (RIGHT.x + 74, y - 18, 8, 8))
            speed = math.hypot(body.vx, body.vy) / 1e3
            amag = math.hypot(ax, ay) * 1e3
            y = self.row(f"pos ({body.x / 1e3:+,.0f}, {body.y / 1e3:+,.0f}) km", y)
            y = self.row(f"vel ({body.vx / 1e3:+.3f}, {body.vy / 1e3:+.3f}) km/s", y)
            y = self.row(f"    |v| = {speed:.4f} km/s", y, VEL_COL)
            y = self.row(f"acc ({ax * 1e3:+.4f}, {ay * 1e3:+.4f}) mm/s2", y)
            y = self.row(f"    |a| = {amag:.4f} mm/s2", y, ACC_COL)
        el = orbit_elements(*sim.bodies)
        y = self.section("MOON AROUND EARTH", y + 6)
        y = self.row(f"distance   {el['r'] / 1e3:>11,.0f} km", y)
        if el["a"] is None:
            y = self.row("semi-major axis   unbound", y)
            y = self.row(f"eccentricity {el['e']:.4f}", y)
            y = self.row("period     none (escapes)", y)
        else:
            y = self.row(f"semi-major {el['a'] / 1e3:>11,.0f} km", y)
            y = self.row(f"eccentricity {el['e']:.4f}", y)
            y = self.row(f"period     {el['period'] / 86400:>8.2f} days", y)
        y = self.section("ENERGY CHECK", y + 6)
        self.row(f"drift  {sim.drift():+.2e}  (0 = conserved)", y)

    def graph(self, rect, title, values, color, fmt, min_span):
        pygame.draw.rect(self.screen, CARD, rect, border_radius=6)
        self.text(title, (rect.x + 12, rect.y + 8), TEXT, self.small)
        plot = pygame.Rect(rect.x + 86, rect.y + 34, rect.w - 102, rect.h - 62)
        for k in range(3):
            gy = plot.y + k * plot.h / 2
            pygame.draw.line(self.screen, LINE, (plot.x, gy), (plot.right, gy))
        n = len(values)
        if n < 2:
            return
        lo, hi = min(values), max(values)
        mid, span = (lo + hi) / 2, max(hi - lo, min_span)
        lo, hi = mid - span / 2, mid + span / 2
        pts = [(plot.x + i / (n - 1) * plot.w,
                plot.bottom - (v - lo) / (hi - lo) * plot.h)
               for i, v in enumerate(values)]
        pygame.draw.lines(self.screen, color, False, pts, 2)
        self.text(fmt(hi), (rect.x + 8, plot.y - 7), DIM, self.small)
        self.text(fmt(mid), (rect.x + 8, plot.centery - 7), DIM, self.small)
        self.text(fmt(lo), (rect.x + 8, plot.bottom - 7), DIM, self.small)
        self.text(f"now {fmt(values[-1])}", (rect.right - 190, rect.y + 8), color, self.small)

    def draw_bottom(self):
        pygame.draw.rect(self.screen, PANEL, BOTTOM)
        pygame.draw.line(self.screen, LINE, BOTTOM.topleft, BOTTOM.topright)
        hist = list(self.sim.hist)
        gap = 12
        w = (BOTTOM.w - 4 * gap) // 3
        rects = [pygame.Rect(gap + i * (w + gap), BOTTOM.y + gap, w, BOTTOM.h - 2 * gap)
                 for i in range(3)]
        self.graph(rects[0], "Earth-Moon distance", [h[1] for h in hist], (120, 170, 255),
                   lambda v: f"{v / 1e3:,.0f} km", 7.7e6)
        self.graph(rects[1], "Moon speed vs Earth", [h[2] for h in hist], VEL_COL,
                   lambda v: f"{v / 1e3:.3f} km/s", 20.0)
        self.graph(rects[2], "Energy drift (flat = good)", [h[3] for h in hist], ACC_COL,
                   lambda v: f"{v:+.1e}", 1e-9)
        if len(hist) > 1:
            days = (hist[-1][0] - hist[0][0]) / 86400
            self.text(f"graphs show the last {days:.1f} simulated days",
                      (BOTTOM.right - 330, BOTTOM.bottom - 18), DIM, self.small)

    def draw(self):
        self.screen.fill(BG)
        self.draw_view()
        self.draw_right()
        self.draw_bottom()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    App().run()
