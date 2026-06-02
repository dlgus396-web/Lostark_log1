# 로스트아크 전투 분석기 플랫폼

## 프로젝트 개요
Streamlit과 Supabase를 이용한 로스트아크 전투 기록 분석 플랫폼의 기본틀입니다.

## 실행 방법
1. 필수 패키지 설치
	```bash
	pip install -r requirements.txt
	```
2. 환경 변수 설정
	- `.streamlit/secrets.toml` 파일을 생성하고 아래와 같이 입력하세요.
	  ```
	  SUPABASE_URL = "your-supabase-url"
	  SUPABASE_KEY = "your-supabase-anon-key"
	  ```
3. 앱 실행
	```bash
	streamlit run app.py
	```
4. 브라우저에서 안내된 주소(일반적으로 http://localhost:8501)로 접속

## 현재 구현 범위
- Streamlit 기본 UI 및 페이지 이동 구조
- Supabase DB 연결 및 조회 (직업, 레이드, 점수 규칙, 기준 데이터)
- mock 데이터 기반 랭킹/내 기록/분석 흐름
- mock 업로드/분석/점수 계산 테스트
- 예외 및 오류 안내 메시지 처리

## 추후 구현 예정 기능
- Discord 로그인 및 사용자 인증
- Supabase Storage 이미지 업로드
- OCR.Space 및 Tesseract 연동
- 실제 combat_records 저장 및 랭킹/내 기록 실시간 조회
- 신고 기능 및 관리자 화면

## 기타
- 프로젝트 루트(app.py, lib, pages) 기준으로 실행됩니다.
- `project/` 등 중복 폴더는 사용하지 않습니다.