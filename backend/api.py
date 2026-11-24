import os
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from parser import NoteParser
from messenger import MessageGenerator

app = FastAPI(
    title="The Wedding Gift Ledger",
    description="Backend API for parsing wedding notes, generating thank-you messages, and managing reciprocal gift records.",
    version="1.0.0"
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------
class ProcessNotesRequest(BaseModel):
    notes: List[str]

class UpdateValueRequest(BaseModel):
    estimated_value: float


# ---------------------------------------------------------
# Storage Layer (Standalone Mock with JSON Persistence)
# Seamlessly swappable with Member 3's Database Module
# ---------------------------------------------------------
LEDGER_FILE = os.path.join(os.path.dirname(__file__), "ledger_store.json")

class LedgerStorage:
    def __init__(self):
        self._entries: dict[int, dict] = {}
        self._next_id = 1
        self._load()

    def _load(self):
        if os.path.exists(LEDGER_FILE):
            try:
                with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._entries = {item["id"]: item for item in data}
                    if self._entries:
                        self._next_id = max(self._entries.keys()) + 1
            except Exception:
                self._entries = {}

    def _save(self):
        with open(LEDGER_FILE, "w", encoding="utf-8") as f:
            json.dump(list(self._entries.values()), f, indent=2, ensure_ascii=False)

    def add_entries(self, parsed_records: List[dict]) -> List[dict]:
        created = []
        for rec in parsed_records:
            entry_id = self._next_id
            self._next_id += 1
            
            entry = {
                "id": entry_id,
                "raw_text": rec["raw_text"],
                "guest_name": rec["guest_name"],
                "is_family": rec["is_family"],
                "gift_description": rec["gift_description"],
                "is_cash": rec["is_cash"],
                "estimated_value": None, # Farhana's mother can add this later for reciprocity
                "needs_review": rec["needs_review"],
                "thanked": False,
                "thank_you_message": rec.get("thank_you_message", ""),
                "notes_or_clues": rec.get("notes_or_clues", "")
            }
            self._entries[entry_id] = entry
            created.append(entry)
        self._save()
        return created

    def get_all(self, thanked: Optional[bool] = None) -> List[dict]:
        items = list(self._entries.values())
        if thanked is not None:
            items = [item for item in items if item["thanked"] == thanked]
        return items

    def get_by_id(self, entry_id: int) -> Optional[dict]:
        return self._entries.get(entry_id)

    def mark_thanked(self, entry_id: int) -> Optional[dict]:
        if entry_id not in self._entries:
            return None
        self._entries[entry_id]["thanked"] = True
        self._save()
        return self._entries[entry_id]

    def update_value(self, entry_id: int, value: float) -> Optional[dict]:
        if entry_id not in self._entries:
            return None
        self._entries[entry_id]["estimated_value"] = value
        self._save()
        return self._entries[entry_id]

    def get_summary(self) -> dict:
        items = list(self._entries.values())
        total = len(items)
        thanked_count = sum(1 for i in items if i["thanked"])
        pending_count = total - thanked_count
        total_reciprocal_val = sum(i["estimated_value"] or 0.0 for i in items)
        cash_count = sum(1 for i in items if i["is_cash"])

        return {
            "total_gifts": total,
            "thanked_count": thanked_count,
            "pending_count": pending_count,
            "total_estimated_value": total_reciprocal_val,
            "cash_gifts_count": cash_count
        }

# Initialize storage instance
storage = LedgerStorage()


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "The Wedding Gift Ledger API is running",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.post("/api/notes/process", response_model=List[dict])
def process_notes(payload: ProcessNotesRequest):
    """
    Takes raw handwritten notes, parses them into structured items,
    generates culturally appropriate thank-you messages, and persists to ledger.
    """
    if not payload.notes:
        raise HTTPException(status_code=400, detail="No notes provided")

    # 1. Parse raw notes (Module 1)
    parsed_gifts = NoteParser.parse_notes(payload.notes)

    # 2. Generate personalized thank-you notes (Module 2)
    processed_records = MessageGenerator.batch_generate(parsed_gifts)

    # 3. Save into Ledger Storage (Module 3 adapter)
    created_entries = storage.add_entries(processed_records)
    return created_entries


@app.get("/api/ledger", response_model=List[dict])
def get_ledger(thanked: Optional[bool] = None):
    """
    Retrieves all gift ledger entries. Optional filter: ?thanked=true or ?thanked=false
    """
    is_thanked = thanked if isinstance(thanked, bool) else None
    return storage.get_all(thanked=is_thanked)


@app.get("/api/ledger/summary")
def get_ledger_summary():
    """
    Returns ledger statistics for Farhana's family.
    """
    return storage.get_summary()


@app.patch("/api/ledger/{entry_id}/thank")
def mark_guest_thanked(entry_id: int):
    """
    Marks a guest as thanked after the message is sent.
    """
    updated = storage.mark_thanked(entry_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Gift entry with ID {entry_id} not found")
    return updated


@app.patch("/api/ledger/{entry_id}/value")
def update_estimated_value(entry_id: int, payload: UpdateValueRequest):
    """
    Updates Farhana's mother's recalled cash/gift value for future reciprocal gifting.
    """
    updated = storage.update_value(entry_id, payload.estimated_value)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Gift entry with ID {entry_id} not found")
    return updated


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
