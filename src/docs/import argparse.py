import argparse
import sys
import time
from pathlib import Path
from src.core.service_manager import get_service_manager

# service_control.py
#!/usr/bin/env python3
"""
백그라운드 서비스 제어 CLI - 터미널 블록 방지
"""

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def create_service_parser():
  """서비스 제어 CLI 파서"""
  parser = argparse.ArgumentParser(
    description='📧 이메일 증거 처리 시스템 - 백그라운드 서비스 제어',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
사용 예시:
  python service_control.py start web --port 5000        # 웹 서비스 백그라운드 시작
  python service_control.py start docs-updater           # 문서 자동 업데이터 시작
  python service_control.py status                       # 모든 서비스 상태 확인
  python service_control.py stop web                     # 웹 서비스 중지
  python service_control.py stop --all                   # 모든 서비스 중지
  python service_control.py restart web                  # 웹 서비스 재시작
    """
  )
  
  subparsers = parser.add_subparsers(dest='command', help='서비스 명령')
  
  # start 명령
  start_parser = subparsers.add_parser('start', help='서비스 시작')
  start_parser.add_argument('service', choices=['web', 'docs-updater'], 
               help='시작할 서비스')
  start_parser.add_argument('--host', default='127.0.0.1', 
               help='웹 서비스 호스트 (기본값: 127.0.0.1)')
  start_parser.add_argument('--port', type=int, default=5000, 
               help='웹 서비스 포트 (기본값: 5000)')
  start_parser.add_argument('--foreground', action='store_true',
               help='포그라운드 실행 (터미널 블록)')
  
  # stop 명령
  stop_parser = subparsers.add_parser('stop', help='서비스 중지')
  stop_parser.add_argument('service', nargs='?', 
              choices=['web', 'docs-updater'],
              help='중지할 서비스')
  stop_parser.add_argument('--all', action='store_true',
              help='모든 서비스 중지')
  
  # status 명령
  subparsers.add_parser('status', help='서비스 상태 확인')
  
  # restart 명령
  restart_parser = subparsers.add_parser('restart', help='서비스 재시작')
  restart_parser.add_argument('service', choices=['web', 'docs-updater'],
                 help='재시작할 서비스')
  restart_parser.add_argument('--host', default='127.0.0.1')
  restart_parser.add_argument('--port', type=int, default=5000)
  
  return parser

def main():
  """서비스 제어 메인 함수"""
  parser = create_service_parser()
  args = parser.parse_args()
  
  if not args.command:
    parser.print_help()
    return 1
  
  # 서비스 매니저 초기화
  service_manager = get_service_manager()
  
  try:
    if args.command == 'start':
      if args.service == 'web':
        success = service_manager.start_web_service(
          host=args.host,
          port=args.port,
          background=not args.foreground
        )
        if success and not args.foreground:
          print(f"🌐 웹 서비스가 백그라운드에서 시작되었습니다.")
          print(f"   URL: http://{args.host}:{args.port}")
          print(f"   상태 확인: python service_control.py status")
        return 0 if success else 1
        
      elif args.service == 'docs-updater':
        success = service_manager.start_docs_auto_updater(
          background=not args.foreground
        )
        if success and not args.foreground:
          print("📚 문서 자동 업데이터가 백그라운드에서 시작되었습니다.")
        return 0 if success else 1
    
    elif args.command == 'stop':
      if args.all:
        success = service_manager.stop_all_services()
        return 0 if success else 1
      elif args.service:
        success = service_manager.stop_service(args.service)
        return 0 if success else 1
      else:
        print("❌ 중지할 서비스를 지정하거나 --all 옵션을 사용하세요.")
        return 1
    
    elif args.command == 'status':
      status = service_manager.get_service_status()
      print("📊 서비스 상태:")
      print("=" * 50)
      
      if not status:
        print("실행 중인 서비스가 없습니다.")
        return 0
      
      for service_name, info in status.items():
        if info['running']:
          uptime = time.time() - info['started_at']
          uptime_str = f"{uptime/3600:.1f}시간" if uptime > 3600 else f"{uptime/60:.1f}분"
          
          print(f"✅ {service_name}")
          print(f"   PID: {info['pid']}")
          print(f"   메모리: {info.get('memory_mb', 0):.1f}MB")
          print(f"   가동시간: {uptime_str}")
          
          if service_name == 'web':
            host = info.get('host', 'unknown')
            port = info.get('port', 'unknown')
            print(f"   URL: http://{host}:{port}")
        else:
          print(f"❌ {service_name} (중지됨)")
        print()
      
      return 0
    
    elif args.command == 'restart':
      print(f"🔄 {args.service} 서비스 재시작 중...")
      
      # 기존 서비스 중지
      service_manager.stop_service(args.service)
      time.sleep(1)
      
      # 서비스 시작
      if args.service == 'web':
        success = service_manager.start_web_service(
          host=args.host,
          port=args.port,
          background=True
        )
      elif args.service == 'docs-updater':
        success = service_manager.start_docs_auto_updater(background=True)
      
      if success:
        print(f"✅ {args.service} 서비스 재시작 완료")
        return 0
      else:
        print(f"❌ {args.service} 서비스 재시작 실패")
        return 1
    
  except KeyboardInterrupt:
    print("\n⚠️ 중단되었습니다.")
    return 1
  except Exception as e:
    print(f"❌ 오류 발생: {e}")
    return 1

if __name__ == "__main__":
  sys.exit(main())