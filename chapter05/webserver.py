"""
>>> uv run webserver.py 20123
"""

import socket
import logging
import argparse

from pathlib import Path

DEFAULT_SERVER_PORT = 28333
HTTP_ENCODING = 'ISO-8859-1'
REQUEST_BUFFER_SIZE = 4096
END_OF_REQUEST = '\r\n\r\n'.encode(HTTP_ENCODING)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('webclient')

parser = argparse.ArgumentParser(
    description='Creates a simple web server in python using the socket library.'
)
parser.add_argument('port', nargs='?', default=DEFAULT_SERVER_PORT, type=int)
args = parser.parse_args()
logger.info(args)

s: socket = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(('', args.port)) # Binds to "any local address"
s.listen()
logger.info(f'Created new server socket listening at {args.port=}')

# Accept new connections
try:
    while True:
        new_conn = s.accept()
        new_socket = new_conn[0]
        client_ip, client_port = new_conn[1]
        logger.debug(f"New connection received from {client_ip=} on {client_port=}")

        # Receive request from client
        request_buffer = b''
        try:
            while True:
                d: bytes = new_socket.recv(REQUEST_BUFFER_SIZE)
                request_buffer += d
                if END_OF_REQUEST in d:
                    logger.debug("END_OF_REQUEST!")
                    print(request_buffer.decode(HTTP_ENCODING))
                    break

            # Send response to client
            example_http_response: bytes = (
                Path('test/http_response')
                .read_text(newline='\r\n')
                .encode(HTTP_ENCODING)
            )
            new_socket.sendall(example_http_response)
        except socket.timeout:
            logger.warning('Timeout! No data received!')
        finally:
            new_socket.close()
            logger.debug(f'Closed socket {s=} {id(s)=}')
except (KeyboardInterrupt, EOFError):
    logger.info('Server shutdown requested')
finally:
    s.close()
