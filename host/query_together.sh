[ "$ENCLAVE_HOST" == "" ] && ENCLAVE_HOST=localhost
[ -e .env ] && . .env

curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "provider": "together",
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "prompt": "Tell me a joke",
        "stream": false
    }' \
    http://${ENCLAVE_HOST}:5001/enclave/query
