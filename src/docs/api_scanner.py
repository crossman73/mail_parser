"""
API 자동 스캔 시스템
현재 Flask 애플리케이션의 모든 라우트와 API를 분석
"""
import ast
import inspect
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class APIScanner:
    """API 엔드포인트 자동 스캐너"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.templates_dir = self.project_root / "templates"
        self.logger = logging.getLogger(__name__)

        # 발견된 API 정보 저장
        self.api_endpoints = {}
        self.route_handlers = {}
        self.api_models = {}

    def scan_all_apis(self) -> Dict[str, Any]:
        """프로젝트 전체 API 스캔"""
        print("🔍 API 엔드포인트 스캔 시작...")

        # 1. Flask 라우트 스캔
        flask_routes = self._scan_flask_routes()

        # 2. API 모델 스캔
        api_models = self._scan_api_models()

        # 3. 템플릿 분석
        template_info = self._analyze_templates()

        # 4. 설정 파일 분석
        config_info = self._analyze_config()

        # 통합 결과
        scan_result = {
            'scan_timestamp': self._get_timestamp(),
            'project_info': {
                'name': '이메일 증거 처리 시스템',
                'version': '2.0',
                'description': '한국 법원 제출용 이메일 증거 처리 및 분류 시스템'
            },
            'flask_routes': flask_routes,
            'api_models': api_models,
            'templates': template_info,
            'configuration': config_info,
            'statistics': self._calculate_statistics(flask_routes, api_models)
        }

        print(
            f"✅ API 스캔 완료: {scan_result['statistics']['total_endpoints']}개 엔드포인트 발견")
        return scan_result

    def _scan_flask_routes(self) -> Dict[str, List[Dict]]:
        """Flask 라우트 스캔"""
        routes = {
            'web_routes': [],
            'api_routes': [],
            'factory_routes': []
        }

        # src/web/routes.py 분석
        routes_file = self.src_dir / "web" / "routes.py"
        if routes_file.exists():
            web_routes = self._parse_routes_file(routes_file)
            routes['web_routes'] = web_routes
            print(f"📄 routes.py: {len(web_routes)}개 라우트 발견")

        # src/web/app_factory.py 분석
        factory_file = self.src_dir / "web" / "app_factory.py"
        if factory_file.exists():
            factory_routes = self._parse_routes_file(factory_file)
            routes['factory_routes'] = factory_routes
            print(f"🏭 app_factory.py: {len(factory_routes)}개 라우트 발견")

        # 기타 라우트 파일들 스캔
        route_files = list(self.src_dir.rglob("*route*.py")) + \
            list(self.src_dir.rglob("*api*.py"))
        for route_file in route_files:
            if route_file not in [routes_file, factory_file]:
                additional_routes = self._parse_routes_file(route_file)
                if '/api/' in str(route_file) or 'api' in route_file.name:
                    routes['api_routes'].extend(additional_routes)
                else:
                    routes['web_routes'].extend(additional_routes)

        return routes

    def _parse_routes_file(self, file_path: Path) -> List[Dict]:
        """개별 라우트 파일 파싱"""
        routes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # AST로 파싱
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    route_info = self._extract_route_info(node, content)
                    if route_info:
                        route_info['source_file'] = str(
                            file_path.relative_to(self.project_root))
                        routes.append(route_info)

        except Exception as e:
            self.logger.error(f"라우트 파일 파싱 실패 {file_path}: {e}")
            print(f"⚠️ 파싱 실패: {file_path} - {e}")

        return routes

    def _extract_route_info(self, func_node: ast.FunctionDef, source_content: str) -> Optional[Dict]:
        """함수에서 라우트 정보 추출"""
        route_info = None

        # 데코레이터에서 @app.route 찾기
        for decorator in func_node.decorator_list:
            if self._is_route_decorator(decorator):
                route_info = {
                    'function_name': func_node.name,
                    'docstring': ast.get_docstring(func_node) or f'{func_node.name} 엔드포인트',
                    'line_number': func_node.lineno,
                    'path': self._extract_route_path(decorator),
                    'methods': self._extract_http_methods(decorator),
                    'parameters': self._extract_function_params(func_node),
                    'returns': self._analyze_return_type(func_node, source_content)
                }
                break

        return route_info

    def _is_route_decorator(self, decorator: ast.expr) -> bool:
        """라우트 데코레이터인지 확인"""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr == 'route'
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr == 'route'
        return False

    def _extract_route_path(self, decorator: ast.Call) -> str:
        """라우트 경로 추출"""
        if hasattr(decorator, 'args') and decorator.args and isinstance(decorator.args[0], ast.Constant):
            return decorator.args[0].value
        return "unknown"

    def _extract_http_methods(self, decorator: ast.Call) -> List[str]:
        """HTTP 메서드 추출"""
        methods = ['GET']  # 기본값

        if hasattr(decorator, 'keywords'):
            for keyword in decorator.keywords:
                if keyword.arg == 'methods':
                    if isinstance(keyword.value, ast.List):
                        methods = []
                        for item in keyword.value.elts:
                            if isinstance(item, ast.Constant):
                                methods.append(item.value)

        return methods

    def _extract_function_params(self, func_node: ast.FunctionDef) -> List[Dict]:
        """함수 파라미터 분석"""
        params = []

        for arg in func_node.args.args:
            param_info = {
                'name': arg.arg,
                'type': self._get_type_annotation(arg.annotation) if arg.annotation else 'Any',
                'description': f'{arg.arg} 파라미터'
            }
            params.append(param_info)

        return params

    def _analyze_return_type(self, func_node: ast.FunctionDef, source_content: str) -> Dict:
        """반환 타입 분석"""
        returns = {'type': 'Unknown', 'description': '응답'}

        # 함수 본문에서 return 문 찾기
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value:
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == 'jsonify':
                            returns['type'] = 'JSON'
                            returns['description'] = 'JSON 응답'
                        elif node.value.func.id == 'render_template':
                            returns['type'] = 'HTML'
                            returns['description'] = 'HTML 템플릿 렌더링'
                        elif node.value.func.id == 'redirect':
                            returns['type'] = 'Redirect'
                            returns['description'] = 'HTTP 리다이렉션'
                break

        return returns

    def _scan_api_models(self) -> Dict[str, List[Dict]]:
        """API에서 사용되는 데이터 모델 스캔"""
        models = {
            'dataclasses': [],
            'unified_architecture': [],
            'custom_classes': []
        }

        # src/core/unified_architecture.py의 SystemConfig 스캔
        unified_arch_file = self.src_dir / "core" / "unified_architecture.py"
        if unified_arch_file.exists():
            dataclass_models = self._scan_dataclass_models(unified_arch_file)
            models['unified_architecture'] = dataclass_models

        # 다른 모델 파일들 스캔
        for model_file in self.src_dir.rglob("*.py"):
            if 'model' in model_file.name.lower() and model_file != unified_arch_file:
                file_models = self._scan_service_models(model_file)
                models['custom_classes'].extend(file_models)

        return models

    def _scan_dataclass_models(self, file_path: Path) -> List[Dict]:
        """데이터클래스 모델 스캔"""
        models = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # @dataclass 데코레이터 확인
                    has_dataclass = any(
                        (isinstance(d, ast.Name) and d.id == 'dataclass') or
                        (isinstance(d, ast.Call) and isinstance(
                            d.func, ast.Name) and d.func.id == 'dataclass')
                        for d in node.decorator_list
                    )

                    if has_dataclass or 'Config' in node.name:
                        model_info = {
                            'name': node.name,
                            'docstring': ast.get_docstring(node) or f'{node.name} 클래스',
                            'fields': self._extract_dataclass_fields(node),
                            'source_file': str(file_path.relative_to(self.project_root)),
                            'type': 'dataclass' if has_dataclass else 'config_class'
                        }
                        models.append(model_info)

        except Exception as e:
            self.logger.error(f"모델 파일 스캔 실패 {file_path}: {e}")

        return models

    def _extract_dataclass_fields(self, class_node: ast.ClassDef) -> List[Dict]:
        """데이터클래스 필드 추출"""
        fields = []

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                field_info = {
                    'name': node.target.id,
                    'type': self._get_type_annotation(node.annotation),
                    'default': self._get_default_value(node.value) if node.value else None,
                    'description': f'{node.target.id} 필드'
                }
                fields.append(field_info)

        return fields

    def _analyze_templates(self) -> Dict[str, Any]:
        """템플릿 파일 분석"""
        template_info = {
            'templates': [],
            'total_count': 0,
            'template_variables': set()
        }

        if not self.templates_dir.exists():
            return template_info

        for template_file in self.templates_dir.glob("*.html"):
            template_data = self._analyze_single_template(template_file)
            template_info['templates'].append(template_data)
            template_info['template_variables'].update(
                template_data['variables'])

        template_info['total_count'] = len(template_info['templates'])
        template_info['template_variables'] = list(
            template_info['template_variables'])

        return template_info

    def _analyze_single_template(self, template_file: Path) -> Dict:
        """개별 템플릿 분석"""
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Jinja2 변수 추출 ({{ variable }})
            variables = re.findall(r'\{\{\s*(\w+(?:\.\w+)*)', content)

            # 블록 추출 ({% block name %})
            blocks = re.findall(r'\{\%\s*block\s+(\w+)', content)

            return {
                'filename': template_file.name,
                'path': str(template_file.relative_to(self.project_root)),
                'variables': list(set(variables)),
                'blocks': list(set(blocks)),
                'size': len(content)
            }

        except Exception as e:
            self.logger.error(f"템플릿 분석 실패 {template_file}: {e}")
            return {
                'filename': template_file.name,
                'path': str(template_file.relative_to(self.project_root)),
                'variables': [],
                'blocks': [],
                'size': 0,
                'error': str(e)
            }

    def _analyze_config(self) -> Dict[str, Any]:
        """설정 파일 분석"""
        config_file = self.project_root / "config.json"
        config_info = {'exists': False, 'settings': {}}

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                config_info = {
                    'exists': True,
                    'settings': config_data,
                    'categories': list(config_data.keys()) if isinstance(config_data, dict) else [],
                    'file_path': str(config_file.relative_to(self.project_root))
                }
            except Exception as e:
                config_info['error'] = str(e)

        return config_info

    def _calculate_statistics(self, routes: Dict, models: Dict) -> Dict[str, int]:
        """통계 계산"""
        total_routes = sum(len(route_list) for route_list in routes.values())
        total_models = sum(len(model_list) for model_list in models.values())

        return {
            'total_endpoints': total_routes,
            'web_routes': len(routes.get('web_routes', [])),
            'api_routes': len(routes.get('api_routes', [])),
            'factory_routes': len(routes.get('factory_routes', [])),
            'total_models': total_models,
            'dataclass_models': len(models.get('dataclasses', [])),
            'unified_models': len(models.get('unified_architecture', [])),
            'custom_models': len(models.get('custom_classes', []))
        }

    def _get_timestamp(self) -> str:
        """현재 타임스탬프"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _get_type_annotation(self, annotation) -> str:
        """타입 어노테이션 문자열로 변환"""
        if annotation is None:
            return 'Any'
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_type_annotation(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            return f"{self._get_type_annotation(annotation.value)}[{self._get_type_annotation(annotation.slice)}]"
        return 'Any'

    def _get_default_value(self, value_node) -> Any:
        """기본값 추출"""
        if isinstance(value_node, ast.Constant):
            return value_node.value
        elif isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Attribute) and value_node.func.attr == 'default_factory':
                return 'default_factory(...)'
        return None

    def _scan_service_models(self, service_file: Path) -> List[Dict]:
        """서비스 파일에서 사용자 정의 클래스 스캔"""
        models = []

        try:
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 중요한 클래스인지 확인
                    if any(keyword in node.name for keyword in ['Service', 'Manager', 'Processor', 'Generator']):
                        model_info = {
                            'name': node.name,
                            'type': 'service_class',
                            'docstring': ast.get_docstring(node) or f'{node.name} 클래스',
                            'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                            'source_file': str(service_file.relative_to(self.project_root))
                        }
                        models.append(model_info)

        except Exception as e:
            self.logger.error(f"서비스 모델 스캔 실패 {service_file}: {e}")

        return models
