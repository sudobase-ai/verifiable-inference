import json

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from web3.auto import w3
from eth_account import Account
from eth_account.messages import encode_defunct
from pydantic import BaseModel
from openai import OpenAI
from core.address import address_to_bytes
from . import utils

class LlmRequest(BaseModel):
    model: str
    provider: str
    prompt: str
    api_key: Optional[str] = None

    suffix: Optional[str] = None
    images: Optional[List[str]] = None

    format: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    system: Optional[str] = None
    template: Optional[str] = None
    stream: Optional[bool] = None
    raw: Optional[bool] = None
    keep_alive: Optional[str] = None
    context: Optional[str] = None

enclave_router = APIRouter(prefix="/enclave")


@enclave_router.get("/address")
async def address(
        private_key: str = Depends(utils.get_enclave_private_key),
        nsm: utils.NSM = Depends(utils.get_nsm)
) -> Any:
    """
    Example usage:
    curl http://localhost:5001/enclave/address
    """
    # pylint: disable=no-value-for-parameter
    account = Account.from_key(private_key)
    address_str = account.address
    address_bytes = address_to_bytes(address_str)
    attestation_doc = nsm.get_attestation_doc(address_bytes)

    return {
        "address": address_str,
        "attestation_doc": attestation_doc,
    }


@enclave_router.post("/query")
async def query(
        request_body: LlmRequest,
        private_key: str = Depends(utils.get_enclave_private_key),
) -> Any:
    """
    Example usage:
    curl -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "provider": "ollama",
            "model": "moondream",
            "prompt": "Explain the significance of prime numbers in mathematics",
            "stream": false
            }' \
        http://localhost:5001/enclave/query
    """

    api_key = utils.get_api_key(request_body.provider)
    base_url = utils.get_base_url(request_body.provider)
    client = OpenAI(api_key=api_key, base_url=base_url)

    # Send the query to LLM provider
    try:
        resp = client.chat.completions.create(
            model=request_body.model,
            messages=[{"role": "user", "content": request_body.prompt}]
        )
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"error contacting provider: {e}") from e

    # Get LLM provider's response
    try:
        llm_response = json.loads(resp.json())
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code = 500,
            detail = f"invalid JSON from LLM: {resp.to_json()}: {e}"
        ) from e

    # Prepare data to be signed by the enclave
    query_data = {
        "request": request_body.prompt,
        "response": llm_response,
    }
    query_data_serialized = json.dumps(query_data, sort_keys=True, ensure_ascii=False)

    # Uses EIP-191 scheme to produce a signable message.
    # This can be more constrained using EIP-712 (structured data signing).
    # We can use EIP-712 once we know the response format.
    message = encode_defunct(text=query_data_serialized)
    signed_message = w3.eth.account.sign_message(message, private_key)

    # For debugging, make sure we can recover the correct address.
    recovered_address = w3.eth.account.recover_message(
        message,
        signature=signed_message.signature
    )

    return {
        "query_data": query_data,
        "signature": signed_message.signature.hex(),
        "recovered_address": recovered_address
    }


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(enclave_router)
