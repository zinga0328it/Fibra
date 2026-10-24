"""Offline tests for the Telegram approval protocol. Synthetic data only."""
import unittest

from telegram_passwordless import (
    LoginError, TelegramBinding, TelegramPasswordless,
)


class PasswordlessTests(unittest.TestCase):
    def setUp(self):
        self.flow = TelegramPasswordless("local-test-secret-of-at-least-32-characters")
        self.binding = TelegramBinding("factory", "operator", 321987, 321987)
        self.browser, self.bot = self.flow.start(self.binding, now=1000)

    def confirm(self, *, sender=321987, chat_id=321987, chat_type="private", secret=None,
                callback=None, now=1001):
        return self.flow.callback_from_verified_webhook(
            callback or self.bot.approve_callback,
            header_secret=secret if secret is not None else "local-test-secret-of-at-least-32-characters",
            telegram_user_id=sender, chat_id=chat_id,
            chat_type=chat_type, now=now,
        )

    def assert_code(self, expected, call):
        with self.assertRaises(LoginError) as caught:
            call()
        self.assertEqual(caught.exception.code, expected)

    def test_private_telegram_confirmation_and_single_use(self):
        self.assertEqual(self.flow.browser_status(self.browser.request_id, self.browser.browser_secret, now=1001), "pending")
        self.assert_code("not_approved", lambda: self.flow.redeem(self.browser.request_id, self.browser.browser_secret, now=1001))
        self.assertEqual(self.confirm(), "approved")
        self.assertEqual(self.flow.browser_status(self.browser.request_id, self.browser.browser_secret, now=1002), "approved")
        grant = self.flow.redeem(self.browser.request_id, self.browser.browser_secret, now=1002)
        self.assertEqual((grant.tenant_id, grant.user_id), ("factory", "operator"))
        self.assertEqual(grant.amr, ("telegram_approval",))
        self.assert_code("not_approved", lambda: self.flow.redeem(self.browser.request_id, self.browser.browser_secret, now=1003))
        self.assert_code("already_handled", self.confirm)

    def test_chat_identity_and_webhook_are_verified(self):
        self.assert_code("untrusted_webhook", lambda: self.confirm(secret="fake"))
        self.assert_code("identity_mismatch", lambda: self.confirm(sender=999, chat_id=999))
        self.assert_code("invalid_chat", lambda: self.confirm(chat_type="group"))
        self.assert_code("invalid_chat", lambda: self.confirm(chat_id=-100))
        self.assertEqual(self.flow.browser_status(self.browser.request_id, self.browser.browser_secret, now=1002), "pending")
        self.assertEqual(self.confirm(), "approved")

    def test_token_theft_wrong_browser_secret_and_attempt_limit(self):
        self.confirm()
        for _ in range(3):
            self.assert_code("invalid_browser_proof", lambda: self.flow.redeem(self.browser.request_id, "stolen", now=1002))
        self.assert_code("invalid_browser_proof", lambda: self.flow.redeem(self.browser.request_id, self.browser.browser_secret, now=1002))

    def test_denial_and_expiry(self):
        self.assertEqual(self.confirm(callback=self.bot.deny_callback), "denied")
        self.assert_code("not_approved", lambda: self.flow.redeem(self.browser.request_id, self.browser.browser_secret, now=1002))
        flow = TelegramPasswordless("local-test-secret-of-at-least-32-characters")
        b, bot = flow.start(self.binding, now=1000)
        self.assertEqual(flow.browser_status(b.request_id, b.browser_secret, now=1120), "expired")
        self.assert_code("already_handled", lambda: flow.callback_from_verified_webhook(
            bot.approve_callback, header_secret="local-test-secret-of-at-least-32-characters",
            telegram_user_id=321987, chat_id=321987, chat_type="private", now=1120,
        ))

    def test_new_challenge_revokes_previous(self):
        new, bot = self.flow.start(self.binding, now=1010)
        self.assertNotEqual(self.browser.request_id, new.request_id)
        self.assertEqual(self.flow.browser_status(self.browser.request_id, self.browser.browser_secret, now=1011), "denied")
        self.assertEqual(self.flow.browser_status(new.request_id, new.browser_secret, now=1011), "pending")
        self.assertIn(new.comparison_code, bot.message)
        self.assertNotIn(new.browser_secret, bot.message)
        self.assertLess(len(bot.approve_callback.encode()), 65)

    def test_delivery_failure_and_invalid_binding(self):
        self.flow.cancel_failed_delivery(self.browser.request_id)
        self.assertEqual(self.flow.browser_status(self.browser.request_id, self.browser.browser_secret, now=1001), "denied")
        self.assert_code("invalid_binding", lambda: self.flow.start(
            TelegramBinding("factory", "stranger", 321987, 123), now=1001))
        self.assert_code("invalid_binding", lambda: self.flow.start(
            TelegramBinding("../etc", "stranger", 123, 123), now=1001))

    def test_invalid_webhook_callback_cannot_approve(self):
        self.assert_code("invalid_callback", lambda: self.confirm(callback="anything"))
        self.assertEqual(self.flow.browser_status(self.browser.request_id, self.browser.browser_secret, now=1002), "pending")


if __name__ == "__main__":
    unittest.main()
