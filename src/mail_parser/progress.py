# src/mail_parser/progress.py

import sys
import time
from typing import Optional


class ProgressBar:
    """
    간단한 진행률 표시 클래스
    """

    def __init__(self, total: int, description: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()

    def update(self, increment: int = 1):
        """
        진행률을 업데이트합니다.
        """
        self.current += increment
        self._display()

    def set_progress(self, current: int):
        """
        현재 진행률을 직접 설정합니다.
        """
        self.current = current
        self._display()

    def finish(self):
        """
        진행률을 100%로 설정하고 완료 메시지를 출력합니다.
        """
        self.current = self.total
        self._display()
        elapsed = time.time() - self.start_time
        print(f"\n완료! (소요시간: {elapsed:.1f}초)")

    def _display(self):
        """
        진행률 바를 화면에 출력합니다.
        """
        if self.total == 0:
            return

        percentage = min(100, (self.current / self.total) * 100)
        filled_width = int(self.width * self.current / self.total)

        bar = "█" * filled_width + "░" * (self.width - filled_width)

        elapsed = time.time() - self.start_time
        if self.current > 0 and elapsed > 0:
            rate = self.current / elapsed
            eta = (self.total - self.current) / rate if rate > 0 else 0
            eta_str = f" (남은시간: {eta:.1f}초)" if eta > 0 else ""
        else:
            eta_str = ""

        sys.stdout.write(
            f"\r{self.description} |{bar}| {self.current}/{self.total} ({percentage:.1f}%){eta_str}")
        sys.stdout.flush()


class EmailProcessingProgress:
    """
    메일 처리 전용 진행률 관리 클래스
    """

    def __init__(self, total_emails: int):
        self.total_emails = total_emails
        self.processed_emails = 0
        self.excluded_emails = 0
        self.pdf_generated = 0
        self.current_stage = "초기화"
        self.stages = {
            "초기화": 0,
            "메타데이터 수집": 10,
            "메일 처리": 70,
            "PDF 변환": 90,
            "보고서 생성": 95,
            "완료": 100
        }

    def set_stage(self, stage_name: str):
        """
        현재 처리 단계를 설정합니다.
        """
        self.current_stage = stage_name
        self._display_stage_info()

    def update_email_processed(self, increment: int = 1):
        """
        처리된 메일 수를 업데이트합니다.
        """
        self.processed_emails += increment
        self._display_progress()

    def update_email_excluded(self, increment: int = 1):
        """
        제외된 메일 수를 업데이트합니다.
        """
        self.excluded_emails += increment
        self._display_progress()

    def update_pdf_generated(self, increment: int = 1):
        """
        생성된 PDF 수를 업데이트합니다.
        """
        self.pdf_generated += increment
        self._display_progress()

    def _display_stage_info(self):
        """
        현재 단계 정보를 출력합니다.
        """
        print(f"\n📧 {self.current_stage} 중...")
        print("─" * 50)

    def _display_progress(self):
        """
        진행 상황을 출력합니다.
        """
        total_processed = self.processed_emails + self.excluded_emails

        if self.current_stage == "메일 처리" and self.total_emails > 0:
            percentage = (total_processed / self.total_emails) * 100
            print(f"진행률: {total_processed}/{self.total_emails} ({percentage:.1f}%) "
                  f"| 처리됨: {self.processed_emails}, 제외됨: {self.excluded_emails}")
        elif self.current_stage == "PDF 변환" and self.processed_emails > 0:
            percentage = (self.pdf_generated / self.processed_emails) * 100
            print(
                f"PDF 변환: {self.pdf_generated}/{self.processed_emails} ({percentage:.1f}%)")

    def display_summary(self):
        """
        최종 처리 요약을 출력합니다.
        """
        print("\n" + "="*50)
        print("📊 처리 완료 요약")
        print("="*50)
        print(f"• 전체 메일 수: {self.total_emails}개")
        print(f"• 처리된 메일: {self.processed_emails}개")
        print(f"• 제외된 메일: {self.excluded_emails}개")
        print(f"• 생성된 PDF: {self.pdf_generated}개")

        if self.total_emails > 0:
            success_rate = (self.processed_emails / self.total_emails) * 100
            print(f"• 처리 성공률: {success_rate:.1f}%")

        print("="*50)


def display_welcome_message():
    """
    프로그램 시작 시 환영 메시지를 출력합니다.
    """
    print("="*60)
    print("📧 법원 제출용 메일박스 증거 분류 시스템")
    print("="*60)
    print("한국 법원의 디지털 증거 제출 규정을 준수하는")
    print("메일박스 증거 처리 및 분류 시스템입니다.")
    print("="*60)


def display_configuration_info(config: dict):
    """
    설정 정보를 사용자에게 출력합니다.
    """
    print("\n🔧 현재 설정:")
    print("─" * 30)

    exclude_keywords = config.get('exclude_keywords', [])
    if exclude_keywords:
        print(f"• 제외 키워드: {len(exclude_keywords)}개 설정")

    exclude_senders = config.get('exclude_senders', [])
    if exclude_senders:
        print(f"• 제외 발신자: {len(exclude_senders)}개 설정")

    date_range = config.get('date_range', {})
    if date_range.get('start') or date_range.get('end'):
        print(
            f"• 날짜 범위: {date_range.get('start', '제한없음')} ~ {date_range.get('end', '제한없음')}")

    required_keywords = config.get('required_keywords', {})
    if isinstance(required_keywords, dict):
        keywords = required_keywords.get('keywords', [])
        if keywords:
            print(f"• 필수 키워드: {len(keywords)}개 설정")

    print("─" * 30)


def display_error_help(error_type: str, error_msg: str = ""):
    """
    오류 타입에 따른 도움말을 출력합니다.
    """
    print(f"\n❌ 오류 발생: {error_type}")

    if error_msg:
        print(f"상세 메시지: {error_msg}")

    help_messages = {
        "파일없음": [
            "💡 해결 방법:",
            "1. 파일 경로가 올바른지 확인하세요",
            "2. 파일명에 특수문자가 포함되어 있지 않은지 확인하세요",
            "3. 파일이 다른 프로그램에서 사용 중이 아닌지 확인하세요"
        ],
        "인코딩오류": [
            "💡 해결 방법:",
            "1. mbox 파일을 UTF-8 인코딩으로 다시 저장해보세요",
            "2. 다른 메일 클라이언트에서 mbox를 다시 내보내보세요",
            "3. 파일이 손상되지 않았는지 확인하세요"
        ],
        "메모리부족": [
            "💡 해결 방법:",
            "1. 다른 프로그램을 종료하여 메모리를 확보하세요",
            "2. mbox 파일을 더 작은 단위로 분할하세요",
            "3. 시스템 메모리가 충분한지 확인하세요"
        ],
        "권한오류": [
            "💡 해결 방법:",
            "1. 관리자 권한으로 프로그램을 실행하세요",
            "2. 출력 폴더에 쓰기 권한이 있는지 확인하세요",
            "3. 바이러스 백신 소프트웨어에서 차단하지 않는지 확인하세요"
        ]
    }

    if error_type in help_messages:
        for msg in help_messages[error_type]:
            print(msg)

    print("\n📞 추가 도움이 필요하시면 프로젝트 GitHub Issues를 확인하세요.")
    print("─" * 50)
