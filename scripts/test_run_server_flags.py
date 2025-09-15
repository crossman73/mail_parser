import run_server
import importlib.util
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


main = run_server.main

print('Testing main(auto_kill=False)')
try:
    main(port=5001, auto_kill=False, start_server=False)
except SystemExit as e:
    print('Exited with', e)
except Exception as e:
    print('Error:', e)

print('\nTesting main(auto_kill=True)')
try:
    main(port=5002, auto_kill=True, start_server=False)
except SystemExit as e:
    print('Exited with', e)
except Exception as e:
    print('Error:', e)
