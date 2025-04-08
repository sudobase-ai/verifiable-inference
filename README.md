# Z2: Verifiable Inference

## Setup the project

```
$ python -m venv env
$ . env/bin/activate
$ make dev-setup
```

## Verify the signer address

Get the (attested) signer address
```
$ curl https://z2-psi-13-217-71-20.dev.nebra.one/enclave/address > address_attestation.json
```

Verify and record the enclave signing address:
```
$ verify_attestation --measurements demo/measurements.json --attestation address_attestation.json > address
```

## Query

Query the enclave and save the signed result.  (Edit the query.sh script)
```
$ ./host/query.sh > query.json
```

> Note: this can take >10s

Verify the query
```
$ verify_query --query query.json --address `cat address`
```

# Enclave image creation and verification

See [enclave/README.md]
