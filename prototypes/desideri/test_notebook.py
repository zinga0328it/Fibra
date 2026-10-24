"""Offline regression tests. No API, Telegram or ChatGPT data is contacted."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from notebook import AuthenticatedPrincipal, WishConflict, WishNotebook, render_private_page


class WishNotebookTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.book = WishNotebook(self.db)
        self.alice = AuthenticatedPrincipal("companyA", "alice")
        self.bob = AuthenticatedPrincipal("companyA", "bob")
        self.other_tenant = AuthenticatedPrincipal("companyB", "alice")

    def add(self, principal=None, **changes):
        args = dict(request_id="turn-001", project_label="Progetto Fibra",
                    title="Calendario per me", description="Mostra le mie WR",
                    source_labels=["specifiche.pdf"])
        args.update(changes)
        return self.book.record(principal or self.alice, **args)

    def test_register_and_read_receipt(self):
        wish = self.add()
        self.assertEqual(wish["status"], "registrato")
        self.assertEqual(wish["source_labels"], ["specifiche.pdf"])
        self.assertEqual(self.book.get_mine(self.alice, wish["id"]), wish)
        self.assertEqual(self.book.history_mine(self.alice, wish["id"])[0]["event_type"], "registrato")

    def test_idempotency_rejects_modified_replay(self):
        original = self.add()
        self.assertEqual(self.add()["id"], original["id"])
        self.assertEqual(len(self.book.history_mine(self.alice, original["id"])), 1)
        with self.assertRaises(WishConflict):
            self.add(title="Something else")

    def test_user_and_tenant_separation(self):
        wish = self.add()
        for stranger in [self.bob, self.other_tenant]:
            self.assertIsNone(self.book.get_mine(stranger, wish["id"]))
            self.assertEqual(self.book.history_mine(stranger, wish["id"]), [])
            self.assertEqual(self.book.list_mine(stranger), [])
        bob_wish = self.add(self.bob)
        self.assertNotEqual(bob_wish["id"], wish["id"])

    def test_html_escapes_content_and_is_scoped(self):
        self.add(title="<script>alert('x')</script>", description="<img src=x onerror=alert(1)>")
        page = render_private_page(self.book, self.alice)
        self.assertNotIn("<script>", page)
        self.assertNotIn("<img", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Nessun desiderio registrato", render_private_page(self.book, self.bob))

    def test_invalid_payload_limits(self):
        with self.assertRaises(ValueError):
            self.add(source_labels=["x"] * 9)
        with self.assertRaises(ValueError):
            self.add(description="")
        with self.assertRaises(ValueError):
            self.book.list_mine(self.alice, limit=10000)
        with self.assertRaises(ValueError):
            self.add(AuthenticatedPrincipal("", "x"))

    def test_sqlite_survives_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "wishes.db"
            first = sqlite3.connect(filename)
            wish = WishNotebook(first).record(self.alice, request_id="persist1", project_label="Progetto",
                                              title="Promemoria", description="Nota per me")
            first.close()
            second = sqlite3.connect(filename)
            book = WishNotebook(second)
            self.assertEqual(book.get_mine(self.alice, wish["id"])["status"], "registrato")
            second.close()


if __name__ == "__main__":
    unittest.main()
