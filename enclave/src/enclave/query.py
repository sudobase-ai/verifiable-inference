from typing import Any, TypedDict


class QueryData(TypedDict):
    request: Any
    response: Any


class SignedQueryData(TypedDict):
    query_data: QueryData
    signature: str
    recovered_address: str
