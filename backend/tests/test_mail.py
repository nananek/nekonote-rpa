"""Tests for nekonote.mail (mocked SMTP/IMAP)."""

from unittest.mock import patch, MagicMock

from nekonote import mail


class TestSend:
    @patch("nekonote.mail.smtplib.SMTP")
    def test_send_basic(self, MockSMTP):
        mock_srv = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_srv)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        mail.send(
            to=["test@example.com"],
            subject="Test",
            body="Hello",
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="user@test.com",
            password="pass",
        )
        mock_srv.starttls.assert_called_once()
        mock_srv.login.assert_called_once_with("user@test.com", "pass")
        mock_srv.sendmail.assert_called_once()

    @patch("nekonote.mail.smtplib.SMTP")
    def test_send_with_cc(self, MockSMTP):
        mock_srv = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_srv)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        mail.send(
            to=["a@b.com"],
            cc=["c@d.com"],
            subject="CC test",
            body="hi",
            username="u",
            password="p",
        )
        call_args = mock_srv.sendmail.call_args
        recipients = call_args[0][1]
        assert "a@b.com" in recipients
        assert "c@d.com" in recipients


class TestReceive:
    @patch("nekonote.mail.imaplib.IMAP4_SSL")
    def test_receive_basic(self, MockIMAP):
        mock_conn = MagicMock()
        MockIMAP.return_value = mock_conn
        mock_conn.search.return_value = ("OK", [b"1 2"])

        # Build a minimal email
        from email.mime.text import MIMEText
        msg = MIMEText("Hello body", "plain", "utf-8")
        msg["Subject"] = "Test Subject"
        msg["From"] = "sender@test.com"
        msg["Date"] = "Mon, 1 Jan 2024 00:00:00 +0000"

        mock_conn.fetch.return_value = ("OK", [(b"1", msg.as_bytes())])

        messages = mail.receive(
            imap_server="imap.test.com",
            username="u",
            password="p",
            limit=2,
        )
        assert len(messages) == 2
        assert messages[0]["subject"] == "Test Subject"
        assert "Hello body" in messages[0]["body"]
