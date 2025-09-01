# batmon

## 개요

- 서버실의 배치프로그램용 pc (window 11)에 스케줄링된 프로그램을 모니터링
- 브라우저를 이용해서 서버실 출입을 하지 않고 log보기, 프로그램 실패성공확인, 재실행 수행
- 윈도우 서비스에 등록해서 실행

## 빌드

- make_exe.sh 
  - pyinstaller를 사용하여 dist/batmon.exe를 만듬
  - .env.local을  사용하게 함.
  - 기본 PORT를 8002로 사용함

- [nssm](https://coding-shop.tistory.com/463)을 이용해 봄
  - 다운로드하면 32bit/64bit가 있음. 
  - 64bit용을 $HOME/.local/bin에 넣음.
  - 172.20.100.65
  ```bash
  nssm --version
  nssm install (GUI화면이 뜸)
  nssm start Batmon
  nssm status Batmon
  nssm stop Batmon
  ```
  

## 기술스택

- python fastapi로 작성
- window 11 service로 등록해서 동작하게 함. 
- port 8002 사용
- pip대신 uv를 사용

### backend
- uvicorn
- fastapi
- sqlite db
- jinja2

### frontend

- alpine.js
- bootstrap5 css

## 주요기능

- 서버에는 3개의 스케줄링 프로그램이 수행되고 있음
  - kindscrap(공시정보 scrapping) : taskschd (하루 1번 수행 오전 6:00)
  - auto_esafe(esafe문서 다운로드) : taskschd (하루 2번 수행, 오전 7:00, 오후:6:30)
  - fund_mail(fund 메일 수집) : window service로 동작 (매 5분마다 수행)

- 위 기술된 프로그램들이 생성하는 로그 관리
  - 로그를 확인
  - 로그 다운로드
  - 로그 삭제
- 스케줄링 프로그램이 생성한 db(sqlite)를 다운로드
- 스케줄링 프로그램의 실행(실패시 batmon의 버튼 클릭으로 실행)
- 스케줄링 프로그램은 각각 실행폴더를 갖고 있는데, 그 폴더의 파일목록을 조회, 가능하면 파일내용을 보기(확장자로 판별해서)

## 주의

- 로그인 기능 없음 (jwt등 불필요)
- 첫화면은 dashboard로 스케줄링 프로그램의 전반적인 동작 상황을 확인
- 주요기능 즉 프로그램 실패를 확인하고 재실행을 할때 내장된 비밀번호(hard coding)를 넣게끔해서 수행

## HISTORY
| 버전  | 날짜        | 주요 변경사항 |
|-------|-------------|---------------|
| 0.0.2 | 2025-09-01 | • 메인에 화면 캡처 기능 버튼 추가<br>• 프로그램 수행 기능(auto_esafe, kindscrap) 추가 |