from src.mail_parser.processor import EmailEvidenceProcessor
import json
import sys
from pathlib import Path

# ensure repo root is on sys.path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


CONFIG_SRC = 'config.json'
CONFIG_TMP = 'config.threaded.json'
MBOX_SAMPLE = 'tests/data/sample_small.mbox'

# create a temporary config enabling threaded loader
with open(CONFIG_SRC, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

cfg.setdefault('processing_options', {})['use_threaded_loader'] = True

with open(CONFIG_TMP, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

# run a few iterations of load_mbox using the threaded loader
for i in range(3):
    print(
        f"Run {i+1}: instantiating processor and loading mbox via threaded loader")
    p = EmailEvidenceProcessor(CONFIG_TMP)
    try:
        p.load_mbox('tests/data/sample_small.mbox')
        print('  -> metadata count:', len(p.metadata_map))
    except Exception as e:
        print('  -> error during load:', e)

print('done')
