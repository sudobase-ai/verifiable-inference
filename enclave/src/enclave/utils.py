from typing import Optional
import os
import sys
import base64

from dotenv import load_dotenv
load_dotenv()

try:
    # pylint: disable=consider-using-from-import
    import enclave.libnsm as libnsm  # type: ignore
except Exception as e:
    print(f"!! libnsm not available: {e}")
    # pylint: disable=invalid-name
    libnsm = None

enclave_private_key: Optional[str] = None

def get_enclave_private_key() -> str:
    global enclave_private_key
    if enclave_private_key is None:
        # pylint: disable=redefined-outer-name
        nsm = get_nsm()
        private_key_bytes = nsm.get_random()
        assert len(private_key_bytes) == 32
        enclave_private_key = "0x" + private_key_bytes.hex()
    return enclave_private_key


def get_env_var_or_exit(var: str) -> str:
    try:
        return os.environ[var]
    except: # pylint: disable=bare-except
        print(f"{var} env var not set.  Did you create a .env file?")
        sys.exit(1)



API_KEYS = {
    "openai": get_env_var_or_exit("OPENAI_API_KEY"),
    "anthropic": get_env_var_or_exit("ANTHROPIC_API_KEY"),
    "together": get_env_var_or_exit("TOGETHER_API_KEY"),
    "ollama": "ollama"
}

def get_api_key(provider: str) -> str:
    provider = provider.lower()
    if provider not in API_KEYS:
        raise ValueError(f"No API key for provider: {provider}")
    return API_KEYS[provider]


def get_base_url(provider: str) -> str:
    """
    Takes a provider name and returns the corresponding base URL.
    """
    provider_urls = {
        "ollama": "http://localhost:11434/v1",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "together": "https://api.together.xyz/v1"
    }

    if provider.lower() not in provider_urls:
        raise ValueError(f"Unknown provider: {provider}")
    return provider_urls[provider.lower()]


class NSM:

    def __init__(self) -> None:
        if libnsm is not None:
            # pylint: disable=c-extension-no-member
            self._nsm_fd = libnsm.nsm_lib_init()
        else:
            self._nsm_fd = None

    def get_attestation_doc(self, public_key: bytes) -> str:
        """
        Returns base64 encoding of the attestation
        """
        if self._nsm_fd is not None:
            # pylint: disable=c-extension-no-member
            att_doc = libnsm.nsm_get_attestation_doc( # type: ignore
                self._nsm_fd,
                public_key,
                len(public_key))
            att_doc_b64 = base64.b64encode(att_doc)
            return att_doc_b64.decode('utf8')

        return "Dummy Attestation"

    def get_random(self) -> bytes:
        """
        Returns random values from NSM
        """
        if self._nsm_fd is not None:
            # pylint: disable=c-extension-no-member
            private_key = libnsm.nsm_get_random(self._nsm_fd, 32)  # type: ignore
            assert isinstance(private_key, bytes)

            # Filter out the 00...00 private key, which is returned when running
            # on linux outside of an enclave.
            if private_key != b'\00' * 32:
                return private_key

        return os.urandom(32)


nsm: Optional[NSM] = None

def get_nsm() -> NSM:
    global nsm
    if nsm is None:
        print("Creating NSM ...")
        nsm = NSM()
    return nsm
