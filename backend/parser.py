import re
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ParsedGift:
    raw_text: str
    guest_name: str
    is_family: bool
    gift_description: str
    is_cash: bool
    needs_review: bool
    notes_or_clues: str = ""

    def to_dict(self):
        return asdict(self)


class NoteParser:
    """
    Parses messy, raw handwritten notes from the wedding into structured gift data.
    """

    CASH_KEYWORDS = {"envelope", "cash", "taka", "money", "tk", "salami"}
    UNKNOWN_NAME_KEYWORDS = [
        "didnt catch name", "didn't catch name", "no card", "no name",
        "unknown", "anonymous", "dont know", "don't know", "???"
    ]
    FAMILY_PATTERNS = [
        r"\+\s*family", r"and\s+family", r"&\s*family", r"family", r"poribar"
    ]

    @classmethod
    def parse_single_note(cls, raw_note: str) -> ParsedGift:
        cleaned_note = raw_note.strip().strip('"').strip("'")
        lower_note = cleaned_note.lower()

        is_cash = any(k in lower_note for k in cls.CASH_KEYWORDS)
        
        # Check if review is needed
        needs_review = any(k in lower_note for k in cls.UNKNOWN_NAME_KEYWORDS)
        if "???" in cleaned_note:
            needs_review = True

        # Check family tag
        is_family = any(re.search(pat, lower_note) for pat in cls.FAMILY_PATTERNS)

        # Splitting logic: usually separated by '-', '–', or ','
        parts = []
        if "-" in cleaned_note:
            parts = [p.strip() for p in cleaned_note.split("-", 1)]
        elif "–" in cleaned_note:
            parts = [p.strip() for p in cleaned_note.split("–", 1)]
        elif "," in cleaned_note and not any(k in cleaned_note.lower() for k in ["sarees", "box"]):
            parts = [p.strip() for p in cleaned_note.split(",", 1)]

        guest_name = "Unknown Guest"
        gift_description = cleaned_note
        notes_or_clues = ""

        if len(parts) == 2:
            raw_name_part, raw_gift_part = parts[0], parts[1]

            # Detect if first part has the name or if it's descriptive
            guest_name = raw_name_part
            gift_description = raw_gift_part
        else:
            # When there is no delimiter (e.g. "big box, no card???")
            if any(k in lower_note for k in ["box", "saree", "set", "envelope", "gift"]):
                gift_description = cleaned_note
                guest_name = "Unknown Guest"
                needs_review = True

        # Clean family suffixes from the primary guest name
        for pat in cls.FAMILY_PATTERNS:
            guest_name = re.sub(pat, "", guest_name, flags=re.IGNORECASE).strip(" +&,")

        # Detect and extract notes/clues (like "didnt catch name", "no card???")
        for k in cls.UNKNOWN_NAME_KEYWORDS:
            if k in gift_description.lower():
                notes_or_clues += f" [{k}]"
                # Strip clue from actual gift description
                gift_description = re.sub(re.escape(k), "", gift_description, flags=re.IGNORECASE).strip(" ,-?")

        if "unknown" in guest_name.lower() or not guest_name or needs_review and guest_name == cleaned_note:
            guest_name = "Unknown Guest"

        # Final cleanup
        gift_description = gift_description.strip(" ,.-?")
        if is_cash and not gift_description:
            gift_description = "Cash envelope"

        return ParsedGift(
            raw_text=cleaned_note,
            guest_name=guest_name.title() if guest_name != "Unknown Guest" else "Unknown Guest",
            is_family=is_family,
            gift_description=gift_description if gift_description else "Gift",
            is_cash=is_cash,
            needs_review=needs_review,
            notes_or_clues=notes_or_clues.strip()
        )

    @classmethod
    def parse_notes(cls, raw_notes: list[str]) -> list[ParsedGift]:
        return [cls.parse_single_note(note) for note in raw_notes if note.strip()]
