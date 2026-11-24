import os
import unittest
from parser import NoteParser
from messenger import MessageGenerator
from api import (
    app,
    storage,
    process_notes,
    get_ledger,
    mark_guest_thanked,
    update_estimated_value,
    get_ledger_summary,
    ProcessNotesRequest,
    UpdateValueRequest
)

class TestWeddingGiftBackend(unittest.TestCase):

    def setUp(self):
        # Sample notes directly from the assessment problem statement
        self.raw_notes = [
            "Rahman uncle - dinner set",
            "Shilpi khala + family, envelope",
            "the people from Chittagong - 2 sarees, didnt catch name",
            "big box, no card???"
        ]

    def test_parser(self):
        parsed = NoteParser.parse_notes(self.raw_notes)
        self.assertEqual(len(parsed), 4)

        # 1. Rahman uncle
        self.assertEqual(parsed[0].guest_name, "Rahman Uncle")
        self.assertEqual(parsed[0].gift_description, "dinner set")
        self.assertFalse(parsed[0].is_cash)
        self.assertFalse(parsed[0].is_family)
        self.assertFalse(parsed[0].needs_review)

        # 2. Shilpi khala + family, envelope
        self.assertEqual(parsed[1].guest_name, "Shilpi Khala")
        self.assertTrue(parsed[1].is_family)
        self.assertTrue(parsed[1].is_cash)

        # 3. the people from Chittagong - 2 sarees, didnt catch name
        self.assertIn("sarees", parsed[2].gift_description)
        self.assertTrue(parsed[2].needs_review)

        # 4. big box, no card???
        self.assertEqual(parsed[3].guest_name, "Unknown Guest")
        self.assertTrue(parsed[3].needs_review)

    def test_strict_cash_rule_and_customization(self):
        parsed = NoteParser.parse_notes(self.raw_notes)
        processed = MessageGenerator.batch_generate(parsed)

        # Rule 1: Specific gift mentioned for Rahman uncle
        rahman_msg = processed[0]["thank_you_message"]
        self.assertIn("dinner set", rahman_msg)
        self.assertIn("Dear Rahman Uncle,", rahman_msg)

        # Rule 2: Strict Cash Rule for Shilpi khala
        shilpi_msg = processed[1]["thank_you_message"]
        self.assertIn("Dear Shilpi Khala and family,", shilpi_msg)
        # MUST NEVER mention money/cash amount
        self.assertNotIn("tk", shilpi_msg.lower())
        self.assertNotIn("taka", shilpi_msg.lower())
        self.assertNotIn("$", shilpi_msg)
        self.assertIn("generous blessing", shilpi_msg)

        # Rule 3: Flagged for review for unknown names
        unknown_msg = processed[3]["thank_you_message"]
        self.assertIn("ATTENTION: Please verify guest details", unknown_msg)

    def test_api_workflow(self):
        # 1. Process notes via API handler
        req = ProcessNotesRequest(notes=self.raw_notes)
        created = process_notes(req)
        self.assertEqual(len(created), 4)
        entry_id = created[0]["id"]

        # 2. Query ledger
        ledger = get_ledger()
        self.assertGreaterEqual(len(ledger), 4)

        # 3. Mark as thanked
        thanked_entry = mark_guest_thanked(entry_id)
        self.assertTrue(thanked_entry["thanked"])

        # 4. Update mother's recalled value for reciprocity
        updated_val_entry = update_estimated_value(entry_id, UpdateValueRequest(estimated_value=5000.0))
        self.assertEqual(updated_val_entry["estimated_value"], 5000.0)

        # 5. Summary statistics
        summary = get_ledger_summary()
        self.assertGreaterEqual(summary["total_gifts"], 4)
        self.assertGreaterEqual(summary["thanked_count"], 1)
        self.assertGreaterEqual(summary["total_estimated_value"], 5000.0)

if __name__ == "__main__":
    unittest.main()
