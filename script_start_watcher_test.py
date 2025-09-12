import os
import time

from src.web.app import create_app

app = create_app()
app.config['ENABLE_DEV_RELOAD'] = True
app.config['ENABLE_FILE_WATCHER'] = True
app.config['DEV_RELOAD_MODULES'] = ['src.core.hot_reload']

# create app to start watcher
# watcher writes watcher_started.txt when it starts

# remove existing marker
if os.path.exists('watcher_started.txt'):
    os.remove('watcher_started.txt')

# instantiate app to trigger watcher
_ = app

# wait a few seconds for watcher thread to start
time.sleep(2)

if os.path.exists('watcher_started.txt'):
    print('watcher started')
    with open('watcher_started.txt', 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print('watcher not started')
