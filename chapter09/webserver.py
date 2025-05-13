"""
>>> uv run webserver.py 20123
"""

import socket
import logging
import argparse

from pathlib import Path
from typing import TypeAlias

DEFAULT_SERVER_PORT = 28333
HTTP_ENCODING = 'ISO-8859-1'
REQUEST_BUFFER_SIZE = 4096
END_OF_REQUEST = '\r\n\r\n'.encode(HTTP_ENCODING)

EXTENSION_TO_MIME_TYPE: dict[str, str] = {
    '.txt': 'text/plain',
    '.html': 'text/html',
}

# TODO: Types and regex/schema. How does one define a grammar+parser for HTTP requests/responses
# and enforce it at the type level? What about a DSL for managing request/response flows?
HTTPRequest: TypeAlias = bytearray
HTTPPath: TypeAlias = str
HTTPHeader: TypeAlias = str
HTTPMethod: TypeAlias = str
HTTPProtocol: TypeAlias = str

# class HTTPMethod(Enum):
#     GET = auto()
#     POST = auto()
#     PUT = auto()
#     DELETE = auto()

# @dataclass
# class HTTPRequest:
#     method: HTTPMethod
#     path: str
#     protocol: str
#     headers: dict[str, str]
#     body: str = ''

# HTTPPath: TypeAlias = str
# HTTPHeader: TypeAlias = str
# HTTPProtocol: TypeAlias = str

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('webclient')

parser = argparse.ArgumentParser(
    description='Creates a simple web server in python using the socket library.'
)
parser.add_argument('port', nargs='?', default=DEFAULT_SERVER_PORT, type=int)
args = parser.parse_args()
logger.info(args)

s: socket.socket = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(('', args.port))  # Binds to "any local address"
s.listen()
logger.info(f'Created new server socket listening at {args.port=}')


def parse_request_header(
    header: bytearray,
) -> tuple[HTTPMethod, HTTPPath, HTTPProtocol]:
    # TODO: how to check well-formedness of header here?

    if header.find(END_OF_REQUEST) == -1:
        raise ValueError(
            'End of HTTP Request header not found'
        )  # TODO: what type of Exception to raise?

    # If we assume that the first line of the string always follows the following structure:
    method, path, protocol = (
        header.split(b'\r\n')[0].decode(HTTP_ENCODING).split()
    )

    # (crudely) 'sanitise' the path by extracting the basename
    path = Path(Path(path).name)

    return (method, path, protocol)


def receive_request(
    sock: socket.socket,
) -> HTTPRequest:  # TODO: how do I encode exceptions at typeleve?
    """
    - [ ] TODO: do I handle closing the socket here? (we can't, in case we need it later to send stuff back!)
    """

    # NOTE: we use a bytearray, which is mutable, instead of a byte type (b'') for performance
    request_buffer = bytearray()
    try:
        while True:
            chunk: bytes = sock.recv(REQUEST_BUFFER_SIZE)
            request_buffer += chunk  # vs .extend
            if END_OF_REQUEST in chunk:
                logger.debug('END_OF_REQUEST!')
                break
        return request_buffer
    except socket.timeout as e:
        logger.exception(f'Timeout! No data received: {e}')


def create_http_response(
    status_line: str, headers: dict[str, str], body: bytes
) -> bytes:
    header_lines = [status_line] + [f'{k}: {v}' for k, v in headers.items()]
    header_string = '\r\n'.join(header_lines) + '\r\n\r\n'
    return header_string.encode(HTTP_ENCODING) + body


def serve_file(sock: socket.socket, path: Path) -> None:
    try:
        # Validate file exists and has valid extension
        if not path.exists():
            raise FileNotFoundError(f'File {path} not found')
        if path.suffix not in EXTENSION_TO_MIME_TYPE:
            raise ValueError(f'Unsupported file type: {path.suffix}')

        # Read file data
        data = path.read_bytes()

        # Prepare response headers
        headers = {
            'Content-Type': f'{EXTENSION_TO_MIME_TYPE[path.suffix]}; charset=iso-8859-1',
            'Content-Length': str(len(data)),
        }

        # Create and send success response
        response = create_http_response('HTTP/1.1 200 OK', headers, data)
        sock.sendall(response)

    except (FileNotFoundError, ValueError) as e:
        # Handle 404 response
        headers = {
            'Content-Type': 'text/plain; charset=iso-8859-1',
            'Content-Length': '13',
            'Connection': 'close',
        }
        response = create_http_response(
            'HTTP/1.1 404 Not Found', headers, b'404 Not Found'
        )
        sock.sendall(response)
        logger.error(f'Error serving file: {e}')


# Accept new connections
try:
    while True:
        new_conn = s.accept()
        new_socket = new_conn[0]
        client_ip, client_port = new_conn[1]
        logger.debug(
            f'New connection received from {client_ip=} on {client_port=}'
        )
        try:
            new_request = receive_request(new_socket)
            method, path, protocol = parse_request_header(new_request)
            serve_file(new_socket, path)
            logger.debug(f'{method=} {path=} {protocol=}')
        except Exception as e:
            logger.exception(e)
        finally:
            new_socket.close()
            logger.debug(f'Closed socket {new_socket=} {id(new_socket)=}')
except (KeyboardInterrupt, EOFError):
    logger.info('Server shutdown requested')
finally:
    s.close()
    logger.debug(f'Closed socket {s=} {id(s)=}')
