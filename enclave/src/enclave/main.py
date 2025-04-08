import socket

import uvicorn
from click import command, option

from core.defaults import DEFAULT_APP_SERVER_PORT

APP = f"{__package__}.app:app"

@command()
@option("--vsock", "-v", is_flag=True, help="Bind to vsock")
@option("--port", "-p", type=int, help="Local port to bind to", default=DEFAULT_APP_SERVER_PORT)
def main(vsock: bool, port: int) -> None:
    # Bind to vsock or regular socket
    if vsock:
        print("VSOCK mode")
        # pylint: disable=no-member
        s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)  # type: ignore
        s.bind((socket.VMADDR_CID_ANY, port))  # type: ignore
        s.listen()
        fd = s.fileno()
        uvicorn.run(APP, fd=fd)
    else:
        print("IP mode")
        uvicorn.run(APP, host="0.0.0.0", port=port)
