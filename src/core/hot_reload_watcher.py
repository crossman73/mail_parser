"""Dev helper: watch filesystem changes and call hot_reload.reload_modules.

This module tries to use `watchdog`. If not installed, the watcher is a no-op.
Only enable in development via app config flags.
"""
import threading
import time
from typing import List, Optional


def _noop_start(*args, **kwargs):
    return None


def start_watcher(app, modules: List[str], paths: Optional[List[str]] = None):
    """Start a background watcher thread that reloads modules on file changes.

    Writes `watcher_started.txt` under project root when started for test visibility.
    """
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except Exception:
        # watchdog not installed — provide noop and write marker file
        try:
            with open('watcher_unavailable.txt', 'w', encoding='utf-8') as f:
                f.write('watchdog not installed; auto-reload disabled\n')
        except Exception:
            pass
        app.logger.info('watchdog not available; auto-reload watcher disabled')
        return _noop_start()

    class _Handler(FileSystemEventHandler):
        def __init__(self, app, modules):
            self.app = app
            self.modules = modules

        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith('.py'):
                try:
                    from src.core import hot_reload
                    with self.app.app_context():
                        hot_reload.reload_modules(self.modules)
                        self.app.logger.info(
                            f"hot_reload: reloaded modules due to change: {event.src_path}")
                except Exception:
                    self.app.logger.exception('hot_reload: reload failed')

    def _run():
        observer = Observer()
        handler = _Handler(app, modules)
        watch_paths = paths or ['.']
        for p in watch_paths:
            try:
                observer.schedule(handler, path=p, recursive=True)
            except Exception:
                app.logger.exception(f'failed to schedule watcher for {p}')
        observer.start()
        # write a small file to indicate watcher started (for test scripts)
        try:
            with open('watcher_started.txt', 'w', encoding='utf-8') as f:
                f.write('watcher started\n')
        except Exception:
            try:
                app.logger.exception('failed to write watcher_started.txt')
            except Exception:
                pass
        try:
            while True:
                time.sleep(1)
        except Exception:
            observer.stop()
        observer.join()

    t = threading.Thread(target=_run, daemon=True, name='hot-reload-watcher')
    t.start()
    return t
