help: ## Prints this help/overview message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-17s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

include .env
export

upload-to-test-pypi:
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload-to-pypi:
	python3 -m twine upload dist/*

clean-build:  # Cleans the last build artifacts
	rm -rf build dist

clean: clean-build ## Cleans all unncessary files
	rm -rf cover .mypy_cache .venv* .coverage .pytest_cache

test: ## Updates requirements, rules and runs all available tests locally.
	bash test.sh --strict

lint: ## Runs linter on source code and tests. Does not update requirements or rules.
	$(RUN_TEST_NO_UPDATE) -p

unittest: ## Runs all unit tests without coverage test. Does not update requirements or rules.
	$(RUN_TEST_NO_UPDATE) -u

coverage: ## Runs unit test coverage test. Does not update requirements or rules.
	$(RUN_TEST_NO_UPDATE) -c

types: ## Runs types test. Does not update requirements or rules.
	$(RUN_TEST_NO_UPDATE) -t

format: ## Runs the code formatter. Does not update requirements or rules.
	$(RUN_TEST_NO_UPDATE) -fmt

build: clean-build # Builds artifacts for Pypi
	python setup.py sdist bdist_wheel