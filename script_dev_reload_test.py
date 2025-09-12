from src.web.app import create_app

app = create_app()
app.testing = True

with app.test_client() as c:
    # enable dev reload in config
    app.config['ENABLE_DEV_RELOAD'] = True
    app.config['DEV_RELOAD_MODULES'] = [
        'src.core.hot_reload', 'src.web.admin_routes']
    app.config['DEV_RELOAD_TOKEN'] = 'test-token-123'
    # ensure session CSRF is created by hitting admin page
    c.get('/admin')
    admin_csrf = None
    with c.session_transaction() as sess:
        admin_csrf = sess.get('admin_csrf')

    data = {'modules': ','.join(app.config['DEV_RELOAD_MODULES']),
            'admin_csrf': admin_csrf, 'token': app.config['DEV_RELOAD_TOKEN']}
    r = c.post('/admin/reload', data=data)
    print('status', r.status_code)
    print('json', r.get_json())
