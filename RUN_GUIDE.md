# 🚀 실행 가이드 - 성능 최적화 & API 서버

## 📋 목차

1. [성능 최적화 크롤러 실행](#1-성능-최적화-크롤러-실행)
2. [API 서버 실행](#2-api-서버-실행)
3. [API 클라이언트 테스트](#3-api-클라이언트-테스트)
4. [성능 비교](#4-성능-비교)
5. [문제 해결](#5-문제-해결)

---

## 1. 성능 최적화 크롤러 실행

### 1.1 의존성 설치
```bash
pip install -r requirements.txt
```

### 1.2 최적화된 크롤러 실행
```bash
python 10000recipe_optimized.py
```

### 1.3 주요 개선사항
- **멀티스레딩**: 4개 스레드로 병렬 처리
- **세션 풀**: 연결 재사용으로 성능 향상
- **배치 처리**: 10개씩 묶어서 처리
- **진행률 표시**: tqdm으로 실시간 진행률 확인
- **지연 시간 최적화**: 1-3초로 단축

### 1.4 설정 조정
`10000recipe_optimized.py`에서 다음 설정을 조정할 수 있습니다:

```python
class CrawlerConfig:
    MAX_WORKERS = 4      # 동시 작업자 수 (CPU 코어 수에 맞게 조정)
    BATCH_SIZE = 10      # 배치 처리 크기
    MIN_DELAY = 1        # 최소 지연 시간 (초)
    MAX_DELAY = 3        # 최대 지연 시간 (초)
```

---

## 2. API 서버 실행

### 2.1 API 서버 시작
```bash
python api_server.py
```

### 2.2 서버 접속
- **API 문서**: http://localhost:8000/docs
- **ReDoc 문서**: http://localhost:8000/redoc
- **API 루트**: http://localhost:8000/
- **헬스 체크**: http://localhost:8000/health

### 2.3 주요 API 엔드포인트

| 엔드포인트 | 설명 | 예시 |
|-----------|------|------|
| `GET /` | 서버 정보 | http://localhost:8000/ |
| `GET /recipes` | 모든 레시피 조회 | http://localhost:8000/recipes?page=1&per_page=20 |
| `GET /recipes/{id}` | 특정 레시피 조회 | http://localhost:8000/recipes/7057555 |
| `GET /search` | 레시피 검색 | http://localhost:8000/search?q=김치&difficulty=아무나 |
| `GET /statistics` | 통계 정보 | http://localhost:8000/statistics |
| `GET /random` | 랜덤 레시피 | http://localhost:8000/random?count=10 |
| `GET /difficulty/{level}` | 난이도별 조회 | http://localhost:8000/difficulty/초급 |

### 2.4 검색 파라미터

```bash
# 기본 검색
GET /search?q=김치

# 고급 검색
GET /search?q=김치&author=홍길동&difficulty=아무나&max_time=30&page=1&per_page=20
```

---

## 3. API 클라이언트 테스트

### 3.1 클라이언트 실행
```bash
python api_client_example.py
```

### 3.2 테스트 기능
- 서버 정보 조회
- 헬스 체크
- 통계 정보 조회
- 레시피 목록 조회
- 검색 기능 테스트
- 랜덤 레시피 조회
- 특정 레시피 상세 조회
- 난이도별 레시피 조회
- 대화형 검색

### 3.3 사용자 정의 클라이언트 예제

```python
from api_client_example import RecipeAPIClient

# 클라이언트 생성
client = RecipeAPIClient("http://localhost:8000")

# 검색 예제
results = client.search_recipes(
    query="감자",
    difficulty="아무나",
    max_time=30,
    per_page=10
)

print(f"검색 결과: {results['total_count']}개")
for recipe in results['recipes']:
    print(f"- {recipe['Title']}")
```

---

## 4. 성능 비교

### 4.1 크롤링 성능

| 버전 | 처리 방식 | 예상 소요 시간 | 처리 속도 |
|------|-----------|---------------|-----------|
| 원본 | 순차 처리 | ~30-45분 | ~1 레시피/초 |
| 개선 | 순차 처리 + 로깅 | ~25-35분 | ~1.2 레시피/초 |
| 최적화 | 멀티스레딩 | ~8-12분 | ~4-6 레시피/초 |

### 4.2 API 응답 시간

| 엔드포인트 | 평균 응답 시간 | 설명 |
|-----------|---------------|------|
| `/health` | <10ms | 헬스 체크 |
| `/recipes` | <50ms | 레시피 목록 |
| `/search` | <100ms | 검색 (인덱스 없음) |
| `/statistics` | <200ms | 통계 계산 |
| `/random` | <30ms | 랜덤 선택 |

### 4.3 시스템 요구사항

| 구성 요소 | 최소 요구사항 | 권장 사항 |
|-----------|---------------|-----------|
| CPU | 2코어 | 4코어 이상 |
| 메모리 | 4GB | 8GB 이상 |
| 네트워크 | 10Mbps | 50Mbps 이상 |
| 저장공간 | 100MB | 500MB 이상 |

---

## 5. 문제 해결

### 5.1 일반적인 문제들

#### A. 크롤링 관련

**문제**: 멀티스레딩 크롤러가 너무 빠르게 실행됨
```bash
# 해결: 지연 시간 증가
MIN_DELAY = 2  # 1초 → 2초
MAX_DELAY = 5  # 3초 → 5초
```

**문제**: 메모리 사용량이 높음
```bash
# 해결: 배치 크기 감소
BATCH_SIZE = 5  # 10 → 5
```

**문제**: 네트워크 오류가 자주 발생
```bash
# 해결: 재시도 횟수 증가
MAX_RETRIES = 5  # 3 → 5
```

#### B. API 서버 관련

**문제**: API 서버가 시작되지 않음
```bash
# 해결: 포트 확인
netstat -an | findstr :8000  # Windows
lsof -i :8000                # Linux/Mac
```

**문제**: CSV 파일을 찾을 수 없음
```bash
# 해결: 크롤링 먼저 실행
python 10000recipe_optimized.py
```

**문제**: API 응답이 느림
```bash
# 해결: 데이터베이스 인덱싱 고려
# 현재는 pandas DataFrame 사용
```

### 5.2 로그 확인

#### 크롤링 로그
```bash
# 최신 로그 파일 확인
tail -f crawler_optimized_*.log

# 오류만 확인
grep "ERROR" crawler_optimized_*.log
```

#### API 서버 로그
```bash
# uvicorn 로그 확인 (터미널에서)
# 자동으로 콘솔에 출력됨
```

### 5.3 성능 튜닝

#### 크롤링 성능 최적화
```python
# CPU 코어 수에 맞게 조정
MAX_WORKERS = os.cpu_count()  # 자동 감지

# 네트워크 상태에 맞게 조정
TIMEOUT = 20  # 느린 네트워크
TIMEOUT = 10  # 빠른 네트워크
```

#### API 서버 성능 최적화
```python
# uvicorn 설정
uvicorn.run(
    "api_server:app",
    host="0.0.0.0",
    port=8000,
    workers=4,  # 멀티 프로세스
    reload=False  # 프로덕션에서는 False
)
```

---

## 6. 고급 사용법

### 6.1 배치 크롤링
```bash
# 여러 페이지 범위로 크롤링
python -c "
from 10000recipe_optimized import OptimizedRecipeCrawler
crawler = OptimizedRecipeCrawler()
crawler.config.MAX_PAGES = 50  # 25 → 50
crawler.run_optimized()
"
```

### 6.2 API 서버 백그라운드 실행
```bash
# Linux/Mac
nohup python api_server.py > api.log 2>&1 &

# Windows
start /B python api_server.py > api.log 2>&1
```

### 6.3 데이터베이스 연동 (향후 개선)
```python
# SQLite 연동 예제
import sqlite3

def save_to_database(data, db_path="recipes.db"):
    conn = sqlite3.connect(db_path)
    df = pd.DataFrame(data)
    df.to_sql('recipes', conn, if_exists='replace', index=False)
    conn.close()
```

---

## 7. 모니터링

### 7.1 크롤링 모니터링
- 진행률 표시 (tqdm)
- 로그 파일 확인
- 메모리 사용량 모니터링

### 7.2 API 서버 모니터링
- 헬스 체크: `GET /health`
- 응답 시간 측정
- 동시 접속자 수 확인

### 7.3 성능 메트릭
```python
# 크롤링 성능 측정
start_time = time.time()
# ... 크롤링 실행 ...
duration = time.time() - start_time
speed = total_recipes / duration
print(f"처리 속도: {speed:.2f} 레시피/초")
```

---

## 8. 다음 단계

### 8.1 추가 개선 계획
- [ ] 데이터베이스 연동 (PostgreSQL)
- [ ] 캐싱 시스템 (Redis)
- [ ] 검색 엔진 (Elasticsearch)
- [ ] 웹 대시보드
- [ ] 모바일 앱

### 8.2 확장 가능한 아키텍처
- [ ] 마이크로서비스 분리
- [ ] 컨테이너화 (Docker)
- [ ] 오케스트레이션 (Kubernetes)
- [ ] CI/CD 파이프라인

---

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 로그 파일 확인
2. 네트워크 연결 상태
3. 시스템 리소스 사용량
4. 의존성 라이브러리 버전

**성공적인 실행을 위해 필요한 것들:**
- 안정적인 인터넷 연결
- 충분한 시스템 리소스
- 최신 Python 환경
- 모든 의존성 라이브러리 설치 