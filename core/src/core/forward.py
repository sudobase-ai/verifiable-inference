from typing import Optional
import socket
import threading

# Match the values in Dockerfile-enclave
KNOWN_HOSTS = [
    b'api.openai.com',
    b'api.anthropic.com',
    b'api.together.xyz',
]

BUFFER_SIZE = 4096


def determine_https_destination(s: socket.socket) -> tuple[Optional[str], bytes]:
    leading_bytes = s.recv(BUFFER_SIZE)
    for dest in KNOWN_HOSTS:
        if dest in leading_bytes:
            return (dest.decode('ascii'), leading_bytes)

    return (None, leading_bytes)


def socket_forward(
        src: socket.socket,
        dst: socket.socket) -> None:
    try:
        while True:
            data = src.recv(BUFFER_SIZE)
            if not data:
                break
            dst.sendall(data)
    except Exception: # pylint: disable = broad-exception-caught
        # print(f"  Data forwarding error ({src} -> {dst}): {e}")
        pass


def connect_sockets(
        s_a: socket.socket,
        s_b: socket.socket
) -> None:

    try:
        # Start two threads to forward data in both directions
        t_a = threading.Thread(target=socket_forward, args=(s_a, s_b))
        t_b = threading.Thread(target=socket_forward, args=(s_b, s_a))
        t_a.start()
        t_b.start()
        t_a.join()
        t_b.join()
    finally:
        s_a.close()
        s_b.close()


def forward_socket_to_ip(
        s: socket.socket,
        remote_host: str,
        remote_port: int,
        leading_bytes: Optional[bytes] = None) -> None:
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r.connect((remote_host, remote_port))
    if leading_bytes:
        r.sendall(leading_bytes)
    connect_sockets(s, r)


def forward_connections_to_ip(
        server_socket: socket.socket,
        remote_host: str,
        remote_port: int) -> None:

    def handle_connection(s: socket.socket) -> None:
        peername = s.getpeername()
        print(f" connection from {peername} -> ({remote_host}:{remote_port})")
        try:
            forward_socket_to_ip(s, remote_host, remote_port)
        except Exception as e: # pylint: disable = broad-exception-caught
            print(f" error handling {peername}: {e}")
            s.close()

        finally:
            print(f" closed {peername}")

    while True:
        # Accept a new client connection
        client_socket, _ = server_socket.accept()
        # Handle the client connection in a new thread
        threading.Thread(
            target=handle_connection,
            args=[client_socket],
        ).start()


def forward_connections_to_vsock(
        server_socket: socket.socket,
        vsock_addr: Optional[int],
        vsock_port: int,
) -> None:

    def handle_connection(s: socket.socket) -> None:
        peername = s.getpeername()
        print(f" connection from {peername} -> ({vsock_addr}:{vsock_port})")
        try:
            #pylint: disable=no-member
            vsock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)  # type: ignore

            vsock.connect((vsock_addr, vsock_port))
            connect_sockets(s, vsock)

        except Exception as e: # pylint: disable=broad-exception-caught
            print(f" error handling {peername}: {e}")
            s.close()

        finally:
            print(f" closed {peername}")

    while True:
        # Accept a new client connection
        client_socket, _ = server_socket.accept()
        # Handle the client connection in a new thread
        threading.Thread(
            target=handle_connection,
            args=[client_socket],
        ).start()


def forward_https_connections_to_ip(
        server_socket: socket.socket,
        remote_port: int,
) -> None:

    def handle_connection(s: socket.socket) -> None:
        try:
            (dest_host, leading_bytes) = determine_https_destination(s)
            if dest_host:
                print(f" (https) connection from {s.getpeername()} -> {dest_host}:{remote_port}")
                forward_socket_to_ip(s, dest_host, remote_port, leading_bytes)
            else:
                print(f"!! no known host in leading bytes: {leading_bytes!r}")

        finally:
            s.close()

    while True:
        client_socket, _ = server_socket.accept()
        peername = client_socket.getpeername()
        print(f" connection from {peername}")
        threading.Thread(
            target=handle_connection,
            args=[client_socket],
        ).start()


def forward_ip_to_vsock(
        local_port: int,
        vsock_port: int,
        vsock_addr: Optional[int],
) -> None:
    # cid = vsock_addr or get_enclave_cid()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", local_port))
    server_socket.listen(5)

    print(
        f"Forward 0.0.0.0:{local_port} -> vsock {vsock_addr}:{vsock_port}"
    )

    forward_connections_to_vsock(server_socket, vsock_addr, vsock_port)


def forward_ip_to_ip(
        local_host: Optional[str],
        local_port: int,
        remote_host: str,
        remote_port: int,
) -> None:
    # cid = vsock_addr or get_enclave_cid()

    local_host = local_host or "0.0.0.0"

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((local_host, local_port))
    server_socket.listen(5)

    print(
        f"Forward 0.0.0.0:{local_port} -> {remote_host}:{remote_port}"
    )

    forward_connections_to_ip(server_socket, remote_host, remote_port)


def forward_vsock_to_ip(
        vsock_port: int,
        remote_host: str,
        remote_port: int,
) -> None:

    # pylint: disable=no-member
    server_socket = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM) # type: ignore
    # pylint: disable=no-member
    server_socket.bind((socket.VMADDR_CID_ANY, vsock_port)) # type: ignore
    server_socket.listen(5)

    print(f"Forward (vsock):{vsock_port} -> {remote_host}:{remote_port}")

    forward_connections_to_ip(server_socket, remote_host, remote_port)


def forward_vsock_https(
        listen_port: int,
        dest_port: int,
) -> None:
    """
    Listen on vsock <listen_port>.  Attempt to determine the intended
    destination of incoming https connections from the list of KNOWN_HOSTS, and
    forward to the appropriate server.
    """

    # pylint: disable=no-member
    server_socket = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)  # type: ignore
    server_socket.bind((socket.VMADDR_CID_ANY, listen_port))  # type: ignore
    print(f"Forward (https) (vsock):{listen_port} -> <host>:{dest_port}")

    server_socket.listen(5)

    forward_https_connections_to_ip(server_socket, dest_port)


def forward_ip_https(
        listen_port: int,
        dest_port: int,
) -> None:
    """
    Listen on <listen_port>.  Attempt to determine the intended destination of
    incoming https connections from the list of KNOWN_HOSTS, and forward to the
    appropriate server.
    """

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", listen_port))
    print(f"Forward 0.0.0.0:{listen_port} -> <host>:{dest_port}")

    server_socket.listen(5)

    forward_https_connections_to_ip(server_socket, dest_port)
