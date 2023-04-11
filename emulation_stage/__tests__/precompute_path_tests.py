import math

def degToRad(deg):
    pi = math.pi
    return deg * pi / 180

def getCoverageLimitL(elevation, depression, altitude):
    R = 6378 * 10 ** 3
    gamma = 90 - (elevation + depression)
    l = R * math.sin(degToRad(gamma))
    theta = (180 - gamma) / 2
    d = l / (math.tan(degToRad(theta)))
    L = math.sqrt((altitude + d) ** 2 + l ** 2)
    return L

print("Starlink L is:", getCoverageLimitL(40, 44.85, 550 * 10 ** 3))

