from pathlib import Path

p = Path('tests/data/sample_large.mbox')
with p.open('a', encoding='utf-8') as f:
    for i in range(1, 5000):
        f.write(f"From test{i}@example.com Sat Sep  6 12:00:00 2025\nSubject: Large test email {i}\nMessage-ID: <large-msg-{i}@example.com>\nFrom: Sender <sender@example.com>\nTo: Recipient <recipient@example.com>\nDate: Sat, 6 Sep 2025 12:00:00 +0900\n\nThis is the body of large test email {i}.\n\n")
print('done')
