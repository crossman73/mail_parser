from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def check_and_init(app) -> List[Dict[str, Any]]:
    """Perform startup checks and initialization.

    Returns a list of structured error dicts found during startup.
    This should be idempotent and safe to call multiple times.
    """
    errors: List[Dict[str, Any]] = []

    # 1) Initialize logging DB first so subsequent checks can log into DB
    try:
        from src.core import log_store, logging_utils
        try:
            log_store.init_db()
        except Exception:
            # ignore - init_db returns a connection or raises; we'll handle below
            pass
        # attach DB logging handler so other modules can log
        try:
            logging_utils.attach_db_handler()
        except Exception as e:
            errors.append({'phase': 'logging_attach', 'error': str(e)})
    except Exception as e:
        errors.append({'phase': 'import_log_modules', 'error': str(e)})

    # 2) Initialize core DBs
    try:
        from src.core import db_manager
        try:
            db_manager.init_all()
        except Exception as e:
            errors.append({'phase': 'db_init', 'error': str(e)})
    except Exception as e:
        errors.append({'phase': 'import_db_manager', 'error': str(e)})

    # 3) Ensure data dir exists and is writable
    try:
        d = Path('data')
        d.mkdir(parents=True, exist_ok=True)
        testfile = d / '.startup_check'
        testfile.write_text('ok')
        testfile.unlink()
    except Exception as e:
        errors.append({'phase': 'data_dir', 'error': str(e)})

    # 4) Render important templates to catch template syntax/runtime errors early
    try:
        tmpl_names = [
            'base.html',
            'admin_logs.html',
            'admin_dashboard.html',
            'admin_evidence_detail.html',
        ]
        # Provide a safe, minimal context for startup-time rendering so that
        # templates which expect application-provided globals (url_for) or
        # required variables (evidence, chain, logs, etc.) do not raise and
        # cause the whole startup check to fail. This keeps the check
        # non-invasive while still surfacing template syntax/runtime issues.
        safe_context = {
            # provide a noop url_for to avoid URL building errors during checks
            'url_for': (lambda *a, **k: '#'),
            # placeholders for commonly-required template variables
            'evidence': {},
            'chain': [],
            'logs': [],
            'evidences': [],
            'statistics': {},
            'features_status': {},
            'evidence_list': [],
            'page': 1,
            'total_pages': 1,
            'admin_csrf': '',
            'jobs': [],
            'file_info': {},
            'uploaded_files': {},
            'processed_emails': {},
        }
        with app.test_request_context('/'):
            for name in tmpl_names:
                try:
                    tpl = app.jinja_env.get_template(name)
                    # render with safe context to avoid startup-time failures
                    tpl.render(**safe_context)
                except Exception as e:
                    errors.append(
                        {'phase': 'template', 'template': name, 'error': str(e)})
    except Exception as e:
        errors.append({'phase': 'template_check', 'error': str(e)})

    # 5) Feature/service checks (e.g., Redis flag)
    try:
        flags = app.config.get('FEATURE_FLAGS', {})
        if flags.get('enable_redis'):
            try:
                import redis as _redis  # type: ignore

                # attempt a no-op connection creation
                _redis.Redis()
            except Exception as e:
                errors.append({'phase': 'redis', 'error': str(e)})
    except Exception as e:
        errors.append({'phase': 'feature_checks', 'error': str(e)})

    # 6) Persist startup errors to logs DB for operator visibility
    try:
        from src.core import db_manager
        if errors:
            for err in errors:
                db_manager.write_log('ERROR', 'startup_check_failure', err)
        else:
            db_manager.write_log('INFO', 'startup_complete', {'status': 'ok'})
    except Exception:
        # best-effort only
        pass

    return errors
