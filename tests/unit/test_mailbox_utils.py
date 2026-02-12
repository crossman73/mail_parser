"""Unit tests for mailbox_utils module."""

import mailbox
import os
import tempfile
from datetime import datetime
from email.message import Message

import pytest


class TestProcessMailbox:
    """Tests for process_mailbox function."""

    def test_file_not_found_raises_error(self):
        """Should raise FileNotFoundError for missing file."""
        from src.mail_parser.mailbox_utils import process_mailbox

        with pytest.raises(FileNotFoundError):
            process_mailbox("/nonexistent/path.mbox")

    def test_empty_mailbox_returns_empty_list(self):
        """Empty mbox should return empty thread list."""
        from src.mail_parser.mailbox_utils import process_mailbox

        with tempfile.NamedTemporaryFile(suffix=".mbox", delete=False) as f:
            mbox_path = f.name

        try:
            mbox = mailbox.mbox(mbox_path)
            mbox.close()

            result = process_mailbox(mbox_path)
            assert result == []
        finally:
            os.unlink(mbox_path)

    def test_single_message_creates_single_thread(self):
        """Single message should create one thread."""
        from src.mail_parser.mailbox_utils import process_mailbox

        with tempfile.NamedTemporaryFile(suffix=".mbox", delete=False) as f:
            mbox_path = f.name

        try:
            mbox = mailbox.mbox(mbox_path)

            msg = Message()
            msg["Message-ID"] = "<msg1@example.com>"
            msg["From"] = "sender@example.com"
            msg["Subject"] = "Test"
            msg["Date"] = "Thu, 06 Feb 2026 10:00:00 +0000"
            msg.set_payload("Hello")
            mbox.add(msg)
            mbox.close()

            result = process_mailbox(mbox_path)
            assert len(result) == 1
            assert len(result[0]) == 1
            assert result[0][0]["Message-ID"] == "<msg1@example.com>"
        finally:
            os.unlink(mbox_path)

    def test_reply_grouped_with_parent(self):
        """Reply message should be grouped with parent."""
        from src.mail_parser.mailbox_utils import process_mailbox

        with tempfile.NamedTemporaryFile(suffix=".mbox", delete=False) as f:
            mbox_path = f.name

        try:
            mbox = mailbox.mbox(mbox_path)

            # Parent message
            parent = Message()
            parent["Message-ID"] = "<parent@example.com>"
            parent["From"] = "a@example.com"
            parent["Subject"] = "Original"
            parent["Date"] = "Thu, 06 Feb 2026 10:00:00 +0000"
            parent.set_payload("Parent")
            mbox.add(parent)

            # Reply message
            reply = Message()
            reply["Message-ID"] = "<reply@example.com>"
            reply["From"] = "b@example.com"
            reply["Subject"] = "Re: Original"
            reply["Date"] = "Thu, 06 Feb 2026 11:00:00 +0000"
            reply["In-Reply-To"] = "<parent@example.com>"
            reply.set_payload("Reply")
            mbox.add(reply)

            mbox.close()

            result = process_mailbox(mbox_path)
            # Should be one thread with two messages
            assert len(result) == 1
            assert len(result[0]) == 2
        finally:
            os.unlink(mbox_path)

    def test_messages_without_id_skipped(self):
        """Messages without Message-ID should be skipped."""
        from src.mail_parser.mailbox_utils import process_mailbox

        with tempfile.NamedTemporaryFile(suffix=".mbox", delete=False) as f:
            mbox_path = f.name

        try:
            mbox = mailbox.mbox(mbox_path)

            # Message without ID
            msg1 = Message()
            msg1["From"] = "a@example.com"
            msg1["Subject"] = "No ID"
            msg1.set_payload("No ID")
            mbox.add(msg1)

            # Message with ID
            msg2 = Message()
            msg2["Message-ID"] = "<valid@example.com>"
            msg2["From"] = "b@example.com"
            msg2["Subject"] = "Has ID"
            msg2["Date"] = "Thu, 06 Feb 2026 10:00:00 +0000"
            msg2.set_payload("Has ID")
            mbox.add(msg2)

            mbox.close()

            result = process_mailbox(mbox_path)
            # Only one thread (the one with ID)
            assert len(result) == 1
            assert result[0][0]["Message-ID"] == "<valid@example.com>"
        finally:
            os.unlink(mbox_path)
