# src/mail_parser/analyzer.py

from collections import defaultdict

class ThreadAnalyzer:
    def __init__(self, metadata_map):
        self.metadata_map = metadata_map
        self.replies = defaultdict(list)
        self.threads = []

    def build_threads(self):
        """Analyzes message relationships from metadata and groups them into threads."""
        print("2단계: 대화 스레드 구성 중...")
        
        # Build reply mapping from metadata
        for msg_id, meta in self.metadata_map.items():
            ref_id = meta.get('in_reply_to') or meta.get('references')
            if ref_id and ref_id in self.metadata_map:
                self.replies[ref_id].append(msg_id)

        processed_ids = set()
        for msg_id in self.metadata_map:
            if msg_id in processed_ids:
                continue
            
            parent_id = self.metadata_map[msg_id].get('in_reply_to') or self.metadata_map[msg_id].get('references')

            # Start a new thread if it's not a reply or its parent is missing
            if not parent_id or parent_id not in self.metadata_map:
                thread_ids = []
                q = [msg_id]
                visited_in_thread = {msg_id}
                
                while q:
                    current_id = q.pop(0)
                    thread_ids.append(current_id)
                    processed_ids.add(current_id)
                    
                    # Sort children by date before adding to the queue
                    children = sorted(self.replies.get(current_id, []), key=lambda x: self.metadata_map[x]['date'])
                    for child_id in children:
                        if child_id not in visited_in_thread:
                            q.append(child_id)
                            visited_in_thread.add(child_id)
                
                # Sort the final thread by date
                thread_ids.sort(key=lambda x: self.metadata_map[x]['date'])
                self.threads.append(thread_ids)
        
        print(f"발견된 대화 스레드: {len(self.threads)}개")
        return self.threads
