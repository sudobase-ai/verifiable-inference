[ "$ENCLAVE_HOST" == "" ] && ENCLAVE_HOST=localhost
[ -e .env ] && . .env

curl -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "provider": "ollama",
            "model": "moondream",
            "prompt": "Tell me a joke",
            "stream": false
            }' \
        http://${ENCLAVE_HOST}:5001/enclave/query
