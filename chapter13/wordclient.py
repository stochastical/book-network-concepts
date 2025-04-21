"""
$ uv run wordclient.py localhost 4041

---
Concepts: pipes, packets, stream buffers, stacks, iterators, generators, encoding packet schemas at the type-level
"""

import sys
import socket
import logging

from typing import TypeAlias, Optional

# Word packet structure
WORD_BYTE_LENGTH = 2
WORD_ENCODING = 'UTF-8'

RESPONSE_BUFFER_SIZE = 10

packet_buffer: bytearray = bytearray()
WordPacket: TypeAlias = tuple[int, str]

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wordclient')

def usage():
    print("usage: wordclient.py server port", file=sys.stderr)

def get_next_word_packet(s: socket.socket) -> Optional[bytearray]:
    """
    A 'packet streamer' - returns whole packets from a stream buffer.

    The word packet consists of the encoded word length followed by the
    UTF-8-encoded word.

    Returns None if there are no more words, i.e. the server has hung
    up.
    """
    # NOTE: could we not pass packet_buffer into this function instead of using a global variable?
    global packet_buffer

    while True:
        # Check to see if we have a complete packet

        # 1. We have the word-length 'header'
        if len(packet_buffer) >= WORD_BYTE_LENGTH:
            word_length: int = int.from_bytes(packet_buffer[:WORD_BYTE_LENGTH], byteorder='big')
            packet_length = WORD_BYTE_LENGTH + word_length
            # 2. We have the word-length header and word payload
            if len(packet_buffer) >= packet_length:
                word_packet: bytes = packet_buffer[:packet_length]

                # Let's lstrip the packet from the buffer and return the packet
                packet_buffer = packet_buffer[packet_length:]
                return word_packet 
        
        # We don't have a complete packet, let's get some more bytes into the stream!
        chunk: bytes = s.recv(RESPONSE_BUFFER_SIZE)

        # Server has closed the connection - let's return
        if not chunk:
            return None
        
        # Let's add the new chunk to the stream stream
        packet_buffer += chunk


def parse_packet(word_packet: bytearray) -> str:
    """
    Parse the word packet (encoded as bytearray) into a single word string.

    word_packet: a word packet consisting of the encoded word length followed by the UTF-8 word.

    Returns the word decoded as a string.
    """

    # NOTE: We should check that the packet is whole
    # i.e., that the packet length conforms to the expected word length
    # it would be nice to be able to enforce this at the type level! It should be impossible to pass
    # a non-valid packet to the parse_packet function
    word_length: int = int.from_bytes(word_packet[:WORD_BYTE_LENGTH], byteorder='big')
    if len(word_packet) != WORD_BYTE_LENGTH + word_length:
        raise BufferError("Length of word packet is incorrect!")
    word: str = word_packet[WORD_BYTE_LENGTH:].decode(encoding=WORD_ENCODING)
    return word
    

# Do not modify:

def main(argv):
    try:
        host = argv[1]
        port = int(argv[2])
    except:
        usage()
        return 1

    s: socket.socket = socket.socket()
    s.connect((host, port))
    logger.info(f"Connected socket {s=} to {host=} on  {port=}")

    print("Getting words:")

    while True:
        word_packet = get_next_word_packet(s)

        if word_packet is None:
            logger.warning("No more word packets!")
            break

        word: str = parse_packet(word_packet)
        print(f"\t{word}")

    s.close()
    logger.info(f"Closed socket {s=}")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
