.PHONY: help install test run clean dev

help:
	@echo "LexZero - Volatility3 TUI"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run installation tests"
	@echo "  make run        - Run the application"
	@echo "  make dev        - Install in development mode"
	@echo "  make clean      - Clean temporary files"

install:
	pip install -r requirements.txt

test:
	python test_installation.py

run:
	python run.py

dev:
	pip install -e .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage
	@echo "Cleaned temporary files"
