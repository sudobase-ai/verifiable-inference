from click import command, option

from core.forward import forward_ip_to_ip
from core.defaults import DEFAULT_REMOTE_HOST


@command()
@option("--listen-host", "-l", default = "0.0.0.0")
@option("--port", "-p", type = int, default = 11434)
@option("--dest-addr", "-v", default = DEFAULT_REMOTE_HOST)
@option("--dest-port", "-v", type = int, default = 11434)
def main(
        listen_host: str,
        port: int,
        dest_addr: str,
        dest_port: int,
) -> None:
    """
    Bind to 0.0.0.0:<port> and forward to ip <dest_addr>:<dest_port>
    """
    forward_ip_to_ip(listen_host, port, dest_addr, dest_port)
