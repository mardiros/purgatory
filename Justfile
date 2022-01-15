default_test_suite := 'tests/unittests'

doc:
    cd docs && poetry run make html
    xdg-open docs/build/html/index.html

cleandoc:
    cd docs && poetry run make clean

rtd:
    poetry export --dev -f requirements.txt -o docs/requirements.txt

gensync:
    poetry run python scripts/gen_unasync.py
    poetry run black src/purgatory/service/_sync/
    poetry run black tests/unittests/_sync/

test: gensync unittest lint

build: test
    poetry build

lf:
    poetry run pytest -sxvvv --lf

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

lint:
    poetry run flake8

black:
    poetry run isort .
    poetry run black .

mypy:
    poetry run mypy src/purgatory/

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov=purgatory {{test_suite}}
    xdg-open htmlcov/index.html
