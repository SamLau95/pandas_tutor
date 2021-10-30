.PHONY: help build clean

CONTENT = pandas_tutor

sam_cmd = python -m pandas_tutor.sams_scratchpad # && echo "\n------------------\n"

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test: ## Runs tests
	python -m unittest

sam: ## Runs what sam wants
	@$(sam_cmd)

sam_watch:
	fswatch -0 $(CONTENT) --one-per-batch | xargs -0 -n 1 -I {} $(MAKE) sam

short_sam: ## Displays make sam with dataframes taken out of json
	@# $(MAKE) sam | jq '(..|objects|select(has("data"))).data |= "<omit>"'
	@$(MAKE) sam | jq '.[].data_frame |= "<omit>"'


typecheck: ## Type checks everything
	mypy pandas_tutor

watch: ## reruns typecheck and tests on file change
	@echo Watching content/ch for changes...
	fswatch -0 $(CONTENT) --one-per-batch | xargs -0 -n 1 -I {} $(MAKE) typecheck test

# OLD STUFF FROM ANOTHER REPO
build: ## Builds extension
	jlpm run build

test_lab: ## Starts lab server in test book folder
	cd codebook/test_book && jupyter lab

lab: ## Starts lab server in actual book folder
	cd ../textbook && jupyter lab

clean:
	jlpm run clean

install: ## installs codebook for local dev
	pip install -e .
	jupyter labextension develop --overwrite .

	@echo "We recommend adding these to your ~/.jupyter/jupyter_lab_config.py"
	@echo ""
	@echo "# --------------------------------------------------------"
	@echo "c.ServerApp.autoreload = True"
	@echo "c.ServerApp.open_browser = False"
	@echo "# --------------------------------------------------------"
