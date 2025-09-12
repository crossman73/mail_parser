from src.core import db_manager
from src.web.app_factory import create_app

app = create_app()
# ensure DBs
db_manager.init_all()

with app.test_client() as c:
    try:
        r = c.get('/admin/logs')
        print('GET /admin/logs status:', r.status_code)
        body = r.get_data(as_text=True)
        print('BODY_HEAD:\n', body[:1000])
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('ERROR /admin/logs:', e)

    try:
        r2 = c.get('/api/admin/logs')
        print('\nGET /api/admin/logs status:', r2.status_code)
        try:
            print('JSON:', r2.get_json())
        except Exception as e:
            print('JSON parse error:', e)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('ERROR /api/admin/logs:', e)
