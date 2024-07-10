TARGET ?= virt-optee
IN_DIR := $(shell pwd)/in/$(TARGET)
OUT_DIR := $(shell pwd)/out/$(TARGET)

.PHONY: build

help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: compose.yaml
	IN=./in docker compose build

run-sh:
	IN=./in \
	OUT=./out \
	docker compose run --rm \
		syncemu /sh-entrypoint.sh

run-rehost:
	IN=$(IN_DIR) \
	OUT=$(OUT_DIR) \
	docker compose run --rm \
		syncemu /rehost-entrypoint.sh $(TARGET)

run-ca-in-the-loop:
	IN=$(IN_DIR) \
	OUT=$(OUT_DIR) \
	docker compose run --rm \
		syncemu /ca-in-the-loop-entrypoint.sh $(TARGET)

run-connect-device:
	docker run --rm -it --privileged -v /dev/bus/usb:/dev/bus/usb -v $(shell pwd)/src/:/src -v $(shell pwd)/out/$(TARGET):/out -v $(shell pwd)/in/$(TARGET):/in syncemu /bin/bash
