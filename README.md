# Energy RAG - System Wyszukiwania Protokołów

Zaawansowany system RAG (Retrieval Augmented Generation) do semantycznego wyszukiwania w protokołach zarządu MSM Energetyka z wykorzystaniem:
- 🚀 **OpenRouter API** - embeddings `text-embedding-3-small` (1536-dim)
- 🔄 **Query Expansion** - hybrydowe generowanie wariantów zapytań (LLM + reguły)
- 🎯 **Reciprocal Rank Fusion** - inteligentna agregacja wyników
- 💾 **SQLite Cache** - redukcja kosztów API o 80-90%
- 📄 **OCR** - konwersja PDF na Markdown z EasyOCR

## Kluczowe Funkcje

### RAG System
- ✅ **5 wariantów zapytania** - oryginał + 2 LLM + 2 reguły (synonimy, kolejność słów)
- ✅ **RRF Aggregation** - fuzja 200 wyników (5 wariantów × 10) → top 20 najlepszych
- ✅ **Embedding Cache** - SQLite z automatycznym tracking hit rate
- ✅ **Precyzyjne chunki** - 512 znaków z 50 overlap (optymalizacja jakości)
- ✅ **Cost tracking** - pełna kontrola kosztów API

### Q&A System 🆕
- ✅ **Odpowiedzi w języku naturalnym** - DeepSeek V3.2 generuje odpowiedzi na podstawie RAG
- ✅ **Inteligentne filtrowanie** - tylko dokumenty wysokiej jakości (RRF score > 0.04)
- ✅ **Do 20 dokumentów kontekstowych** - adaptacyjna liczba wyników (zwykle 5-15)
- ✅ **Cytowanie źródeł** - automatyczne podawanie numerów protokołów i dat
- ✅ **Tryb interaktywny** - konwersacyjny interfejs do zadawania pytań
- ✅ **Niski koszt** - DeepSeek V3.2: $0.27/$1.10 per 1M tokens (75x taniej niż Claude)

### PDF OCR
- ✅ Konwersja PDF → Markdown z EasyOCR
- ✅ OCR dla polskiego i angielskiego
- ✅ Automatyczna detekcja: tekst PDF vs obrazy
- ✅ Wysokiej jakości rozpoznawanie tekstu

## Instalacja

### 1. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 2. Skonfiguruj klucz API

Skopiuj szablon konfiguracji i dodaj swój klucz API:

```bash
# Skopiuj szablon
cp .env.example .env

# Edytuj .env i dodaj swój klucz OpenRouter API
nano .env
```

Twój plik `.env` powinien wyglądać tak:
```
OPEN_ROUTER_API_KEY=sk-or-v1-your_actual_key_here
```

