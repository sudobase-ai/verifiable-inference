import subprocess
import json


def get_enclave_cid() -> int:
    """
    Determine CID of Current Enclave
    """
    with subprocess.Popen(
        ["/bin/nitro-cli", "describe-enclaves"], stdout=subprocess.PIPE
    ) as proc:
        output = json.loads(proc.communicate()[0].decode())
        enclave_cid = output[0]["EnclaveCID"]
        assert isinstance(enclave_cid, int)
        return enclave_cid
