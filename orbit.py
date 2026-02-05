import numpy as np
import pygame

SCALE = 910.142e3

class Planet:
    def __init__(self, x, y, radius, color, vx, vy, mass):
        self.x = x
        self.y = y
        self.radius = radius 
        self.color = color
        self.vx = vx
        self.vy = vy
        self.mass = mass

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x/SCALE), int(self.y/SCALE)), self.radius)
        

    def move(self, dt): 
        self.x += float(self.vx*dt)
        self.y += float(self.vy*dt)



pygame.init()

screen = pygame.display.set_mode((1900,1120))
clock = pygame.time.Clock()
dt = (clock.tick(60) /1000) * 100000

earth = Planet(950*SCALE, 560*SCALE, 7, (0,0,255), 0, 0, 6e24)
vm = np.sqrt((6.67e-11*6e24)/(445.75*910.142e3))
moon = Planet(504*SCALE, 560*SCALE, 2, (255,255,255), 0, vm, 7.347e22)
mars = Planet(100*SCALE, 560*SCALE, 2, (0, 255, 0), 0, 400, 1)

def calculateForce(obj1, obj2, dt):
    dis = np.sqrt((obj1.x - obj2.x)**2 + (obj1.y - obj2.y)**2) 
    F = (6.67e-11*obj1.mass*obj2.mass)/(dis**2)
    Fx = F*(obj1.x-obj2.x)/dis
    Fy = F*(obj1.y-obj2.y)/dis

    return Fx, Fy
    
def ForceSum(a, b):
    fx = a[0]+b[0]
    fy = a[1]+b[1]

    return fx, fy


def calculateAcceleration(obj, Fx, Fy):
    ax= Fx/obj.mass
    ay= Fy/obj.mass

    return ax, ay

def update_vel(obj1, obj2, obj3, dt):

    F1x, F1y = ForceSum(calculateForce(obj1, obj2, dt), calculateForce(obj1, obj3, dt))
    F2x, F2y = ForceSum(calculateForce(obj1, obj2, dt), calculateForce(obj3, obj2, dt))
    F3x, F3y = ForceSum(calculateForce(obj1, obj3, dt), calculateForce(obj2, obj3, dt))

    a1x, a1y = calculateAcceleration(obj1, F1x, F1y)
    a2x, a2y = calculateAcceleration(obj2, F2x, F2y)
    a3x, a3y = calculateAcceleration(obj3, F3x, F3y)



    obj1.vx += a1x*dt
    obj1.vy += a1y*dt

    obj2.vx +=a2x*dt
    obj2.vy +=a2y*dt

    obj3.vx +=a3x*dt
    obj3.vy +=a3y*dt

    
    obj1.x += obj1.vx*dt + 0.5*a1x*(dt**2)
    obj1.y += obj1.vy*dt + 0.5*a1y*(dt**2)

    obj2.x += obj2.vx*dt + 0.5*a2x*(dt**2)
    obj2.y += obj2.vy*dt + 0.5*a2y*(dt**2)

    obj3.x += obj3.vx*dt + 0.5*a3x*(dt**2)
    obj3.y += obj3.vy*dt + 0.5*a3y*(dt**2)



running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False

    update_vel(earth, moon, mars, dt)
    #earth.move(dt)
    #moon.move(dt)

    screen.fill((0,0,0))
    earth.draw(screen)
    moon.draw(screen)
    mars.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
        

    