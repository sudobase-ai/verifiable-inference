from typing import Optional
from click import command, option

from core.forward import forward_ip_to_vsock
from core.defaults import DEFAULT_APP_SERVER_PORT


@command()
@option("--port", "-p", type = int, default = DEFAULT_APP_SERVER_PORT)
@option("--vsock-addr", "-v", type = int)
@option("--vsock-port", "-v", type = int, default = DEFAULT_APP_SERVER_PORT)
def main(
        port: int,
        vsock_addr: Optional[int],
        vsock_port: int,
) -> None:
    """
    Bind to 0.0.0.0:<port> and forward to enclave vsock port <vsock_port>
    """
    forward_ip_to_vsock(port, vsock_port, vsock_addr)
