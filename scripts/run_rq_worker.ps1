# PowerShell helper: run RQ worker connecting to local docker redis
# Requires docker-compose up -d
docker-compose exec email-parser rq worker --url redis://redis:6379
