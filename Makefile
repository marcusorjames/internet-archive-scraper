.PHONY: install test lint clean

install:
	pip install --upgrade pip
	pip install -r requirements.txt -r requirements-dev.txt

test:
	pytest tests/ -v --cov=scraper --cov-report=term-missing

lint:
	python -m py_compile scraper.py config.py version.py
	@echo "Syntax OK"

clean:
	python scraper.py --clean
