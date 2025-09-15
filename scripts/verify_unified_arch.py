from src.web.app_factory import create_app
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'src' package imports work when
# running this script from the scripts/ directory.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


app = create_app()
ua = getattr(app, 'unified_arch', None)
print('has unified_arch =', ua is not None)
if ua:
    s = ua.get_system_status()
    print('system_status keys:', list(s.keys()))
    print('registered_services:', s.get('registered_services'))
    print("uploads dir:", s.get('directories', {}).get('uploads'))
