import traceback

out = []
try:
    import src.web.admin_routes as ar
    out.append('import ok')
    try:
        admin = getattr(ar, 'admin', None)
        out.append(f'has admin attr: {bool(admin)}')
        if admin:
            out.append(f'blueprint: {admin.name} prefix={admin.url_prefix}')
    except Exception as e:
        out.append('error inspecting admin: ' + str(e))
except Exception as e:
    out.append('import failed')
    out.append(traceback.format_exc())

with open('admin_import_result.txt', 'w', encoding='utf-8') as f:
    for line in out:
        f.write(line + '\n')
print('wrote admin_import_result.txt')
