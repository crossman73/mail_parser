import traceback

from src.web.app import create_app

app = create_app()
out = []
try:
    import src.web.admin_routes as ar
    out.append('import ok')
    admin_bp = getattr(ar, 'admin', None)
    out.append(f'has admin attr: {bool(admin_bp)}')
    try:
        app.register_blueprint(admin_bp)
        out.append('registered blueprint OK')
    except Exception as e:
        out.append('register failed')
        out.append(traceback.format_exc())
except Exception as e:
    out.append('import failed')
    out.append(traceback.format_exc())

# list routes
try:
    rules = sorted([(r.rule, r.endpoint) for r in app.url_map.iter_rules()])
    out.append('routes:')
    for rule, endpoint in rules:
        out.append(f"{rule} -> {endpoint}")
except Exception:
    out.append('routes listing failed')
    out.append(traceback.format_exc())

with open('routes_with_admin.txt', 'w', encoding='utf-8') as f:
    for line in out:
        f.write(line + '\n')
print('wrote routes_with_admin.txt')
