.PHONY: help build clean

WATCH_EXCLUDE = -e .*__pycache__.* -e .*.tmp
CONTENT = pandas_tutor

sam_cmd = python -m pandas_tutor.sams_scratchpad # && echo "\n------------------\n"

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test: ## Runs tests
	python -m unittest

sam: ## Runs what sam wants
	@$(sam_cmd)

sam_watch:
	fswatch -0 $(WATCH_EXCLUDE) $(CONTENT) --one-per-batch |\
		xargs -0 -n 1 -I {} $(MAKE) sam

typecheck: ## Type checks everything
	mypy pandas_tutor

watch: ## reruns typecheck and tests on file change
	fswatch -0 $(WATCH_EXCLUDE) $(CONTENT) |\
		xargs -0 -n 1 -I {} sh -c "echo {} && $(MAKE) typecheck test"
