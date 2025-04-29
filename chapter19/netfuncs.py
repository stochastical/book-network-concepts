import sys
import json

from typing import Optional


def ipv4_to_value(ipv4_addr: str) -> int:
    """
    Convert a dots-and-numbers string IP address to a single 32-bit numeric
    value of integer type.

    We compute the integer equivalent by bitshifting each octet to produce the 32-bit
    little-endian representation.

    Examples:
    >>> ipv4_to_value('255.255.0.0')
    4294901760
    -> binary: ['0b11111111', '0b11111111', '0b0', '0b0']
    -> hex   : ['0xff', '0xff', '0x0', '0x0']
    >>> ipv4_to_value('1.2.3.4')
    16909060
    -> binary: ['0b1', '0b10', '0b11', '0b100']
    -> hex   : ['0x1', '0x2', '0x3', '0x4']
    """

    # 8 * [3, 2, 1, 0] == [24, 16, 8, 0]
    OCTET_SHIFTS = [0o30, 0o20, 0o10, 0o0]

    ipv4_addr: list[str] = ipv4_addr.split('.')
    ipv4_addr: list[int] = [int(octet) for octet in ipv4_addr]
    ipv4_addr: int = sum(octet << shift for octet, shift in zip(ipv4_addr, OCTET_SHIFTS))
    # ^ Note: functionally, this would be a 'starmap' in Python (zipWith in Haskell)
    return ipv4_addr


def value_to_ipv4(addr: int) -> str:
    """
    Convert a single 32-bit numeric value of integer type to a
    dots-and-numbers IP address. Returns a string type.

    There is only one input value, but it is shown here in 3 bases.
    >>> value_to_ipv4(4294901760) # == 0xffff0000 == 0b11111111111111110000000000000000
    "255.255.0.0"
    >>> value_to_ipv4(16909060) # == 0x01020304 == 0b00000001000000100000001100000100
    "1.2.3.4"
    """

    # 8 * [3, 2, 1, 0] == [24, 16, 8, 0]
    OCTET_SHIFTS = [0o30, 0o20, 0o10, 0o0]
    # Shift down to chunk to bits, and then mask off the irrelevant octet bits
    addr: list[int] = [(addr >> shift) & 0xFF for shift in OCTET_SHIFTS]
    addr: list[str] = [str(octet) for octet in addr]
    addr: str = '.'.join(addr)

    return addr


def get_subnet_mask_value(slash: str) -> int:
    """
    Given a subnet mask in slash notation, return the value of the mask
    as a single number of integer type. The input can contain an IP
    address optionally, but that part should be discarded.

    Returns an integer type.

    Example:

    There is only one return value, but it is shown here in 3 bases.
    >>> get_subnet_mask_value("/16")
    0xffff0000 # == 0b11111111111111110000000000000000 == 4294901760
    >>> get_subnet_mask_value("10.20.30.40/23")
    0xfffffe00 # == 0b11111111111111111111111000000000 == 4294966784
    """

    # First we produce a run of 1's of length `slash`,
    # then we shift everything by the remaining digit-count to pad out 32 bits! - this is precisely the bitwise mask!
    slash: str = int(slash.split('/')[1])
    slash: int = ((1 << slash) - 1) << (32 - slash)

    return slash


def ips_same_subnet(ip1: str, ip2: str, slash: str) -> bool:
    """
    Given two dots-and-numbers IP addresses and a subnet mask in slash
    nottaion, return true if the two IP addresses are on the same
    subnet.

    Returns a boolean.

    FOR FULL CREDIT: this must use your get_subnet_mask_value() and
    ipv4_to_value() functions. Don't do it with pure string
    manipulation.

    This needs to work with any subnet from /1 to /31

    Example:

    ip1:    "10.23.121.17"
    ip2:    "10.23.121.225"
    slash:  "/23"
    return: True

    ip1:    "10.23.230.22"
    ip2:    "10.24.121.225"
    slash:  "/16"
    return: False
    """

    ip1: int = ipv4_to_value(ip1)
    ip2: int = ipv4_to_value(ip2)
    subnet_mask: int = get_subnet_mask_value(slash)

    # 'Do they have the same subnet bits?'
    return (ip1 & subnet_mask) == (ip2 & subnet_mask)


