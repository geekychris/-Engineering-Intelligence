SHELL := /usr/bin/env bash

.PHONY: all html pdf diagrams validate source-validate clean clean-diagrams

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

source-validate:
	python3 scripts/validate_sources.py

clean-diagrams:
	rm -rf build/figures/mermaid

clean:
	rm -rf build .build-src
