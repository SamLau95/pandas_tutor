.PHONY: help build clean

WATCH_EXCLUDE = -e .*__pycache__.* -e .*.tmp
CONTENT = pandas_tutor

sam_cmd = python -m pandas_tutor.sams_scratchpad # && echo "\n------------------\n"

# add Chris make
chris:
	python -m pandas_tutor.chris_scratchpad

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test: ## Runs tests
	python -m unittest

sam: ## Runs what sam wants
	@$(sam_cmd)

sam_watch: ## Watches what sam wants
	fswatch -0 $(WATCH_EXCLUDE) $(CONTENT) --one-per-batch |\
		xargs -0 -n 1 -I {} $(MAKE) sam

typecheck: ## Type checks everything
	mypy pandas_tutor

watch: ## reruns typecheck and tests on file change
	fswatch -0 $(WATCH_EXCLUDE) $(CONTENT) |\
		xargs -0 -n 1 -I {} sh -c "echo {} && $(MAKE) typecheck test"

build: ## makes wheel for pypi
	python -m build

clean: ## removes pypi built files
	rm -rf build/ dist/

# to install package from test pypi:
# pip install --index-url https://test.pypi.org/simple/ --no-deps pandas_tutor
test_publish: clean build ## uploads wheel to test pypi
	python -m twine upload --repository testpypi dist/*


publish: clean build ## uploads wheel to REAL pypi
	python -m twine upload dist/*

# requires 'pip install wheel' in your current python environment
pyodide_build:
	rm -rf build/
	python setup.py bdist_wheel

pyodide_clean:
	rm -rf build/ dist/ pandastutor.egg-info/
