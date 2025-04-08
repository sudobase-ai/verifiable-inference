import threading

from click import command, option
from core.forward import forward_ip_to_vsock, forward_vsock_to_ip, \
    forward_vsock_https, forward_ip_https
from core.defaults import DEFAULT_APP_SERVER_PORT, DEFAULT_REMOTE_HOST

from .utils import get_enclave_cid

OLLAMA_PORT = 11434

@command()
@option("--dev", "-p", is_flag = True, help="Perform only https forwarding")
@option("--server-port", "-p", type = int, default = DEFAULT_APP_SERVER_PORT)
@option(
    "--proxy-port", "-v",
    type = int,
    default = OLLAMA_PORT,
    help="vsock port to listen for connections from enclave")
@option("--proxy-dest-host", default = DEFAULT_REMOTE_HOST)
def main(
        server_port: int,
        proxy_port: int,
        proxy_dest_host: str,
        dev: bool,
) -> None:
    """
    Perform all forwarding for the enclave.
      0:5001 -> enclave(vsock):5001       (incoming connections)
      0(vsock):443 -> <external>:443      (https connections from enclave)
      0(vsock):11434<proxy-vsock-port> -> localhost:11434<proxy-dest-port>
                                          (local ollama connection from enclave)

    If the --dev flag is given, only the https forwarding is
    performed:
      0:443 -> <external>:443      (https connections from enclave)
    (for use with the docker version).
    """

    if dev:

        # :443 -> external hosts (https)
        forward_ip_https(443, 443)

    else:

        enclave_cid = get_enclave_cid()

        # Local server port to vsock with the same port in the enclave
        local_to_enclave = threading.Thread(
            target=forward_ip_to_vsock,
            args=[server_port, server_port, enclave_cid],
        )

        # vsock:443 -> external hosts (https)
        enclave_to_external = threading.Thread(
            target = forward_vsock_https,
            args=[443, 443],
        )

        # vsock:11434 -> localhost:11434
        enclave_to_provider = threading.Thread(
            target=forward_vsock_to_ip,
            args=[proxy_port, proxy_dest_host, proxy_port]
        )

        local_to_enclave.start()
        enclave_to_external.start()
        enclave_to_provider.start()

        local_to_enclave.join()
        enclave_to_external.join()
        enclave_to_provider.join()
