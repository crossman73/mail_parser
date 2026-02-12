"""HTML 내보내기"""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict

from .base import TimelineExporter


class HtmlExporter(TimelineExporter):
    """타임라인을 HTML로 내보내기"""

    @property
    def format_name(self) -> str:
        return 'HTML'

    @property
    def content_type(self) -> str:
        return 'text/html; charset=utf-8'

    @property
    def file_extension(self) -> str:
        return 'html'

    def export(self, timeline: Dict[str, Any]) -> BytesIO:
        title = self._esc(timeline.get('title', '타임라인'))
        desc = self._esc(timeline.get('description', ''))
        events = timeline.get('events', [])
        status = timeline.get('status', 'draft')
        start = timeline.get('date_range_start', '')
        end = timeline.get('date_range_end', '')
        key_count = sum(1 for e in events if e.get('is_key_event'))
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        events_html = []
        for idx, evt in enumerate(events, 1):
            ts = evt.get('timestamp', '')
            if isinstance(ts, str) and len(ts) > 10:
                ts = ts[:10]
            is_key = evt.get('is_key_event', False)
            marker = '<span class="key-badge">★ 핵심</span> ' if is_key else ''
            etype = self._esc(evt.get('event_type', 'email'))
            evt_title = self._esc(evt.get('title', ''))
            evt_desc = self._esc(evt.get('description', ''))
            legal = self._esc(evt.get('legal_significance', ''))
            notes = self._esc(evt.get('notes', ''))
            participants = evt.get('participants', [])
            attachments = evt.get('attachments', [])

            extra = ''
            if evt_desc:
                extra += f'<p class="evt-desc">{evt_desc}</p>'
            if participants:
                extra += f'<p class="evt-meta"><strong>참여자:</strong> {self._esc(", ".join(participants))}</p>'
            if legal:
                extra += f'<p class="evt-legal">⚖ {legal}</p>'
            if notes:
                extra += f'<p class="evt-notes"><strong>비고:</strong> {notes}</p>'
            if attachments:
                extra += f'<p class="evt-meta"><strong>첨부:</strong> {self._esc(", ".join(attachments))}</p>'

            key_cls = ' key-event' if is_key else ''
            events_html.append(f'''
        <div class="event-card{key_cls}">
            <div class="event-header">
                <span class="event-date">{self._esc(ts)}</span>
                <span class="event-type">{etype}</span>
            </div>
            <h3>{marker}{evt_title}</h3>
            {extra}
        </div>''')

        html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
:root {{
    --bg: #ffffff; --fg: #1a1a2e; --card-bg: #f8f9fa;
    --border: #dee2e6; --accent: #0066cc; --key-bg: #fff3cd;
}}
@media (prefers-color-scheme: dark) {{
    :root {{
        --bg: #1a1a2e; --fg: #e0e0e0; --card-bg: #2a2a4a;
        --border: #444; --accent: #66b3ff; --key-bg: #3d3520;
    }}
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Malgun Gothic', sans-serif; background: var(--bg); color: var(--fg); padding: 2rem; max-width: 900px; margin: 0 auto; }}
h1 {{ text-align: center; margin-bottom: 0.5rem; }}
.subtitle {{ text-align: center; color: #888; margin-bottom: 2rem; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.summary-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; }}
.summary-card .value {{ font-size: 1.5rem; font-weight: bold; color: var(--accent); }}
.summary-card .label {{ font-size: 0.85rem; color: #888; }}
.event-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem; }}
.event-card.key-event {{ border-left: 4px solid #ffc107; background: var(--key-bg); }}
.event-header {{ display: flex; justify-content: space-between; margin-bottom: 0.5rem; }}
.event-date {{ font-weight: bold; color: var(--accent); }}
.event-type {{ background: var(--border); border-radius: 4px; padding: 2px 8px; font-size: 0.8rem; }}
.event-card h3 {{ margin-bottom: 0.5rem; }}
.key-badge {{ background: #ffc107; color: #000; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; }}
.evt-desc {{ margin: 0.3rem 0; }}
.evt-legal {{ color: var(--accent); font-style: italic; }}
.evt-notes {{ color: #888; font-size: 0.9rem; }}
.evt-meta {{ font-size: 0.9rem; color: #666; }}
.footer {{ text-align: center; margin-top: 2rem; color: #888; font-size: 0.85rem; }}
@media print {{ body {{ max-width: 100%; padding: 1rem; }} }}
</style>
</head>
<body>
    <h1>{title}</h1>
    <p class="subtitle">{desc}</p>

    <div class="summary">
        <div class="summary-card"><div class="value">{len(events)}</div><div class="label">총 이벤트</div></div>
        <div class="summary-card"><div class="value">{start or 'N/A'}</div><div class="label">시작일</div></div>
        <div class="summary-card"><div class="value">{end or 'N/A'}</div><div class="label">종료일</div></div>
        <div class="summary-card"><div class="value">{key_count}</div><div class="label">핵심 이벤트</div></div>
    </div>

    <h2>이벤트 상세</h2>
    {"".join(events_html)}

    <div class="footer">
        이 문서는 {now}에 자동 생성되었습니다. | 상태: {self._esc(status)}
    </div>
</body>
</html>'''

        buf = BytesIO()
        buf.write(html.encode('utf-8'))
        buf.seek(0)
        return buf

    @staticmethod
    def _esc(text: str) -> str:
        """HTML 이스케이프"""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))
