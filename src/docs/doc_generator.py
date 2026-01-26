"""
API 문서 자동 생성 엔진
스캔된 API 정보를 바탕으로 다양한 형식의 문서 생성
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class DocumentGenerator:
    """문서 자동 생성기"""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            output_dir = Path("docs")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def generate_all_docs(self, scan_result: Dict[str, Any]) -> Dict[str, Path]:
        """모든 문서 생성"""
        print("📚 API 문서 생성 시작...")

        generated_docs = {}

        try:
            # 1. API Reference (Markdown)
            api_ref_path = self._generate_api_reference_md(scan_result)
            generated_docs['api_reference_md'] = api_ref_path

            # 2. OpenAPI Specification (JSON)
            openapi_path = self._generate_openapi_spec(scan_result)
            generated_docs['openapi_spec'] = openapi_path

            # 3. HTML Documentation
            html_docs_path = self._generate_html_docs(scan_result)
            generated_docs['html_docs'] = html_docs_path

            # 4. Developer Guide
            dev_guide_path = self._generate_developer_guide(scan_result)
            generated_docs['developer_guide'] = dev_guide_path

            # 5. Postman Collection
            postman_path = self._generate_postman_collection(scan_result)
            generated_docs['postman_collection'] = postman_path

            # 6. README 업데이트
            readme_path = self._update_readme(scan_result)
            generated_docs['readme'] = readme_path

            print(f"✅ 문서 생성 완료: {len(generated_docs)}개 파일")
            return generated_docs

        except Exception as e:
            self.logger.error(f"문서 생성 실패: {e}")
            print(f"❌ 문서 생성 실패: {e}")
            return {}

    def _generate_api_reference_md(self, scan_result: Dict[str, Any]) -> Path:
        """API 레퍼런스 마크다운 생성"""
        output_path = self.output_dir / "API_Reference.md"

        project_info = scan_result.get('project_info', {})
        routes = scan_result.get('flask_routes', {})
        models = scan_result.get('api_models', {})
        statistics = scan_result.get('statistics', {})

        md_content = f"""# {project_info.get('name', 'API')} 레퍼런스 📧

**버전**: {project_info.get('version', '1.0')}
**생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**설명**: {project_info.get('description', '')}

## 📊 시스템 현황

- **총 엔드포인트**: {statistics.get('total_endpoints', 0)}개
- **웹 라우트**: {statistics.get('web_routes', 0)}개
- **API 라우트**: {statistics.get('api_routes', 0)}개
- **팩토리 라우트**: {statistics.get('factory_routes', 0)}개
- **데이터 모델**: {statistics.get('total_models', 0)}개

## 📋 목차

