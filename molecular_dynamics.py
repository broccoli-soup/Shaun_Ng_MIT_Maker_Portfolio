import numpy as np
from vpython import *
import random
import matplotlib.pyplot as plt

class Par:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity

print("Hello!")
N_in = input("\nHow many particles would you like to simulate? Press 'enter' for the default, which is 200. ")

try:
    N = int(N_in)
except ValueError:
    N = 200

a_in = input("\nHow large do you want the box to be? Press 'enter' for the default, which is 7. ")

try:
    a = int(a_in)
except ValueError:
    a = 7

F_max = 100
dt = 0.01


initialVelocity_in = input("\nWhat do you want the initial velocity to be? Press 'enter' for the default, which is 1.4. ")
try:
    intialVelocity = float(initialVelocity_in)
except ValueError:
    initialVelocity = 1.4

targetTemperature_in = input("\nWhat do you want the initial velocity to be? Press 'enter' for the default, which is 0.3. ")
try:
    targetTemperature = float(targetTemperature_in)
except ValueError:
    targetTemperature = 0.3

highlight = False
frame_rate = 60

# Bonding / box parameters
r_cutoff = 1.4 # distance threshold for bond visualization
bounds = a * 1.5
damping = 1
collisionDamping = 0.9

# irrelevant
walls = True

showBonds_in = input("\nWould you like to show 'bonds' between close atoms? (y/n) – default: y ")
showBonds = showBonds_in.lower().strip() in ["y", "yes", ""]
colorOnCoordinationNumber_in = input("Would you like to color atoms on their coordination number? (y/n) - default: y ")
colorOnCoordinationNumber = colorOnCoordinationNumber_in.lower().strip() in ["y", "yes", ""]

lengthAnimation_in = input("\nHow many seconds would you like the animation to go for? Press 'enter' for default, which is 10. ")
try:
    maxFrames = int(lengthAnimation_in) * 60
except ValueError:
    maxFrames = 500

# all the spheres
particles = []

# physics
data = []

# how many neighbours?
coordinationNumber = [0] * N   

for idx in range(N):
    position = vector(random.uniform(-a,a), random.uniform(-a,a), 0)
    
    velocity = vector(random.uniform(-1,1), random.uniform(-1,1), 0)
    velocity = norm(velocity) * initialVelocity
    
    particleColor = color.green if (idx == 0 or not highlight) else color.white

    particles.append(sphere(pos=position, radius=0.2, color=particleColor))
    data.append(Par(position, velocity))

def lennard_jones_force(r_vec, epsilon=0.9, sigma=0.15):
    r = mag(r_vec)
    if r == 0:
        return vector(0,0,0)
    # Standard LJ formula
    F_mag = 24 * epsilon * (2*(sigma/r)**12 - (sigma/r)**6) / r
    F_mag = min(F_mag, F_max)
    #
    
    return F_mag * norm(r_vec)

# dict for bond cylinders
bonds = {}                      
currentTemperature = initialVelocity ** 2
tau = 0.1 # thermostat parameter                        

for frameCount in range(maxFrames):
    if frameCount % 50 == 0:
        print(frameCount)

    rate(frame_rate)  # animation speed, don't make too high 
    previousTemperature = currentTemperature
    currentTemperature = 0

    for i in range(N):
        p = particles[i]
        par = data[i]

        # pos update
        p.pos += par.velocity * dt
        par.position += par.velocity * dt

        # damping
        par.velocity *= damping

        # thermostat
        if previousTemperature == 0: previousTemperature = 0.01
        lambda_factor = (1 + dt / tau * ((targetTemperature / previousTemperature) - 1))**0.5
        par.velocity *= lambda_factor

        # what's the current temperature right now?
        currentTemperature += (par.velocity.mag)**2 / N

        # bounce off wall
        if walls:
            if par.position.x > bounds:
                par.position.x = bounds
                p.pos.x = bounds
                par.velocity.x *= -1
            elif par.position.x < -bounds:
                par.position.x = -bounds
                p.pos.x = -bounds
                par.velocity.x *= -1
            if par.position.y > bounds:
                par.position.y = bounds
                p.pos.y = bounds
                par.velocity.y *= -1
            elif par.position.y < -bounds:
                par.position.y = -bounds
                p.pos.y = -bounds
                par.velocity.y *= -1
            if par.position.z > bounds:
                par.position.z = bounds
                p.pos.z = bounds
                par.velocity.z *= -1
            elif par.position.z < -bounds:
                par.position.z = -bounds
                p.pos.z = -bounds
                par.velocity.z *= -1

        # color if coord. number
        if colorOnCoordinationNumber:
            p.color = color.white if coordinationNumber[i] == 6 else color.red

        for j in range(i+1, N):
            r_vec = data[j].position - par.position
            dist = mag(r_vec)
            key = (i, j)

            if showBonds:
                if dist < r_cutoff:
                    if key not in bonds:
                        bonds[key] = cylinder(pos=par.position, axis=r_vec, radius=0.05)
                        coordinationNumber[i] += 1
                        coordinationNumber[j] += 1
                    else:
                        bonds[key].pos = par.position
                        bonds[key].axis = r_vec
                else:
                    if key in bonds:
                        bonds[key].visible = False
                        del bonds[key]
                        coordinationNumber[i] -= 1
                        coordinationNumber[j] -= 1

            F = lennard_jones_force(par.position - data[j].position, 2, 1)
            par.velocity += F * dt
            data[j].velocity -= F * dt

# g(r)
distances = [(data[i].position - data[j].position).mag 
             for i in range(N) for j in range(i+1, N)]

dr = 0.05
r_max = 5.0
bins = np.arange(0, r_max+dr, dr)
hist, edges = np.histogram(distances, bins=bins)

r_centers = (edges[:-1] + edges[1:])/2
shell_areas = np.pi * (edges[1:]**2 - edges[:-1]**2)  # 2D: area instead of volume
g_r = hist / shell_areas

# plot
plt.plot(r_centers, g_r)
plt.xlabel("r")
plt.ylabel("g(r)")
plt.title("2D Radial Distribution Function")

plt.show()