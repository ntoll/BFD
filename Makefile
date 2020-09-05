XARGS := xargs -0 $(shell test $$(uname) = Linux && echo -r)
GREP_T_FLAG := $(shell test $$(uname) = Linux && echo -T)
export PYFLAKES_BUILTINS=_

all:
	@echo "\nThere is no default Makefile target right now. Try:\n"
	@echo "make run - run the local development version of BFD."
	@echo "make clean - reset the project and remove auto-generated assets."
	@echo "make flake8 - run the PyFlakes code checker."
	@echo "make mypy - run the static type checker."
	@echo "make test - run the test suite."
	@echo "make coverage - view a report on test coverage."
	@echo "make tidy - tidy code with the 'black' formatter."
	@echo "make check - run all the checkers and tests."
	@echo "make docs - use Sphinx to create project documentation."

clean:
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf docs/_build
	rm -rf .eggs
	rm -rf build
	rm -rf dist
	find . \( -name '*.py[co]' -o -name dropin.cache \) -delete
	find . \( -name '*.bak' -o -name dropin.cache \) -delete
	find . \( -name '*.tgz' -o -name dropin.cache \) -delete
	find . | grep -E "(__pycache__)" | xargs rm -rf

run: clean
ifeq ($(VIRTUAL_ENV),)
	@echo "\n\nCannot run BFD. Your Python virtualenv is not activated."
else
	hypercorn bfd.app:app	
endif

flake8:
	flake8 --ignore=E231,W503 --exclude=docs,bfd/bfd,bfd/datastore/migrations,bfd/datastore/apps.py

mypy:
	mypy --config-file=.mypy.ini

validate:
	cd bfd && python manage.py check

test: clean
	cd bfd && python manage.py test

coverage: clean
	cd bfd && coverage run --omit=manage.py,bfd/*,datastore/apps.py,datastore/migrations/*,datastore/tests/* --source='.' manage.py test
	cd bfd && coverage report -m

tidy: clean
	@echo "\nTidying code with black..."
	black -l 79 bfd 

check: clean tidy flake8 mypy validate coverage

docs: clean
	$(MAKE) -C docs html
	@echo "\nDocumentation can be found here:"
	@echo file://`pwd`/docs/_build/html/index.html
	@echo "\n"
