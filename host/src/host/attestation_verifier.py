from typing import Any, Optional
import base64

from OpenSSL import crypto # type: ignore
import cbor2 # type: ignore
import cose # type: ignore
from cose import EC2, CoseAlgorithms, CoseEllipticCurves
from Crypto.Util.number import long_to_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_der_x509_certificate


# pylint: disable=too-many-locals
def verify_attestation_doc(
        attestation_doc: str,
        pcrs: Optional[list[Any]]=None,
        root_cert_pem: Optional[Any]=None) -> None:
    """
    Verify the attestation document
    If invalid, raise an exception
    """
    pcrs = pcrs or []

    # Decode CBOR attestation document
    data = cbor2.loads(attestation_doc)

    # Load and decode document payload
    doc = data[2]
    doc_obj = cbor2.loads(doc)

    # Get PCRs from attestation document
    document_pcrs_arr = doc_obj["pcrs"]

    # Part 1: Validating PCRs
    for index, pcr in enumerate(pcrs):
        # Attestation document doesn't have specified PCR, raise exception
        if index not in document_pcrs_arr or document_pcrs_arr[index] is None:
            # pylint: disable=broad-exception-raised
            raise Exception(f"Wrong PCR{index}")

        # Get PCR hexcode
        doc_pcr = document_pcrs_arr[index].hex()

        # Check if PCR match
        if pcr != doc_pcr:
            # pylint: disable=broad-exception-raised
            raise Exception(f"Wrong PCR{index}\nEnclaves PCR{index}: {doc_pcr}")

    # Part 2: Validating signature

    # Get signing certificate from attestation document
    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, doc_obj["certificate"])

    # Get the key parameters from the cert public key
    cert_public_numbers = cert.get_pubkey().to_cryptography_key().public_numbers()
    x = cert_public_numbers.x
    y = cert_public_numbers.y
    _curve = cert_public_numbers.curve

    x = long_to_bytes(x)
    y = long_to_bytes(y)

    # Create the EC2 key from public key parameters
    key = EC2(alg=CoseAlgorithms.ES384, x=x, y=y, crv=CoseEllipticCurves.P_384)

    # Get the protected header from attestation document
    phdr = cbor2.loads(data[0])

    # Construct the Sign1 message
    msg = cose.Sign1Message(phdr=phdr, uhdr=data[1], payload=doc)
    msg.signature = data[3]

    # Verify the signature using the EC2 key
    if not msg.verify_signature(key):
        # pylint: disable=broad-exception-raised
        raise Exception("Wrong signature")

    # Part 3: Validating signing certificate PKI
    if root_cert_pem is not None:
        # Create an X509Store object for the CA bundles
        store = crypto.X509Store()

        # Create the CA cert object from PEM string, and store into X509Store
        _cert = crypto.load_certificate(crypto.FILETYPE_PEM, root_cert_pem)
        store.add_cert(_cert)

        # Get the CA bundle from attestation document and store into X509Store
        # Except the first certificate, which is the root certificate
        for _cert_binary in doc_obj["cabundle"][1:]:
            _cert = crypto.load_certificate(crypto.FILETYPE_ASN1, _cert_binary)
            store.add_cert(_cert)

        # Get the X509Store context
        store_ctx = crypto.X509StoreContext(store, cert)

        # Validate the certificate
        # If the cert is invalid, it will raise exception
        try:
            store_ctx.verify_certificate()
        except crypto.X509StoreContextError as exc:
            if str(exc) == "certificate has expired":
                cert = load_der_x509_certificate(
                    doc_obj["certificate"], default_backend()
                )
                # _print_cert_expired_msg(cert)
            else:
                raise exc


def _print_cert_expired_msg(cert: Any) -> None:
    valid_from_der = cert.not_valid_before_utc
    valid_until_der = cert.not_valid_after_utc
    print(f"\nCertificate was valid from: {valid_from_der} until {valid_until_der}")
    # pylint: disable=line-too-long
    print(
        "The AWS enclave attestation certification is valid only for 3 hours from issuing."
    )
    print(
        "For this reason, when verifying an attestation that is more than 3 hours old, you have to consider "
    )
    print("that the only reason for an invalid attestation is the certificate expiry.")
    print(
        "The attestation document's validity does not depend on whether the certificate is expired or not,"
    )
    print(
        " as long as the certificate was valid at the time of the attestation document creation."
    )


def encrypt(public_key: RSA.RsaKey, plaintext: str) -> str:
    """
    Encrypt message using public key
    """

    # Encrypt the plaintext with the public key and encode the cipher text in base64
    cipher = PKCS1_OAEP.new(public_key)
    ciphertext = cipher.encrypt(str.encode(plaintext))

    return base64.b64encode(ciphertext).decode()


def get_public_key(attestation_doc: bytes) -> bytes:
    data = cbor2.loads(attestation_doc)

    # Load and decode document payload
    doc = data[2]
    doc_obj = cbor2.loads(doc)

    # Get the public key from attestation document
    public_key_bytes = doc_obj["public_key"]
    assert isinstance(public_key_bytes, bytes)
    return public_key_bytes
