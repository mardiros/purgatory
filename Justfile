default_test_suite := 'tests/unittests'

test: unittest

lf:
    poetry run pytest -sxvvv --lf

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

lint:
    poetry run flake8

black:
    poetry run isort .
    poetry run black .

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov=aiobreak {{test_suite}}
    xdg-open htmlcov/index.html
