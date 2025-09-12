from src.web import app_factory
app = app_factory.create_app({'TESTING': True})
for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    print(r.rule, '->', list(r.methods))
