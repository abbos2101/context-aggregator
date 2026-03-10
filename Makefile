.DEFAULT_GOAL := help

help:
	@echo "Mavjud komandalar:"
	@echo "  make up ENV=local"
	@echo "  make test"
	@echo "  make test group=auth"
	@echo "  make test ENV=dev"

run:
	uvicorn main:app --reload --port 2101

run-prod:
	uvicorn main:app --port 2101

build-mac:
	.venv/bin/pyinstaller --onefile --name context-ai main.py
	chmod +x dist/context-ai
	@echo "Tayyor: dist/context-ai"