import mailbox
import os
from collections import defaultdict
from datetime import datetime
from typing import List

from src.utils.email_utils import get_email_date


def process_mailbox(mbox_path: str, output_dir: str = None) -> List[List[object]]:
    """Read an mbox file and group messages into threads.

    Returns a list of threads; each thread is a list of email.message.Message
    objects sorted by date.
    """
    if not os.path.exists(mbox_path):
        raise FileNotFoundError(mbox_path)

    mbox = mailbox.mbox(mbox_path)
    messages = {}
    replies = defaultdict(list)

    for msg in mbox:
        msg_id = msg.get('Message-ID')
        if not msg_id:
            continue
        messages[msg_id] = msg
        refs = msg.get('References', '').split()
        in_reply = msg.get('In-Reply-To')
        parent = in_reply or (refs[-1] if refs else None)
        if parent:
            replies[parent].append(msg_id)

    processed = set()
    threads = []

    for mid in list(messages.keys()):
        if mid in processed:
            continue

        # find root (message without parent in messages)
        cur = messages[mid]
        parent_id = cur.get('In-Reply-To') or (cur.get('References',
                                                       '').split()[-1] if cur.get('References') else None)
        if parent_id and parent_id in messages:
            # will be processed when root iterated
            continue

        # BFS collect thread
        q = [mid]
        thread = []
        visited = set()
        while q:
            cid = q.pop(0)
            if cid in visited:
                continue
            visited.add(cid)
            if cid in messages:
                thread.append(messages[cid])
                children = sorted(replies.get(cid, []),
                                  key=lambda x: get_email_date(messages[x]))
                q.extend(children)

        thread.sort(key=get_email_date)
        for m in thread:
            processed.add(m.get('Message-ID'))
        if thread:
            threads.append(thread)

    return threads
