PACKAGE = mpdlcd
TESTS_DIR = tests

FLAKE8 = flake8


# Default targets
# ===============

all: default
default:

.PHONY: all default


# Packaging
# =========

clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -path '*/__pycache__/*' -delete
	find . -type d -empty -delete

update:
	pip install --upgrade pip setuptools
	pip install --upgrade -r requirements_dev.txt
	pip freeze

release:
	fullrelease

.PHONY: clean update release


# Tests and quality
# =================

test:
	python -W default setup.py test

lint:
	$(FLAKE8) --config .flake8 $(PACKAGE)
	check-manifest


.PHONY: test lint
