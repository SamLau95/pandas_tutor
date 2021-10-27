.PHONY: help build clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test: ## Runs tests
	python -m unittest


# OLD STUFF FROM ANOTHER REPO
build: ## Builds extension
	jlpm run build

watch: ## Watches TS code
	jlpm run watch

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
