"""
>>> uv run webclient.py example.com 80
"""

import socket
import logging
import argparse

from pathlib import Path

HTTP_ENCODING = 'ISO-8859-1'
BUFF_SIZE = 4096

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('webclient')

parser = argparse.ArgumentParser(
    description='Creates a simple web client in python using the socket library.'
)
parser.add_argument('host')
parser.add_argument('port', nargs='?', default=80, type=int)
args = parser.parse_args()
logger.info(args)

s: socket = socket.socket()
s.connect((args.host, args.port))
logger.info(f'Created new socket for {args.host=} at {args.port=}')

example_http_get_request: bytes = (
    Path('http_get_request')
    .read_text(newline='\r\n')
    .format(args.host)
    .encode(HTTP_ENCODING)
)
s.sendall(example_http_get_request)
logger.info(f'Sent {example_http_get_request=} to {args.host=}')

response_buffer = b''
try:
    d: bytes = s.recv(BUFF_SIZE)
    while len(d):
        logger.debug(f'Received (partial) response {d=}')
        response_buffer += d
        d = s.recv(BUFF_SIZE)
    print(response_buffer.decode(HTTP_ENCODING))
except socket.timeout:
    logger.warning('Timeout! No data received!')
finally:
    s.close()
    logger.debug(f'Closed socket {s=} {id(s)=}')
