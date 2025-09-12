import os

from src.parser.mailbox_processor import process_mailbox
from src.utils.email_utils import (decode_text, get_email_date,
                                   sanitize_filename)


def test_utils_basic():
    assert decode_text('=?utf-8?b?VGVzdA==?=') == 'Test'
    assert sanitize_filename('bad:/name?*') == 'badname'


def test_process_mailbox_empty(tmp_path):
    mbox = tmp_path / 'test.mbox'
    mbox.write_text('', encoding='utf-8')

    # empty mbox should not raise FileNotFoundError but return []
    threads = process_mailbox(str(mbox), str(tmp_path))
    assert isinstance(threads, list)
