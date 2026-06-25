.DEFAULT_GOAL := help

.PHONY: help install test test-lib test-cli test-integration test-cov lint typecheck format check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install package with dev and CLI extras
	pip install -e ".[dev,cli]" --break-system-packages

test: ## Run all tests
	python -m pytest tests/

test-lib: ## Run pysavant library tests only
	python -m pytest tests/pysavant/

test-cli: ## Run CLI tests only
	python -m pytest tests/cli/

test-integration: ## Run HA integration tests only
	python -m pytest tests/integration/

test-cov: ## Run tests with coverage report
	python -m pytest tests/ --cov=pysavant --cov-report=term-missing

lint: ## Run ruff linter
	ruff check pysavant/ savant_cli/ tests/ custom_components/savant/

typecheck: ## Run mypy strict type checking
	mypy pysavant/

format: ## Auto-fix lint errors and format code
	ruff check --fix pysavant/ savant_cli/ tests/ custom_components/savant/
	ruff format pysavant/ savant_cli/ tests/ custom_components/savant/

check: lint typecheck test ## Run lint + typecheck + tests (full CI gate)

clean: ## Remove build artifacts and caches
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
