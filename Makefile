SHELL := /usr/bin/env bash

.PHONY: all html pdf diagrams validate clean clean-diagrams

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

clean-diagrams:
	rm -rf build/figures/mermaid

clean:
	rm -rf build .build-src
