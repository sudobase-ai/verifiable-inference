from typing import Any
import base64
import json
from click import command, option

from core.address import address_from_bytes

from .attestation_verifier import verify_attestation_doc, get_public_key

def read_root_pem(root_pem_file: str) -> Any:
    with open(root_pem_file, "r", encoding="utf-8") as file:
        return file.read()


@command()
@option("--measurements", required=True, help="Path to the measurements file")
@option("--attestation", required=True, help="Path to the attestation file")
@option("--root-certificate", "-r", default="sample_data/root.pem", help="Root public key")
def main(
        measurements: str,
        attestation: str,
        root_certificate: str) -> None:
    with open(measurements, "r", encoding="utf-8") as f:
        measurements_data = json.load(f)

    with open(attestation, "r", encoding="utf-8") as f:
        attestation_data = json.load(f)

    pcrs = [
        measurements_data["Measurements"]["PCR0"]
    ]
    attestation_doc = attestation_data["attestation_doc"]

    root_cert_pem = read_root_pem(root_certificate)
    attestation_doc = base64.b64decode(attestation_doc)

    verify_attestation_doc(
        attestation_doc=attestation_doc, pcrs=pcrs, root_cert_pem=root_cert_pem
    )

    # The "public_key" field is the Ethereum address used for signing
    public_key_bytes = get_public_key(attestation_doc)
    address = address_from_bytes(public_key_bytes)
    print(address)
