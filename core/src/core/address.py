from eth_account import Account
from web3.auto import w3


def address_for_private_key(private_key: str) -> str:
    # pylint: disable=no-value-for-parameter
    account = Account.from_key(private_key)
    address = account.address
    assert isinstance(address, str)
    return address


def address_to_bytes(address: str) -> bytes:
    if address.startswith("0x"):
        address = address[2:]
    assert len(address) == 40
    address_bytes = bytes.fromhex(address)
    assert len(address_bytes) == 20
    return address_bytes


def address_from_bytes(address_bytes: bytes) -> str:
    assert len(address_bytes) == 20
    address = "0x" + address_bytes.hex()
    return w3.to_checksum_address(address)
