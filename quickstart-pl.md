# Energy RAG - Szybki Start

Przewodnik krok po kroku w języku polskim, jak skonfigurować i uruchomić system wyszukiwania dokumentów.

## Spis treści

1. [Pobieranie plików PDF](#1-pobieranie-plików-pdf)
2. [Konwersja PDF do Markdown (OCR)](#2-konwersja-pdf-do-markdown-ocr)
3. [Konfiguracja zmiennych środowiskowych](#3-konfiguracja-zmiennych-środowiskowych)
4. [Tworzenie bazy wektorowej](#4-tworzenie-bazy-wektorowej)
5. [Uruchomienie wyszukiwania](#5-uruchomienie-wyszukiwania)

---

## Metody uruchamiania

System można uruchomić na dwa sposoby:

### Opcja A: Lokalnie (bez Docker)

**Wymaga:**
- Python 3.10+
- Zainstalowane zależności: `pip install -r requirements.txt`
- Lokalnie działający Qdrant (przez Docker lub natywnie)

**Zalety:**
- Szybsze debugowanie
- Łatwiejsza edycja kodu
- Bezpośredni dostęp do plików

**Przykład:**
```bash
python scripts/ask.py "pytanie"
```

### Opcja B: Docker

**Wymaga:**
- Docker
- Docker Compose (opcjonalnie, ale zalecane)

**Zalety:**
- Izolowane środowisko
- Nie trzeba instalować zależności Pythona
- Wszystko działa "out of the box"
- Łatwe przenoszenie między maszynami

**Przykład:**
```bash
docker-compose run --rm app python scripts/ask.py "pytanie"
```

**W tej instrukcji** pokazujemy oba sposoby dla każdego kroku. Wybierz ten, który pasuje do Twojego środowiska.

---

## Szybki start (TL;DR)

Jeśli chcesz szybko uruchomić cały system z Docker:

```bash
# 1. Sklonuj repo i przejdź do katalogu
cd energy-rag

# 2. Skopiuj i skonfiguruj .env
cp .env.example .env
nano .env  # Dodaj klucz OPEN_ROUTER_API_KEY

# 3. Dodaj pliki PDF do input/
cp twoje-pliki/*.pdf input/

# 4. Uruchom Qdrant
docker-compose up -d qdrant

# 5. Zbuduj obraz aplikacji
docker-compose build

# 6. Konwersja PDF → Markdown (OCR)
docker-compose run --rm app python scripts/pdf_to_markdown.py

# 7. Zbuduj indeks wektorowy
docker-compose run --rm app python scripts/build_index.py

# 8. Zadaj pytanie!
docker-compose run --rm app python scripts/ask.py "twoje pytanie"
```

Gotowe! 🎉

Jeśli chcesz poznać szczegóły każdego kroku, czytaj dalej.

---

## 1. Pobieranie plików PDF

### Opcja A: Ręczne dodanie plików

Skopiuj swoje pliki PDF do katalogu `input/`:

```bash
cp /ścieżka/do/twoich/plików/*.pdf input/
```

### Opcja B: Automatyczne pobieranie z listy URL

1. **Stwórz plik z listą URL**

   ```bash
   cp input/urls.example.csv input/urls.csv
   ```

2. **Edytuj plik `input/urls.csv`** i dodaj swoje linki do PDF:

   ```csv
   url,filename
   https://przyklad.pl/dokument1.pdf,Moja Własna Nazwa Dokumentu
   https://przyklad.pl/raporty/raport-roczny.pdf,
   https://przyklad.pl/polityka.pdf,Wytyczne Polityki Energetycznej
   ```

   **Format CSV:**
   - Kolumna 1 (`url`): Wymagana - adres URL do pliku PDF
   - Kolumna 2 (`filename`): Opcjonalna - własna nazwa pliku (bez rozszerzenia .pdf)
     - Jeśli podana: użyta zostanie własna nazwa
     - Jeśli pusta: nazwa zostanie wyciągnięta z URL
     - Format końcowy: `[nazwa_z_url (50 znaków)] - [własna_nazwa]`

3. **Uruchom skrypt pobierania:**

   ```bash
   python scripts/download_pdfs.py
   ```

   Skrypt:
   - Pobierze wszystkie pliki PDF z listy
   - Zapisze je w katalogu `input/`
   - Automatycznie oczyści nazwy plików ze znaków specjalnych
   - Wyświetli podsumowanie: ile plików pobrano, ile błędów

---

## 2. Konwersja PDF do Markdown (OCR)

System używa EasyOCR do rozpoznawania tekstu z plików PDF.

### Opcja A: Uruchomienie lokalnie (bez Docker)

1. **Upewnij się, że masz zainstalowane zależności:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Uruchom konwersję:**

   ```bash
   python scripts/pdf_to_markdown.py
   ```

   **Co robi ten skrypt?**
   - Wczytuje wszystkie pliki PDF z katalogu `input/`
   - Dla każdej strony:
     - Sprawdza czy PDF zawiera tekst
     - Jeśli tak: wyciąga tekst bezpośrednio z PDF
     - Jeśli nie: używa OCR (EasyOCR) do rozpoznania tekstu z obrazu
   - Zapisuje wyniki jako pliki Markdown w katalogu `output/`

   **Uwaga:** Przy pierwszym uruchomieniu EasyOCR pobierze modele (~100-200MB). To normalne.

### Opcja B: Uruchomienie w Docker

1. **Zbuduj obraz Docker:**

   ```bash
   docker build -t energy-rag-ocr .
   ```

2. **Uruchom kontener z konwersją:**

   ```bash
   docker run --rm \
     -v $(pwd)/input:/app/input \
     -v $(pwd)/output:/app/output \
     energy-rag-ocr \
     python scripts/pdf_to_markdown.py
   ```

   **Wyjaśnienie parametrów:**
   - `--rm` - automatycznie usuń kontener po zakończeniu
   - `-v $(pwd)/input:/app/input` - montuj katalog `input/` jako wolumen
   - `-v $(pwd)/output:/app/output` - montuj katalog `output/` jako wolumen
   - `energy-rag-ocr` - nazwa obrazu Docker
   - `python scripts/pdf_to_markdown.py` - polecenie do wykonania w kontenerze

### Jakość OCR

- **Drukowany tekst:** 95-99% dokładności
- **Skanowane dokumenty:** 90-95% dokładności
- **Tekst odręczny:** 60-80% dokładności

---

## 3. Konfiguracja zmiennych środowiskowych

System wymaga klucza API OpenRouter do generowania embeddingów i odpowiedzi.

### Krok 1: Uzyskaj klucz API OpenRouter

1. **Zarejestruj się na OpenRouter:**

   Odwiedź: https://openrouter.ai/

2. **Przejdź do zakładki z kluczami:**

   https://openrouter.ai/keys

3. **Stwórz nowy klucz API:**

   Kliknij "Create Key" i skopiuj wygenerowany klucz (zaczyna się od `sk-or-v1-...`)

### Krok 2: Skonfiguruj plik .env

1. **Skopiuj przykładowy plik konfiguracji:**

   ```bash
   cp .env.example .env
   ```

2. **Edytuj plik `.env`:**

   ```bash
   nano .env
   ```

   Lub użyj swojego ulubionego edytora tekstu.

3. **Dodaj swój klucz API:**

   ```env
   OPEN_ROUTER_API_KEY=sk-or-v1-twoj_prawdziwy_klucz_tutaj
   ```

   Zastąp `twoj_prawdziwy_klucz_tutaj` kluczem skopiowanym z OpenRouter.

### ⚠️ BEZPIECZEŃSTWO

- **NIGDY** nie commituj pliku `.env` do git (plik `.env` jest już w `.gitignore`)
- Jeśli klucz wycieknie, natychmiast go usuń na https://openrouter.ai/keys
- Nie udostępniaj klucza publicznie

### Koszty API

System jest bardzo tani w użyciu:

**Koszt jednorazowy (indeksowanie):**
- ~4,500 fragmentów dokumentów: **$0.01-0.02**

**Koszt za zapytanie:**
- Wyszukiwanie (search): **$0.000025** (~$0.03 za 1000 zapytań)
- Q&A z odpowiedzią (ask): **$0.000160** (~$0.16 za 1000 zapytań)

**Przykładowe koszty miesięczne:**
- 1000 zapytań Q&A/miesiąc = **$0.16** → rocznie ~$1.92
- 500 zapytań search + 500 Q&A/miesiąc = **$0.09** → rocznie ~$1.11

---

## 4. Tworzenie bazy wektorowej

Po skonwertowaniu plików PDF do Markdown, musisz stworzyć bazę wektorową Qdrant.

### Krok 1: Uruchom Qdrant

**Opcja A: Docker (zalecane):**

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

**Opcja B: Docker Compose:**

```bash
docker-compose up -d qdrant
```

### Krok 2: Zbuduj indeks

**Opcja A: Uruchomienie lokalne (bez Docker):**

```bash
python scripts/build_index.py
```

**Opcja B: Uruchomienie w Docker:**

```bash
# Jeśli używasz Docker Compose
docker-compose run --rm app python scripts/build_index.py

# Jeśli używasz samego Docker
docker run --rm \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/embedding_cache.db:/app/embedding_cache.db \
  -v $(pwd)/.env:/app/.env:ro \
  --network host \
  energy-rag-ocr \
  python scripts/build_index.py
```

**Co się stanie?**

   Skrypt wykonuje następujące kroki:

   ```
   1. Inicjalizacja klienta Qdrant i embeddera
   2. Tworzenie kolekcji wektorowej
   3. Przetwarzanie dokumentów (chunking)
   4. Szacowanie kosztów indeksowania
   5. Generowanie embeddingów (z cache'owaniem)
   6. Wstawianie do bazy Qdrant
   ```

3. **Potwierdzenie:**

   Skrypt wyświetli szacowany koszt i zapyta o potwierdzenie:

   ```
   Chunks to embed: 4,523
   Estimated tokens: 452,300
   Estimated cost: $0.0090
   Cost per chunk: $0.000002

   Proceed with indexing? (yes/no):
   ```

   Wpisz `yes` aby kontynuować.

4. **Czas trwania:**

   - Małe zbiory (10-20 plików): 1-2 minuty
   - Średnie zbiory (50-100 plików): 5-10 minut
   - Duże zbiory (200+ plików): 15-30 minut

### Cache embeddingów

System używa SQLite cache do przechowywania embeddingów:
- Po ~50 zapytaniach: 70-90% trafień w cache
- Redukcja kosztów API: 80-90%
- Plik cache: `embedding_cache.db` (auto-generowany)

---

## 5. Uruchomienie wyszukiwania

System oferuje dwa tryby wyszukiwania:

### A. System Q&A (odpowiedzi w języku naturalnym)

Używa DeepSeek V3.2 do generowania odpowiedzi na podstawie znalezionych dokumentów.

**Pojedyncze zapytanie:**

**Opcja A: Lokalnie:**

```bash
python scripts/ask.py "jakie remonty przeprowadzono na ul. Bonifacego 66?"
```

**Opcja B: Docker:**

```bash
# Docker Compose
docker-compose run --rm app python scripts/ask.py "jakie remonty przeprowadzono na ul. Bonifacego 66?"

# Docker standalone
docker run --rm -it \
  -v $(pwd)/embedding_cache.db:/app/embedding_cache.db \
  -v $(pwd)/.env:/app/.env:ro \
  --network host \
  energy-rag-ocr \
  python scripts/ask.py "jakie remonty przeprowadzono na ul. Bonifacego 66?"
```

**Przykładowy wynik:**

```
======================================================================
Q&A System - Protokoły Zarządu MSM Energetyka
Powered by RAG + DeepSeek V3.2
======================================================================

Question: jakie remonty przeprowadzono na ul. Bonifacego 66?

======================================================================
ANSWER:
======================================================================
Na podstawie przeszukanych dokumentów, na ul. Bonifacego 66
przeprowadzono następujące remonty:

1. **Remont instalacji c.o.** (Protokół nr 15, 2024)
   - Wymiana grzejników w mieszkaniach
   - Koszt: 45 000 zł

2. **Remont dachu** (Protokół nr 23, 2023)
   - Naprawa pokrycia dachowego
   - Wymiana rynien
   - Koszt: 78 000 zł

📚 Źródła (20 dokumentów):
  1. Protokół Nr 15, Strona 2 (Data: 19.08.-03.09.2024)
  2. Protokół Nr 23, Strona 1 (Data: 21.-28.06.2023)
  ...
======================================================================
```

**Tryb interaktywny:**

**Opcja A: Lokalnie:**

```bash
python scripts/ask.py
```

**Opcja B: Docker:**

```bash
# Docker Compose
docker-compose run --rm app python scripts/ask.py

# Docker standalone
docker run --rm -it \
  -v $(pwd)/embedding_cache.db:/app/embedding_cache.db \
  -v $(pwd)/.env:/app/.env:ro \
  --network host \
  energy-rag-ocr \
  python scripts/ask.py
```

Pozwala zadawać wiele pytań w jednej sesji:

```
💬 Question: jakie decyzje podjęto ws. wiat śmietnikowych?
💬 Question: kto został zatrudniony w 2023?
💬 Question: exit
```

**Opcje dodatkowe:**

**Lokalnie:**

```bash
# Tryb szczegółowy (statystyki RAG)
python scripts/ask.py --verbose "pytanie"

# Bez wyświetlania źródeł
python scripts/ask.py --no-sources "pytanie"

# Statystyki systemu
python scripts/ask.py --stats
```

**Docker:**

```bash
# Tryb szczegółowy
docker-compose run --rm app python scripts/ask.py --verbose "pytanie"

# Bez źródeł
docker-compose run --rm app python scripts/ask.py --no-sources "pytanie"

# Statystyki
docker-compose run --rm app python scripts/ask.py --stats
```

### B. Klasyczne wyszukiwanie (fragmenty dokumentów)

Zwraca fragmenty dokumentów bez generowania odpowiedzi.

**Podstawowe wyszukiwanie:**

**Opcja A: Lokalnie:**

```bash
python scripts/search.py "sprawy pracownicze"
```

**Opcja B: Docker:**

```bash
# Docker Compose
docker-compose run --rm app python scripts/search.py "sprawy pracownicze"

# Docker standalone
docker run --rm -it \
  -v $(pwd)/embedding_cache.db:/app/embedding_cache.db \
  -v $(pwd)/.env:/app/.env:ro \
  --network host \
  energy-rag-ocr \
  python scripts/search.py "sprawy pracownicze"
```

**Tryb szczegółowy:**

**Lokalnie:**

```bash
python scripts/search.py --verbose "sprawy pracownicze"
```

**Docker:**

```bash
docker-compose run --rm app python scripts/search.py --verbose "sprawy pracownicze"
```

Pokazuje:
- Wygenerowane warianty zapytania (5 wersji)
- Statystyki fuzji RRF
- Trafienia w cache
- Liczbę wywołań API

**Tryb interaktywny:**

**Lokalnie:**

```bash
python scripts/search.py
```

**Docker:**

```bash
docker-compose run --rm app python scripts/search.py
```

**Dostępne komendy:**
- `--verbose` - przełącz tryb szczegółowy
- `--stats` - pokaż statystyki sesji (cache, wywołania API)
- `exit` / `quit` - wyjdź

---

## Rozwiązywanie problemów

### Problem: "No PDF files found in folder 'input'"

**Rozwiązanie:** Upewnij się, że pliki PDF znajdują się w katalogu `input/`.

```bash
ls -la input/
```

### Problem: "Rate limited. Waiting 5s..."

**Rozwiązanie:** OpenRouter ogranicza liczbę zapytań. System automatycznie czeka i ponawia próbę.

Możesz zwiększyć czas oczekiwania w pliku `rag/openrouter_client.py`:
```python
time.sleep(1.0)  # zamiast 0.5
```

### Problem: "Could not connect to Qdrant"

**Rozwiązanie:** Upewnij się, że Qdrant działa:

```bash
docker ps | grep qdrant
```

Jeśli nie działa, uruchom ponownie:

```bash
docker run -d --name qdrant -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### Problem: "OPEN_ROUTER_API_KEY not found"

**Rozwiązanie:** Sprawdź czy plik `.env` istnieje i zawiera klucz:

```bash
cat .env | grep OPEN_ROUTER_API_KEY
```

Jeśli nie, skopiuj `.env.example` i dodaj swój klucz.

### Problem: OCR nie rozpoznaje tekstu

**Rozwiązanie:**
- Sprawdź jakość pliku PDF (czy jest czytelny)
- Zwiększ rozdzielczość renderowania w `scripts/pdf_to_markdown.py`:
  ```python
  zoom = 3  # zamiast 2
  ```

### Problem: Za mało wyników

**Rozwiązanie:** Zmniejsz próg jakości w `rag/config.py`:

```python
MIN_RRF_SCORE = 0.02  # zamiast 0.04 (mniej restrykcyjny)
```

### Problem: Za dużo słabych wyników

**Rozwiązanie:** Zwiększ próg jakości w `rag/config.py`:

```python
MIN_RRF_SCORE = 0.06  # zamiast 0.04 (bardziej restrykcyjny)
```

---

## Docker Compose - Kompletne środowisko

Uruchom cały system (Qdrant + aplikacja) za pomocą Docker Compose:

### 1. Zbuduj obrazy

```bash
docker-compose build
```

### 2. Uruchom Qdrant

```bash
docker-compose up -d qdrant
```

### 3. Zbuduj indeks (jednorazowo)

```bash
docker-compose run --rm app python scripts/build_index.py
```

### 4. Uruchom konwersję OCR (opcjonalnie)

```bash
docker-compose run --rm app python scripts/pdf_to_markdown.py
```

### 5. Zadaj pytanie

```bash
docker-compose run --rm app python scripts/ask.py "pytanie"
```

### 6. Tryb interaktywny

```bash
docker-compose run --rm app python scripts/ask.py
```

---

## Wskazówki

### Optymalizacja kosztów

1. **Cache jest Twoim przyjacielem** - po ~50 zapytaniach cache redukuje koszty o 80-90%
2. **Używaj search zamiast ask** - jeśli nie potrzebujesz odpowiedzi w formie tekstu, używaj `search.py`
3. **DeepSeek jest tani** - 75x tańszy niż Claude, 47x tańszy niż GPT-4o

### Jakość wyników

1. **Eksperymentuj z MIN_RRF_SCORE** - dostosuj próg do swoich potrzeb
2. **Używaj pełnych pytań** - zamiast "remonty" napisz "jakie remonty przeprowadzono?"
3. **Tryb verbose** - pomaga zrozumieć jak system przetwarza zapytania

### Bezpieczeństwo

1. **Nigdy nie commituj .env** - zawiera klucz API
2. **Regularnie rotuj klucze** - zwłaszcza jeśli podejrzewasz wyciek
3. **Monitoruj koszty** - sprawdzaj https://openrouter.ai/activity

---

## Przykładowe zapytania

Wypróbuj te zapytania aby zobaczyć możliwości systemu.

### Lokalnie:

```bash
# Zapytania z automatycznym rozwinięciem skrótów
python scripts/ask.py "ZO osiedle"          # → "zarząd osiedla"
python scripts/ask.py "c.o. budynek"        # → "centralne ogrzewanie"

# Zapytania semantyczne
python scripts/ask.py "jakie remonty przeprowadzono?"
python scripts/ask.py "decyzje dotyczące zatrudnienia"
python scripts/ask.py "wydatki na remonty w 2024"

# Zapytania szczegółowe
python scripts/ask.py "jakie decyzje podjęto ws. wiat śmietnikowych?"
python scripts/ask.py "kto został zatrudniony w 2023?"
python scripts/ask.py "jakie prace planowane są na 2025?"
```

### Docker:

```bash
# Zapytania z automatycznym rozwinięciem skrótów
docker-compose run --rm app python scripts/ask.py "ZO osiedle"
docker-compose run --rm app python scripts/ask.py "c.o. budynek"

# Zapytania semantyczne
docker-compose run --rm app python scripts/ask.py "jakie remonty przeprowadzono?"
docker-compose run --rm app python scripts/ask.py "decyzje dotyczące zatrudnienia"

# Zapytania szczegółowe
docker-compose run --rm app python scripts/ask.py "jakie decyzje podjęto ws. wiat śmietnikowych?"
```

---

## Dalsze informacje

- **Pełna dokumentacja:** `README.md`
- **Szczegóły techniczne:** `IMPLEMENTATION_SUMMARY.md`
- **Ulepszone funkcje:** `QUICKSTART_IMPROVEMENTS.md`
- **Docker:** `DOCKER_GUIDE.md`

---

**Zbudowano z ❤️ dla lepszego wyszukiwania dokumentów**
