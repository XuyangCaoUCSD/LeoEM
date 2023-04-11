import networkx as nx
import math

def degToRad(deg):
    pi = math.pi
    return deg * pi / 180

"""
    input: (lat, long, alt)
    output: (x, y, z)
    algorithm borrowed from StarPerf's MATLAB codes; conversion of coordinate systems
"""
def lla2cbf(position):
    R = 6371 * (10 ** 3)
    pi = math.pi
    r = R + position[2]
    theta = pi / 2 - position[0] * pi / 180
    phi = 2 * pi + position[1] * pi / 180
    x = (r * math.sin(theta)) * math.cos(phi)
    y = (r * math.sin(theta)) * math.sin(phi)
    z = r * math.cos(theta)
    return (x, y, z)

"""
    get the ground converage limit L of a celestial object
    see README.md for more details
"""
def getCoverageLimitL(elevation, depression, altitude):
    R = 6378 * 10 ** 3
    gamma = 90 - (elevation + depression)
    l = R * math.sin(degToRad(gamma))
    theta = (180 - gamma) / 2
    d = l / (math.tan(degToRad(theta)))
    L = math.sqrt((altitude + d) ** 2 + l ** 2)
    return L

'''
    given coordinates of a satellite, a ground station, and coverage limit L, check 
    if the satellite can cover the ground station
'''
def checkSatCoverGroundStation(sat_position_cbf, gs_position_cbf, L):
    x1, y1, z1 = sat_position_cbf
    x2, y2, z2 = gs_position_cbf
    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)
    return dist <= L

'''
    compute (electromagnetic) wave's propogation latency between two points in vacuum
'''
def computeLatency(point_a_cbf, point_b_cbf):
    dist = math.sqrt((point_a_cbf[0] - point_b_cbf[0])**2 + (point_a_cbf[1] - point_b_cbf[1])**2 + (point_a_cbf[1] - point_b_cbf[1])**2)
    return dist / (3 * 10**8)

'''
    given a source, destination, and the graph, check whether an e2e path exists
'''
def pathExists(gw1, gw2, G):
    if gw1 == -1 or gw2 == -1:
        return False
    return nx.has_path(G, gw1, gw2)