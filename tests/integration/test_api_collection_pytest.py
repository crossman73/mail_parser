from src.api.api_collector import collect_api_docs
from src.database.connection import db_connection
from src.web.app import create_app


def test_collect_api_docs_runs_and_returns_int():
    app = create_app()
    with app.app_context():
        count = collect_api_docs(app, db_connection)
        assert isinstance(count, int)
        assert count >= 0
