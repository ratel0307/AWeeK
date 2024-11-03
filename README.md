# AWeeK
차감 카운트 코드입니다. 

Slack 활동 자동화 스크립트
이 프로젝트는 Slack 채널에서 사용자들의 활동을 수집하여 Google 스프레드시트에 기록하는 Python 스크립트입니다. 각 조별로 글 작성 및 댓글 활동을 추적하고, 주차별로 결과를 정리할 수 있습니다.

기능
글 및 댓글 활동 추적: 각 사용자의 글 작성 여부와 댓글 참여 여부를 추적합니다.
시간대 구분: 완료, 지각, 결석 상태를 자동으로 계산합니다.
자기 댓글 제외: 사용자가 자신의 메시지에 단 댓글은 제외하고, 다른 사람의 메시지에 단 댓글만 인정합니다.
자동화된 데이터 입력: 수집된 데이터를 Google 스프레드시트에 자동으로 기록합니다.
조별 처리: 여러 조의 데이터를 한 번에 처리하고, 결과를 정리합니다.
설치 방법
1. 필수 라이브러리 설치
bash
코드 복사
pip install gspread google-auth slack_sdk ratelimit
2. Google Cloud Platform 설정
**서비스 계정 키(JSON 파일)**를 생성합니다.
Google Drive API 및 Google Sheets API를 활성화합니다.
서비스 계정에 스프레드시트 편집 권한을 부여합니다.
3. Slack 앱 설정
Slack API 페이지에서 새로운 앱을 생성합니다.
OAuth & Permissions에서 필요한 권한 범위를 추가합니다:
channels:history
channels:read
groups:history
groups:read
users:read
OAuth 토큰을 발행하고, 봇을 해당 채널에 초대합니다.
사용 방법
1. 환경 변수 및 설정 업데이트
스크립트 내에서 다음 변수를 자신의 설정에 맞게 수정합니다.

python
코드 복사
SLACK_BOT_TOKEN = "YOUR_SLACK_BOT_TOKEN"
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"
BOT_USER_ID = "YOUR_BOT_USER_ID"
ADMIN_USER_IDS = ["ADMIN_USER_ID_1", "ADMIN_USER_ID_2"]
CHANNEL_IDS = ["CHANNEL_ID_1", "CHANNEL_ID_2", ..., "CHANNEL_ID_14"]
SLACK_BOT_TOKEN: Slack 앱의 OAuth 토큰입니다.
SPREADSHEET_ID: 데이터를 기록할 Google 스프레드시트의 ID입니다.
BOT_USER_ID: Slack 봇의 사용자 ID입니다.
ADMIN_USER_IDS: 활동 추적에서 제외할 관리자 사용자 ID의 리스트입니다.
CHANNEL_IDS: 각 조의 Slack 채널 ID 리스트입니다.
2. 스크립트 실행
bash
코드 복사
python your_script_name.py
3. 시트 이름 입력
실행 시 프롬프트에 따라 사용할 시트 이름을 입력합니다.

arduino
코드 복사
사용할 시트 이름을 입력하세요 (예: '1주차'):
4. 결과 확인
스크립트 실행이 완료되면, 지정한 Google 스프레드시트에서 결과를 확인할 수 있습니다.

주의 사항
API 호출 제한: Slack API는 일정 시간 내에 호출 수를 제한합니다. 스크립트는 ratelimit 라이브러리를 사용하여 호출 빈도를 조절하지만, 많은 데이터를 처리할 경우 제한에 도달할 수 있습니다.
채널 접근 권한: 봇이 각 채널에 초대되어 있어야 해당 채널의 정보를 가져올 수 있습니다.
개인정보 보호: 사용자 정보 취급 시 개인정보 보호에 유의하세요.
기여 방법
이 저장소를 포크(Fork) 합니다.
기능을 추가하거나 버그를 수정합니다.
변경 내용을 커밋(Commit) 합니다.
Pull Request를 생성하여 변경 사항을 제출합니다.
라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참고하세요.

문의 사항
프로젝트와 관련하여 질문이나 제안 사항이 있으시면 이슈(Issue) 를 등록해 주세요.
