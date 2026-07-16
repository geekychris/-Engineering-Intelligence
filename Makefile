SHELL := /usr/bin/env bash

.PHONY: all html pdf diagrams validate source-validate clean clean-diagrams

all: source-validate clean-diagrams
	bash scripts/build.sh all

html: source-validate clean-diagrams
	bash scripts/build.sh html

pdf: source-validate clean-diagrams
	bash scripts/build.sh pdf

diagrams: source-validate clean-diagrams
	bash scripts/build.sh diagrams

validate: source-validate clean-diagrams
	bash scripts/build.sh validate

source-validate:
	python3 scripts/validate_sources.py

clean-diagrams:
	rm -rf build/figures/mermaid

clean:
	rm -rf build .build-src
