"""
Integrity 관련 Blueprint
무결성 검증, 법원 제출용 보고서 다운로드
"""

from pathlib import Path

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, send_file, url_for)

integrity_bp = Blueprint('integrity', __name__)


@integrity_bp.route('/integrity')
def integrity():
    """무결성 검증 페이지 (verify_integrity로 redirect)"""
    return redirect(url_for('integrity.verify_integrity'))


@integrity_bp.route('/verify_integrity')
def verify_integrity():
    """법원 제출용 무결성 검증 페이지"""
    try:
        # Lazy import to avoid loading heavy dependencies at startup
        from src.legal_compliance.court_evidence_verifier import \
            CourtEvidenceIntegrityVerifier

        # 처리된 이메일 폴더 확인
        processed_dir = Path('processed_emails')
        if not processed_dir.exists() or not any(processed_dir.iterdir()):
            flash('검증할 증거 데이터가 없습니다. 먼저 mbox 파일을 업로드하고 처리해주세요.', 'warning')
            return render_template('verify_integrity.html',
                                   verification_report=None,
                                   no_data=True)

        # 기본 프로젝트 디렉토리에서 검증
        verifier = CourtEvidenceIntegrityVerifier("processed_emails")
        verification_report = verifier.verify_integrity()

        # 검증할 파일이 없는 경우
        if not verification_report or not hasattr(verification_report, 'verified_files') or len(verification_report.verified_files) == 0:
            flash('검증할 파일이 없습니다.', 'info')
            return render_template('verify_integrity.html',
                                   verification_report=None,
                                   no_data=True)

        return render_template('verify_integrity.html',
                               verification_report=verification_report,
                               no_data=False)
    except Exception as e:
        flash(f'무결성 검증 오류: {str(e)}', 'error')
        current_app.logger.error(
            f'Verify integrity error: {str(e)}', exc_info=True)
        return redirect(url_for('index'))


@integrity_bp.route('/api/verify_integrity')
def api_verify_integrity():
    """법원 제출용 무결성 검증 API"""
    try:
        # Lazy import to avoid loading heavy dependencies at startup
        from src.legal_compliance.court_evidence_verifier import \
            CourtEvidenceIntegrityVerifier

        verifier = CourtEvidenceIntegrityVerifier("processed_emails")
        verification_report = verifier.verify_integrity()

        return jsonify({
            'success': True,
            'verification_report': verification_report
        })
    except Exception as e:
        current_app.logger.error(
            f'API verify integrity error: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@integrity_bp.route('/download_verification_report')
def download_verification_report():
    """무결성 검증 보고서 다운로드"""
    try:
        # 가장 최근 검증 보고서 찾기
        verification_dir = Path("processed_emails") / "04_검증자료"
        if not verification_dir.exists():
            flash('검증 보고서가 없습니다. 먼저 무결성 검증을 실행하세요.', 'error')
            return redirect(url_for('integrity.verify_integrity'))

        # JSON 보고서 파일 찾기
        json_reports = list(verification_dir.glob("무결성검증보고서_*.json"))
        if not json_reports:
            flash('검증 보고서 파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('integrity.verify_integrity'))

        # 가장 최근 파일
        latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)

        return send_file(str(latest_report.absolute()),
                         as_attachment=True,
                         download_name=f"무결성검증보고서_{latest_report.stem.split('_')[-1]}.json")

    except Exception as e:
        flash(f'보고서 다운로드 오류: {str(e)}', 'error')
        return redirect(url_for('integrity.verify_integrity'))


@integrity_bp.route('/download_court_certificate')
def download_court_certificate():
    """법원 제출용 무결성 증명서 다운로드"""
    try:
        # 법원 제출용 증명서 찾기
        verification_dir = Path("processed_emails") / "04_검증자료"
        if not verification_dir.exists():
            flash('검증 증명서가 없습니다. 먼저 무결성 검증을 실행하세요.', 'error')
            return redirect(url_for('integrity.verify_integrity'))

        # 법원 제출용 증명서 파일 찾기
        cert_files = list(verification_dir.glob("법원제출용_무결성증명서_*.txt"))
        if not cert_files:
            flash('법원 제출용 증명서 파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('integrity.verify_integrity'))

        # 가장 최근 파일
        latest_cert = max(cert_files, key=lambda p: p.stat().st_mtime)

        return send_file(str(latest_cert.absolute()),
                         as_attachment=True,
                         download_name=f"법원제출용_무결성증명서_{latest_cert.stem.split('_')[-1]}.txt")

    except Exception as e:
        flash(f'증명서 다운로드 오류: {str(e)}', 'error')
        return redirect(url_for('integrity.verify_integrity'))
