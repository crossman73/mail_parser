"""Mailbox processing utilities for thread grouping."""

import mailbox
import os
from collections import defaultdict
from datetime import datetime
from email.message import Message
from typing import Dict, List, Optional, Set

from ..utils.email_utils import get_email_date


def process_mailbox(
    mbox_path: str, output_dir: Optional[str] = None
) -> List[List[Message]]:
    """Read an mbox file and group messages into threads.

    Returns a list of threads; each thread is a list of email.message.Message
    objects sorted by date.
    """
    if not os.path.exists(mbox_path):
        raise FileNotFoundError(mbox_path)

    mbox_file = mailbox.mbox(mbox_path)
    messages: Dict[str, Message] = {}
    replies: Dict[str, List[str]] = defaultdict(list)

    for msg in mbox_file:
        msg_id: Optional[str] = msg.get('Message-ID')
        if not msg_id:
            continue
        messages[msg_id] = msg
        refs_str: str = msg.get('References', '') or ''
        refs: List[str] = refs_str.split()
        in_reply: Optional[str] = msg.get('In-Reply-To')
        parent: Optional[str] = in_reply or (refs[-1] if refs else None)
        if parent:
            replies[parent].append(msg_id)

    processed: Set[str] = set()
    threads: List[List[Message]] = []

    for mid in list(messages.keys()):
        if mid in processed:
            continue

        # find root (message without parent in messages)
        cur: Message = messages[mid]
        cur_refs_str: str = cur.get('References', '') or ''
        parent_id: Optional[str] = cur.get('In-Reply-To') or (
            cur_refs_str.split()[-1] if cur.get('References') else None
        )
        if parent_id and parent_id in messages:
            # will be processed when root iterated
            continue

        # BFS collect thread
        q: List[str] = [mid]
        thread: List[Message] = []
        visited: Set[str] = set()
        while q:
            cid: str = q.pop(0)
            if cid in visited:
                continue
            visited.add(cid)
            if cid in messages:
                thread.append(messages[cid])
                children: List[str] = sorted(
                    replies.get(cid, []),
                    key=lambda x: get_email_date(messages[x]) or datetime.min
                )
                q.extend(children)

        thread.sort(key=lambda m: get_email_date(m) or datetime.min)
        for m in thread:
            msg_id_val: Optional[str] = m.get('Message-ID')
            if msg_id_val:
                processed.add(msg_id_val)
        if thread:
            threads.append(thread)

    return threads
