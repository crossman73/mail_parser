"""
API routes for the email evidence system
REST API 라우트 정의
"""

from pathlib import Path

from flask import jsonify, request
from werkzeug.utils import secure_filename

from src.services import (EmailService, EvidenceService, FileService,
                          TimelineService)


def register_api_routes(app):
    """API 라우트 등록"""

    # 서비스 인스턴스 생성
    email_service = EmailService(app.config.get('EMAIL_PROCESSOR_CONFIG'))
    evidence_service = EvidenceService()
    timeline_service = TimelineService()
    file_service = FileService()

    @app.route('/api/emails/load', methods=['POST'])
    def api_load_emails():
        """이메일 로드 API"""
        try:
            data = request.get_json()
            filename = data.get('filename')

            if not filename:
                return jsonify({
                    'success': False,
                    'message': 'filename이 필요합니다.'
                }), 400

            upload_path = Path(app.config['UPLOAD_FOLDER']) / filename
            result = email_service.load_mbox(str(upload_path))

            return jsonify(result)

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'API 오류: {str(e)}'
            }), 500

    @app.route('/api/emails/process', methods=['POST'])
    def api_process_emails():
        """이메일 처리 API"""
        try:
            data = request.get_json()
            selected_indices = data.get('selected_indices', [])

            if not selected_indices:
                return jsonify({
                    'success': False,
                    'message': '처리할 이메일이 선택되지 않았습니다.'
                }), 400

            result = email_service.process_selected_emails(selected_indices)
            return jsonify(result)

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'처리 오류: {str(e)}'
            }), 500

    @app.route('/api/emails/search', methods=['GET'])
    def api_search_emails():
        """이메일 검색 API"""
        try:
            keyword = request.args.get('keyword', '')
            field = request.args.get('field', 'all')

            if not keyword:
                return jsonify({
                    'success': False,
                    'message': '검색어가 필요합니다.'
                }), 400

            results = email_service.search_emails(keyword, field)

            return jsonify({
                'success': True,
                'results': results,
                'count': len(results)
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'검색 오류: {str(e)}'
            }), 500

    @app.route('/api/emails/statistics', methods=['GET'])
    def api_email_statistics():
        """이메일 통계 API"""
        try:
            stats = email_service.get_email_statistics()
            return jsonify({
                'success': True,
                'statistics': stats
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'통계 조회 오류: {str(e)}'
            }), 500

    @app.route('/api/evidence', methods=['GET'])
    def api_evidence_list():
        """증거 목록 API"""
        try:
            evidence_list = evidence_service.get_evidence_list()
            stats = evidence_service.get_evidence_statistics()

            return jsonify({
                'success': True,
                'evidence_list': evidence_list,
                'statistics': stats
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'증거 목록 조회 오류: {str(e)}'
            }), 500

    @app.route('/api/evidence/<folder_name>', methods=['GET'])
    def api_evidence_detail(folder_name):
        """증거 상세 API"""
        try:
            result = evidence_service.get_evidence_details(folder_name)
            return jsonify(result)

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'증거 상세 조회 오류: {str(e)}'
            }), 500

    @app.route('/api/evidence/<folder_name>', methods=['DELETE'])
    def api_delete_evidence(folder_name):
        """증거 삭제 API"""
        try:
            result = evidence_service.delete_evidence(folder_name)
            return jsonify(result)

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'증거 삭제 오류: {str(e)}'
            }), 500

    @app.route('/api/evidence/export', methods=['GET'])
    def api_export_evidence():
        """증거 목록 내보내기 API"""
        try:
            format = request.args.get('format', 'json')

            if format not in ['json', 'csv']:
                return jsonify({
                    'success': False,
                    'message': '지원하지 않는 형식입니다. (json, csv만 지원)'
                }), 400

            export_data = evidence_service.export_evidence_list(format)

            return jsonify({
                'success': True,
                'format': format,
                'data': export_data
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'내보내기 오류: {str(e)}'
            }), 500

    @app.route('/api/evidence/integrity', methods=['GET'])
    def api_evidence_integrity():
        """증거 무결성 검증 API"""
        try:
            result = evidence_service.validate_evidence_integrity()
            return jsonify({
                'success': True,
                'integrity_check': result
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'무결성 검증 오류: {str(e)}'
            }), 500

    @app.route('/api/timeline', methods=['GET'])
    def api_timeline():
        """타임라인 API"""
        try:
            # 증거 목록으로부터 타임라인 생성
            evidence_list = evidence_service.get_evidence_list()
            timeline_result = timeline_service.generate_timeline_from_evidence(
                evidence_list)

            if timeline_result['success']:
                # 웹용 데이터 변환
                timeline_data = timeline_result['timeline']
                summary = timeline_service.get_timeline_summary(timeline_data)

                return jsonify({
                    'success': True,
                    'timeline': timeline_data,
                    'summary': summary
                })
            else:
                return jsonify(timeline_result), 400

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'타임라인 생성 오류: {str(e)}'
            }), 500

    @app.route('/api/timeline/filter', methods=['POST'])
    def api_timeline_filter():
        """타임라인 필터링 API"""
        try:
            data = request.get_json()
            filters = data.get('filters', {})

            # 증거 목록으로부터 타임라인 생성
            evidence_list = evidence_service.get_evidence_list()
            timeline_result = timeline_service.generate_timeline_from_evidence(
                evidence_list)

            if not timeline_result['success']:
                return jsonify(timeline_result), 400

            # 필터 적용
            filtered_timeline = timeline_service.filter_timeline(
                timeline_result['timeline'], filters
            )

            return jsonify({
                'success': True,
                'timeline': filtered_timeline,
                'filters_applied': filters
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'타임라인 필터링 오류: {str(e)}'
            }), 500

    @app.route('/api/timeline/export', methods=['GET'])
    def api_timeline_export():
        """타임라인 내보내기 API"""
        try:
            format = request.args.get('format', 'json')

            if format not in ['json', 'csv', 'html']:
                return jsonify({
                    'success': False,
                    'message': '지원하지 않는 형식입니다. (json, csv, html만 지원)'
                }), 400

            # 타임라인 생성
            evidence_list = evidence_service.get_evidence_list()
            timeline_result = timeline_service.generate_timeline_from_evidence(
                evidence_list)

            if not timeline_result['success']:
                return jsonify(timeline_result), 400

            # 내보내기 데이터 생성
            export_data = timeline_service.export_timeline(
                timeline_result['timeline'], format)

            return jsonify({
                'success': True,
                'format': format,
                'data': export_data
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'타임라인 내보내기 오류: {str(e)}'
            }), 500

    @app.route('/api/files/info', methods=['GET'])
    def api_file_info():
        """파일 정보 API"""
        try:
            file_path = request.args.get('path')

            if not file_path:
                return jsonify({
                    'success': False,
                    'message': 'path 매개변수가 필요합니다.'
                }), 400

            file_info = file_service.get_file_info(file_path)
            return jsonify({
                'success': True,
                'file_info': file_info
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'파일 정보 조회 오류: {str(e)}'
            }), 500

    # Single /api/upload handler (supports GET: list, POST: multipart upload)

    @app.route('/api/files/list', methods=['GET'])
    def api_list_files():
        """파일 목록 API"""
        try:
            directory = request.args.get('directory', '.')
            file_type = request.args.get('type', 'all')

            files = file_service.list_directory(directory, file_type)

            return jsonify({
                'success': True,
                'directory': directory,
                'files': files,
                'count': len(files)
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'파일 목록 조회 오류: {str(e)}'
            }), 500

    @app.route('/api/upload', methods=['GET', 'POST'])
    def api_upload_file():
        """파일 업로드 (GET: 목록, POST: 업로드)"""
        try:
            # Respect feature flag for uploads
            flags = app.config.get('FEATURE_FLAGS', {})
            if not flags.get('enable_upload', True):
                return jsonify({'success': False, 'message': '업로드 기능이 비활성화되어 있습니다.'}), 403

            upload_dir = Path(app.config.get('UPLOAD_FOLDER', 'uploads'))
            upload_dir.mkdir(parents=True, exist_ok=True)

            if request.method == 'GET':
                files = []
                for p in sorted(upload_dir.iterdir()):
                    # skip hidden/temp files
                    if p.name.startswith('.'):
                        continue
                    try:
                        size = p.stat().st_size
                    except Exception:
                        size = None
                    files.append({
                        'name': p.name,
                        'path': str(p),
                        'size': size,
                        'is_dir': p.is_dir()
                    })
                return jsonify({'success': True, 'upload_folder': str(upload_dir), 'files': files})

            # POST handling
            # Optional token-based access control: if UPLOAD_API_TOKEN is set in
            # app config, require Authorization: Bearer <token> header.
            upload_token = app.config.get('UPLOAD_API_TOKEN')
            if upload_token:
                auth = request.headers.get('Authorization', '')
                if not auth.startswith('Bearer '):
                    return jsonify({'success': False, 'message': '인증 토큰이 필요합니다.'}), 401
                provided = auth.split(' ', 1)[1].strip()
                if provided != upload_token:
                    return jsonify({'success': False, 'message': '유효하지 않은 인증 토큰입니다.'}), 401

            if 'file' not in request.files:
                return jsonify({'success': False, 'message': "'file' 필드가 필요합니다."}), 400

            upload = request.files['file']
            if not upload:
                return jsonify({'success': False, 'message': "업로드된 파일이 없습니다."}), 400

            # filename may be None (some clients). Guard before calling secure_filename
            filename_raw = upload.filename
            if not filename_raw:
                return jsonify({'success': False, 'message': '파일 이름이 비어 있습니다.'}), 400

            # sanitize and enforce safe filename
            filename = secure_filename(filename_raw)
            if not filename:
                return jsonify({'success': False, 'message': '안전한 파일명을 생성할 수 없습니다.'}), 400

            # Basic filename length guard
            if len(filename) > 255:
                return jsonify({'success': False, 'message': '파일 이름이 너무 깁니다.'}), 400

            # Allowed extension check (configurable) - normalize to lowercase
            allowed = set([e.lower() for e in app.config.get('ALLOWED_UPLOAD_EXTENSIONS', [
                'mbox', 'eml', 'txt', 'pdf', 'zip', '7z', 'tar', 'gz', 'csv', 'xlsx', 'xls', 'msg'
            ])])
            ext = Path(filename).suffix.lower().lstrip('.')
            if ext and ext not in allowed:
                return jsonify({'success': False, 'message': f'허용되지 않는 파일 확장자: .{ext}'}), 400

            # Optional content-length pre-check
            content_length = request.content_length
            max_len = app.config.get('MAX_CONTENT_LENGTH')
            if content_length and max_len and content_length > max_len:
                return jsonify({'success': False, 'message': '업로드 파일이 허용 크기를 초과합니다.'}), 413
            # Avoid overwriting existing files: create a unique filename if needed
            dest = upload_dir / filename
            if dest.exists():
                base = Path(filename).stem
                suffix = Path(filename).suffix
                counter = 1
                while True:
                    candidate = f"{base}_{counter}{suffix}"
                    candidate_path = upload_dir / candidate
                    if not candidate_path.exists():
                        dest = candidate_path
                        filename = candidate
                        break
                    counter += 1

            # Save uploaded file atomically to a temp file then rename
            import os
            import tempfile
            tmp_path = None
            try:
                fd, tmp_name = tempfile.mkstemp(
                    prefix='.tmp_upload_', dir=str(upload_dir))
                os.close(fd)
                tmp_path = Path(tmp_name)
                # Use the Werkzeug FileStorage.save() to write to temp path
                upload.save(str(tmp_path))
                # Move into place atomically
                try:
                    os.replace(str(tmp_path), str(dest))
                except Exception:
                    # Fall back to rename
                    os.rename(str(tmp_path), str(dest))
                # Try to set restrictive permissions (best-effort; Windows may ignore)
                try:
                    os.chmod(str(dest), 0o600)
                except Exception:
                    pass
            except Exception as e:
                # cleanup temp file if present
                try:
                    if tmp_path and tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass
                if hasattr(app, 'logger'):
                    app.logger.error(f"파일 저장 실패: {e}")
                return jsonify({'success': False, 'message': f'파일 저장 실패: {e}'}), 500

            # Validate / gather file info using existing file_service
            try:
                info = file_service.get_file_info(str(dest))
            except Exception:
                # fall back to basic info if service fails
                info = {
                    'path': str(dest),
                    'size': dest.stat().st_size if dest.exists() else None,
                }

            return jsonify({
                'success': True,
                'message': '파일 업로드 완료',
                'filename': filename,
                'file_info': info
            })

        except Exception as e:
            return jsonify({'success': False, 'message': f'업로드 오류: {str(e)}'}), 500

    @app.route('/api/system/disk-usage', methods=['GET'])
    def api_disk_usage():
        """디스크 사용량 API"""
        try:
            path = request.args.get('path', '.')
            usage = file_service.get_disk_usage(path)

            return jsonify({
                'success': True,
                'disk_usage': usage
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'디스크 사용량 조회 오류: {str(e)}'
            }), 500

    @app.route('/api/system/cleanup', methods=['POST'])
    def api_cleanup():
        """시스템 정리 API"""
        try:
            temp_dir = request.json.get(
                'temp_dir', 'temp') if request.json else 'temp'
            result = file_service.clean_temp_files(temp_dir)

            return jsonify(result)

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'시스템 정리 오류: {str(e)}'
            }), 500
