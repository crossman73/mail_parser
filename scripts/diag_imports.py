import os
import site
import sys
from pathlib import Path

print('sys.executable=', sys.executable)
print('\n'.join(sys.path))

for name in ('mcp', 'mcp_server_fetch'):
    try:
        mod = __import__(name)
        print(f"\n{name} imported, file={getattr(mod, '__file__', None)}")
    except Exception as e:
        print(f"\n{name} import failed: {e}")

# Also print site-packages locations

print('\nsite.getsitepackages():')
for p in site.getsitepackages():
    print(p)

# Print environment vars relevant to Python

print('\nPYTHONPATH=' + os.environ.get('PYTHONPATH', '<unset>'))
print('PATH=' + os.environ.get('PATH', '')[:300])
