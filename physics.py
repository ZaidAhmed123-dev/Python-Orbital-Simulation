import math

G = 6.6743e-11


class Body:
    def __init__(self, name, x, y, vx, vy, mass):
        self.name = name
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.mass = mass


def accelerations(bodies):
    acc = []
    for i, a in enumerate(bodies):
        ax = ay = 0.0
        for j, b in enumerate(bodies):
            if i == j:
                continue
            dx, dy = b.x - a.x, b.y - a.y
            r = math.hypot(dx, dy)
            k = G * b.mass / r**3
            ax += k * dx
            ay += k * dy
        acc.append((ax, ay))
    return acc


def step_verlet(bodies, dt):
    old = accelerations(bodies)
    for b, (ax, ay) in zip(bodies, old):
        b.x += b.vx * dt + 0.5 * ax * dt**2
        b.y += b.vy * dt + 0.5 * ay * dt**2
    new = accelerations(bodies)
    for b, (ax, ay), (bx, by) in zip(bodies, old, new):
        b.vx += 0.5 * (ax + bx) * dt
        b.vy += 0.5 * (ay + by) * dt


def total_energy(bodies):
    ke = sum(0.5 * b.mass * (b.vx**2 + b.vy**2) for b in bodies)
    pe = 0.0
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            r = math.hypot(bodies[i].x - bodies[j].x, bodies[i].y - bodies[j].y)
            pe -= G * bodies[i].mass * bodies[j].mass / r
    return ke + pe


def orbit_elements(primary, secondary):
    mu = G * (primary.mass + secondary.mass)
    rx, ry = secondary.x - primary.x, secondary.y - primary.y
    vx, vy = secondary.vx - primary.vx, secondary.vy - primary.vy
    r = math.hypot(rx, ry)
    v2 = vx * vx + vy * vy
    eps = 0.5 * v2 - mu / r
    h = rx * vy - ry * vx
    e = math.sqrt(max(0.0, 1.0 + 2.0 * eps * h * h / (mu * mu)))
    a = period = None
    if eps < 0:
        a = -mu / (2.0 * eps)
        period = 2.0 * math.pi * math.sqrt(a**3 / mu)
    return {"r": r, "speed": math.sqrt(v2), "e": e, "a": a, "period": period}


def make_earth_moon(speed_factor=1.0):
    M, m = 5.972e24, 7.342e22
    d = 3.844e8
    v_rel = math.sqrt(G * (M + m) / d) * speed_factor
    earth = Body("Earth", -d * m / (M + m), 0.0, 0.0, -m / (M + m) * v_rel, M)
    moon = Body("Moon", d * M / (M + m), 0.0, 0.0, M / (M + m) * v_rel, m)
    return [earth, moon]