def get_network(ip_value: int, netmask: int) -> int:
    """
    Return the network portion of an address value as integer type.

    Example:

    ip_value: 0x01020304
    netmask:  0xffffff00
    return:   0x01020300
    """

    return ip_value & netmask


def find_router_for_ip(
    routers: dict[str, dict[str, str]], ip: str
) -> Optional[str]:
    """
    Search a dictionary of routers (keyed by router IP) to find which
    router belongs to the same subnet as the given IP.

    Return None if no routers is on the same subnet as the given IP.

    FOR FULL CREDIT: you must do this by calling your ips_same_subnet()
    function.

    Example:

    [Note there will be more data in the routers dictionary than is
    shown here--it can be ignored for this function.]

    >>> routers = {
        "1.2.3.1": {
            "netmask": "/24"
        },
        "1.2.4.1": {
            "netmask": "/24"
        }
    }
    >>> ip = "1.2.3.5"
    >>> find_router_for_ip(routers, ip)
    "1.2.3.1"


    >>> routers = {
        "1.2.3.1": {
            "netmask": "/24"
        },
        "1.2.4.1": {
            "netmask": "/24"
        }
    }
    >>> ip = "1.2.5.6"
    >>> find_router_for_ip(routers, ip)
    None
    """

    for router_ip, router_info in routers.items():
        if ips_same_subnet(ip, router_ip, router_info['netmask']):
            return router_ip
    return None


## -------------------------------------------
## The below is provided by Beej's source code
## -------------------------------------------


def usage():
    print('usage: netfuncs.py infile.json', file=sys.stderr)


def read_routers(file_name):
    with open(file_name) as fp:
        json_data = fp.read()
    return json.loads(json_data)


def print_routers(routers):
    print('Routers:')

    routers_list = sorted(routers.keys())

    for router_ip in routers_list:
        # Get the netmask
        slash_mask = routers[router_ip]['netmask']
        netmask_value = get_subnet_mask_value(slash_mask)
        netmask = value_to_ipv4(netmask_value)

        # Get the network number
        router_ip_value = ipv4_to_value(router_ip)
        network_value = get_network(router_ip_value, netmask_value)
        network_ip = value_to_ipv4(network_value)

        print(f' {router_ip:>15s}: netmask {netmask}: network {network_ip}')


def print_same_subnets(src_dest_pairs):
    print('IP Pairs:')

    src_dest_pairs_list = sorted(src_dest_pairs)

    for src_ip, dest_ip in src_dest_pairs_list:
        print(f' {src_ip:>15s} {dest_ip:>15s}: ', end='')

        if ips_same_subnet(src_ip, dest_ip, '/24'):
            print('same subnet')
        else:
            print('different subnets')


def print_ip_routers(routers, src_dest_pairs):
    print('Routers and corresponding IPs:')

    all_ips = sorted(set([i for pair in src_dest_pairs for i in pair]))

    router_host_map = {}

    for ip in all_ips:
        router = str(find_router_for_ip(routers, ip))

        if router not in router_host_map:
            router_host_map[router] = []

        router_host_map[router].append(ip)

    for router_ip in sorted(router_host_map.keys()):
        print(f' {router_ip:>15s}: {router_host_map[router_ip]}')


def main(argv):
    if 'my_tests' in globals() and callable(my_tests):
        my_tests()
        return 0

    try:
        router_file_name = argv[1]
    except:
        usage()
        return 1

    json_data = read_routers(router_file_name)

    routers = json_data['routers']
    src_dest_pairs = json_data['src-dest']

    print_routers(routers)
    print()
    print_same_subnets(src_dest_pairs)
    print()
    print_ip_routers(routers, src_dest_pairs)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
