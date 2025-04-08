## Setup (AWS parent instance)

Launch and log into a Nitro-enabled AWS instance (e.g. `m5.xlarge`). Remember to enable Nitro Enclave in Advanced Details.

```
$ sudo yum install -y git python3.12 python3-pip make
$ sudo dnf install aws-nitro-enclaves-cli aws-nitro-enclaves-cli-devel -y
$ sudo usermod -aG ne ec2-user
$ sudo usermod -aG docker ec2-user
$ sudo systemctl enable --now nitro-enclaves-allocator.service
$ sudo systemctl enable --now docker.service
$ sudo setcap 'cap_net_bind_service=+ep' $(realpath `which python3`)
```
Log out and log back in to reflect group changes.

Edit `/etc/nitro_enclaves/allocator.yaml`:
```
...
memory_mib: 6508
...
```

Restart service:
```
sudo systemctl restart nitro-enclaves-allocator.service
```

## Setup env

```
$ python3 -m venv env
$ . env/bin/activate
(env) $ make dev-setup
$ nano .env
```

Fill in the API keys to be used for querying:
```
OPENAI_API_KEY = openai_api_key_here
ANTHROPIC_API_KEY = anthropic_api_key_here
TOGETHER_API_KEY = together_api_key_here
```

## Run the server

### in the enclave

On a nitro-enabled parent host.

Build the image:
```
$ make enclave-image
```

Record and publish the measurement output:
```
{
  "Measurements": {
    "HashAlgorithm": "Sha384 { ... }",
    "PCR0": "4fca2a321f2f672ed8ad44a02f8c174aec4f7ca6b314741574b05d2028c639f18547d6c49ed7e0d2403d1314a5024cd0",
    "PCR1": "4b4d5b3661b3efc12920900c80e126e4ce783c522de6c02a2a5bf7af3a2b9327b86776f188e4be1c1c404a129dbda493",
    "PCR2": "9796114a457d77c7ad42a12c1bd1ba264e7cb8ddd91a870d887f06dc0f721c08c23a5fd8ea2b90135c160048e1ce667f"
  }
}
```

Start the enclave:
```
$ make start
```

> To run in debug mode:
> ```
> $ make start-debug
> ```
>
> The enclave console can then be viewed:
> ```
> $ nitro-cli console --enclave-name z2
> ```

Run port forwarder (host to enclave) in another terminal:
```
$ forward
```

### local dev server

```
make start-dev
```

### using docker (for testing more network functionality during development)

```
make enclave-docker-image
make start-docker
```

Run the https forwarder:
```
forward --dev
```

## Run a local LLM server

Start the server
```
$ docker run --rm -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

Download a model:
```
$ curl -X POST -H "Content-Type: application/json" -d '{"model": "moondream"}' http://localhost:11434/api/pull
```

> ollama console:
> ```
> docker exec -it ollama ollama run llama3
> ```

## Make a query

Get the (attested) signer address
```
$ curl http://localhost:5001/enclave/address > address_attestation.json
```

(In the ../verify directory) Verify the attestation against known measurements
```
$ python verify.py --attestation address_attestation.json --measurements [measurements.json] > address
```

Query the enclave (via the forwarder)
```
$ . query.sh > query.json
```

Verify the query signature
```
$ python verify_query.py --query query.json --address `cat address`
```

## Stop the enclave

```
$ make stop
```