- [웹 라우트](#웹-라우트)
- [팩토리 라우트](#팩토리-라우트)
- [API 엔드포인트](#api-엔드포인트)
- [데이터 모델](#데이터-모델)
- [템플릿 정보](#템플릿-정보)
- [설정 정보](#설정-정보)

---

## 🌐 웹 라우트

"""

        # 웹 라우트 문서화
        web_routes = routes.get('web_routes', [])
        if web_routes:
            for route in sorted(web_routes, key=lambda x: x.get('path', '')):
                md_content += self._format_route_markdown(route, 'web')
        else:
            md_content += "현재 웹 라우트가 없습니다.\n\n"

        # 팩토리 라우트 문서화
        md_content += "---\n\n## 🏭 팩토리 라우트\n\n"

        factory_routes = routes.get('factory_routes', [])
        if factory_routes:
            for route in sorted(factory_routes, key=lambda x: x.get('path', '')):
                md_content += self._format_route_markdown(route, 'factory')
        else:
            md_content += "현재 팩토리 라우트가 없습니다.\n\n"

        # API 라우트 문서화
        md_content += "---\n\n## 🔌 API 엔드포인트\n\n"

        api_routes = routes.get('api_routes', [])
        if api_routes:
            for route in sorted(api_routes, key=lambda x: x.get('path', '')):
                md_content += self._format_route_markdown(route, 'api')
        else:
            md_content += "현재 API 라우트가 없습니다.\n\n"

        # 데이터 모델 문서화
        md_content += "---\n\n## 📊 데이터 모델\n\n"

        unified_models = models.get('unified_architecture', [])
        if unified_models:
            for model in unified_models:
                md_content += self._format_model_markdown(model)

        custom_models = models.get('custom_classes', [])
        if custom_models:
            md_content += "\n### 🔧 서비스 클래스\n\n"
            for model in custom_models:
                md_content += self._format_service_class_markdown(model)

        if not unified_models and not custom_models:
            md_content += "현재 발견된 데이터 모델이 없습니다.\n\n"

        # 템플릿 정보
        md_content += self._generate_template_section(
            scan_result.get('templates', {}))

        # 설정 정보
        md_content += self._generate_config_section(
            scan_result.get('configuration', {}))

        # 에러 코드
        md_content += self._generate_error_codes_section()

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"📄 API Reference 생성: {output_path}")
        return output_path

    def _format_route_markdown(self, route: Dict[str, Any], route_type: str) -> str:
        """라우트 정보를 마크다운으로 포맷"""
        path = route.get('path', 'unknown')
        methods = route.get('methods', ['GET'])
        function_name = route.get('function_name', 'unknown')
        docstring = route.get('docstring', '설명 없음')
        source_file = route.get('source_file', 'unknown')

        # HTTP 메서드 뱃지
        method_badges = ' '.join([f"`{method}`" for method in methods])

        md = f"""### {method_badges} `{path}`

**함수**: `{function_name}`
**파일**: `{source_file}`
**설명**: {docstring}

"""

        # 파라미터 정보
        parameters = route.get('parameters', [])
        if parameters:
            md += "**파라미터**:\n"
            for param in parameters:
                md += f"- `{param['name']}` ({param['type']}): {param['description']}\n"
            md += "\n"

        # 응답 정보
        returns = route.get('returns', {})
        if returns.get('type'):
            md += f"**응답**: {returns['type']} - {returns['description']}\n\n"

        # 예시 (API인 경우)
        if route_type == 'api':
            md += self._generate_api_example(path, methods[0])

        md += "---\n\n"
        return md

    def _format_model_markdown(self, model: Dict[str, Any]) -> str:
        """데이터 모델을 마크다운으로 포맷"""
        name = model.get('name', 'Unknown')
        docstring = model.get('docstring', '설명 없음')
        fields = model.get('fields', [])
        source_file = model.get('source_file', 'unknown')

        md = f"""### 📋 {name}

**파일**: `{source_file}`
**설명**: {docstring}

**필드**:
"""

        if fields:
            for field in fields:
                default_info = f" (기본값: `{field['default']}`)" if field['default'] is not None else ""
                md += f"- `{field['name']}: {field['type']}` - {field['description']}{default_info}\n"
        else:
            md += "- 필드 정보를 찾을 수 없습니다.\n"

        md += "\n---\n\n"
        return md

    def _format_service_class_markdown(self, model: Dict[str, Any]) -> str:
        """서비스 클래스를 마크다운으로 포맷"""
        name = model.get('name', 'Unknown')
        docstring = model.get('docstring', '설명 없음')
        methods = model.get('methods', [])
        source_file = model.get('source_file', 'unknown')

        md = f"""#### 🔧 {name}

**파일**: `{source_file}`
**설명**: {docstring}

**메서드**: {', '.join(methods) if methods else '없음'}

---

"""
        return md

    def _generate_api_example(self, path: str, method: str) -> str:
        """API 사용 예시 생성"""
        example = f"""
**사용 예시**:
```bash
curl -X {method} "http://localhost:5000{path}"
```

**응답 예시**:
```json
{{
  "success": true,
  "data": {{}},
  "message": "성공"
}}
```

"""
        return example

    def _generate_template_section(self, template_info: Dict[str, Any]) -> str:
        """템플릿 섹션 생성"""
        section = "\n---\n\n## 🎨 템플릿 정보\n\n"

        templates = template_info.get('templates', [])
        if templates:
            section += f"**총 템플릿**: {len(templates)}개\n\n"

            for template in templates:
                section += f"### 📄 {template['filename']}\n\n"
                section += f"- **경로**: `{template['path']}`\n"
                section += f"- **크기**: {template['size']} bytes\n"

                variables = template.get('variables', [])
                if variables:
                    section += f"- **변수**: {', '.join([f'`{var}`' for var in variables])}\n"

                blocks = template.get('blocks', [])
                if blocks:
                    section += f"- **블록**: {', '.join([f'`{block}`' for block in blocks])}\n"

                section += "\n"
        else:
            section += "현재 발견된 템플릿이 없습니다.\n\n"

        return section

    def _generate_config_section(self, config_info: Dict[str, Any]) -> str:
        """설정 섹션 생성"""
        section = "\n---\n\n## ⚙️ 설정 정보\n\n"

        if config_info.get('exists'):
            section += f"**설정 파일**: `{config_info.get('file_path', 'config.json')}`\n\n"

            categories = config_info.get('categories', [])
            if categories:
                section += f"**설정 카테고리**: {', '.join([f'`{cat}`' for cat in categories])}\n\n"

            settings = config_info.get('settings', {})
            if isinstance(settings, dict) and len(settings) > 0:
                section += "**주요 설정**:\n"
                for key, value in list(settings.items())[:5]:  # 처음 5개만 표시
                    if isinstance(value, (str, int, bool)):
                        section += f"- `{key}`: `{value}`\n"
                    else:
                        section += f"- `{key}`: (복합 설정)\n"
                section += "\n"
        else:
            section += "설정 파일이 없거나 로드할 수 없습니다.\n\n"

        return section

    def _generate_openapi_spec(self, scan_result: Dict[str, Any]) -> Path:
        """OpenAPI 3.0 명세 생성"""
        output_path = self.output_dir / "openapi.json"

        project_info = scan_result.get('project_info', {})
        routes = scan_result.get('flask_routes', {})

        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": project_info.get('name', 'Email Evidence Processing API'),
                "version": project_info.get('version', '2.0'),
                "description": project_info.get('description', ''),
                "contact": {
                    "name": "개발팀",
                    "email": "dev@example.com"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:5000",
                    "description": "개발 서버"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "responses": {
                    "Success": {
                        "description": "성공 응답",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {"type": "object"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "Error": {
                        "description": "오류 응답",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean", "example": False},
                                        "error": {"type": "string"},
                                        "code": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # 모든 라우트를 OpenAPI paths로 변환
        all_routes = []
        for route_list in routes.values():
            all_routes.extend(route_list)

        for route in all_routes:
            path = route.get('path', '')
            methods = route.get('methods', ['GET'])

            if path == 'unknown':
                continue

            # OpenAPI path 형식으로 변환
            openapi_path = path.replace('<', '{').replace('>', '}')

            if openapi_path not in openapi_spec['paths']:
                openapi_spec['paths'][openapi_path] = {}

            for method in methods:
                openapi_spec['paths'][openapi_path][method.lower()] = {
                    "summary": route.get('docstring', ''),
                    "operationId": route.get('function_name', ''),
                    "responses": {
                        "200": {"$ref": "#/components/responses/Success"},
                        "400": {"$ref": "#/components/responses/Error"},
                        "500": {"$ref": "#/components/responses/Error"}
                    },
                    "tags": [self._get_route_tag(path)]
                }

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)

        print(f"🔌 OpenAPI 명세 생성: {output_path}")
        return output_path

    def _generate_html_docs(self, scan_result: Dict[str, Any]) -> Path:
        """HTML 문서 생성"""
        output_path = self.output_dir / "api_docs.html"

        project_info = scan_result.get('project_info', {})
        routes = scan_result.get('flask_routes', {})
        statistics = scan_result.get('statistics', {})

        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_info.get('name', 'API')} 문서</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .nav {{
            background: #34495e;
            padding: 15px;
        }}
        .nav a {{
            color: white;
            margin-right: 20px;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background 0.3s;
        }}
        .nav a:hover {{ background: rgba(255,255,255,0.2); }}
        .content {{ padding: 30px; }}
        .endpoint {{
            border: 1px solid #e0e6ed;
            margin-bottom: 20px;
            border-radius: 6px;
            overflow: hidden;
        }}
        .endpoint-header {{
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #e0e6ed;
        }}
        .endpoint-body {{ padding: 20px; }}
        .method-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
        }}
        .method-get {{ background: #28a745; }}
        .method-post {{ background: #007bff; }}
        .method-put {{ background: #ffc107; color: #212529; }}
        .method-delete {{ background: #dc3545; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .section {{ margin-bottom: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{project_info.get('name', 'API Documentation')}</h1>
            <p>버전 {project_info.get('version', '1.0')} | 생성일: {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>

        <div class="nav">
            <a href="#overview">개요</a>
            <a href="#web-routes">웹 라우트</a>
            <a href="#factory-routes">팩토리 라우트</a>
            <a href="#api-routes">API 엔드포인트</a>
        </div>

        <div class="content">
            <section id="overview" class="section">
                <h2>📊 시스템 개요</h2>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{statistics.get('total_endpoints', 0)}</div>
                        <div>총 엔드포인트</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{statistics.get('web_routes', 0)}</div>
                        <div>웹 라우트</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{statistics.get('factory_routes', 0)}</div>
                        <div>팩토리 라우트</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{statistics.get('api_routes', 0)}</div>
                        <div>API 라우트</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{statistics.get('total_models', 0)}</div>
                        <div>데이터 모델</div>
                    </div>
                </div>
                <p>{project_info.get('description', '')}</p>
            </section>
"""

        # 웹 라우트 섹션
        html_content += self._generate_routes_html_section(
            "웹 라우트", "web-routes", routes.get('web_routes', [])
        )

        # 팩토리 라우트 섹션
        html_content += self._generate_routes_html_section(
            "팩토리 라우트", "factory-routes", routes.get('factory_routes', [])
        )

        # API 라우트 섹션
        html_content += self._generate_routes_html_section(
            "API 엔드포인트", "api-routes", routes.get('api_routes', [])
        )

        html_content += """
        </div>
    </div>

    <script>
        // 부드러운 스크롤
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>"""

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"🌐 HTML 문서 생성: {output_path}")
        return output_path

    def _generate_routes_html_section(self, title: str, section_id: str, routes: List[Dict]) -> str:
        """라우트 섹션 HTML 생성"""
        html = f"""
            <section id="{section_id}" class="section">
                <h2>🌐 {title}</h2>
"""

        if routes:
            for route in sorted(routes, key=lambda x: x.get('path', '')):
                path = route.get('path', 'unknown')
                methods = route.get('methods', ['GET'])
                function_name = route.get('function_name', 'unknown')
                docstring = route.get('docstring', '설명 없음')
                source_file = route.get('source_file', 'unknown')

                # HTTP 메서드 뱃지
                method_badges = ''
                for method in methods:
                    badge_class = f"method-{method.lower()}"
                    method_badges += f'<span class="method-badge {badge_class}">{method}</span>'

                html += f"""
                <div class="endpoint">
                    <div class="endpoint-header">
                        <strong>{path}</strong>
                        <div style="margin-top: 8px;">
                            {method_badges}
                            <span style="color: #6c757d;">함수: {function_name} | 파일: {source_file}</span>
                        </div>
                    </div>
                    <div class="endpoint-body">
                        <p>{docstring}</p>
                    </div>
                </div>
"""
        else:
            html += f"<p>현재 {title.lower()}가 없습니다.</p>"

        html += "            </section>\n"
        return html

    def _generate_developer_guide(self, scan_result: Dict[str, Any]) -> Path:
        """개발자 가이드 생성"""
        output_path = self.output_dir / "Developer_Guide.md"

        project_info = scan_result.get('project_info', {})
        statistics = scan_result.get('statistics', {})

        guide_content = f"""# {project_info.get('name', '시스템')} 개발자 가이드 🚀

> **자동 생성된 개발자 문서** | 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 프로젝트 현황

- **총 엔드포인트**: {statistics.get('total_endpoints', 0)}개
- **웹 라우트**: {statistics.get('web_routes', 0)}개
- **팩토리 라우트**: {statistics.get('factory_routes', 0)}개
- **API 라우트**: {statistics.get('api_routes', 0)}개
- **데이터 모델**: {statistics.get('total_models', 0)}개

## 🚀 빠른 시작

### 설치 및 실행

```bash
# 1. 저장소 클론
git clone [repository-url]
cd python-email

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 서버 시작
python app.py
# 또는
python main.py --web
```

### 개발 서버

```bash
# 개발 모드로 시작 (자동 재시작)
FLASK_ENV=development python app.py

# 특정 포트로 시작
python main.py --web --port 8080

# 시스템 테스트
python main.py --test
```

## 🏗️ 프로젝트 구조

```
python-email/
├── src/                    # 소스 코드
│   ├── core/               # 핵심 비즈니스 로직
│   │   └── unified_architecture.py  # 통합 아키텍처
│   ├── docs/               # 문서 생성 시스템
│   │   ├── api_scanner.py  # API 자동 스캔
│   │   └── doc_generator.py # 문서 자동 생성
│   ├── mail_parser/        # 이메일 처리 엔진
│   └── web/                # 웹 인터페이스
│       ├── routes.py       # 웹 라우트
│       └── app_factory.py  # Flask 팩토리
├── templates/              # HTML 템플릿
├── static/                 # 정적 파일
├── docs/                   # 문서 (자동 생성)
└── tests/                  # 테스트
```

## 🔧 개발 환경 설정

### Phase 1 - 통합 아키텍처

```bash
# Phase 1 검증
python test_phase1.py

# 시스템 상태 확인
python main.py --test
```

### Phase 2 - API 문서 자동화

```bash
# API 스캔 및 문서 생성
python -c "from src.docs import generate_all_documentation; generate_all_documentation()"

# 개별 문서 생성 테스트
python test_docs_generation.py
```

## 🧪 테스트

### 단위 테스트 실행

```bash
# Phase 1 테스트
python test_phase1.py

# 전체 시스템 테스트
python main.py --test

# 문서 생성 테스트
python test_docs_generation.py
```

## 📝 코딩 스타일

### Python 스타일 가이드

- PEP 8 준수
- Type hints 사용 권장
- Docstring 필수 (Google 스타일)

```python
def process_email(email_path: str, party: str = "갑") -> Dict[str, Any]:
    '''이메일 처리 함수

    Args:
        email_path: 이메일 파일 경로
        party: 당사자 구분 (갑/을)

    Returns:
        처리 결과 딕셔너리

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
    '''
    pass
```

## 🔌 API 개발

### 새 API 엔드포인트 추가

1. 적절한 파일에 라우트 추가 (app_factory.py, routes.py 등)
2. 적절한 HTTP 상태 코드 사용
3. JSON 응답 형식 일관성 유지

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    '''새 API 엔드포인트'''
    try:
        # 처리 로직
        return jsonify({{
            'success': True,
            'data': result,
            'message': '성공'
        }})
    except Exception as e:
        return jsonify({{
            'success': False,
            'error': str(e)
        }}), 500
```

### 자동 문서화

새로운 API를 추가하면 자동으로 문서가 업데이트됩니다:

1. **API 스캔**: `APIScanner`가 자동으로 새 엔드포인트 감지
2. **문서 생성**: `DocumentGenerator`가 마크다운, HTML, OpenAPI 명세 생성
3. **문서 배포**: `docs/` 폴더에 자동 저장

## 📚 문서 시스템

### 자동 생성되는 문서

- **API_Reference.md**: 전체 API 레퍼런스
- **api_docs.html**: 웹용 HTML 문서
- **openapi.json**: OpenAPI 3.0 명세
- **Developer_Guide.md**: 개발자 가이드 (이 파일)
- **postman_collection.json**: Postman 테스트 컬렉션

### 문서 재생성

```bash
# 전체 문서 재생성
python -c "from src.docs import generate_all_documentation; generate_all_documentation()"
```

## 🚀 배포

### 프로덕션 배포

```bash
# Docker로 프로덕션 배포
docker-compose up -d

# 직접 배포
gunicorn -w 4 -b 0.0.0.0:5000 'src.web.app:create_app()'
```

## 📚 추가 리소스

- [API Reference](API_Reference.md) - 전체 API 문서
- [설정 가이드](config_guide.md) - 설정 가이드 (생성 예정)
- [아키텍처 문서](architecture_refactoring.md) - 아키텍처 문서 (생성 예정)

---

**이 문서는 자동으로 생성되었습니다.** Phase 2 API 문서 자동화 시스템이 프로젝트를 스캔하여 실시간으로 업데이트합니다.
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)

        print(f"📖 개발자 가이드 생성: {output_path}")
        return output_path

    def _generate_postman_collection(self, scan_result: Dict[str, Any]) -> Path:
        """Postman 컬렉션 생성"""
        output_path = self.output_dir / "postman_collection.json"

        project_info = scan_result.get('project_info', {})
        routes = scan_result.get('flask_routes', {})

        collection = {
            "info": {
                "name": f"{project_info.get('name', 'API')} Collection",
                "description": project_info.get('description', ''),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "http://localhost:5000",
                    "type": "string"
                }
            ],
            "item": []
        }

        # 모든 라우트를 Postman 요청으로 변환
        all_routes = []
        for route_list in routes.values():
            all_routes.extend(route_list)

        for route in all_routes:
            path = route.get('path', '')
            methods = route.get('methods', ['GET'])

            if path == 'unknown':
                continue

            for method in methods:
                request_item = {
                    "name": f"{method} {path}",
                    "request": {
                        "method": method,
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "url": {
                            "raw": "{{baseUrl}}" + path,
                            "host": ["{{baseUrl}}"],
                            "path": path.strip('/').split('/') if path != '/' else ['']
                        }
                    },
                    "response": []
                }

                # POST/PUT 요청인 경우 샘플 body 추가
                if method in ['POST', 'PUT']:
                    request_item["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps({"example": "data"}, indent=2)
                    }

                collection["item"].append(request_item)

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)

        print(f"📮 Postman 컬렉션 생성: {output_path}")
        return output_path

    def _update_readme(self, scan_result: Dict[str, Any]) -> Path:
        """README.md 업데이트"""
        readme_path = self.output_dir.parent / "README.md"

        project_info = scan_result.get('project_info', {})
        statistics = scan_result.get('statistics', {})

        # 기존 README 백업
        if readme_path.exists():
            backup_path = readme_path.with_suffix('.md.backup')
            try:
                readme_path.rename(backup_path)
                print(f"📄 기존 README 백업: {backup_path}")
            except Exception as e:
                print(f"⚠️ README 백업 실패 (계속 진행): {e}")

        readme_content = f"""# {project_info.get('name', '이메일 증거 처리 시스템')} 📧

> 한국 법원 제출용 이메일 증거 처리 및 분류 시스템 v{project_info.get('version', '2.0')}

## 🎯 주요 기능

- 📧 **mbox/eml 파일 자동 파싱**: Outlook, Thunderbird 등 다양한 메일 클라이언트 지원
- ⚖️ **법정 증거 자동 생성**: 한국 법원 규정에 맞는 증거 번호 및 형식 자동 적용
- 📊 **타임라인 시각화**: 이메일 송수신 흐름을 직관적인 타임라인으로 표시
- 🔒 **무결성 검증**: SHA-256 해시값 기반 디지털 증거 무결성 보장
- 🌐 **웹 인터페이스**: 직관적인 웹 UI로 누구나 쉽게 사용 가능
- 📚 **자동 문서화**: API 스캔을 통한 실시간 문서 생성

## 📊 시스템 현황

- **총 엔드포인트**: {statistics.get('total_endpoints', 0)}개
- **웹 라우트**: {statistics.get('web_routes', 0)}개
- **팩토리 라우트**: {statistics.get('factory_routes', 0)}개
- **API 라우트**: {statistics.get('api_routes', 0)}개
- **데이터 모델**: {statistics.get('total_models', 0)}개

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone [repository-url]
cd python-email

# 의존성 설치
pip install -r requirements.txt
```

### 2. 실행

```bash
# 웹 서버 시작
python app.py

# CLI 모드 (mbox 파일 직접 처리)
python main.py email_files/sample.mbox --party 갑

# Docker로 실행
docker-compose up -d
```

### 3. 접속

- **웹 인터페이스**: http://localhost:5000
- **API 문서**: http://localhost:5000/docs
- **시스템 상태**: http://localhost:5000/system/status
- **헬스체크**: http://localhost:5000/health

## 📋 사용법

### 웹 인터페이스 사용

1. **파일 업로드**: mbox 또는 eml 파일을 업로드
2. **이메일 선택**: 증거로 사용할 이메일들 선택
3. **증거 생성**: 당사자 구분(갑/을) 설정 후 증거 자동 생성
4. **결과 다운로드**: PDF, HTML, Excel 형식으로 다운로드

### CLI 사용

```bash
# 기본 사용법
python main.py [mbox파일] --party [갑|을]

# 웹 서버 모드
python main.py --web --port 8080

# 시스템 테스트
python main.py --test

# Phase 1 검증
python test_phase1.py
```

## 🏗️ 아키텍처

### Phase 1: 통합 아키텍처 ✅
- **SystemConfig**: 중앙 집중식 설정 관리
- **UnifiedArchitecture**: 서비스 레지스트리 패턴
- **Flask Factory**: 모듈화된 웹 애플리케이션

### Phase 2: API 문서 자동화 ✅
- **APIScanner**: 코드 자동 스캔 및 분석
- **DocumentGenerator**: 다양한 형식 문서 생성
- **실시간 문서화**: 코드 변경 시 자동 업데이트

### Phase 3: 백그라운드 서비스 (구현 예정)
- 터미널 블록 없는 서비스 실행
- 로그 모니터링 시스템
- 서비스 상태 관리

## 🔧 설정

### config.json 주요 설정

```json
{{
  "exclude_keywords": ["광고", "스팸"],
  "date_range": {{
    "start": "2020-01-01",
    "end": "2025-12-31"
  }},
  "processing_options": {{
    "generate_hash_verification": true,
    "create_backup": true
  }},
  "output_settings": {{
    "evidence_number_format": "{{party}} 제{{number}}호증"
  }}
}}
```

## 🧪 테스트

```bash
# Phase 1 검증
python test_phase1.py

# Phase 2 문서 생성 테스트
python test_docs_generation.py

# 시스템 전체 테스트
python main.py --test
```

## 📚 문서

**자동 생성된 문서들**:
- [📖 API Reference](docs/API_Reference.md) - 전체 API 문서
- [🔧 Developer Guide](docs/Developer_Guide.md) - 개발자 가이드
- [🌐 HTML 문서](docs/api_docs.html) - 웹용 API 문서
- [🔌 OpenAPI 명세](docs/openapi.json) - OpenAPI 3.0 스펙
- [📮 Postman Collection](docs/postman_collection.json) - API 테스트 컬렉션

**수동 문서들**:
- [⚙️ Config Guide](docs/config_guide.md) - 설정 가이드 (생성 예정)
- [🏗️ Architecture](docs/architecture_refactoring.md) - 아키텍처 문서

## 🐳 Docker 지원

```bash
# 개발 환경
docker-compose -f docker-compose.dev.yml up

# 프로덕션 환경
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

## 🔌 API 엔드포인트

현재 발견된 엔드포인트 ({statistics.get('total_endpoints', 0)}개):

**주요 엔드포인트**:
- `GET /` - 메인 페이지
- `GET /health` - 시스템 헬스체크
- `GET /system/status` - 시스템 상태 정보
- `GET /docs` - API 문서 페이지
- `GET /upload` - 파일 업로드 페이지 (구현 예정)

자세한 API 문서는 [API Reference](docs/API_Reference.md)를 참고하세요.

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스하에 배포됩니다.

---

**마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**문서 자동 생성**: Phase 2 API 문서 생성 시스템
**문서 버전**: v2.0 (통합 아키텍처 + 자동 문서화)
"""

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"📄 README.md 업데이트: {readme_path}")
        return readme_path

    def _generate_error_codes_section(self) -> str:
        """에러 코드 섹션 생성"""
        return """
---

## ❌ 에러 코드

### HTTP 상태 코드

| 코드 | 설명 | 대응 방법 |
|------|------|-----------|
| 200  | 성공 | - |
| 400  | 잘못된 요청 | 요청 파라미터 확인 |
| 404  | 리소스 없음 | URL 경로 확인 |
| 413  | 파일 크기 초과 | 2GB 이하 파일 사용 |
| 500  | 서버 오류 | 서버 로그 확인 |

### 커스텀 에러 코드

| 코드 | 메시지 | 설명 |
|------|--------|------|
| E001 | 파일 형식 오류 | 지원되지 않는 파일 형식 |
| E002 | 파싱 실패 | 손상된 메일 파일 |
| E003 | 메모리 부족 | 시스템 리소스 부족 |
| E004 | 권한 오류 | 파일 접근 권한 없음 |

"""

    def _get_route_tag(self, path: str) -> str:
        """라우트 경로에서 태그 추출"""
        if path.startswith('/api/'):
            return 'API'
        elif path.startswith('/admin'):
            return 'Admin'
        else:
            return 'Web'
