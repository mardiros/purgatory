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

test: gensync unittest lint mypy

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

release major_minor_patch: gensync test rtd && changelog build
    poetry version {{major_minor_patch}}
    poetry install

poetry_shell:
    poetry shell

changelog: poetry_shell && changelog_tail
    #!/usr/bin/env python3
    import datetime
    import purgatory
    header = f"{purgatory.__version__}  - Released on {datetime.datetime.now().date().isoformat()}"
    with open("CHANGELOG.rst.new", 'w') as changelog:
        changelog.write(header)
        changelog.write("\n")
        changelog.write("-" * len(header))
        changelog.write("\n")
        changelog.write("* please write here \n\n")

changelog_tail:
    cat CHANGELOG.rst >> CHANGELOG.rst.new
    rm CHANGELOG.rst
    mv CHANGELOG.rst.new CHANGELOG.rst
    $EDITOR CHANGELOG.rst

build:
    poetry build

publish:
    git commit -am "Release $(poetry run python scripts/show_release.py)"
    poetry build
    poetry publish
    git tag "$(poetry run python scripts/show_release.py)"
    git push origin "$(poetry run python scripts/show_release.py)"
