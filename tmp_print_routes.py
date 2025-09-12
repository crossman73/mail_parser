from src.web.app import create_app

app = create_app()
for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule.rule, sorted(rule.methods))
