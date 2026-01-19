# PDF to Markdown Converter z OCR

Narzędzie do konwersji zeskanowanych dokumentów PDF (zawierających obrazy) na format Markdown przy użyciu **EasyOCR**.

## Funkcje

- ✅ Konwersja PDF → Markdown
- ✅ OCR dla polskiego i angielskiego
- ✅ Automatyczna detekcja: tekst PDF vs obrazy
- ✅ Bez sudo - tylko pip install!
- ✅ Wysokiej jakości rozpoznawanie tekstu

## Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt
```

**Uwaga:** Pierwsze uruchomienie pobierze modele OCR (~100-200MB).

## Użycie

### Podstawowe użycie

```bash
python pdf_to_markdown_easyocr.py
```

### Jako moduł Python

```python
from pdf_to_markdown_easyocr import PDFToMarkdownConverter

# Stwórz konwerter
converter = PDFToMarkdownConverter(languages=['pl', 'en'])

# Konwertuj PDF
markdown_text = converter.pdf_to_markdown(
    "input/dokument.pdf",
    "output/dokument.md"
)

print(f"Rozpoznano {len(markdown_text)} znaków")
```

## Przykład wyniku

```markdown
# Protokół nr 1 z ustaleń Zarządu w dniach  02.-14.01.2025 r

*Dokument zawiera 3 stron*
*Tekst rozpoznany automatycznie przez OCR*

---

## Strona 1

Protokół nr 1
ustaleń Zarządu MSM "Energetyka"
...
```

## Struktura projektu

```
energy-rag/
├── input/                          # Pliki PDF do konwersji
├── output/                         # Wygenerowane pliki Markdown
│   └── protokol_zarzadu_01_2025.md
├── rag/                           # Moduł RAG (wyszukiwarka)
│   ├── config.py                  # Konfiguracja
│   ├── embedder.py                # Polski model embeddingów
│   ├── chunker.py                 # Parsowanie i dzielenie dokumentów
│   └── retriever.py               # Wyszukiwanie w Qdrant
├── scripts/                       # Skrypty użytkowe
│   ├── build_index.py             # Indeksowanie dokumentów
│   └── search.py                  # CLI wyszukiwarki
├── pdf_to_markdown_easyocr.py     # Główne narzędzie konwersji
├── requirements.txt               # Zależności Python
└── README.md                      # Dokumentacja
```

## Wymagania systemowe

- Python 3.8+
- ~4GB wolnego miejsca (dla PyTorch + modeli OCR)
- Brak wymagań sudo!

## Jak to działa?

1. **PyMuPDF** wyciąga strony z PDF jako obrazy
2. **EasyOCR** rozpoznaje tekst na obrazach (polski + angielski)
3. Wynik formatowany jako Markdown z nagłówkami stron

## Dokładność OCR

- ✅ Czysty druk: ~95-99%
- ✅ Skanowane dokumenty: ~90-95%
- ⚠️ Pisane ręcznie: ~60-80%

## Rozwiązywanie problemów

### Wolne przetwarzanie
- Używamy CPU (brak GPU)
- Pierwsze uruchomienie = pobieranie modeli
- Kolejne uruchomienia będą szybsze

### Błędy OCR
- Sprawdź jakość skanów (min 150 DPI)
- Jasne obrazy z dobrym kontrastem

### Brak pamięci
- Zmniejsz `zoom` w kodzie (linia 89: `zoom = 2` → `zoom = 1.5`)

---

# Wyszukiwarka RAG dla protokołów

System RAG (Retrieval Augmented Generation) do semantycznego wyszukiwania informacji w protokołach zarządu.

## Funkcje RAG

- 🔍 Semantyczne wyszukiwanie w języku polskim
- 📚 Indeksowanie dokumentów markdown z folderu `output/`
- 🎯 Wyświetlanie źródła danych (nazwa pliku, numer protokołu, strona)
- 💾 Baza wektorowa Qdrant
- 🤖 Polski model embeddingów: `sdadas/mmlw-retrieval-roberta-base`

## Szybki start z RAG

### 1. Uruchom Qdrant (Docker)

```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 2. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 3. Zbuduj indeks

```bash
python scripts/build_index.py
```

To przetworzy wszystkie pliki `.md` z folderu `output/`, podzieli je na semantyczne fragmenty i zaindeksuje w Qdrant.

### 4. Wyszukuj informacje

**Tryb single-query:**
```bash
python scripts/search.py "sprawy pracownicze"
python scripts/search.py "wiaty śmietnikowe"
python scripts/search.py "ul. Konstancińska"
```

**Tryb interaktywny:**
```bash
python scripts/search.py
# Zapytanie: Komisja Przetargowa
# Zapytanie: inwestycje budowlane
# Zapytanie: exit
```

## Przykład wyniku wyszukiwania

```
======================================================================
1. [Protokół nr 3, Strona 1] (podobieństwo: 0.87)
Źródło: Protokół nr 3 z ustaleń Zarządu w dniach  29.01. - 11.02.2025 r
Data: 29.01. - 11.02.2025

Ad 3 Zarząd na wniosek: Zespołu Nadzoru Eksploatacyjnego Koordynacji
Remontów zaakceptował skład Komisji Przetargowej w przetargu nr 4/2025...
======================================================================
```

## Konfiguracja RAG

Parametry można dostosować w pliku [rag/config.py](rag/config.py):

- `MAX_CHUNK_SIZE`: Maksymalny rozmiar fragmentu (domyślnie: 1000 znaków)
- `CHUNK_OVERLAP`: Nakładanie między fragmentami (domyślnie: 100 znaków)
- `DEFAULT_TOP_K`: Liczba wyników (domyślnie: 5)
- `MIN_SCORE_THRESHOLD`: Próg podobieństwa (domyślnie: 0.5)

## Jak działa RAG?

1. **Chunking**: Dokumenty dzielone po nagłówkach `## Strona X`, długie sekcje dodatkowo dzielone
2. **Embedding**: Każdy fragment zamieniany na wektor 768-wymiarowy przez polski model
3. **Indexing**: Wektory zapisywane w Qdrant z metadanymi (źródło, numer strony, data)
4. **Search**: Zapytanie użytkownika → wektor → wyszukiwanie najbardziej podobnych fragmentów
5. **Results**: Top 5 wyników z informacją o źródle

## Wymagania systemowe RAG

- Docker (dla Qdrant)
- Python 3.8+
- ~2GB wolnego miejsca (model embeddingów + PyTorch)
- 4GB RAM (dla modelu)

## Rebuild indeksu

Jeśli dodasz nowe pliki markdown do `output/`, po prostu uruchom ponownie:

```bash
python scripts/build_index.py
```

Stary indeks zostanie nadpisany nowym.

---

## Licencja

Open source - wykorzystuj dowolnie!
