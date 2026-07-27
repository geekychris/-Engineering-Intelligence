SHELL := /usr/bin/env bash

.PHONY: all html pdf epub decks diagrams validate test source-validate manifest-validate pages publish clean clean-diagrams clean-pages

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

decks:
	bash scripts/build-decks.sh

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

pages: all
	bash scripts/build-pages.sh build site

publish:
	@if [[ -n "$$(git status --porcelain)" ]]; then \
		echo "Working tree is dirty. Commit or stash before publishing."; \
		exit 1; \
	fi
	@echo "Pushing main; the publish-book workflow will deploy Pages."
	git push origin main

clean-diagrams:
	rm -rf build/figures/mermaid

clean-pages:
	rm -rf site

clean:
	rm -rf build .build-src site
