SHELL := /usr/bin/env bash

.PHONY: all html pdf diagrams validate clean

all:
	bash scripts/build.sh all

html:
	bash scripts/build.sh html

pdf:
	bash scripts/build.sh pdf

diagrams:
	bash scripts/build.sh diagrams

validate:
	bash scripts/build.sh validate

clean:
	rm -rf build .build-src
