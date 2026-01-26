"""
Logs 관련 Blueprint
DB 기반 로그 뷰어, 로그 파일 관리
"""

from datetime import datetime, timedelta
from pathlib import Path

from flask import (Blueprint, current_app, jsonify, render_template, request,
                   send_file)

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/logs')
def logs_viewer():
    """로그 뷰어 페이지"""
    try:
        return render_template('log_viewer.html')
    except Exception as e:
        current_app.logger.error(f"로그 뷰어 페이지 로드 실패: {str(e)}", exc_info=True)
        return f"로그 뷰어 로드 실패: {str(e)}", 500


@logs_bp.route('/api/logs')
def api_logs():
    """최근 로그 조회 API (DB 기반 - 실패 시 메모리 폴백)"""
    try:
        from src.database.email_db import db

        level = request.args.get('level', None)
        limit = request.args.get('limit', 1000, type=int)
        offset = request.args.get('offset', 0, type=int)

        try:
            logs = db.get_logs(limit=limit, offset=offset, level=level)
            total_count = db.get_log_count(level=level)
        except Exception as db_err:
            current_app.logger.warning(f"⚠️ DB 로그 조회 실패 (빈 결과 반환): {db_err}")
            logs = []
            total_count = 0

        # 통계 계산
        stats = {}
        for log in logs:
            log_level = log.get('level', 'INFO')
            stats[log_level] = stats.get(log_level, 0) + 1

        return jsonify({
            'success': True,
            'logs': logs,
            'stats': stats,
            'count': len(logs),
            'total': total_count,
            'offset': offset,
            'limit': limit
        })
    except Exception as e:
        current_app.logger.error(f"로그 조회 API 실패: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@logs_bp.route('/api/logs/download')
def api_logs_download():
    """로그 다운로드 (JSON) - DB 실패 시 빈 파일"""
    try:
        import json

        from src.database.email_db import db

        level = request.args.get('level', None)
        limit = request.args.get('limit', 5000, type=int)

        try:
            logs = db.get_logs(limit=limit, level=level)
        except Exception as db_err:
            current_app.logger.warning(f"⚠️ DB 로그 조회 실패 (빈 파일 생성): {db_err}")
            logs = []

        # JSON 파일로 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs_{timestamp}.json"

        # temp_manager 가져오기
        from src.utils.temp_file_manager import temp_manager
        temp_file = temp_manager.create_temp_file(filename, cleanup=False)

        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

        return send_file(
            temp_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
    except Exception as e:
        current_app.logger.error(f"로그 다운로드 실패: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@logs_bp.route('/api/logs/clear', methods=['POST'])
def api_logs_clear():
    """DB 로그 초기화 API - DB 실패 시 안내"""
    try:
        from src.database.email_db import db

        # 7일 이전 로그만 삭제 (안전장치)
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()

        try:
            deleted = db.clear_logs(before_time=cutoff)
        except Exception as db_err:
            current_app.logger.warning(f"⚠️ DB 로그 삭제 실패: {db_err}")
            return jsonify({
                'success': False,
                'error': 'DB 연결 실패 - 로그를 삭제할 수 없습니다.',
                'db_available': False
            }), 503

        return jsonify({
            'success': True,
            'message': f'{deleted}개의 로그가 삭제되었습니다.'
        })
    except Exception as e:
        current_app.logger.error(f"로그 초기화 실패: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@logs_bp.route('/api/logs/files')
def api_log_files():
    """로그 파일 목록 조회 API"""
    try:
        log_dir = Path('logs')
        if not log_dir.exists():
            return jsonify({
                'success': True,
                'files': [],
                'count': 0
            })

        files = []
        for log_file in sorted(log_dir.glob('*.log'), reverse=True)[:50]:
            stat = log_file.stat()
            files.append({
                'name': log_file.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        current_app.logger.error(f"로그 파일 목록 조회 실패: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@logs_bp.route('/api/logs/file/<filename>')
def api_log_file_view(filename):
    """특정 로그 파일 내용 보기 (HTML)"""
    try:
        log_dir = Path('logs')
        file_path = log_dir / filename

        if not file_path.exists() or not file_path.is_file():
            return "로그 파일을 찾을 수 없습니다.", 404

        # 경로 탐색 공격 방지
        if not str(file_path.resolve()).startswith(str(log_dir.resolve())):
            return "잘못된 파일 경로입니다.", 403

        lines = request.args.get('lines', 500, type=int)

        # 파일 읽기 (마지막 N줄)
        with open(file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            content_lines = all_lines[-lines:] if len(
                all_lines) > lines else all_lines
            content = ''.join(content_lines)

        # HTML로 렌더링
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{filename}</title>
            <style>
                body {{
                    font-family: 'Consolas', 'Monaco', monospace;
                    background: #1e1e1e;
                    color: #d4d4d4;
                    padding: 2rem;
                    margin: 0;
                }}
                pre {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                .header {{
                    margin-bottom: 1rem;
                    padding-bottom: 1rem;
                    border-bottom: 1px solid #444;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{filename}</h2>
                <p>마지막 {lines}줄 표시</p>
            </div>
            <pre>{content}</pre>
        </body>
        </html>
        """

        return html_content
    except Exception as e:
        current_app.logger.error(f"로그 파일 뷰어 실패: {str(e)}", exc_info=True)
        return f"로그 파일 읽기 실패: {str(e)}", 500


@logs_bp.route('/api/logs/file/<filename>/download')
def api_log_file_download(filename):
    """특정 로그 파일 다운로드"""
    try:
        log_dir = Path('logs')
        file_path = log_dir / filename

        if not file_path.exists() or not file_path.is_file():
            return "로그 파일을 찾을 수 없습니다.", 404

        # 경로 탐색 공격 방지
        if not str(file_path.resolve()).startswith(str(log_dir.resolve())):
            return "잘못된 파일 경로입니다.", 403

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    except Exception as e:
        current_app.logger.error(f"로그 파일 다운로드 실패: {str(e)}", exc_info=True)
        return f"로그 파일 다운로드 실패: {str(e)}", 500
