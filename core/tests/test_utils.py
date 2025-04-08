from unittest import TestCase

from core import address


class TestUtils(TestCase):

    def test_addresses(self) -> None:
        pk = "0x0000000000000000000000000000000000000000000000000000000000000001"
        addr = address.address_for_private_key(pk)
        addr_bytes = address.address_to_bytes(addr)
        addr_2 = address.address_from_bytes(addr_bytes)

        self.assertEqual(addr, addr_2)
