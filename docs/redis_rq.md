docker-compose up -d redis
docker-compose exec email-parser rq worker --url redis://redis:6379
# Redis + RQ 개발 가이드

로컬 개발에서 Redis와 RQ를 사용하려면 아래 단계를 따르면 됩니다.

1. Docker Compose로 Redis 실행

```bash
docker-compose up -d redis
```

2. RQ 워커 실행 (컨테이너 내부 또는 로컬 환경에서)

로컬에서 실행하려면(가상환경 활성화 후):

```powershell
# PowerShell
rq worker --url redis://localhost:6379
```

또는 컨테이너 내부에서 실행하려면:

```bash
docker-compose exec email-parser rq worker --url redis://redis:6379
```

3. 업로드 엔드포인트 사용

앱을 실행하고 `/api/upload/stream`으로 POST하면 RQ 큐에 작업이 등록됩니다. 작업 상태는 `/api/upload/job/<job_id>`로 확인하세요.

4. Procfile (제공됨)

`Procfile`에는 웹과 워커를 정의했습니다. 플랫폼(예: Heroku, dokku) 또는 `honcho`/`foreman`로 로컬에서 동시에 실행할 수 있습니다.

```bash
# foreman/honcho 사용 예
pip install honcho
honcho start
```

주의사항
- 운영환경에서는 Redis 접근을 TLS로 보호하거나 내부 네트워크로 한정하세요.
- 대용량 mbox 처리는 StreamingEmailProcessor로 분할해 처리하도록 worker 함수를 개선하세요.

## 로컬 개발자 주의

- 이 저장소는 Redis 기반 작업 큐를 전제로 하지만, 로컬 머신의 자원이 부족할 경우 Docker와 Redis를 실행하는 것은 권장하지 않습니다. 특히 다음과 같은 환경에서는 Docker/Redis 실행으로 인해 성능 저하 또는 실패가 발생할 수 있습니다:
  - 메모리 4GB 미만인 노트북/VM
  - 단일 CPU 코어만 할당된 인스턴스
  - HDD 기반의 느린 디스크 I/O 환경

- 로컬에서 Redis 사용이 불가능하거나 성능이 낮을 것으로 예상되면 현재 구현된 `src/web/upload_stream.py`의 로컬 스레드 폴백을 사용해 기능을 검증하세요. 이 폴백은 개발/테스트 용도로만 권장됩니다(프로덕션 신뢰성/확장성 보장 안 됨).

## 배포 체크리스트 (반드시 수행할 항목)

다음 항목들은 스테이징/프로덕션 환경으로 배포할 때 반드시 수행해야 합니다. 로컬에서 생략하지 말고 배포 전에 전부 확인하세요.

1. 인프라 자원 확보
	- 권장: 2 vCPU 이상, 8GB RAM, SSD 스토리지.
	- 디스크 I/O가 중요한 작업(대용량 mbox 처리)이 있으니 EBS/SSD 같은 빠른 스토리지를 사용하세요.

2. Redis 구성 및 보안
	- Redis를 전용 인스턴스 또는 내부 네트워크로 배치하세요.
	- TLS와 인증(ACL)을 활성화하고 공용 접근을 차단하세요.
	- AOF/RDB 영속성 및 백업 정책을 설정하세요.

3. 워커 운영 방식
	- RQ 워커는 웹 프로세스와 분리하여 별도 프로세스로 운영하세요.
	- 워커 프로세스를 모니터링하고 자동 재시작 정책(systemd, supervisor, k8s 등)을 적용하세요.
	- 작업 큐 모니터링(예: rq-dashboard)을 사용해 지연/실패를 파악하세요.

4. 데이터베이스 및 동시성
	- SQLite는 단일 쓰기 제한이 있으므로 프로덕션에서는 Postgres나 MySQL로 전환하세요.
	- DB 마이그레이션 및 백업/복구 절차를 문서화하세요.

5. 대용량 mbox 처리
	- StreamingEmailProcessor 같은 스트리밍 처리기로 큰 파일을 분할 처리하도록 워커를 개선하세요.
	- 메모리 사용량과 파일 핸들 관리를 철저히 하세요.

6. 배포 전 검증
	- 로드 테스트(작업 큐 높은 부하 시나리오) 수행.
	- 장애 복구 테스트(워커 재시작, Redis 재기동) 수행.

문서 및 코드 내 주석은 로컬 개발자에게 Docker/Redis를 무조건 실행하지 말라는 의미가 아니라, 호스트 자원이 충분하지 않으면 실행을 보류하고 로컬 폴백을 사용하라는 안내입니다. 프로덕션 배포 전에 위 체크리스트를 반드시 수행하세요.
