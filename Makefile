all: default


PACKAGE=mpdlcd


default:


clean:
	find . -type f -name '*.pyc' -delete


test:
	python -W default setup.py test

coverage:
	coverage erase
	coverage run "--include=$(PACKAGE)/*.py,tests/*.py" --branch setup.py test
	coverage report "--include=$(PACKAGE)/*.py,tests/*.py"
	coverage html "--include=$(PACKAGE)/*.py,tests/*.py"


.PHONY: all default clean coverage doc test
