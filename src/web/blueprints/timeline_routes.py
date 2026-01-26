"""
Timeline 관련 Blueprint
타임라인 생성, 통합 타임라인, 법원 제출용 패키지 생성
"""

import zipfile
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   send_file, url_for)

timeline_bp = Blueprint('timeline', __name__)

# 전역 변수 (routes.py의 register_routes에서 초기화됨)
timeline_service = None
evidence_service = None


def init_timeline_services(tl_service, ev_service):
    """Timeline 서비스 초기화

    Args:
        tl_service: TimelineService 인스턴스
        ev_service: EvidenceService 인스턴스
    """
    global timeline_service, evidence_service
    timeline_service = tl_service
    evidence_service = ev_service


@timeline_bp.route('/timeline')
def timeline_page():
    """타임라인 페이지"""
    try:
        # 증거 목록으로부터 타임라인 생성
        evidence_list = evidence_service.get_evidence_list()
        timeline_result = timeline_service.generate_timeline_from_evidence(
            evidence_list)

        if not timeline_result['success']:
            flash(timeline_result['message'], 'error')
            return redirect(url_for('index'))

        # 웹용 타임라인 데이터 생성
        timeline_data = timeline_result['timeline']
        summary = timeline_service.get_timeline_summary(timeline_data)

        return render_template('timeline.html',
                               timeline_data=timeline_data,
                               summary=summary,
                               page_title='이메일 타임라인')

    except Exception as e:
        flash(f'타임라인 로드 오류: {str(e)}', 'error')
        return redirect(url_for('index'))


@timeline_bp.route('/integrated_timeline')
def integrated_timeline():
    """통합 타임라인 페이지"""
    try:
        # 처리된 이메일 폴더 확인
        processed_dir = Path('processed_emails')
        if not processed_dir.exists() or not any(processed_dir.iterdir()):
            flash('처리된 이메일 데이터가 없습니다. 먼저 mbox 파일을 업로드하고 처리해주세요.', 'warning')
            return render_template('integrated_timeline.html',
                                   timeline_result=None,
                                   no_data=True)

        from ...timeline.integrated_timeline_generator import \
            IntegratedTimelineGenerator

        generator = IntegratedTimelineGenerator()
        result = generator.generate_integrated_timeline()

        # 타임라인 항목이 없는 경우
        if not result or not hasattr(result, 'timeline_items') or len(result.timeline_items) == 0:
            flash('타임라인에 표시할 데이터가 없습니다.', 'info')
            return render_template('integrated_timeline.html',
                                   timeline_result=None,
                                   no_data=True)

        return render_template('integrated_timeline.html',
                               timeline_result=result,
                               no_data=False)
    except Exception as e:
        flash(f'통합 타임라인 생성 오류: {str(e)}', 'error')
        current_app.logger.error(
            f'Integrated timeline error: {str(e)}', exc_info=True)
        return redirect(url_for('index'))


@timeline_bp.route('/generate_timeline_package')
def generate_timeline_package():
    """법원 제출용 타임라인 패키지 생성"""
    try:
        from ...timeline.integrated_timeline_generator import \
            IntegratedTimelineGenerator

        generator = IntegratedTimelineGenerator()
        result = generator.generate_integrated_timeline()

        # 가장 최근 패키지 디렉토리 찾기
        timeline_dir = Path("processed_emails") / "06_통합타임라인"
        package_dirs = list(timeline_dir.glob("법원제출용_통합증거_*"))

        if not package_dirs:
            flash('생성된 패키지가 없습니다.', 'error')
            return redirect(url_for('timeline.integrated_timeline'))

        # 가장 최근 패키지를 ZIP으로 압축
        latest_package = max(package_dirs, key=lambda p: p.stat().st_mtime)

        zip_path = f"{latest_package}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in latest_package.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(latest_package.parent)
                    zipf.write(file_path, arcname)

        return send_file(zip_path, as_attachment=True,
                         download_name=f"법원제출용_통합증거_{datetime.now().strftime('%Y%m%d')}.zip")

    except Exception as e:
        flash(f'타임라인 패키지 생성 실패: {str(e)}', 'error')
        return redirect(url_for('timeline.integrated_timeline'))


@timeline_bp.route('/download_timeline_excel')
def download_timeline_excel():
    """통합 타임라인 Excel 다운로드"""
    try:
        timeline_dir = Path("processed_emails") / "06_통합타임라인"
        excel_files = list(timeline_dir.glob("통합타임라인_*.xlsx"))

        if not excel_files:
            flash('생성된 Excel 파일이 없습니다. 먼저 통합 타임라인을 생성하세요.', 'error')
            return redirect(url_for('timeline.integrated_timeline'))

        # 가장 최근 Excel 파일
        latest_excel = max(excel_files, key=lambda p: p.stat().st_mtime)

        return send_file(str(latest_excel.absolute()),
                         as_attachment=True,
                         download_name=f"통합타임라인_{datetime.now().strftime('%Y%m%d')}.xlsx")

    except Exception as e:
        flash(f'Excel 다운로드 실패: {str(e)}', 'error')
        return redirect(url_for('timeline.integrated_timeline'))
