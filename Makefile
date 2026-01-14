.PHONY: install install-dev test lint format clean run demo

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src/publix_scraper --cov-report=html

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/ scripts/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov .mypy_cache
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

run:
	python -m src.publix_scraper.main

demo:
	python scripts/demo.py

scheduler:
	python -m src.publix_scraper.scheduler
