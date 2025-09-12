from src.core import db_manager

ok = db_manager.set_setting('DEV_RELOAD_TOKEN', 'test-token-123')
print('set ok', ok)
