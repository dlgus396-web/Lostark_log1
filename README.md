# 로스트아크 전투 분석기 플랫폼

로스트아크 전투 분석기 스크린샷을 기반으로 전투 기록을 저장하고, 직업별 핵심 행동 지표를 계산하여 개인 기록 조회와 랭킹 비교 기능을 제공하는 Streamlit 기반 웹 DB 응용 프로젝트입니다.

---

## 실행 방법

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

EasyOCR 실행 중 `libGL.so.1` 오류가 발생하면 아래 명령어를 추가로 실행합니다.

```bash
sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0
```

### 2. Supabase 환경 변수 설정

`.streamlit/secrets.toml` 파일을 생성하고 아래 내용을 입력합니다.

```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-anon-key"
```

`secrets.toml`은 민감 정보를 포함하므로 GitHub에 업로드하지 않습니다.

### 3. 앱 실행

```bash
streamlit run app.py
```

실행 후 브라우저에서 안내되는 주소로 접속합니다.

```text
http://localhost:8501
```

GitHub Codespaces에서는 `PORTS` 탭에서 8501 포트를 열어 접속합니다.

---

## 프로젝트 개요

이 프로젝트는 로스트아크 게임 내 전투 분석기 화면을 활용하여 전투 기록을 관리하는 웹 DB 응용입니다.

사용자는 전투 분석기 스크린샷을 업로드하고, OCR을 통해 전투 시간과 핵심 행동 사용 횟수 등을 추출할 수 있습니다. 추출된 값은 사용자가 직접 확인 및 수정할 수 있으며, 최종 분석 결과는 Supabase DB에 저장됩니다.

저장된 기록은 내 기록 화면에서 캐릭터별, 레이드별로 조회할 수 있고, 영상 링크가 포함된 기록은 랭킹 화면에 표시됩니다.

---

## 주요 기능

* 이메일 / 비밀번호 기반 로그인 및 회원가입
* 로그인 사용자 기준 전투 기록 저장
* 전투 분석기 스크린샷 업로드
* OCR 기반 전투 시간 및 핵심 행동 사용 횟수 추출
* 직업별 핵심 행동 CPM 계산
* 분석 결과 확인 및 DB 저장
* 내 기록 조회
* 캐릭터별 / 레이드별 내 기록 필터
* 내 기록 삭제
* 직업별 / 레이드별 랭킹 조회
* 영상 링크가 있는 기록만 랭킹 표시
* 랭킹 상위 10개 표시
* 랭킹 기록 신고 기능
* DB 연결 상태 확인 페이지

---

## 지원 직업 및 핵심 지표

| 직업   | 핵심 지표                   |
| ---- | ----------------------- |
| 블레이드 | 블레이드 버스트 사용 횟수, 백어택 적중률 |
| 브레이커 | 권왕십이식 : 낙화 사용 횟수        |
| 아르카나 | 카드 사용 횟수                |

핵심 행동 CPM은 다음 방식으로 계산합니다.

```text
CPM = 핵심 행동 사용 횟수 / 전투 시간(분)
```

예를 들어 전투 시간이 `07:15`이고 사용 횟수가 `31`이면 다음과 같이 계산됩니다.

```text
7분 15초 = 7.25분
31 / 7.25 = 4.28 CPM
```

---

## 사용 기술

| 구분             | 기술                           |
| -------------- | ---------------------------- |
| Web UI         | Streamlit                    |
| Language       | Python                       |
| Database       | Supabase PostgreSQL          |
| Authentication | Supabase Email/Password Auth |
| OCR            | EasyOCR                      |
| 개발 환경          | GitHub Codespaces            |
| Vibe Coding 도구 | GitHub Copilot               |

---

## 데이터베이스 주요 테이블

| 테이블명                | 설명           |
| ------------------- | ------------ |
| `profiles`          | 사용자 프로필 정보   |
| `supported_classes` | 지원 직업 정보     |
| `bosses`            | 레이드 및 관문 정보  |
| `combat_records`    | 전투 분석 기록     |
| `score_rules`       | 직업별 점수 계산 규칙 |
| `scoring_baselines` | 점수 계산 기준값    |
| `reports`           | 랭킹 기록 신고 정보  |

---

## 페이지 구성

| 파일                           | 기능                 |
| ---------------------------- | ------------------ |
| `app.py`                     | 메인 화면              |
| `pages/0_login.py`           | 로그인 / 회원가입         |
| `pages/1_ranking.py`         | 상위 랭킹 조회 및 신고      |
| `pages/2_upload.py`          | 전투 기록 업로드 및 OCR 분석 |
| `pages/3_analysis_result.py` | 분석 결과 확인 및 DB 저장   |
| `pages/4_my_records.py`      | 내 기록 조회 및 삭제       |
| `pages/5_db_check.py`        | DB 연결 상태 확인        |

---

## 프로젝트 구조

```text
.
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
├── .streamlit
│   └── config.toml
├── lib
│   ├── auth.py
│   ├── db_queries.py
│   ├── image_analysis.py
│   ├── scoring.py
│   ├── supabase_client.py
│   └── utils.py
├── pages
│   ├── 0_login.py
│   ├── 1_ranking.py
│   ├── 2_upload.py
│   ├── 3_analysis_result.py
│   ├── 4_my_records.py
│   └── 5_db_check.py
└── sql
```

---

## 현재 제한 사항

* Supabase Storage를 이용한 실제 이미지 저장은 구현하지 않았습니다.
* OCR 결과는 이미지 품질에 따라 부정확할 수 있습니다.
* OCR 결과가 틀린 경우 사용자가 직접 수정할 수 있습니다.
* 현재 지원 직업은 블레이드, 브레이커, 아르카나입니다.
* 관리자용 신고 관리 화면은 구현하지 않았습니다.

---

## 주의사항

`.gitignore`에는 아래 항목을 포함해야 합니다.

```gitignore
.streamlit/secrets.toml
.venv/
__pycache__/
*.pyc
.env
```

프로젝트는 루트 폴더에서 실행해야 합니다.

```bash
streamlit run app.py
```

`.venv` 폴더는 GitHub에 업로드하지 않고, 새 환경에서는 `pip install -r requirements.txt`로 다시 설치합니다.

---

## 개발 메모

본 프로젝트는 웹 DB 응용 프로젝트의 최종 구현을 목표로 개발되었습니다.
기본 UI와 DB 연결에서 시작하여 로그인, OCR 분석, 점수 계산, DB 저장, 내 기록 조회, 랭킹, 삭제, 신고 기능을 단계적으로 구현했습니다.
