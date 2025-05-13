"""
$ python -m chapter22.dijkstra chapter22/example1.json
"""

import sys
import json
import math

from typing import Optional

from chapter19 import netfuncs


def dijkstras_shortest_path(
    routers: dict, src_ip: str, dest_ip: str
) -> list[str]:
    """
    This function takes a dictionary representing the network, a source
    IP, and a destination IP, and returns a list with all the routers
    along the shortest path.

    The source and destination IPs are **not** included in this path.

    Note that the source IP and destination IP will probably not be
    routers! They will be on the same subnet as the router. You'll have
    to search the routers to find the one on the same subnet as the
    source IP. Same for the destination IP. [Hint: make use of your
    find_router_for_ip() function from the last project!]

    The dictionary keys are router IPs, and the values are dictionaries
    with a bunch of information, including the routers that are directly
    connected to the key.

    This partial example shows that router `10.31.98.1` is connected to
    three other routers: `10.34.166.1`, `10.34.194.1`, and `10.34.46.1`:

    {
        "10.34.98.1": {
            "connections": {
                "10.34.166.1": {
                    "netmask": "/24",
                    "interface": "en0",
                    "ad": 70
                },
                "10.34.194.1": {
                    "netmask": "/24",
                    "interface": "en1",
                    "ad": 93
                },
                "10.34.46.1": {
                    "netmask": "/24",
                    "interface": "en2",
                    "ad": 64
                }
            },
            "netmask": "/24",
            "if_count": 3,
            "if_prefix": "en"
        },
        ...

    The "ad" (Administrative Distance) field is the edge weight for that
    connection.
    """

    # First, find the router that belongs to the same subnet as the given src and dest IPs
    start_router = netfuncs.find_router_for_ip(routers, src_ip)
    end_router = netfuncs.find_router_for_ip(routers, dest_ip)
    if start_router == end_router:  # we're already on the same subnet!
        return []

    # Apply Djikstra to find the shortest path between the source and dest routers
    dist: dict[str, float] = {}
    prev: dict[str, Optional[str]] = {}
    queue = []

    # initialisation
    for router in routers:
        dist[router] = math.inf
        prev[router] = None
        queue.append(router)
    dist[start_router] = 0

    # Greedily compute the shortest paths between each router using the Administrative Distance as edge-weights
    while queue:
        # Get the router in the queue that currently has the shortest distance
        u = min(queue, key=dist.get)
        queue.remove(u)

        # Determine the next shortest distance
        for neighbour_router, connection in routers[u]['connections'].items():
            if neighbour_router in queue:
                alt = dist[u] + connection['ad']
                if alt < dist[neighbour_router]:
                    dist[neighbour_router] = alt
                    prev[neighbour_router] = u

    # Now that we've computed the shortest distance traversals, construct the path of interest
    # between the src and dest routers, by preceding backwards from the end_router
    cur = end_router
    path = []
    while cur != start_router:
        path.append(cur)
        cur = prev[cur]
    path.append(start_router)
    return list(reversed(path))


# ------------------------------
# DO NOT MODIFY BELOW THIS LINE
# ------------------------------
def read_routers(file_name):
    with open(file_name) as fp:
        data = fp.read()

    return json.loads(data)


def find_routes(routers, src_dest_pairs):
    for src_ip, dest_ip in src_dest_pairs:
        path = dijkstras_shortest_path(routers, src_ip, dest_ip)
        print(f'{src_ip:>15s} -> {dest_ip:<15s}  {repr(path)}')


def usage():
    print('usage: dijkstra.py infile.json', file=sys.stderr)


def main(argv):
    try:
        router_file_name = argv[1]
    except:
        usage()
        return 1

    json_data = read_routers(router_file_name)

    routers = json_data['routers']
    routes = json_data['src-dest']

    find_routes(routers, routes)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
