#!/usr/bin/env python3
"""
실제 서비스 실행 스크립트
"""

import os
import sys
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가 (가장 먼저 실행)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"DEBUG: Project root = {project_root.resolve()}")
print(f"DEBUG: sys.path[0] = {sys.path[0]}")


# App factory selection policy
# - For day-to-day development we prefer the legacy/full UI (src.web.app)
#   because it provides the richer `/upload` template and developer UX.
# - In CI / production or when explicitly requested, you can choose the
#   lighter-weight compatibility factory (`src.web.app_factory`) by setting
#   USE_MINIMAL_UI=1 in the environment.
# - For backwards compatibility we also honor USE_FULL_UI truthy values.
try:
    use_minimal = os.environ.get(
        'USE_MINIMAL_UI', '').lower() in ('1', 'true', 'yes', 'on')
    use_full = os.environ.get('USE_FULL_UI', '').lower() in (
        '1', 'true', 'yes', 'on')

    # Prefer the main application factory; compatibility factory removed.
    # Keep a simple import to avoid import-time issues during linting.
    from src.web.app import create_app

try:
    import psutil
except Exception:
    psutil = None


def _find_processes_using_port(port: int):
    procs = []
    if psutil is None:
        return procs

    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.laddr.port == port:
            try:
                p = psutil.Process(conn.pid)
                procs.append((p.pid, p.name(), p.cmdline()))
            except Exception:
                pass
    return procs


def _terminate_process(pid: int, timeout: float = 5.0):
    if psutil is None:
        return False

    # PID 0은 시스템 프로세스이므로 건너뜀
    if pid == 0:
        return False

    try:
        p = psutil.Process(pid)
        print(f'⚠️ 종료 시도: PID={pid}, name={p.name()}')
        p.terminate()
        try:
            p.wait(timeout=timeout)
            print(f'✅ PID={pid} 종료 완료')
            return True
        except psutil.TimeoutExpired:
            print(f'⏳ PID={pid} 종료 대기 초과, 강제종료 시도')
            p.kill()
            p.wait(timeout=2)
            return True
    except Exception as e:
        print(f'❌ PID={pid} 종료 실패: {e}')
    return False


def main(port: int = 5000, auto_kill: bool = False, start_server: bool = True):
    print('🚀 Flask 웹 서버 시작 중...')

    # 데이터베이스 초기화
    print('💾 데이터베이스 초기화 중...')
    try:
        from src.database.connection import db_connection
        from src.database.migrations import MigrationManager

        # DB 초기화
        db_path = project_root / 'data' / 'db' / 'email_parser.db'
        if db_connection.initialize(str(db_path)):
            print(f'✅ DB 초기화 완료: {db_path}')

            # 마이그레이션 실행
            migrator = MigrationManager(db_connection)
            if migrator.run_migrations():
                current_version = migrator.get_current_version()
                print(f'✅ DB 마이그레이션 완료 (버전: {current_version})')
            else:
                print('⚠️ 마이그레이션 실패 (기존 스키마 유지)')
        else:
            print('⚠️ DB 초기화 실패 (계속 진행)')
    except Exception as e:
        print(f'⚠️ DB 초기화 오류: {e} (계속 진행)')

    # 포트 사용 중인 프로세스 확인
    procs = _find_processes_using_port(port)
    if procs:
        print(f'🔍 포트 {port} 사용 프로세스 발견:')
        for pid, name, cmd in procs:
            print(f'  - PID={pid} name={name} cmd={cmd}')

        if auto_kill:
            print('ℹ️ 자동 종료 모드가 활성화되어 사용 중인 프로세스를 종료합니다...')
            for pid, _, _ in procs:
                _terminate_process(pid)
            # 잠시 대기
            time.sleep(1)
        else:
            # Non-destructive default: do not kill processes automatically.
            print('⚠️ 포트가 사용 중입니다. 자동 종료가 비활성화되어 있습니다.\n   - 기존 프로세스를 수동으로 종료하거나\n   - --auto-kill 옵션 또는 AUTO_KILL=1 환경변수로 강제 종료를 허용하세요.')
            sys.exit(1)

    # Flask 애플리케이션 생성
    app = create_app()

    print('✅ Flask 애플리케이션 생성 완료')
    print(f'📍 등록된 라우트: {len(list(app.url_map.iter_rules()))}개')

    # 주요 엔드포인트 안내
    print('\n🌐 서비스 접속 URL:')
    print(f'  - 메인 페이지: http://localhost:{port}/')
    print(f'  - 📚 문서 페이지: http://localhost:{port}/docs')
    print(f'  - 🔧 Swagger UI: http://localhost:{port}/swagger')
    print(f'  - 📋 API 목록: http://localhost:{port}/api/endpoints')

    print('\n🔄 서버를 중지하려면 Ctrl+C를 누르세요')
    print('=' * 50)

    try:
        # 개발 서버 실행
        print(f'🔎 현재 프로세스 PID: {os.getpid()}')
        if start_server:
            app.run(
                host='0.0.0.0',
                port=port,
                debug=True,
                use_reloader=False
            )
        else:
            # For testability: skip starting the blocking server loop
            print('ℹ️ start_server=False 이므로 Flask 서버 시작을 건너뜁니다 (테스트 모드).')
    except KeyboardInterrupt:
        print('\n🛑 서버가 종료되었습니다.')


if __name__ == '__main__':
    import os

    # 기본 포트는 5000
    # 자동 종료는 기본적으로 비활성화되어 있어 무중단 배포 상황에서
    # 의도치 않은 프로세스 종료를 방지합니다. 필요하면 --auto-kill
    # 옵션(또는 AUTO_KILL=1)을 사용해 강제 종료할 수 있습니다.
    env_auto = os.environ.get('AUTO_KILL', '').lower() in (
        '1', 'true', 'yes', 'on')
    cmd_auto = '--auto-kill' in sys.argv
    main(port=5000, auto_kill=(env_auto or cmd_auto))
