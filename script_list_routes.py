from src.web.app import create_app

app = create_app()

rules = sorted([(r.rule, r.endpoint) for r in app.url_map.iter_rules()])
with open('routes_listing.txt', 'w', encoding='utf-8') as f:
    for rule, endpoint in rules:
        f.write(f"{rule} -> {endpoint}\n")
print('wrote routes_listing.txt')
