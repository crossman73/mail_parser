"""
Swagger UI 통합 서비스
OpenAPI 명세를 기반으로 실시간 API 문서 인터페이스 제공
"""
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request


class SwaggerUIService:
    """Swagger UI 서비스 클래스"""

    def __init__(self, app: Flask = None, openapi_json_path: str = None):
        self.app = app
        self.openapi_json_path = Path(openapi_json_path or "docs/openapi.json")
        self.logger = logging.getLogger(__name__)

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Flask 앱에 Swagger UI 라우트 등록"""
        self.app = app

        # Swagger UI 메인 페이지
        app.add_url_rule(
            '/api/swagger-ui',
            'swagger_ui',
            self.swagger_ui,
            methods=['GET']
        )

        # OpenAPI JSON 동적 서빙
        app.add_url_rule(
            '/api/openapi.json',
            'openapi_json',
            self.serve_openapi_json,
            methods=['GET']
        )

        # API 문서 대시보드
        app.add_url_rule(
            '/api/docs-dashboard',
            'api_docs_dashboard',
            self.docs_dashboard,
            methods=['GET']
        )

        # Swagger UI 설정 API
        app.add_url_rule(
            '/api/swagger-config',
            'swagger_config',
            self.swagger_config,
            methods=['GET']
        )

        print("🔌 Swagger UI 서비스 초기화 완료")

    def swagger_ui(self):
        """Swagger UI 메인 페이지"""
        try:
            swagger_html = self._generate_swagger_html()
            return swagger_html
        except Exception as e:
            self.logger.error(f"Swagger UI 로드 실패: {e}")
            return f"<h1>Swagger UI 로드 실패</h1><p>{e}</p>", 500

    def serve_openapi_json(self):
        """OpenAPI JSON 명세 동적 서빙"""
        try:
            if not self.openapi_json_path.exists():
                # OpenAPI JSON이 없으면 실시간 생성
                return self._generate_openapi_on_demand()

            # 파일에서 로드
            with open(self.openapi_json_path, 'r', encoding='utf-8') as f:
                openapi_data = json.load(f)

            # 서버 URL 동적 업데이트
            base_url = request.url_root.rstrip('/')
            openapi_data['servers'] = [
                {
                    "url": base_url,
                    "description": "현재 서버"
                }
            ]

            return jsonify(openapi_data)

        except Exception as e:
            self.logger.error(f"OpenAPI JSON 서빙 실패: {e}")
            return jsonify({
                "openapi": "3.0.3",
                "info": {
                    "title": "API 문서 로드 실패",
                    "version": "1.0.0",
                    "description": f"OpenAPI 명세 로드 중 오류가 발생했습니다: {e}"
                },
                "paths": {}
            })

    def docs_dashboard(self):
        """API 문서 대시보드"""
        try:
            dashboard_html = self._generate_docs_dashboard()
            return dashboard_html
        except Exception as e:
            self.logger.error(f"문서 대시보드 생성 실패: {e}")
            return f"<h1>문서 대시보드 오류</h1><p>{e}</p>", 500

    def swagger_config(self):
        """Swagger UI 설정 정보"""
        config = {
            "swagger": "2.0",
            "info": {
                "version": "2.0.0",
                "title": "이메일 증거 처리 시스템 API"
            },
            "host": request.host,
            "schemes": ["http", "https"],
            "consumes": ["application/json"],
            "produces": ["application/json"],
            "securityDefinitions": {},
            "security": [],
            "paths": {}
        }
        return jsonify(config)

    def _generate_swagger_html(self) -> str:
        """Swagger UI HTML 생성"""
        base_url = request.url_root.rstrip('/')

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API 문서 - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin: 0;
            background: #fafafa;
        }}
        .swagger-ui .topbar {{
            display: none;
        }}
        .custom-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .custom-header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 300;
        }}
        .custom-header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        .api-info {{
            background: white;
            padding: 15px;
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .api-links {{
            display: flex;
            gap: 10px;
        }}
        .api-links a {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            transition: background 0.3s;
        }}
        .api-links a:hover {{
            background: #5a67d8;
        }}
    </style>
</head>
<body>
    <div class="custom-header">
        <h1>📧 이메일 증거 처리 시스템 API</h1>
        <p>실시간 API 문서 및 테스트 인터페이스 | Phase 2.3 Swagger UI</p>
    </div>

    <div class="api-info">
        <div>
            <strong>🔌 API 베이스 URL:</strong> <code>{base_url}</code>
            <br>
            <strong>📅 문서 생성:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        <div class="api-links">
            <a href="{base_url}/api/openapi.json" target="_blank">📋 OpenAPI JSON</a>
            <a href="{base_url}/api/docs-dashboard">📊 문서 대시보드</a>
            <a href="{base_url}/docs">📖 기존 문서</a>
        </div>
    </div>

    <div id="swagger-ui"></div>

    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: '{base_url}/api/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                requestInterceptor: function(request) {{
                    // API 요청에 한국어 헤더 추가
                    request.headers['Accept-Language'] = 'ko-KR,ko;q=0.9,en;q=0.8';
                    return request;
                }},
                responseInterceptor: function(response) {{
                    // 응답 로깅
                    console.log('API Response:', response.status, response.url);
                    return response;
                }}
            }});

            // 로딩 완료 후 추가 설정
            setTimeout(function() {{
                console.log('🔌 Swagger UI 로드 완료');

                // Try It Out 기본 활성화
                const tryItOutButtons = document.querySelectorAll('.btn.try-out__btn');
                tryItOutButtons.forEach(btn => {{
                    if (btn.textContent.includes('Try it out')) {{
                        btn.click();
                    }}
                }});
            }}, 2000);
        }};
    </script>
</body>
</html>"""

    def _generate_docs_dashboard(self) -> str:
        """문서 대시보드 HTML 생성"""
        base_url = request.url_root.rstrip('/')

        # docs 디렉토리 정보 수집
        docs_dir = Path("docs")
        docs_info = []

        if docs_dir.exists():
            for doc_file in docs_dir.glob("*"):
                if doc_file.is_file():
                    stat = doc_file.stat()
                    docs_info.append({
                        'name': doc_file.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'path': str(doc_file)
                    })

        # 문서 목록 HTML 생성
        docs_list_html = ""
        for doc in sorted(docs_info, key=lambda x: x['modified'], reverse=True):
            file_icon = self._get_file_icon(doc['name'])
            size_mb = doc['size'] / 1024 / 1024
            docs_list_html += f"""
            <div class="doc-item">
                <div class="doc-icon">{file_icon}</div>
                <div class="doc-info">
                    <h3>{doc['name']}</h3>
                    <p>크기: {size_mb:.2f} MB | 수정: {doc['modified'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="doc-actions">
                    <a href="{base_url}/docs/{doc['name']}" target="_blank" class="btn">📂 열기</a>
                </div>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 API 문서 대시보드</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f7fa;
            color: #2d3748;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .dashboard-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #667eea;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .docs-section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .doc-item {{
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #e2e8f0;
            transition: background 0.2s;
        }}
        .doc-item:hover {{
            background: #f8f9fa;
        }}
        .doc-icon {{
            font-size: 24px;
            margin-right: 15px;
            min-width: 40px;
        }}
        .doc-info {{
            flex: 1;
        }}
        .doc-info h3 {{
            margin: 0 0 5px 0;
            font-size: 16px;
        }}
        .doc-info p {{
            color: #718096;
            font-size: 14px;
        }}
        .doc-actions {{
            display: flex;
            gap: 10px;
        }}
        .btn {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #5a67d8;
        }}
        .quick-actions {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .action-btn {{
            padding: 12px 24px;
            background: #48bb78;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background 0.3s;
        }}
        .action-btn:hover {{
            background: #38a169;
        }}
        .action-btn.secondary {{
            background: #ed8936;
        }}
        .action-btn.secondary:hover {{
            background: #dd6b20;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 API 문서 대시보드</h1>
        <p>실시간 문서 관리 및 모니터링 | Phase 2.3</p>
    </div>

    <div class="container">
        <div class="quick-actions">
            <a href="{base_url}/api/swagger-ui" class="action-btn">🔌 Swagger UI</a>
            <a href="{base_url}/api/openapi.json" class="action-btn" target="_blank">📋 OpenAPI JSON</a>
            <a href="{base_url}/docs" class="action-btn secondary">📖 기존 문서</a>
            <button onclick="regenerateDocs()" class="action-btn secondary">🔄 문서 재생성</button>
        </div>

        <div class="dashboard-grid">
            <div class="dashboard-card">
                <div class="card-title">📈 문서 통계</div>
                <div class="stat-number">{len(docs_info)}</div>
                <p>생성된 문서 파일</p>
            </div>

            <div class="dashboard-card">
                <div class="card-title">⏱️ 마지막 업데이트</div>
                <div class="stat-number">{datetime.now().strftime('%H:%M')}</div>
                <p>{datetime.now().strftime('%Y-%m-%d')}</p>
            </div>

            <div class="dashboard-card">
                <div class="card-title">🔌 API 상태</div>
                <div class="stat-number">✅</div>
                <p>서비스 정상 운영</p>
            </div>
        </div>

        <div class="docs-section">
            <h2 class="card-title">📚 생성된 문서 목록</h2>
            {docs_list_html if docs_list_html else '<p>생성된 문서가 없습니다.</p>'}
        </div>
    </div>

    <script>
        function regenerateDocs() {{
            if (confirm('문서를 재생성하시겠습니까?')) {{
                // 문서 재생성 API 호출
                fetch('{base_url}/api/regenerate-docs', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                }})
                .then(response => response.json())
                .then(data => {{
                    alert('문서 재생성 완료: ' + data.message);
                    location.reload();
                }})
                .catch(error => {{
                    alert('문서 재생성 실패: ' + error);
                }});
            }}
        }}

        console.log('📊 문서 대시보드 로드 완료');
    </script>
</body>
</html>"""

    def _generate_openapi_on_demand(self):
        """실시간 OpenAPI 명세 생성"""
        try:
            from .api_scanner import APIScanner
            from .doc_generator import DocumentGenerator

            # API 스캔
            scanner = APIScanner()
            scan_result = scanner.scan_all_apis()

            # OpenAPI JSON만 생성
            generator = DocumentGenerator()
            openapi_path = generator._generate_openapi_spec(scan_result)

            # 생성된 파일 로드
            with open(openapi_path, 'r', encoding='utf-8') as f:
                openapi_data = json.load(f)

            return jsonify(openapi_data)

        except Exception as e:
            self.logger.error(f"실시간 OpenAPI 생성 실패: {e}")
            return jsonify({
                "openapi": "3.0.3",
                "info": {
                    "title": "실시간 API 문서 생성 실패",
                    "version": "1.0.0",
                    "description": f"OpenAPI 명세 실시간 생성 중 오류: {e}"
                },
                "paths": {}
            })

    def _get_file_icon(self, filename: str) -> str:
        """파일 확장자별 아이콘 반환"""
        ext = Path(filename).suffix.lower()

        icon_map = {
            '.md': '📄',
            '.html': '🌐',
            '.json': '🔧',
            '.pdf': '📋',
            '.txt': '📝',
            '.py': '🐍',
            '.js': '📜',
            '.css': '🎨',
            '.yml': '⚙️',
            '.yaml': '⚙️'
        }

        return icon_map.get(ext, '📁')


def init_swagger_ui(app: Flask, openapi_json_path: str = None) -> SwaggerUIService:
    """Flask 앱에 Swagger UI 서비스 초기화 (편의 함수)"""
    swagger_service = SwaggerUIService(app, openapi_json_path)
    return swagger_service
