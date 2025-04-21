"""
>>> uv run timeclient.py
NIST time    : 3954235334
System time  : 3954235334
"""

import time
import socket
import logging

TIME_SERVER = 'time.nist.gov'
TIME_PROTOCOL_PORT = 37
RESPONSE_BUFFER_SIZE = 4

logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger('timeclient')


def system_seconds_since_1900() -> int:
    """
    The time server returns the number of seconds since 1900, but Unix
    systems return the number of seconds since 1970. This function
    computes the number of seconds since 1900 on the system.
    """
    # Number of seconds between 1900-01-01 and 1970-01-01
    EPOCHS_DELTA = 2_208_988_800
    seconds_since_unix_epoch = int(time.time())
    seconds_since_1900_epoch = seconds_since_unix_epoch + EPOCHS_DELTA
    return seconds_since_1900_epoch


s: socket.socket = socket.socket()
s.connect((TIME_SERVER, TIME_PROTOCOL_PORT))
logger.info(f'Created new socket for {TIME_SERVER=} at {TIME_PROTOCOL_PORT=}')

response_buffer: bytearray = bytearray()
try:
    chunk: bytes = s.recv(RESPONSE_BUFFER_SIZE)
    while len(chunk):
        response_buffer += chunk
        chunk = s.recv(RESPONSE_BUFFER_SIZE)
    logger.debug(f'{response_buffer=}')

    nist_time: int = int.from_bytes(response_buffer, byteorder='big')
    system_time: int = system_seconds_since_1900()
    print(f'NIST time    : {nist_time}')
    print(f'System time  : {system_time}')
except Exception as e:
    logger.exception(e)
finally:
    s.close()
    logger.debug(f'Closed socket {s=}')
