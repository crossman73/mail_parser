이 저장소에서 권장하는 무중단 배포 가이드

목표
- 개발 환경에서 서비스 프로세스를 개별적으로 제어해 전체 서비스를 중단하지 않고도 특정 구성요소만 재시작/교체할 수 있도록 돕습니다.

핵심 원칙
1. 프로세스 분리: 주요 구성 요소(예: 이메일 처리기, 성능 모니터, 스트리밍 프로세서)는 서로 분리된 서비스로 등록되어야 하며, UnifiedArchitecture에서 관리합니다.
2. 비파괴 기본 동작: `run_server.py`는 기본적으로 기존 프로세스를 강제 종료하지 않습니다. 운영자가 명시적으로 `--auto-kill` 또는 `AUTO_KILL=1` 로 허용해야 합니다.
3. 배포 단계:
   - 준비: 새 버전 이미지를 빌드
   - 배포: 새 인스턴스를 시작(다른 포트 또는 새로운 호스트) -> 런타임 상태(헬스체크) 확인
   - 트래픽 전환: 로드밸런서/리버스 프록시에서 트래픽을 새 인스턴스로 전환
   - 정리: 구 인스턴스에서 서비스 중지/정리 후 종료

로컬 도구
- `scripts/manage_services.py` : UnifiedArchitecture에 등록된 서비스들을 나열하고, 개별 서비스(stop/start/restart) 또는 전체 서비스(stop-all/restart-all)를 제어하는 간단한 도구입니다. 개발/테스트 용도로만 사용하세요.

예시
- 서비스 목록 조회
  ```powershell
  python scripts\manage_services.py list
  ```

- 특정 서비스 중지
  ```powershell
  python scripts\manage_services.py stop email_processor
  ```

- 전체 서비스 재시작
  ```powershell
  python scripts\manage_services.py restart-all
  ```

운영 권장
- 실제 운영/프로덕션에서는 systemd, supervisord, 또는 쿠버네티스같은 오케스트레이션을 사용하세요. 이 로컬 스크립트는 단지 개발자가 개별 서비스 동작을 테스트하거나 문제를 국소화할 때 유용합니다.
