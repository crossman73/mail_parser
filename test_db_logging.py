"""DB 로깅 시스템 테스트"""
from src.database.email_db import db
import logging

from src.utils.db_logger import setup_db_logging

# 테스트 로거
logger = logging.getLogger('test_logger')
logger.setLevel(logging.INFO)

# DB 핸들러 추가
setup_db_logging(logger, 'data/db/email_parser.db')

# 테스트 로그 생성
print("📝 테스트 로그 생성 중...")
logger.info('테스트 로그 메시지 1')
logger.warning('테스트 경고 메시지 2')
logger.error('테스트 에러 메시지 3')

print('✅ 로그 3개 생성 완료')

# DB에서 확인

logs = db.get_logs(limit=10)
print(f'\n✅ DB에 저장된 로그: {len(logs)}개')
for log in logs[:5]:
    print(f"  [{log['level']}] {log['timestamp']} - {log['message']}")
