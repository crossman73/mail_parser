import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional
import psutil
import logging
from ..docs.auto_updater import start_auto_updater
import json

# src/core/service_manager.py
"""
백그라운드 서비스 매니저 - 터미널 블록 방지
"""

class BackgroundServiceManager:
  """백그라운드 서비스 관리자"""
  
  def __init__(self, project_root: Path = None):
    self.project_root = project_root or Path(__file__).parent.parent.parent
    self.services: Dict[str, Dict] = {}
    self.pid_file = self.project_root / "services.pid"
    self.logger = self._setup_logger()
  
  def _setup_logger(self) -> logging.Logger:
    """로깅 설정"""
    logger = logging.getLogger("ServiceManager")
    if not logger.handlers:
      handler = logging.StreamHandler()
      formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      )
      handler.setFormatter(formatter)
      logger.addHandler(handler)
      logger.setLevel(logging.INFO)
    return logger
  
  def start_web_service(self, host: str = "127.0.0.1", port: int = 5000, 
             background: bool = True) -> bool:
    """웹 서비스 백그라운드 시작"""
    try:
      if self.is_service_running("web"):
        print(f"⚠️ 웹 서비스가 이미 실행 중입니다 (PID: {self.get_service_pid('web')})")
        return True
      
      app_path = self.project_root / "app.py"
      if not app_path.exists():
        print(f"❌ app.py 파일을 찾을 수 없습니다: {app_path}")
        return False
      
      env = os.environ.copy()
      env.update({
        'HOST': host,
        'PORT': str(port),
        'PYTHONPATH': str(self.project_root),
        'FLASK_ENV': 'production'
      })
      
      if background:
        # 백그라운드 실행 (플랫폼별 처리)
        if sys.platform.startswith('win'):
          # Windows: CREATE_NEW_PROCESS_GROUP 사용
          process = subprocess.Popen(
            [sys.executable, str(app_path)],
            env=env,
            cwd=str(self.project_root),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
          )
        else:
          # Unix/Linux: nohup 사용
          process = subprocess.Popen(
            [sys.executable, str(app_path)],
            env=env,
            cwd=str(self.project_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp
          )
        
        # 서비스 정보 저장
        service_info = {
          'name': 'web',
          'pid': process.pid,
          'host': host,
          'port': port,
          'started_at': time.time(),
          'process': process
        }
        
        self.services['web'] = service_info
        self._save_service_info()
        
        # 서비스 시작 확인
        time.sleep(2)
        if self._verify_web_service(host, port):
          print("🚀 웹 서비스 백그라운드 시작 완료")
          print(f"   URL: http://{host}:{port}")
          print(f"   PID: {process.pid}")
          return True
        else:
          print("❌ 웹 서비스 시작 실패")
          return False
      else:
        # 포그라운드 실행
        print(f"🚀 웹 서비스 포그라운드 실행: http://{host}:{port}")
        subprocess.run([sys.executable, str(app_path)], env=env, cwd=str(self.project_root))
        return True
        
    except Exception as e:
      print(f"❌ 웹 서비스 시작 실패: {e}")
      self.logger.error(f"웹 서비스 시작 오류: {e}")
      return False
  
  def start_docs_auto_updater(self, background: bool = True) -> bool:
    """문서 자동 업데이터 백그라운드 시작"""
    try:
      if self.is_service_running("docs_updater"):
        print("⚠️ 문서 자동 업데이터가 이미 실행 중입니다")
        return True
      
      if background:
        # 별도 프로세스로 실행
        updater_script = self.project_root / "scripts" / "run_docs_updater.py"
        self._create_docs_updater_script(updater_script)
        
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root)
        
        process = subprocess.Popen(
          [sys.executable, str(updater_script)],
          env=env,
          cwd=str(self.project_root),
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL
        )
        
        service_info = {
          'name': 'docs_updater',
          'pid': process.pid,
          'started_at': time.time(),
          'process': process
        }
        
        self.services['docs_updater'] = service_info
        self._save_service_info()
        
        print(f"📚 문서 자동 업데이터 백그라운드 시작 (PID: {process.pid})")
        return True
      else:
        # 동기 실행
        updater = start_auto_updater(self.project_root)
        return updater is not None
        
    except Exception as e:
      print(f"❌ 문서 자동 업데이터 시작 실패: {e}")
      return False
  
  def _create_docs_updater_script(self, script_path: Path):
    """문서 업데이터 실행 스크립트 생성"""
    script_path.parent.mkdir(exist_ok=True)
    
    script_content = '''#!/usr/bin/env python3
"""
문서 자동 업데이터 백그라운드 실행 스크립트
"""

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def signal_handler(signum, frame):
  print("\\n⏹️ 문서 자동 업데이터 종료 중...")
  sys.exit(0)

if __name__ == "__main__":
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  
  updater = start_auto_updater(project_root)
  if updater:
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      stop_auto_updater(updater)
    finally:
      stop_auto_updater(updater)
  else:
    sys.exit(1)
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
      f.write(script_content)
  
  def _verify_web_service(self, host: str, port: int) -> bool:
    """웹 서비스 동작 확인"""
    try:
      import urllib.request
      url = f"http://{host}:{port}/health"
      with urllib.request.urlopen(url, timeout=5) as response:
        return response.getcode() == 200
    except Exception:
      return False
  
  def stop_service(self, service_name: str) -> bool:
    """서비스 중지"""
    try:
      if service_name not in self.services:
        print(f"⚠️ '{service_name}' 서비스가 실행되지 않았습니다.")
        return True
      
      service_info = self.services[service_name]
      pid = service_info['pid']
      
      # 프로세스 존재 확인
      if not psutil.pid_exists(pid):
        print(f"⚠️ PID {pid} 프로세스가 이미 종료되었습니다.")
        del self.services[service_name]
        self._save_service_info()
        return True
      
      # 프로세스 종료
      process = psutil.Process(pid)
      process.terminate()
      
      # 강제 종료 대기
      try:
        process.wait(timeout=5)
      except psutil.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)
      
      print(f"⏹️ '{service_name}' 서비스 중지 완료 (PID: {pid})")
      
      del self.services[service_name]
      self._save_service_info()
      return True
      
    except Exception as e:
      print(f"❌ '{service_name}' 서비스 중지 실패: {e}")
      return False
  
  def stop_all_services(self) -> bool:
    """모든 서비스 중지"""
    print("⏹️ 모든 백그라운드 서비스 중지 중...")
    
    success = True
    for service_name in list(self.services.keys()):
      if not self.stop_service(service_name):
        success = False
    
    if success:
      print("✅ 모든 서비스 중지 완료")
    else:
      print("⚠️ 일부 서비스 중지 실패")
    
    return success
  
  def get_service_status(self) -> Dict[str, Dict]:
    """모든 서비스 상태 조회"""
    status = {}
    
    for service_name, service_info in self.services.items():
      pid = service_info['pid']
      
      try:
        process = psutil.Process(pid)
        status[service_name] = {
          'running': process.is_running(),
          'pid': pid,
          'memory_mb': process.memory_info().rss / 1024 / 1024,
          'cpu_percent': process.cpu_percent(),
          'started_at': service_info['started_at']
        }
        
        if service_name == 'web':
          status[service_name].update({
            'host': service_info.get('host', 'unknown'),
            'port': service_info.get('port', 'unknown')
          })
          
      except psutil.NoSuchProcess:
        status[service_name] = {
          'running': False,
          'pid': pid,
          'error': 'Process not found'
        }
    
    return status
  
  def is_service_running(self, service_name: str) -> bool:
    """특정 서비스 실행 상태 확인"""
    if service_name not in self.services:
      return False
    
    pid = self.services[service_name]['pid']
    return psutil.pid_exists(pid)
  
  def get_service_pid(self, service_name: str) -> Optional[int]:
    """서비스 PID 조회"""
    return self.services.get(service_name, {}).get('pid')
  
  def _save_service_info(self):
    """서비스 정보 파일에 저장"""
    try:
      service_data = {}
      
      for name, info in self.services.items():
        service_data[name] = {
          'pid': info['pid'],
          'started_at': info['started_at']
        }
        if name == 'web':
          service_data[name].update({
            'host': info.get('host'),
            'port': info.get('port')
          })
      
      with open(self.pid_file, 'w', encoding='utf-8') as f:
        json.dump(service_data, f, indent=2)
        
    except Exception as e:
      self.logger.error(f"서비스 정보 저장 실패: {e}")
  
  def _load_service_info(self):
    """서비스 정보 파일에서 로드"""
    try:
      if self.pid_file.exists():
        with open(self.pid_file, 'r', encoding='utf-8') as f:
          service_data = json.load(f)
        
        for name, info in service_data.items():
          pid = info['pid']
          if psutil.pid_exists(pid):
            self.services[name] = {
              'name': name,
              'pid': pid,
              'started_at': info['started_at']
            }
            if name == 'web':
              self.services[name].update({
                'host': info.get('host'),
                'port': info.get('port')
              })
        
    except Exception as e:
      self.logger.error(f"서비스 정보 로드 실패: {e}")

# 전역 서비스 매니저 인스턴스
_service_manager = None

def get_service_manager() -> BackgroundServiceManager:
  """서비스 매니저 싱글톤 인스턴스 반환"""
  global _service_manager
  if _service_manager is None:
    _service_manager = BackgroundServiceManager()
    _service_manager._load_service_info()
  return _service_manager