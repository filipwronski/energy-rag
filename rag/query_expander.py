"""Hybrid query expansion combining LLM and rule-based methods"""

import re
from typing import List, Dict, Optional


class QueryExpander:
    """
    Hybrid query expansion using LLM paraphrasing and rule-based transformations
    """

    # Extended Polish synonyms dictionary (100+ terms)
    SYNONYMS = {
        # Administrative terms
        "protokół": ["protokół", "uchwała", "dokument", "zapis"],
        "zarząd": ["zarząd", "kierownictwo", "dyrekcja", "rada"],
        "pracownik": ["pracownik", "zatrudniony", "personel", "kadra", "pracobiorca"],
        "komisja": ["komisja", "zespół", "grupa robocza", "komitet"],
        "posiedzenie": ["posiedzenie", "spotkanie", "zebranie", "sesja"],
        "decyzja": ["decyzja", "postanowienie", "rozstrzygnięcie", "werdykt"],
        "wniosek": ["wniosek", "propozycja", "sugestia", "podanie"],
        "zgoda": ["zgoda", "akceptacja", "przyzwolenie", "aprobata"],
        "wybór": ["wybór", "selekcja", "wyłonienie", "desygnacja"],
        "sprawa": ["sprawa", "kwestia", "zagadnienie", "temat"],

        # Construction and maintenance
        "budowa": ["budowa", "konstrukcja", "montaż", "wzniesienie", "budowanie"],
        "remont": ["remont", "naprawa", "modernizacja", "odnowa", "renowacja"],
        "naprawa": ["naprawa", "reperacja", "odnowienie", "poprawka"],
        "wymiana": ["wymiana", "zamiana", "podmiana", "substytucja"],
        "instalacja": ["instalacja", "montaż", "zainstalowanie", "założenie"],
        "konserwacja": ["konserwacja", "utrzymanie", "serwis", "pielęgnacja"],
        "rozbiórka": ["rozbiórka", "demontaż", "rozebranie", "wyburzenie"],
        "izolacja": ["izolacja", "ocieplenie", "zabezpieczenie"],
        "malowanie": ["malowanie", "malatura", "pokrycie farbą"],
        "tynkowanie": ["tynkowanie", "tynk", "otynkowanie"],

        # Building elements
        "dach": ["dach", "pokrycie dachowe", "krycie"],
        "elewacja": ["elewacja", "fasada", "zewnętrzna ściana"],
        "okno": ["okno", "stolarka okienna", "okna"],
        "drzwi": ["drzwi", "stolarka drzwiowa", "drzwi wejściowe"],
        "balkon": ["balkon", "taras", "loggia"],
        "klatka": ["klatka", "klatka schodowa", "korytarz"],
        "piwnica": ["piwnica", "pom. piwniczne", "suterena"],
        "strych": ["strych", "poddasze", "loft"],
        "garaż": ["garaż", "miejsce postojowe", "parking"],
        "parking": ["parking", "miejsca parkingowe", "parkomat"],

        # Infrastructure and systems
        "winda": ["winda", "dźwing", "wind"],
        "ogrzewanie": ["ogrzewanie", "c.o.", "centralne ogrzewanie", "grzanie"],
        "wentylacja": ["wentylacja", "wywiew", "wentylator"],
        "kanalizacja": ["kanalizacja", "odpływ", "ściek"],
        "woda": ["woda", "wodociąg", "instalacja wodna"],
        "prąd": ["prąd", "energia elektryczna", "instalacja elektryczna", "elektryka"],
        "gaz": ["gaz", "instalacja gazowa", "gazu"],
        "domofon": ["domofon", "cyfral", "domofonowy"],
        "antena": ["antena", "telewizja kablowa", "sat"],
        "internet": ["internet", "sieć", "łącze internetowe"],

        # Financial terms
        "inwestycja": ["inwestycja", "nakład", "wydatek kapitałowy", "inwestowanie"],
        "koszt": ["koszt", "wydatek", "nakład finansowy", "kwota"],
        "budżet": ["budżet", "plan finansowy", "preliminarz"],
        "dotacja": ["dotacja", "dofinansowanie", "wsparcie finansowe", "grant"],
        "opłata": ["opłata", "należność", "czynsz", "składka"],
        "faktura": ["faktura", "rachunek", "fakturę"],
        "zaliczka": ["zaliczka", "przedpłata", "zadatek"],
        "rozliczenie": ["rozliczenie", "bilans", "podsumowanie finansowe"],
        "kara": ["kara", "penalizacja", "sankcja", "grzywna"],
        "refundacja": ["refundacja", "zwrot kosztów", "zwrot"],

        # Procurement and contracts
        "przetarg": ["przetarg", "konkurs", "postępowanie przetargowe", "tender"],
        "umowa": ["umowa", "kontrakt", "porozumienie", "ugoda"],
        "oferta": ["oferta", "propozycja handlowa", "ofertę"],
        "wykonawca": ["wykonawca", "kontrahent", "firma", "dostawca"],
        "zlecenie": ["zlecenie", "zamówienie", "zadanie"],
        "dostawa": ["dostawa", "transport", "przesyłka"],
        "materiał": ["materiał", "surowiec", "towar"],
        "usługa": ["usługa", "świadczenie", "serwis"],

        # Administrative entities
        "spółdzielnia": ["spółdzielnia", "współnota", "spółdzielni"],
        "wspólnota": ["wspólnota", "właściciele", "wspólnoty"],
        "mieszkańcy": ["mieszkańcy", "lokatorzy", "najemcy", "mieszkaniec"],
        "osiedle": ["osiedle", "zespół mieszkaniowy", "zespół budynków"],
        "budynek": ["budynek", "blok", "kamienica", "dom"],
        "lokal": ["lokal", "mieszkanie", "lokal mieszkalny"],
        "właściciel": ["właściciel", "posiadacz", "gospodarz"],

        # Legal and documentation
        "regulamin": ["regulamin", "przepisy", "zasady"],
        "statut": ["statut", "reguły organizacyjne", "statutu"],
        "zezwolenie": ["zezwolenie", "pozwolenie", "zgoda administracyjna"],
        "pozwolenie": ["pozwolenie", "zezwolenie", "licencja"],
        "zaświadczenie": ["zaświadczenie", "certyfikat", "dokument potwierdzający"],
        "pełnomocnictwo": ["pełnomocnictwo", "upoważnienie", "mandat"],
        "odpowiedzialność": ["odpowiedzialność", "zobowiązanie", "liability"],

        # Time-related
        "termin": ["termin", "deadline", "data", "termin wykonania"],
        "harmonogram": ["harmonogram", "plan", "schedule", "grafik"],
        "okres": ["okres", "czas trwania", "przedział czasowy"],
        "data": ["data", "dzień", "termin"],

        # Actions
        "wykonanie": ["wykonanie", "realizacja", "implementacja", "przeprowadzenie"],
        "rozpoczęcie": ["rozpoczęcie", "start", "inicjacja", "otwarcie"],
        "zakończenie": ["zakończenie", "finalizacja", "zakończona", "zamknięcie"],
        "przegląd": ["przegląd", "kontrola", "inspekcja", "sprawdzenie"],
        "ocena": ["ocena", "ewaluacja", "oszacowanie"],
        "przyjęcie": ["przyjęcie", "akceptacja", "zatwierdzenie"],
        "odrzucenie": ["odrzucenie", "odmowa", "negacja"],

        # Other common terms
        "problem": ["problem", "kwestia", "trudność", "issue"],
        "rozwiązanie": ["rozwiązanie", "solucja", "wyjście"],
        "informacja": ["informacja", "komunikat", "wiadomość"],
        "zgłoszenie": ["zgłoszenie", "raport", "doniesienie"],
        "awaria": ["awaria", "usterka", "defekt", "failure"],
        "bezpieczeństwo": ["bezpieczeństwo", "ochrona", "zabezpieczenie", "safety"],
        "jakość": ["jakość", "standard", "poziom", "quality"],
        "dostępność": ["dostępność", "availability", "osiągalność"]
    }

    # Polish abbreviations and their expansions
    ABBREVIATIONS = {
        # Organizations
        "zo": "zarząd osiedla",
        "msm": "międzyzakładowa spółdzielnia mieszkaniowa",
        "sm": "spółdzielnia mieszkaniowa",
        "tbs": "towarzystwo budownictwa społecznego",
        "wspólnota": "wspólnota mieszkaniowa",

        # Technical systems
        "c.o.": "centralne ogrzezanie",
        "co": "centralne ogrzezanie",
        "c.w.u.": "centralna woda użytkowa",
        "cwu": "centralna woda użytkowa",
        "inst.": "instalacja",
        "wod-kan": "wodociągowo-kanalizacyjna",

        # Building elements
        "pom.": "pomieszczenie",
        "kl.": "klatka",
        "lok.": "lokal",
        "m.": "metr",
        "m2": "metr kwadratowy",
        "mkw": "metr kwadratowy",

        # Financial
        "zł": "złotych",
        "tys.": "tysiące",
        "mln": "milion",
        "vat": "podatek vat",
        "netto": "wartość netto",
        "brutto": "wartość brutto",

        # Administrative
        "nr": "numer",
        "pkt": "punkt",
        "str.": "strona",
        "ul.": "ulica",
        "os.": "osiedle",
        "godz.": "godzina",
        "r.": "rok",
        "art.": "artykuł",
        "par.": "paragraf",
        "ust.": "ustęp",

        # Other
        "np.": "na przykład",
        "tj.": "to jest",
        "tzn.": "to znaczy",
        "itd.": "i tak dalej",
        "itp.": "i tym podobne",
        "tzw.": "tak zwany",
        "m.in.": "między innymi",
        "n/w": "niżej wymieniony",
        "ww.": "wyżej wymieniony",
        "p.o.": "pełniący obowiązki"
    }

    def __init__(self, openrouter_client):
        """
        Initialize query expander

        Args:
            openrouter_client: OpenRouterClient instance for LLM-based expansion
        """
        self.client = openrouter_client
        self._spacy_model = None  # Lazy load spaCy model

    def expand_with_synonyms(self, query: str) -> str:
        """
        Generate query variant by replacing words with synonyms

        Args:
            query: Original query text

        Returns:
            Query variant with synonym substitutions
        """
        words = query.lower().split()
        expanded_words = []

        for word in words:
            # Clean punctuation
            clean_word = re.sub(r'[^\w\s]', '', word)

            # Find synonyms
            replaced = False
            for key, synonyms in self.SYNONYMS.items():
                if clean_word in synonyms and key != clean_word:
                    # Use a different synonym from the list
                    for syn in synonyms:
                        if syn != clean_word:
                            expanded_words.append(syn)
                            replaced = True
                            break
                    break

            if not replaced:
                expanded_words.append(word)

        return " ".join(expanded_words)

    def expand_abbreviations(self, query: str) -> str:
        """
        Expand abbreviations in the query

        Args:
            query: Original query text

        Returns:
            Query with abbreviations expanded
        """
        expanded = query.lower()

        # Sort abbreviations by length (longest first) to avoid partial matches
        sorted_abbrevs = sorted(self.ABBREVIATIONS.items(), key=lambda x: len(x[0]), reverse=True)

        for abbrev, full_form in sorted_abbrevs:
            # For abbreviations with dots, match with optional spaces
            if '.' in abbrev:
                # Replace dots with flexible pattern that allows optional spaces
                pattern = re.escape(abbrev).replace(r'\\.', r'\\.?\s*')
                pattern = r'(?:^|\s)(' + pattern + r')(?:\s|$)'
                expanded = re.sub(pattern, f' {full_form} ', expanded, flags=re.IGNORECASE)
            else:
                # Match abbreviation as whole word (with word boundaries)
                pattern = r'\b' + re.escape(abbrev) + r'\b'
                expanded = re.sub(pattern, full_form, expanded, flags=re.IGNORECASE)

        # Clean up extra spaces
        expanded = re.sub(r'\s+', ' ', expanded).strip()

        return expanded

    def lemmatize_polish(self, query: str) -> Optional[str]:
        """
        Lemmatize Polish text using spaCy

        Args:
            query: Original query text

        Returns:
            Lemmatized query or None if spaCy not available
        """
        try:
            # Lazy load spaCy model
            if self._spacy_model is None:
                import spacy
                self._spacy_model = spacy.load("pl_core_news_sm")

            doc = self._spacy_model(query)
            lemmas = [token.lemma_ for token in doc]
            return " ".join(lemmas)
        except (ImportError, OSError):
            # spaCy not installed or model not available
            return None

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract named entities from query (addresses, amounts, protocol numbers)

        Args:
            query: Query text

        Returns:
            Dictionary with entity types and their values
        """
        entities = {
            "protocol_numbers": [],
            "amounts": [],
            "addresses": [],
            "dates": []
        }

        # Protocol numbers: "protokół nr 15", "nr 15/2024"
        protocol_matches = re.finditer(r'(?:protokół\s+)?nr\s*(\d+(?:/\d{4})?)', query, re.IGNORECASE)
        entities["protocol_numbers"] = [m.group(1) for m in protocol_matches]

        # Amounts: "50 000 zł", "50000zł", "50 tys. zł"
        amount_matches = re.finditer(r'(\d+[\s\u00A0]*(?:\d{3}[\s\u00A0]*)*(?:tys\.?|mln)?)\s*(?:zł|złotych)', query, re.IGNORECASE)
        entities["amounts"] = [m.group(1) for m in amount_matches]

        # Addresses: "Bonifacego 66", "ul. Bonifacego 66"
        address_matches = re.finditer(r'(?:ul\.\s*)?([A-ZŁĄĆĘŃÓŚŹŻ][a-złąćęńóśźż]+(?:\s+[A-ZŁĄĆĘŃÓŚŹŻ][a-złąćęńóśźż]+)*)\s+(\d+[a-z]?)', query)
        entities["addresses"] = [f"{m.group(1)} {m.group(2)}" for m in address_matches]

        # Dates: "29.01.2025", "29.01. - 11.02.2025"
        date_matches = re.finditer(r'\d{2}\.\d{2}\.(?:\d{4})?(?:\s*-\s*\d{2}\.\d{2}\.\d{4})?', query)
        entities["dates"] = [m.group(0) for m in date_matches]

        return entities

    def expand_with_word_order(self, query: str) -> str:
        """
        Generate query variant by reordering words

        Args:
            query: Original query text

        Returns:
            Query variant with reordered words
        """
        # Split by common Polish conjunctions and prepositions
        parts = re.split(r'(\s+(?:i|oraz|w|z|o|na|do|dla|przez|pod|nad)\s+)', query, flags=re.IGNORECASE)

        # If we have multiple parts, try reversing main parts
        if len(parts) > 1:
            # Separate main parts from separators
            main_parts = [parts[i] for i in range(0, len(parts), 2)]
            separators = [parts[i] for i in range(1, len(parts), 2)]

            if len(main_parts) > 1:
                main_parts.reverse()

                # Reconstruct with separators
                result = []
                for i, part in enumerate(main_parts):
                    result.append(part)
                    if i < len(separators):
                        result.append(separators[i])

                return "".join(result)

        # Fallback: simple word reversal for short queries
        words = query.split()
        if len(words) > 2:
            return " ".join(reversed(words))

        return query

    def expand_hybrid(self, query: str, num_variants: int = 5) -> List[Dict[str, str]]:
        """
        Generate hybrid query variants combining LLM and rule-based methods

        Args:
            query: Original search query
            num_variants: Total number of variants to generate (default: 5)

        Returns:
            List of variant dictionaries with 'text' and 'method' keys
        """
        from .config import USE_ABBREVIATION_EXPANSION, USE_LEMMATIZATION

        variants = []

        # 1. Original query (always included)
        variants.append({
            "text": query,
            "method": "original"
        })

        # 2. Abbreviation expansion (if enabled)
        if USE_ABBREVIATION_EXPANSION and len(variants) < num_variants:
            abbrev_variant = self.expand_abbreviations(query)
            if abbrev_variant != query.lower() and abbrev_variant not in [v["text"] for v in variants]:
                variants.append({
                    "text": abbrev_variant,
                    "method": "abbreviation"
                })

        # 3. Lemmatization (if enabled)
        if USE_LEMMATIZATION and len(variants) < num_variants:
            lemma_variant = self.lemmatize_polish(query)
            if lemma_variant and lemma_variant != query and lemma_variant not in [v["text"] for v in variants]:
                variants.append({
                    "text": lemma_variant,
                    "method": "lemmatization"
                })

        # 4. LLM-based variants (2-3)
        num_llm = min(2, num_variants - len(variants))
        if num_llm > 0:
            try:
                llm_variants = self.client.generate_query_variants(query, num_variants=num_llm)
                for variant in llm_variants:
                    if variant and variant != query:  # Skip empty or duplicate
                        variants.append({
                            "text": variant,
                            "method": "llm"
                        })
            except Exception as e:
                print(f"Warning: LLM expansion failed: {e}")
                # Continue with rule-based only

        # 5. Rule-based variants
        # Synonym variant
        if len(variants) < num_variants:
            synonym_variant = self.expand_with_synonyms(query)
            if synonym_variant != query and synonym_variant not in [v["text"] for v in variants]:
                variants.append({
                    "text": synonym_variant,
                    "method": "synonym"
                })

        # Word order variant
        if len(variants) < num_variants:
            word_order_variant = self.expand_with_word_order(query)
            if word_order_variant != query and word_order_variant not in [v["text"] for v in variants]:
                variants.append({
                    "text": word_order_variant,
                    "method": "word_order"
                })

        # 6. Pad with original query if we don't have enough variants
        while len(variants) < num_variants:
            variants.append({
                "text": query,
                "method": "duplicate_original"
            })

        return variants[:num_variants]
