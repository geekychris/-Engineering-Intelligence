SHELL := /usr/bin/env bash

.PHONY: all html pdf epub diagrams validate test source-validate manifest-validate clean clean-diagrams

all:
	bash scripts/build.sh all
	python3 scripts/validate_manifest.py build

html:
	bash scripts/build.sh html
	python3 scripts/validate_manifest.py build

pdf:
	bash scripts/build.sh pdf
	python3 scripts/validate_manifest.py build

epub:
	bash scripts/build.sh epub
	python3 scripts/validate_manifest.py build

diagrams:
	bash scripts/build.sh diagrams

validate: test
	bash scripts/build.sh validate
	python3 scripts/validate_manifest.py build

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v

source-validate:
	python3 scripts/validate_sources.py

manifest-validate:
	python3 scripts/validate_manifest.py build

clean-diagrams:
	rm -rf build/figures/mermaid

clean:
	rm -rf build .build-src
