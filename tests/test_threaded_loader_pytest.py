import json
import sys
from pathlib import Path

from src.mail_parser.processor import EmailEvidenceProcessor

CONFIG_TMP = 'config.threaded.json'


def setup_module(module):
    cfg = json.load(open('config.json', 'r', encoding='utf-8'))
    cfg.setdefault('processing_options', {})['use_threaded_loader'] = True
    open(CONFIG_TMP, 'w', encoding='utf-8').write(json.dumps(cfg,
                                                             ensure_ascii=False, indent=2))


def test_threaded_loader_runs():
    p = EmailEvidenceProcessor(CONFIG_TMP)
    p.load_mbox('tests/data/sample_small.mbox')
    assert len(p.metadata_map) >= 1
