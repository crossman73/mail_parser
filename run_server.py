#!/usr/bin/env python3
"""
실제 서비스 실행 스크립트
"""

import sys
import time

from src.web.app_factory import create_app

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


def main(port: int = 5000, auto_kill: bool = True):
    print('🚀 Flask 웹 서버 시작 중...')

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
            print('⚠️ 자동 종료 비활성화. 먼저 사용 중인 프로세스를 종료하세요.')
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
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print('\n🛑 서버가 종료되었습니다.')


if __name__ == '__main__':
    import os

    # 기본 포트는 5000, 자동 종료 모드 활성화
    main(port=5000, auto_kill=True)
