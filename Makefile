SHELL := /usr/bin/env bash

.PHONY: all html pdf diagrams validate source-validate clean clean-diagrams

all: clean-diagrams
	bash scripts/build.sh all

html: clean-diagrams
	bash scripts/build.sh html

pdf: clean-diagrams
	bash scripts/build.sh pdf

diagrams: clean-diagrams
	bash scripts/build.sh diagrams

validate: clean-diagrams
	bash scripts/build.sh validate

source-validate:
	python3 scripts/validate_sources.py

clean-diagrams:
	rm -rf build/figures/mermaid

clean:
	rm -rf build .build-src
