"""src.web 패키지

경량화: 패키지 임포트 시 서브모듈을 즉시 불러오지 않도록 구현합니다.
서브모듈은 필요할 때 (`from src.web import app_factory; app_factory.create_app`) 직접 임포트하세요.
"""

__all__ = [
    'routes',
    'api'
]

# 주의: 패키지 임포트 시 heavy dependencies(openpyxl, numpy 등)를 피하기 위해
# 하위 모듈을 여기에 직접 import 하지 않습니다. 사용 시 명시적으로 불러오세요.

# 프로젝트 루트를 sys.path에 추가하여 `src.*` 절대 임포트가 정상 동작하도록 함
from pathlib import Path
import sys

try:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except Exception:
    # 실패 시 무시 — 런타임에서 다른 진입점이 sys.path를 설정할 수 있음
    pass
