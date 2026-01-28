.PHONY: help build up down download convert index ask search shell logs

# Automatically detect host UID/GID
USER_ID := $(shell id -u)
GROUP_ID := $(shell id -g)
export USER_ID
export GROUP_ID

help:
	@echo "Energy RAG - Polecenia Docker"
	@echo ""
	@echo "Setup:"
	@echo "  make build      - Zbuduj obraz Docker"
	@echo "  make up         - Uruchom Qdrant"
	@echo "  make down       - Zatrzymaj wszystkie serwisy"
	@echo ""
	@echo "Pipeline danych:"
	@echo "  make download   - Pobierz PDF-y z files.json"
	@echo "  make convert    - Konwertuj PDF na Markdown (OCR)"
	@echo "  make index      - Zbuduj indeks Qdrant"
	@echo ""
	@echo "Użycie:"
	@echo "  make ask        - Interaktywne Q&A"
	@echo "  make search     - Interaktywne wyszukiwanie"
	@echo "  make shell      - Otwórz bash w kontenerze"
	@echo ""
	@echo "Maintenance:"
	@echo "  make logs       - Zobacz logi Qdrant"

build:
	docker-compose build

up:
	docker-compose up -d qdrant
	@echo "Qdrant uruchomiony na http://localhost:6333"

down:
	docker-compose down

download:
	docker-compose run --rm app python scripts/download_pdfs.py

convert:
	docker-compose run --rm app python scripts/pdf_to_markdown.py

index:
	docker-compose run --rm app python scripts/build_index.py

ask:
	docker-compose run --rm app python scripts/ask.py

search:
	docker-compose run --rm app python scripts/search.py

shell:
	docker-compose run --rm app /bin/bash

logs:
	docker-compose logs -f qdrant
