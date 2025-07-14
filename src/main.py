import os
import email
from email.header import decode_header
from datetime import datetime
import re
import mailbox
import base64
from collections import defaultdict

# --- 설정 ---
INPUT_DIR = 'email_files'
OUTPUT_DIR = 'processed_emails'

# --- 유틸리티 함수 ---

def decode_text(header_text):
    """헤더 텍스트(제목, 파일명 등)를 디코딩합니다."""
    if not header_text:
        return ""
    decoded_parts = decode_header(header_text)
    parts = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                parts.append(part.decode(charset or 'utf-8', errors='ignore'))
            except (UnicodeDecodeError, LookupError):
                parts.append(part.decode('cp949', errors='ignore'))
        else:
            parts.append(str(part))
    return ''.join(parts)

def sanitize_filename(filename):
    """공백을 '_'로 바꾸고, 파일 및 폴더명으로 사용할 수 없는 문자를 제거합니다."""
    sanitized = filename.replace(" ", "_")
    sanitized = re.sub(r'[\\/*?:"<>|]', "", sanitized).strip()
    sanitized = re.sub(r'__+', '_', sanitized)
    return sanitized[:150]

def get_email_date(msg):
    """이메일 메시지에서 날짜를 파싱하여 datetime 객체로 반환합니다."""
    date_str = msg.get('Date')
    if not date_str:
        return datetime.now()
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except (TypeError, ValueError):
        return datetime.now()

# --- 핵심 로직 ---

def save_message_parts(msg, output_path, base_filename):
    """단일 이메일의 HTML 본문(CID 이미지를 Base64로 내장)과 첨부파일을 저장합니다."""
    html_body = None
    html_part = None
    cid_map = {}
    attachments = []

    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        
        disposition = part.get('Content-Disposition', '')
        content_id = part.get('Content-ID')

        if not html_part and part.get_content_type() == 'text/html' and 'attachment' not in disposition:
            html_part = part
        elif content_id and ('inline' in disposition or not disposition):
            cid = content_id.strip('<>')
            cid_map[cid] = part
        elif 'attachment' in disposition:
            attachments.append(part)

    if html_part:
        charset = html_part.get_content_charset() or 'utf-8'
        try:
            html_body = html_part.get_payload(decode=True).decode(charset, errors='ignore')
        except (UnicodeDecodeError, LookupError):
            html_body = html_part.get_payload(decode=True).decode('cp949', errors='ignore')

        # CID 링크를 Base64 데이터 URI로 교체
        for cid, image_part in cid_map.items():
            image_data = image_part.get_payload(decode=True)
            mime_type = image_part.get_content_type()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            data_uri = f"data:{mime_type};base64,{base64_data}"
            cid_src = f'cid:{cid}'
            
            # 정규표현식을 사용하여 더 안정적으로 교체
            html_body = re.sub(f'src=["\"]?{re.escape(cid_src)}["\"]?', f'src="{data_uri}"', html_body, flags=re.IGNORECASE)

        html_filepath = os.path.join(output_path, f"{base_filename}.html")
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_body)
        print(f"  - HTML 저장 (이미지 내장): {html_filepath}")

    for part in attachments:
        filename = part.get_filename()
        if filename:
            decoded_filename = decode_text(filename)
            sanitized_filename = sanitize_filename(decoded_filename)
            if sanitized_filename:
                filepath = os.path.join(output_path, sanitized_filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    print(f"  - 첨부파일 저장: {filepath}")

def process_mailbox(mbox_path):
    """Mailbox 파일을 분석하여 대화 스레드별로 이메일을 처리합니다."""
    mbox = mailbox.mbox(mbox_path)
    messages = {}
    replies = defaultdict(list)
    
    print(f"\n1단계: '{os.path.basename(mbox_path)}'에서 메시지 정보 수집 중...")
    for msg in mbox:
        msg_id = msg.get('Message-ID')
        if not msg_id:
            continue
        messages[msg_id] = msg
        
        references = msg.get('References', "").split()
        ref_id = msg.get('In-Reply-To') or (references[-1] if references else None)
        if ref_id and ref_id in messages:
            replies[ref_id].append(msg_id)

    print("2단계: 대화 스레드 구성 중...")
    processed_ids = set()
    threads = []
    for msg_id, msg in messages.items():
        if msg_id in processed_ids:
            continue
        
        is_reply = msg.get('In-Reply-To') or msg.get('References')
        parent_id = (msg.get('In-Reply-To') or (msg.get('References', " ").split()[-1])) if is_reply else None

        if not parent_id or parent_id not in messages:
            thread = []
            q = [msg_id]
            visited_in_thread = {msg_id}
            
            while q:
                current_id = q.pop(0)
                if current_id in messages:
                    thread.append(messages[current_id])
                    processed_ids.add(current_id)
                    
                    for child_id in sorted(replies.get(current_id, []), key=lambda x: get_email_date(messages[x])):
                        if child_id not in visited_in_thread:
                            q.append(child_id)
                            visited_in_thread.add(child_id)
            
            thread.sort(key=get_email_date)
            threads.append(thread)

    print(f"3단계: {len(threads)}개의 대화 스레드를 저장합니다...")
    for thread in threads:
        if not thread:
            continue
        
        root_msg = thread[0]
        root_date = get_email_date(root_msg)
        root_subject = decode_text(root_msg.get('Subject', '제목 없음'))
        
        thread_folder_name = sanitize_filename(f"[{root_date.strftime('%Y-%m-%d')}] {root_subject}")
        thread_path = os.path.join(OUTPUT_DIR, thread_folder_name)
        
        if os.path.exists(thread_path):
            print(f"\n[건너뜀] 이미 처리된 대화: '{thread_folder_name}'")
            continue

        os.makedirs(thread_path, exist_ok=True)
        print(f"\n[대화 시작] '{thread_folder_name}'")

        for i, msg in enumerate(thread):
            subject = decode_text(msg.get('Subject', '제목 없음'))
            base_filename = sanitize_filename(f"{i+1:02d}_{subject}")
            print(f" - 처리 중: {base_filename}")
            save_message_parts(msg, thread_path, base_filename)

def main():
    """메인 실행 함수"""
    if not os.path.isdir(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"생성됨: 입력 폴더 '{INPUT_DIR}'. 여기에 .mbox 파일을 넣어주세요.")
        return

    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"'{INPUT_DIR}' 폴더의 .mbox 파일 처리를 시작합니다...")
    
    found_mbox = False
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith('.mbox'):
            found_mbox = True
            mbox_path = os.path.join(INPUT_DIR, filename)
            process_mailbox(mbox_path)
    
    if not found_mbox:
        print("처리할 .mbox 파일을 찾을 수 없습니다.")

    print("\n모든 작업이 완료되었습니다.")
    print(f"결과는 '{OUTPUT_DIR}' 폴더에 저장되었습니다.")

if __name__ == '__main__':
    main()
