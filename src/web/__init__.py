"""src.web 패키지

경량화: 패키지 임포트 시 서브모듈을 즉시 불러오지 않도록 구현합니다.
서브모듈은 필요할 때 (`from src.web import app_factory; app_factory.create_app`) 직접 임포트하세요.
"""

__all__ = [
    'app_factory',
    'routes',
    'api'
]

# 주의: 패키지 임포트 시 heavy dependencies(openpyxl, numpy 등)를 피하기 위해
# 하위 모듈을 여기에 직접 import 하지 않습니다. 사용 시 명시적으로 불러오세요.
