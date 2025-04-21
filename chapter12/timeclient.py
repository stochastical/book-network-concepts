"""
>>> uv run timeclient.py
NIST time    : 3954235334
System time  : 3954235334
"""

import time
import socket
import logging
from contextlib import closing

TIME_SERVER = 'time.nist.gov'
TIME_PROTOCOL_PORT = 37
RESPONSE_BUFFER_SIZE = 4
EPOCHS_DELTA = 2_208_988_800  # Seconds between 1900-01-01 and 1970-01-01

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('timeclient')

def system_seconds_since_1900() -> int:
    return int(time.time()) + EPOCHS_DELTA

def get_nist_time() -> int:
    with closing(socket.socket()) as s:
        s.connect((TIME_SERVER, TIME_PROTOCOL_PORT))
        logger.info(f'Connected to {TIME_SERVER}:{TIME_PROTOCOL_PORT}')
        
        response = b''.join(iter(lambda: s.recv(RESPONSE_BUFFER_SIZE), b''))
        logger.debug(f'Response: {response}')
        
        return int.from_bytes(response, byteorder='big')

try:
    nist_time = get_nist_time()
    system_time = system_seconds_since_1900()
    print(f'NIST time    : {nist_time}')
    print(f'System time  : {system_time}')
except Exception as e:
    logger.exception(e)
