.PHONY: lint test check setup dev-setup default

SHELL := $(shell which bash)

PACKAGES := core enclave host

# Ensure virtual env is active
ifeq ($(origin VIRTUAL_ENV),undefined)
  $(error Not in virtual env))
endif

lint:
	set -e ; for p in $(PACKAGES) ; \
	  do pushd $$p ; \
	  mypy -p $$p ; \
	  pylint --rcfile ../.pylintrc src ; \
	  popd ; \
	done

test:
	@echo "=================================================="
	@echo "      TODO: enable tests for other packages"
	@echo "=================================================="
	set -e ; for p in core ; \
	  do pushd $$p ; \
	  python -m unittest ; \
	  popd ; \
	done

check: lint test

dev-setup:
	pip install --upgrade pip
	pip install -e core
	pip install -e core[dev]
	pip install -e enclave
	pip install -e host

# Create the enclave docker image
enclave-docker-image:
	docker build -f Dockerfile-enclave -t z2 .

# Launch the enclave server in a docker container
start-docker:
	docker run -it -p 5001:5001 --rm z2:latest

start-docker-bg:
	docker run -d --cidfile container.cid -p 5001:5001 --rm z2:latest
	echo CID written to container.cid

# Launch the enclave server on the host
start-dev:
	cd enclave ; ./run.sh

# Create the enclave image
enclave-image: enclave-docker-image
	nitro-cli build-enclave --docker-uri z2:latest --output-file z2.eif

# Run the enclave
start:
	nitro-cli run-enclave --cpu-count 2 --memory 4016 --enclave-cid 16 --eif-path z2.eif

# Run the enclave in debug mode
start-debug:
	nitro-cli run-enclave --cpu-count 2 --memory 4016 --enclave-cid 16 --eif-path z2.eif --debug-mode

# Stop the enclave
stop:
	nitro-cli terminate-enclave --enclave-name z2