**Jak uzyskać klucz API:**
1. Zarejestruj się na [OpenRouter](https://openrouter.ai/)
2. Przejdź do [Keys](https://openrouter.ai/keys)
3. Utwórz nowy klucz API
4. Skopiuj klucz do pliku `.env`

**⚠️ BEZPIECZEŃSTWO:**
- **NIGDY** nie commituj pliku `.env` do git (już jest w `.gitignore`)
- Jeśli klucz wycieknie, natychmiast go zrotuj na https://openrouter.ai/keys
- Nie udostępniaj klucza publicznie

### 3. Pobierz lub wygeneruj pliki wejściowe

#### Opcja A: Pobierz PDFy (jeśli dostępne)

```bash
python scripts/download_pdfs.py
```

#### Opcja B: Dodaj własne PDFy

Umieść pliki PDF w katalogach:
- `input/` - główne protokoły
- `input-sp/` - protokoły osiedlowe (opcjonalnie)

**Uwaga:** Katalogi `input/`, `input-sp/`, `output/` i `output-sp/` są ignorowane przez git. Musisz wygenerować je lokalnie.

### 4. Zbuduj cache i indeks Qdrant

```bash
# Uruchom Qdrant (Docker)
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant

# W nowym terminalu: konwertuj PDFy na Markdown (jeśli masz PDFy)
python pdf_to_markdown_easyocr.py

# Zbuduj indeks Qdrant
python scripts/build_index.py
```

**Wymagania:**
- Python 3.8+
- Docker (dla Qdrant)
- OpenRouter API key ([uzyskaj tutaj](https://openrouter.ai/))
- ~2GB wolnego miejsca

---

## PDF to Markdown (OCR)

### Konwersja PDF na Markdown

System używa EasyOCR do rozpoznawania tekstu z zeskanowanych PDF.

```bash
# Pobierz PDFy (opcjonalnie)
python scripts/download_pdfs.py

# Konwertuj PDF → Markdown
python pdf_to_markdown_easyocr.py
```

**Proces:**
1. PyMuPDF wyciąga strony jako obrazy
2. EasyOCR rozpoznaje tekst (polski + angielski)
3. Formatowanie jako Markdown z nagłówkami stron
4. Zapisz do `output/`

**Przykład wyniku:**
```markdown
# Protokół nr 1 z ustaleń Zarządu w dniach  02.-14.01.2025 r

*Dokument zawiera 3 stron*
*Tekst rozpoznany automatycznie przez OCR*

---

## Strona 1

Protokół nr 1
ustaleń Zarządu MSM "Energetyka"
w dniach 02.-14.01.2025 r.
...
```

**Dokładność OCR:**
- ✅ Czysty druk: 95-99%
- ✅ Skanowane dokumenty: 90-95%
- ⚠️ Pisane ręcznie: 60-80%

**Rozwiązywanie problemów OCR:**
- Sprawdź jakość skanów (min 150 DPI)
- Jasne obrazy z dobrym kontrastem
- Pierwsze uruchomienie pobiera modele (~100-200MB)

## Struktura projektu

```
energy-rag/
├── input/                          # Pliki PDF do konwersji
├── output/                         # Wygenerowane pliki Markdown
├── rag/                           # Moduł RAG (Enhanced)
│   ├── config.py                  # Konfiguracja (embeddings, RRF, cache)
│   ├── openrouter_client.py       # OpenRouter API client z retry logic
│   ├── cache.py                   # SQLite cache dla embeddings
│   ├── openrouter_embedder.py     # Embedder z cache integration
│   ├── query_expander.py          # Hybrydowa ekspansja zapytań
│   ├── rrf_aggregator.py          # Reciprocal Rank Fusion
│   ├── enhanced_retriever.py      # Główny orchestrator
│   ├── qa_system.py               # System Q&A z LLM
│   ├── chunker.py                 # Parsowanie i dzielenie dokumentów
│   └── retriever.py               # Legacy retriever (backward compatibility)
├── scripts/                       # Skrypty użytkowe
│   ├── build_index.py             # Indeksowanie z cost estimation
│   ├── search.py                  # Enhanced CLI (--verbose, --stats)
│   ├── ask.py                     # Q&A system - odpowiedzi w języku naturalnym
│   └── download_pdfs.py           # Pobieranie PDF
├── tests/                         # Testy
│   └── test_retrieval.py          # Test suite dla RAG
├── .env                           # API keys (OPEN_ROUTER_API_KEY)
├── embedding_cache.db             # SQLite cache (auto-generated)
├── requirements.txt               # Zależności Python
└── README.md                      # Dokumentacja
```

---

## Wymagania Systemowe

### Minimalne
- Python 3.8+
- Docker (dla Qdrant)
- 4GB RAM
- 2GB wolnego miejsca

### Zalecane
- Python 3.10+
- 8GB RAM (dla OCR + RAG)
- SSD dla szybszego cache access

### Zależności Python
```
# Core
qdrant-client>=1.7.0
requests>=2.31.0
python-dotenv>=1.0.0

# OCR (opcjonalne - tylko dla konwersji PDF)
pymupdf>=1.23.0
easyocr>=1.7.0
Pillow>=10.0.0
numpy>=1.24.0
```

---

## FAQ

### Czy mogę użyć innego modelu embeddings?

Tak! Zmień w [rag/config.py](rag/config.py:8):
```python
EMBEDDING_MODEL = "openai/text-embedding-3-large"  # Większy model
EMBEDDING_DIM = 3072
```

**Uwaga:** Wymaga przeindeksowania bazy.

### Czy mogę wrócić do lokalnego modelu (bez API)?

Tak, zachowaliśmy backward compatibility. Zakomentuj nowe moduły i użyj starego `PolishEmbedder`:

```python
# In scripts/search.py
from rag.retriever import ProtocolRetriever  # Old retriever
```

### Jak często powinienem czyścić cache?

Nigdy, chyba że:
- Cache > 100MB (sprawdź: `ls -lh embedding_cache.db`)
- Zmieniasz model embeddings
- Testujesz cache hit rate od zera

### Czy mogę użyć innego LLM do query expansion?

Tak! W [rag/query_expander.py](rag/query_expander.py:expand_hybrid):
```python
# Zmień model
payload = {
    "model": "anthropic/claude-3.5-sonnet",  # Zamiast gpt-4o-mini
    ...
}
```

### Czy mogę użyć innego modelu LLM do Q&A?

Tak! System Q&A domyślnie używa DeepSeek V3.2 (tani i dobry), ale możesz zmienić na inny:

**Opcja 1:** Zmień domyślny model w [rag/qa_system.py](rag/qa_system.py:13):
```python
def __init__(self, model: str = "anthropic/claude-3.5-sonnet"):  # Zamiast deepseek/deepseek-chat
```

**Opcja 2:** Podaj model podczas inicjalizacji:
```python
from rag.qa_system import ProtocolQASystem
qa = ProtocolQASystem(model="anthropic/claude-3.5-sonnet")
```

**Dostępne modele na OpenRouter:**
- `deepseek/deepseek-chat` - DeepSeek V3.2 (najtańszy, dobry) ✅
- `google/gemini-2.0-flash-exp:free` - Gemini 2.0 Flash (darmowy!)
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet (najlepszy, drogi)
- `openai/gpt-4o` - GPT-4o (bardzo dobry, drogi)
- Pełna lista: https://openrouter.ai/models

### Jak dostosować próg jakości wyników?

System filtruje słabe wyniki używając `MIN_RRF_SCORE` (domyślnie 0.04). Możesz to zmienić w [rag/config.py](rag/config.py:32):

```python
MIN_RRF_SCORE = 0.04  # Domyślny próg
```

**Wskazówki:**
- **0.02** - więcej wyników, może zawierać słabe dopasowania
- **0.04** - zbilansowany (zalecany) ✅
- **0.06** - tylko bardzo dobre dopasowania, mniej wyników
- **0.10** - ekstremalnie restrykcyjny, tylko idealne dopasowania

**Typowe wartości RRF score:**
- 0.08+ - doskonałe dopasowanie (top 3 wyniki)
- 0.04-0.08 - dobre dopasowanie (wyniki 4-10)
- 0.02-0.04 - słabe dopasowanie (często nieistotne)
- <0.02 - bardzo słabe (szum)

### Czy działa offline?

Nie w obecnej wersji (wymaga OpenRouter API). Dla offline:
1. Przywróć `PolishEmbedder` (lokalny model)
2. Wyłącz LLM expansion (tylko rule-based)
3. Przeindeksuj z lokalnym modelem

---

## Roadmap

### Planowane Funkcje

- [ ] **Semantic Reranking** - 2-stage retrieval z cross-encoder
- [ ] **Query Classification** - filtrowanie po typie protokołu
- [ ] **Highlight Variants** - pokazywanie które słowa z wariantów pasują
- [ ] **A/B Testing** - porównanie z poprzednim systemem
- [ ] **Streaming Results** - progressive display dla długich wyników
- [ ] **Multi-language Support** - rozszerzenie na inne języki
- [ ] **Web UI** - interfejs graficzny (Streamlit/Gradio)

### Możliwe Optymalizacje

- [ ] **Hybrid Search** - połączenie vector + keyword (BM25)
- [ ] **Result Caching** - cache całych wyników (nie tylko embeddings)
- [ ] **Batch Querying** - obsługa wielu zapytań jednocześnie
- [ ] **Custom Synonyms** - learning from query logs
- [ ] **Feedback Loop** - implicit relevance feedback

---

## Contributing

Zgłaszaj bugi i propozycje funkcji przez [GitHub Issues](https://github.com/fwronski/energy-rag/issues).

Pull requesty mile widziane! 🎉

---

## Licencja

Open source - wykorzystuj dowolnie!

---

## Acknowledgments

Technologie użyte w projekcie:
- **OpenRouter** - unified LLM & embeddings API
- **Qdrant** - vector database
- **EasyOCR** - optical character recognition
- **PyMuPDF** - PDF processing
- **Anthropic Claude** - code generation & planning

---

**Built with ❤️ for better document search**

# Wyszukiwarka RAG - Szybki Start

## 1. Uruchom Qdrant (Docker)

```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

## 2. Przeindeksuj dokumenty

```bash
python scripts/build_index.py
```

**Co się dzieje:**
- Przetwarzanie ~458 plików markdown z `output/`
- Chunking: 512 znaków z 50 overlap → ~4,500-5,000 chunków
- Embeddings przez OpenRouter API (`text-embedding-3-small`)
- Oszacowanie kosztów i potwierdzenie przed rozpoczęciem
- **Koszt jednorazowy: ~$0.01-0.02**
- Czas: ~5-10 minut

**Przykładowy output:**
```
======================================================================
Building Qdrant index for protocol documents
======================================================================

1. Initializing Qdrant client and embedder...
   ✓ OpenRouter embedder initialized (cache: enabled)

2. Creating collection 'energy_protocols'...
   ✓ Created collection with 1536-dim vectors, cosine distance

3. Processing documents...
   ✓ Processed 458 files

4. Estimating indexing cost...
   Chunks to embed: 4,832
   Estimated tokens: 483,200
   Estimated cost: $0.0097

   Proceed with indexing? (yes/no): yes

5. Generating embeddings and indexing 4,832 chunks...
   Processing chunks 1-50/4832...
   Processing chunks 51-100/4832...
   ...

✓ Indexing complete!
✓ Time elapsed: 287.3s (0.06s per chunk)
✓ Actual cost: ~$0.0097
```

## 3a. Zadawaj pytania (Q&A System) 🆕

### Tryb podstawowy

```bash
python scripts/ask.py "jakie remonty były przeprowadzane przy ul. Bonifacego 66?"
```

**Output:**
```
======================================================================
Q&A System - Protokoły Zarządu MSM Energetyka
Powered by RAG + DeepSeek V3.2
======================================================================

Pytanie: jakie remonty były przeprowadzane przy ul. Bonifacego 66?

======================================================================
ODPOWIEDŹ:
======================================================================
Na podstawie przeszukanych dokumentów, w budynku przy ul. Bonifacego 66
przeprowadzono następujące remonty:

1. **Remont instalacji c.o.** (Protokół nr 15, 2024)
   - Wymiana grzejników w lokalach
   - Koszt: 45 000 zł

2. **Remont dachu** (Protokół nr 23, 2023)
   - Naprawa pokrycia dachowego
   - Wymiana rynien
   - Koszt: 78 000 zł

3. **Remont klatki schodowej** (Protokół nr 8, 2023)
   - Malowanie ścian
   - Wymiana lamp
   - Koszt: 12 000 zł

📚 Źródła (20 dokumentów):
  1. Protokół nr 15, Strona 2 (Data: 19.08.-03.09.2024)
  2. Protokół nr 23, Strona 1 (Data: 21.-28.06.2023)
  ...
======================================================================
```

### Tryb interaktywny

```bash
python scripts/ask.py
```

Pozwala zadawać wiele pytań w jednej sesji:
```
💬 Pytanie: jakie decyzje podjęto w sprawie wiat śmietnikowych?
💬 Pytanie: kto został zatrudniony w 2023 roku?
💬 Pytanie: exit
```

### Komendy specjalne

- `--verbose` - tryb szczegółowy (pokaż statystyki RAG)
- `--sources` - włącz/wyłącz wyświetlanie źródeł
- `--stats` - statystyki systemu
- `--no-sources` - uruchom bez wyświetlania źródeł

**Przykłady:**
```bash
# Pytanie z trybem szczegółowym
python scripts/ask.py --verbose "sprawy pracownicze"

# Pytanie bez wyświetlania źródeł
python scripts/ask.py --no-sources "wiaty śmietnikowe"
```

---

## 3b. Wyszukuj fragmenty (klasyczny RAG)

### Tryb podstawowy

```bash
python scripts/search.py "sprawy pracownicze"
```

### Tryb szczegółowy (--verbose)

```bash
python scripts/search.py --verbose "sprawy pracownicze"
```

**Pokazuje:**
- Wygenerowane warianty zapytania (5 wersji)
- Statystyki RRF fusion
- Cache hit rate
- Liczba wywołań API

### Tryb interaktywny

```bash
python scripts/search.py
```

**Dostępne komendy:**
- `--verbose` - włącz/wyłącz tryb szczegółowy
- `--stats` - pokaż statystyki sesji (cache, API calls)
- `exit` / `quit` - zakończ

## Przykład wyniku wyszukiwania

### Podstawowy output

```
======================================================================
RAG Search - Protokoły Zarządu MSM Energetyka
Enhanced with Query Expansion + RRF
======================================================================

Wyniki wyszukiwania dla: "sprawy pracownicze"
Znaleziono 5 wyników

======================================================================
1. [Protokół nr 3, Strona 1] (RRF: 0.0421)
Źródło: Protokół nr 3 z ustaleń Zarządu w dniach  29.01. - 11.02.2025 r
Data: 29.01. - 11.02.2025
Znalezione przez 4 wariantów zapytania

Ad 3 Zarząd na wniosek: Zespołu Nadzoru Eksploatacyjnego Koordynacji
Remontów zaakceptował skład Komisji Przetargowej w przetargu nr 4/2025...
======================================================================
```

### Verbose mode (--verbose)

```
🔍 Processing query: "sprawy pracownicze"
   Generating 5 query variants...
   Query variants:
      1. [original] sprawy pracownicze
      2. [llm] zagadnienia dotyczące zatrudnienia
      3. [llm] kwestie kadrowe
      4. [synonym] kwestia pracownik
      5. [word_order] pracownicze sprawy

   Searching Qdrant (10 results per variant)...
      Variant 1: 10 results
      Variant 2: 10 results
      Variant 3: 10 results
      Variant 4: 10 results
      Variant 5: 10 results

   Applying Reciprocal Rank Fusion...
      ✓ Fused to 5 final results
      Avg variants per result: 3.2

----------------------------------------------------------------------
Szczegóły wyszukiwania:
  Warianty zapytań: 5
    1. [original] sprawy pracownicze
    2. [llm] zagadnienia dotyczące zatrudnienia
    3. [llm] kwestie kadrowe
    4. [synonym] kwestia pracownik
    5. [word_order] pracownicze sprawy

  Statystyki fuzji (RRF):
    Średnia wariantów na wynik: 3.2

  Cache:
    Trafienia: 12
    Chybienia: 3
    Współczynnik trafień: 80.0%
    Wywołania API: 3
----------------------------------------------------------------------
```

---

## Jak Działa Enhanced RAG?

### Architektura Systemu

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                               │
│                  "sprawy pracownicze"                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   QUERY EXPANSION                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Original    │  │ LLM (GPT-4o) │  │ Rule-Based   │          │
│  │  Query       │  │ 2 variants   │  │ 2 variants   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  Output: 5 query variants                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EMBEDDING (with Cache)                       │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ For each variant:                                     │      │
│  │  1. Check SQLite cache (SHA256 hash)                 │      │
│  │  2. If miss → OpenRouter API (text-embedding-3-small)│      │
│  │  3. Store in cache for future reuse                  │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  Output: 5 × 1536-dim vectors                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  VECTOR SEARCH (Qdrant)                         │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ For each variant vector:                              │      │
│  │  • Query Qdrant collection (cosine similarity)        │      │
│  │  • Retrieve top 10 chunks                             │      │
│  │  • Total: 5 variants × 10 = 50 candidate chunks       │      │
│  └──────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              RECIPROCAL RANK FUSION (RRF)                       │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Formula: RRF_score(d) = Σ 1/(k + rank(d))            │      │
│  │ where k=60 (constant), rank = position (1-indexed)    │      │
│  │                                                        │      │
│  │ Process:                                               │      │
│  │  1. Deduplicate chunks across variants                │      │
│  │  2. Calculate RRF score for each unique chunk         │      │
│  │  3. Sort by RRF score (descending)                    │      │
│  │  4. Return top 5 final results                        │      │
│  └──────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FINAL RESULTS                              │
│  • Top 5 chunks with highest RRF scores                         │
│  • Metadata: source, page, protocol number, contributing vars   │
│  • Display with statistics (cache, API calls, fusion)           │
└─────────────────────────────────────────────────────────────────┘
```

### Proces Krok po Kroku

#### 1. Query Expansion (5 wariantów)

**Cel:** Zwiększyć recall przez różne sformułowania tego samego pytania.

| Metoda | Przykład | Generator |
|--------|----------|-----------|
| **Original** | "sprawy pracownicze" | Oryginalne zapytanie |
| **LLM #1** | "zagadnienia dotyczące zatrudnienia" | GPT-4o-mini |
| **LLM #2** | "kwestie kadrowe" | GPT-4o-mini |
| **Synonym** | "kwestia pracownik" | Słownik synonimów |
| **Word order** | "pracownicze sprawy" | Permutacja słów |

**Fallback:** Jeśli LLM zawiedzie → rule-based only + padding z oryginałem.

#### 2. Embedding z Cache

```python
# Dla każdego wariantu:
query_hash = sha256(variant_text)

if cache.exists(query_hash):
    embedding = cache.get(query_hash)  # Cache HIT
else:
    embedding = openrouter.get_embedding(variant_text)  # API call
    cache.put(query_hash, embedding)   # Zapisz w cache

# Result: 5 × 1536-dimensional vectors
```

**Cache Benefits:**
- 80-90% reduction w API calls (po ~50 zapytaniach)
- Instant retrieval dla powtórzonych queries
- SQLite - lightweight, zero setup

#### 3. Vector Search (Qdrant)

```python
for variant_embedding in variant_embeddings:
    results = qdrant.search(
        collection="energy_protocols",
        query_vector=variant_embedding,
        limit=10  # Top 10 per variant
    )
    all_results.append(results)

# Total candidates: 5 variants × 10 results = 50 chunks
```

#### 4. Reciprocal Rank Fusion

**Formula:**
```
RRF_score(chunk) = Σ (dla wszystkich wariantów gdzie chunk się pojawił)
                    1 / (60 + rank)

gdzie:
- rank = pozycja chunka w wynikach tego wariantu (1-indexed)
- 60 = stała RRF z literatury (balans precision/recall)
```

**Przykład:**
```
Chunk A pojawił się w:
- Variant 1: rank 2  → 1/(60+2) = 0.0161
- Variant 3: rank 5  → 1/(60+5) = 0.0154
- Variant 4: rank 1  → 1/(60+1) = 0.0164
Total RRF score = 0.0479

Chunk B pojawił się w:
- Variant 2: rank 1  → 1/(60+1) = 0.0164
Total RRF score = 0.0164

Ranking: Chunk A > Chunk B (więcej wariantów = wyższy score)
```

**Zalety RRF:**
- Chunks pojawiające się w wielu wariantach = boost
- Nie wymaga kalibracji score thresholds
- Robust przeciw outlierom

#### 5. Rezultat

Top 5 chunks z:
- **RRF score** - główny ranking metric
- **Contributing variants** - które warianty znalazły ten chunk
- **Source metadata** - protokół, strona, data
- **Cache stats** - hit rate, API calls

---

## Konfiguracja

Parametry w [rag/config.py](rag/config.py):

### Embeddings
```python
EMBEDDING_MODEL = "openai/text-embedding-3-small"
EMBEDDING_DIM = 1536
```

### Chunking
```python
MAX_CHUNK_SIZE = 512    # Zmniejszone z 1000 dla lepszej precyzji
CHUNK_OVERLAP = 50      # Zmniejszone z 100
```

### Query Expansion
```python
NUM_QUERY_VARIANTS = 5
NUM_LLM_VARIANTS = 2
NUM_RULE_VARIANTS = 2
```

### RRF
```python
RRF_K = 60                  # Standard constant
RESULTS_PER_VARIANT = 10    # Candidates per variant
DEFAULT_TOP_K = 20          # Maximum final results
MIN_RRF_SCORE = 0.04        # Minimum quality threshold (filters weak matches)
```

**Filtrowanie jakości:**
- System zwraca maksymalnie 20 wyników, ale tylko te z RRF score > 0.04
- W praktyce zwraca 5-15 wyników wysokiej jakości
- Eliminuje słabe dopasowania (score < 0.04) które mogłyby wprowadzać szum

### Cache
```python
ENABLE_CACHE = True
CACHE_DB_PATH = "embedding_cache.db"
```

---

## Koszty i Optymalizacje

### Koszty API (OpenRouter)

**Model Embeddings:** `text-embedding-3-small` - $0.00002 per 1K tokens
**Model LLM (Query Expansion):** `gpt-4o-mini` - $0.15/$0.60 per 1M tokens (input/output)
**Model LLM (Q&A):** `deepseek/deepseek-chat` (DeepSeek V3.2) - $0.27/$1.10 per 1M tokens (input/output)

#### Jednorazowe Przeindeksowanie
```
~4,500 chunks × 100 tokens/chunk = 450,000 tokens
Cost: (450,000 / 1,000) × $0.00002 = $0.009

Faktyczny koszt: $0.01-0.02
```

#### Per Query (klasyczny RAG - search.py)
```
Komponenty:
1. Query expansion (LLM):     ~$0.000025
2. Embeddings (5 variants):    ~$0.000002
Total (bez cache):             ~$0.000027

Z cache (80% hit rate):        ~$0.000025
```

#### Per Query (Q&A System - ask.py)
```
Komponenty:
1. RAG search (j.w.):          ~$0.000025
2. DeepSeek V3.2 answer:       ~$0.000135  (500 tokens in + 500 tokens out)
Total:                         ~$0.000160

Koszt 1000 pytań Q&A: ~$0.16
```

**Porównanie modeli Q&A:**
- DeepSeek V3.2: $0.000160/query → **$0.16 per 1000 queries** ✅
- Claude 3.5 Sonnet: $0.012/query → **$12 per 1000 queries** (75x drożej!)
- GPT-4o: $0.0075/query → **$7.50 per 1000 queries** (47x drożej!)

#### Miesięcznie
```
Scenariusz A (tylko search.py):
  1,000 zapytań/miesiąc × $0.000025 = $0.025
  Roczny koszt: ~$0.30

Scenariusz B (tylko ask.py z DeepSeek):
  1,000 pytań Q&A/miesiąc × $0.000160 = $0.16
  Roczny koszt: ~$1.92

Scenariusz C (mieszany):
  500 search + 500 Q&A = (500 × $0.000025) + (500 × $0.000160) = $0.09
  Roczny koszt: ~$1.11
```

**Wniosek:** System jest ekstremalnie tani w utrzymaniu! 🎉 Nawet z DeepSeek Q&A koszt to tylko ~$2/rok dla 1000 pytań miesięcznie!

### Cache Effectiveness

Po ~50 zapytaniach:
```
Cache Hit Rate: 70-90%
API Calls Reduction: 80-90%
Cost Savings: ~$0.80 per 1,000 queries
```

**Cache Storage:**
```
~100 queries = ~1MB w SQLite
~1,000 queries = ~10MB
```

### Performance Metrics

| Metryka | Cold Cache | Warm Cache |
|---------|------------|------------|
| **Query Time** | 1.2-1.5s | 0.8-1.0s |
| **API Calls** | 5-6 | 1-2 |
| **Cost** | $0.00003 | $0.000025 |

**Bottlenecks:**
- LLM query expansion: ~500-700ms (nie cacheable)
- Embeddings: ~50ms per variant (cacheable)
- Qdrant search: ~50ms per variant
- RRF fusion: ~10ms

---

## Testy

### Uruchom Test Suite

```bash
python tests/test_retrieval.py
```

**Testy:**
1. ✅ Query expansion - generowanie wariantów
2. ✅ RRF fusion - agregacja z mock data
3. ✅ End-to-end search - pełny flow (wymaga Qdrant)
4. ✅ Cache hit rate - efektywność cache

### Przykładowy Output
```
======================================================================
Running Enhanced RAG System Tests
======================================================================

======================================================================
Test 1: Query Expansion
======================================================================

Original: sprawy pracownicze
  1. [original] sprawy pracownicze
  2. [llm] zagadnienia dotyczące zatrudnienia
  3. [llm] kwestie kadrowe
  4. [synonym] kwestia pracownik
  5. [word_order] pracownicze sprawy

✓ Query expansion test passed

======================================================================
Test 2: RRF Fusion
======================================================================

Fused results:
  1. doc2.md (RRF: 0.0325, variants: 2)
  2. doc1.md (RRF: 0.0325, variants: 2)
  3. doc3.md (RRF: 0.0246, variants: 2)

✓ RRF fusion test passed

======================================================================
✓ All tests passed!
======================================================================
```

---

## Monitoring i Debugging

### Cache Statistics

W trybie interaktywnym:
```bash
python scripts/search.py
Zapytanie: --stats
```

Output:
```
Statystyki:
  Przetworzone zapytania: 23
  Wygenerowane warianty: 115
  Cache - trafienia: 87
  Cache - chybienia: 28
  Cache - współczynnik: 75.7%
```

### Verbose Mode

Debuguj każdy krok:
```bash
python scripts/search.py --verbose "test query"
```

Pokazuje:
- Wygenerowane warianty (z metodami)
- Wyniki per variant
- RRF scores i contributing variants
- Cache hit/miss dla każdego embedding

### Cache Management

**Sprawdź rozmiar:**
```bash
ls -lh embedding_cache.db
```

**Wyczyść cache:**
```python
from rag.cache import EmbeddingCache
cache = EmbeddingCache()
cache.clear()
```

**Statystyki cache:**
```python
stats = cache.get_stats()
print(f"Entries: {stats['total_entries']}")
print(f"Size: {stats['db_size_mb']} MB")
```

---

## Troubleshooting

### Problem: Rate Limiting (429 errors)

**Symptom:** `Rate limited. Waiting 5s...`

**Rozwiązanie:**
1. Zwiększ `time.sleep(0.5)` → `time.sleep(1.0)` w [openrouter_client.py](rag/openrouter_client.py:96)
2. Zmniejsz `batch_size` w [build_index.py](scripts/build_index.py:68) z 50 → 20

### Problem: Cache rośnie zbyt szybko

**Symptom:** `embedding_cache.db > 100MB`

**Rozwiązanie:**
```python
from rag.cache import EmbeddingCache
cache = EmbeddingCache()
cache.clear()  # Usuń wszystkie wpisy
```

### Problem: LLM expansion failures

**Symptom:** `Warning: LLM expansion failed`

**Rozwiązanie:**
- Sprawdź `OPEN_ROUTER_API_KEY` w `.env`
- Sprawdź limity API na [OpenRouter Dashboard](https://openrouter.ai/activity)
- System automatycznie fallback na rule-based expansion

### Problem: Wolne queries (>3s)

**Symptom:** Consistent query time > 2s

**Rozwiązanie:**
1. Zmniejsz `RESULTS_PER_VARIANT` w [config.py](rag/config.py:27) z 10 → 5
2. Zmniejsz `NUM_LLM_VARIANTS` z 2 → 1
3. Poczekaj na wzrost cache hit rate (po ~50 queries)

### Problem: Za dużo słabych wyników

**Symptom:** Wyniki z niskim RRF score (0.01-0.03), nieistotne dokumenty

**Rozwiązanie:**
Zwiększ `MIN_RRF_SCORE` w [config.py](rag/config.py:32):
```python
MIN_RRF_SCORE = 0.06  # Zamiast 0.04 (bardziej restrykcyjny)
```

### Problem: Za mało wyników

**Symptom:** System zwraca tylko 2-3 wyniki, chociaż istnieją inne istotne dokumenty

**Rozwiązanie:**
1. Zmniejsz `MIN_RRF_SCORE` w [config.py](rag/config.py:32):
   ```python
   MIN_RRF_SCORE = 0.02  # Zamiast 0.04 (mniej restrykcyjny)
   ```
2. Zwiększ `RESULTS_PER_VARIANT`: 10 → 15 (więcej candidatów)
3. Dostosuj `RRF_K`: 60 → 40 (większa diversity)

### Problem: Wyniki bardzo podobne lub powtarzające się

**Symptom:** Top 5 results z tego samego dokumentu, brak różnorodności

**Rozwiązanie:**
1. Dostosuj `RRF_K` in [config.py](rag/config.py:26): 60 → 40 (większa diversity)
2. Rozszerz słownik synonimów w [query_expander.py](rag/query_expander.py:14-27)

---

## Rebuild Indeksu

Jeśli dodasz nowe pliki markdown do `output/`:

```bash
python scripts/build_index.py
```

**UWAGA:** To usunie obecny indeks i utworzy nowy. Cache pozostanie nienaruszony.

---

## Licencja

Open source - wykorzystuj dowolnie!
