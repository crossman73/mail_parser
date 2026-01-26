#!/usr/bin/env python3
"""test_manager 객체 확인"""

from src.database.email_db import test_manager

print(f"test_manager 타입: {type(test_manager)}")
print(f"test_manager 클래스: {test_manager.__class__.__name__}")
print(f"test_manager DB 경로: {test_manager.db_path}")
print(f"\ntest_manager의 메서드:")
for attr in dir(test_manager):
    if not attr.startswith('_') and callable(getattr(test_manager, attr)):
        print(f"  - {attr}")

print(f"\nget_execution_history() 호출 결과:")
history = test_manager.get_execution_history(limit=2)
print(f"  항목 수: {len(history)}")
if history:
    print(f"  첫 번째 항목의 키: {list(history[0].keys())}")
    print(f"  첫 번째 항목: {history[0]}")
