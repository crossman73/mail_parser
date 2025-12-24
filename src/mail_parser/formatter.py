# src/mail_parser/formatter.py

import os

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


class CourtFormatter:
    def __init__(self):
        try:
            # 폰트 파일이 현재 디렉토리에 있다고 가정합니다.
            # 실제 배포 시에는 폰트 경로를 적절히 설정해야 합니다.
            font_path = r'C:\dev\python-email\email_files\NanumGothic.ttf'
            if not os.path.exists(font_path):
                # 폰트 파일이 없으면 경고 메시지를 출력하고 기본 폰트를 사용합니다.
                print(f"경고: 폰트 파일 '{font_path}'을(를) 찾을 수 없습니다. 기본 폰트를 사용합니다.")
                self.font_name = 'Helvetica'
            else:
                pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                self.font_name = 'NanumGothic'
        except Exception as e:
            print(f"경고: 폰트 등록 중 오류 발생: {e}. 기본 폰트를 사용합니다.")
            self.font_name = 'Helvetica'  # Fallback to a default font

    def to_pdf(self, html_content, output_filepath, evidence_number):
        doc = SimpleDocTemplate(output_filepath, pagesize=letter)
        styles = getSampleStyleSheet()

        evidence_style = styles['Normal']
        evidence_style.alignment = TA_CENTER
        evidence_style.fontName = self.font_name
        evidence_style.fontSize = 14

        story = []

        story.append(Paragraph(evidence_number, evidence_style))
        story.append(Spacer(1, 0.2 * inch))

        import re
        text_content = re.sub(r'<[^>]+>', '', html_content)

        body_style = styles['Normal']
        body_style.fontName = self.font_name
        body_style.fontSize = 10

        for line in text_content.split('\n'):
            if line.strip():
                story.append(Paragraph(line, body_style))
                story.append(Spacer(1, 0.05 * inch))

        try:
            print(f"PDF 생성을 시도 중: {output_filepath}")
            doc.build(story)
            print(f"PDF 생성 완료: {output_filepath}")
        except Exception as e:
            print(f"PDF 생성 중 치명적인 오류 발생 ({output_filepath}): {e}")
            # 오류 발생 시 파일이 생성되지 않도록 명시적으로 삭제
            if os.path.exists(output_filepath):
                os.remove(output_filepath)
            raise  # 예외를 다시 발생시켜 상위 호출자에게 알림
