"""
$ hexdump -C tcp_data/tcp_data_0.dat
$ python3 validate_tcp_packet.py tcp_data/tcp_addrs_0.txt tcp_data/tcp_data_0.dat
"""

import logging
import argparse

from pathlib import Path

TCP_PROTOCOL_BYTE = b'\x06'
TCP_HEADER_CHECKSUM_SLICE = slice(16,18)
WORD_BIT_MASK = 0xffff
WORD_BIT_LENGTH = 16
WORD_BYTE_LENGTH = 2

logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger('validate_tcp')

def parse_address_file(fp: Path) -> tuple[bytes, bytes]:
    source_ip, dest_ip = fp.read_text().split()
    logger.info(f"str: {source_ip=} -> {dest_ip=}")

    source_ip, dest_ip = parse_ipv4_address(source_ip), parse_ipv4_address(dest_ip)
    logger.debug(f"bytes: {source_ip=} -> {dest_ip=}")

    return source_ip, dest_ip

def parse_ipv4_address(ip: str) -> bytes:
    """ Map IPv4 address from "dots-and-numbers" string format to sequence of 4 bytes.
    WARNING: This function does not validate the format of the input string is correct.
    >>> parse_ipv4_address('198.51.100.77')
    b'\xc63dM'
    """

    # THOUGHT: How would you validate the syntax of an IPv4 address? Regex? Grammar?
    # What about the semantics (i.e. 'ilegal' addresses)
    # Do you encode valid vs invalid addresses at the type level?
    return b''.join(int.to_bytes(int(octet)) for octet in ip.split('.'))

def parse_data_file(fp: Path) -> tuple[bytes, int]:
    tcp_packet: bytes = fp.read_bytes()
    tcp_checksum: int = int.from_bytes(tcp_packet[TCP_HEADER_CHECKSUM_SLICE]) #WARNING: do we need to parse?
    logging.debug(f"{tcp_packet=}")
    logging.debug(f"{tcp_checksum=}")
    return tcp_packet, tcp_checksum

def compute_tcp_packet_checksum(
        source_ip: bytes,
        dest_ip: bytes,
        tcp_packet: bytes,
    ) -> int: #WARNING: int or byte?

    """
    SPEC: The checksum field is the 16 bit one's complement of the one's complement sum
    of all 16 bit words in the header and text.
    If a segment contains an odd number of header and text octets to be checksummed,
    the last octet is padded on the right with zeros to form a 16 bit word for checksum purposes.
    """

    tcp_packet_length: int = len(tcp_packet)
    logger.debug(f"{tcp_packet_length=}")

    tcp_zero_checksum_header: bytes = (
        tcp_packet[:TCP_HEADER_CHECKSUM_SLICE.start]
        + b'\x00\x00' # Zero out the checksum byte-pair
        + tcp_packet[TCP_HEADER_CHECKSUM_SLICE.stop:]
    ) #REFACTOR: instead of splice, let's mutate!

    # REFACTOR: use l-just? 
    if tcp_packet_length % 2 == 1:
        tcp_zero_checksum_header += b'\x00'
    logger.debug(f"{tcp_zero_checksum_header=}")
    
    pseudo_header: bytes = (
        source_ip
        + dest_ip
        + b'\x00'
        + TCP_PROTOCOL_BYTE
        + int.to_bytes(tcp_packet_length, length=2)
    )
    logger.debug(f"{pseudo_header=}")
    pseudo_tcp_data: bytes = pseudo_header + tcp_zero_checksum_header
    
    # Iterate over the bytestring in two-byte pairs (words) and forcing 16-bit arithmetic (not python integer arithmetic)
    # QUESTION: how would I naturally do 16 bit-arithmetic here instead of python variable integer arithmetic
    # REFACTOR: How would I refactor to use a window function to iterate over bytes in two byte pairs
    total = offset = 0
    while offset < len(pseudo_tcp_data):
        word = int.from_bytes(pseudo_tcp_data[offset: offset + WORD_BYTE_LENGTH])
        total += word
        total = (total & WORD_BIT_MASK) + (total >> WORD_BIT_LENGTH)

        offset += WORD_BYTE_LENGTH
    return (~total) & WORD_BIT_MASK

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate TCP packet data')
    parser.add_argument('address_file', type=Path, help='Path to address file') #WARNING can we parse to arbitrary python objects? is that a security risk?!!
    parser.add_argument('data_file', type=Path, help='Path to data file')
    args = parser.parse_args()

    logger.info(f"{args=}")

    source_ip, dest_ip = parse_address_file(args.address_file)
    tcp_packet, tcp_checksum = parse_data_file(args.data_file)

    test_checksum = compute_tcp_packet_checksum(source_ip, dest_ip, tcp_packet)

    logger.info(f"{test_checksum=}")
    logger.info(f"{tcp_checksum=}")

    print("PASS" if test_checksum == tcp_checksum else "FAIL")
