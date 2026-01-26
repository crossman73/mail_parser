"""
API 문서 재생성 엔드포인트
"""
import time
from pathlib import Path

from flask import Blueprint, jsonify

# Blueprint 생성
docs_api = Blueprint('docs_api', __name__, url_prefix='/api')


@docs_api.route('/regenerate-docs', methods=['POST'])
def regenerate_docs():
    """문서 재생성 API"""
    try:
        from ..docs import generate_all_documentation

        start_time = time.time()

        # 문서 생성 실행
        result = generate_all_documentation()

        if result and 'generated_docs' in result:
            generated_docs = result['generated_docs']
            scan_result = result.get('scan_result', {})
            statistics = scan_result.get('statistics', {})

            execution_time = time.time() - start_time

            return jsonify({
                'success': True,
                'message': f'{len(generated_docs)}개 문서 재생성 완료',
                'execution_time': round(execution_time, 2),
                'statistics': {
                    'total_endpoints': statistics.get('total_endpoints', 0),
                    'web_routes': statistics.get('web_routes', 0),
                    'api_routes': statistics.get('api_routes', 0),
                    'factory_routes': statistics.get('factory_routes', 0),
                    'total_models': statistics.get('total_models', 0)
                },
                'generated_files': list(generated_docs.keys())
            })
        else:
            return jsonify({
                'success': False,
                'message': '문서 생성 실패',
                'error': '결과가 없습니다'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '문서 재생성 중 오류 발생',
            'error': str(e)
        }), 500


@docs_api.route('/docs-status', methods=['GET'])
def docs_status():
    """문서 상태 확인 API"""
    try:
        docs_dir = Path("docs")
        docs_info = []

        if docs_dir.exists():
            for doc_file in docs_dir.glob("*"):
                if doc_file.is_file():
                    stat = doc_file.stat()
                    docs_info.append({
                        'name': doc_file.name,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'exists': True
                    })

        return jsonify({
            'success': True,
            'docs_count': len(docs_info),
            'docs': docs_info,
            'docs_directory_exists': docs_dir.exists()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_docs_api(app):
    """Flask 앱에 문서 API 등록"""
    app.register_blueprint(docs_api)
    print("📚 문서 API 블루프린트 등록 완료")
