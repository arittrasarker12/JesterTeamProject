# Backend Module - The Wedding Gift Ledger

This module implements the core business logic, handwritten notes parsing, culturally sensitive thank-you message generation, and REST API for Farhana's family wedding gift ledger.

## Features
1. **Raw Notes Parsing (`parser.py`)**:
   - Parses haphazard raw notes (e.g., `"Rahman uncle - dinner set"`, `"Shilpi khala + family, envelope"`, `"the people from Chittagong - 2 sarees, didnt catch name"`, `"big box, no card???"`).
   - Extracts: Guest name, family indicator, gift description, cash indicator, and flags ambiguous entries for manual verification.

2. **Thank-You Message Generator (`messenger.py`)**:
   - Mentions specific gift items (e.g. dinner set, 2 sarees).
   - **STRICT CASH RULE**: Never mentions any cash figure or amount in the message. Expresses gratitude for warm presence and generous blessings.
   - Addresses families jointly if `+ family` is detected.
   - Flags uncertain gifts with `[ATTENTION: Please verify guest details before sending]` for human review.

3. **REST API & Storage (`api.py`)**:
   - `POST /api/notes/process`: Ingests raw notes and returns structured, message-generated records.
   - `GET /api/ledger`: Lists all ledger entries. Supports `?thanked=true|false`.
   - `PATCH /api/ledger/{id}/thank`: Marks a guest as thanked.
   - `PATCH /api/ledger/{id}/value`: Updates mother's recalled cash/gift value for future reciprocity.
   - `GET /api/ledger/summary`: Returns summary statistics.
   - Built-in JSON persistent storage (`ledger_store.json`), allowing standalone execution and seamless replacement by Member 3's Database module.

## How to Run

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the API Server:
```bash
uvicorn api:app --reload --port 8000
```
- Interactive Swagger API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Run Unit Tests:
```bash
python test_backend.py
```
