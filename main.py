# 코랩에 복붙해서 실행하세요

# 필요한 라이브러리 설치
!pip install --upgrade gspread google-auth slack_sdk ratelimit

from slack_sdk import WebClient
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import re
from gspread.exceptions import WorksheetNotFound
from time import sleep
from ratelimit import limits, sleep_and_retry

# 슬랙과 구글 시트 설정
SLACK_BOT_TOKEN = "YOUR_SLACK_BOT_TOKEN"  # 슬랙 API 토큰 입력
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"    # 스프레드시트 ID 입력

# 제외할 사용자 ID 설정
BOT_USER_ID = "YOUR_BOT_USER_ID"  # 봇 사용자 ID 설정
ADMIN_USER_IDS = ["ADMIN_USER_ID_1", "ADMIN_USER_ID_2", "ADMIN_USER_ID_3"]  # 관리자 사용자 ID 리스트 설정
EXCLUDED_USER_IDS = [BOT_USER_ID] + ADMIN_USER_IDS

# 각 조의 채널 ID 리스트 설정 (1조부터 14조까지)
CHANNEL_IDS = [
    "CHANNEL_ID_1", "CHANNEL_ID_2", "CHANNEL_ID_3", "CHANNEL_ID_4",
    "CHANNEL_ID_5", "CHANNEL_ID_6", "CHANNEL_ID_7", "CHANNEL_ID_8",
    "CHANNEL_ID_9", "CHANNEL_ID_10", "CHANNEL_ID_11", "CHANNEL_ID_12",
    "CHANNEL_ID_13", "CHANNEL_ID_14"
]

# 슬랙 클라이언트 초기화
client = WebClient(token=SLACK_BOT_TOKEN)

# 구글 스프레드시트 인증 설정
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(
    "PATH_TO_YOUR_SERVICE_ACCOUNT_JSON_FILE",  # 서비스 계정 키 파일 경로를 업데이트하세요
    scopes=SCOPES
)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# 사용할 시트 이름 입력받기
sheet_name = input("사용할 시트 이름을 입력하세요 (예: '1주차'): ")

# 시트 열기 또는 생성하기
try:
    worksheet = spreadsheet.worksheet(sheet_name)
except WorksheetNotFound:
    # 시트가 없으면 생성
    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
    print(f"새로운 시트를 생성했습니다: {sheet_name}")

# 메인 실행

# 시트 초기화 및 헤더 추가
worksheet.clear()
header = ['조', '이름', '글', '댓글']
worksheet.append_row(header)

for idx, channel_id in enumerate(CHANNEL_IDS):
    group_number = idx + 1  # 조 번호 (1부터 시작)
    CHANNEL_ID = channel_id

    print(f"{group_number}조 데이터를 처리 중입니다...")

    # 채널 멤버 가져오기
    try:
        channel_members = get_channel_members(CHANNEL_ID)
    except Exception as e:
        print(f"{group_number}조 채널 멤버를 가져오는 중 오류 발생: {e}")
        continue  # 다음 조로 넘어감

    # 사용자 ID와 이름 매핑
    try:
        user_id_name = get_user_id_name_mapping(channel_members)
    except Exception as e:
        print(f"{group_number}조 사용자 정보를 가져오는 중 오류 발생: {e}")
        continue  # 다음 조로 넘어감

    # 사용자 활동 수집
    try:
        user_posts, user_comments = get_user_activity(channel_members, CHANNEL_ID)
    except Exception as e:
        print(f"{group_number}조 사용자 활동을 가져오는 중 오류 발생: {e}")
        continue  # 다음 조로 넘어감

    # 스프레드시트 업데이트
    update_spreadsheet(user_posts, user_comments, user_id_name, group_number)

    # API 호출 제한을 고려하여 지연 시간 추가
    sleep(1)  # 각 조별로 1초 지연

print("모든 조의 데이터 처리가 완료되었습니다!")

# 함수 정의 부분

@sleep_and_retry
@limits(calls=50, period=60)  # 슬랙 API 호출 제한을 고려한 데코레이터
def get_channel_members(channel_id):
    response = client.conversations_members(channel=channel_id)
    members = response['members']
    # 제외할 사용자 제거
    members = [user_id for user_id in members if user_id not in EXCLUDED_USER_IDS]
    return members

@sleep_and_retry
@limits(calls=50, period=60)
def get_user_id_name_mapping(user_ids):
    user_id_name = {}
    for user_id in user_ids:
        response = client.users_info(user=user_id)
        user_info = response.get('user', {})
        real_name = user_info.get('real_name', '')
        user_id_name[user_id] = real_name
    return user_id_name

def sort_user_ids_by_name(user_id_name):
    user_list = [(user_id, name) for user_id, name in user_id_name.items()]

    def is_korean(char):
        return '가' <= char <= '힣'

    def sort_key(item):
        name = item[1]
        if name:
            first_char = name[0]
            if is_korean(first_char):
                return (0, name)
            else:
                return (1, name.lower())
        else:
            return (2, '')

    sorted_user_list = sorted(user_list, key=sort_key)
    sorted_user_ids = [user_id for user_id, name in sorted_user_list]
    return sorted_user_ids

def get_time_ranges():
    today = datetime.utcnow() + timedelta(hours=9)  # 한국 시간으로 변환
    today_weekday = today.weekday()

    # 이번 주 목요일 오전 0시 계산
    this_thursday = today - timedelta(days=(today_weekday - 3))
    this_thursday = this_thursday.replace(hour=0, minute=0, second=0, microsecond=0)
    last_thursday = this_thursday - timedelta(weeks=1)

    # 글 상태를 위한 시간대
    post_complete_start = last_thursday
    post_complete_end = last_thursday + timedelta(days=3, hours=23, minutes=59, seconds=59)

    post_late_start = post_complete_end + timedelta(seconds=1)
    post_late_end = this_thursday - timedelta(seconds=1)

    # 댓글 상태를 위한 시간대
    comment_complete_start = last_thursday
    comment_complete_end = last_thursday + timedelta(days=4, hours=23, minutes=59, seconds=59)

    comment_late_start = comment_complete_end + timedelta(seconds=1)
    comment_late_end = this_thursday - timedelta(seconds=1)

    return {
        'post_complete': (int(post_complete_start.timestamp()), int(post_complete_end.timestamp())),
        'post_late': (int(post_late_start.timestamp()), int(post_late_end.timestamp())),
        'comment_complete': (int(comment_complete_start.timestamp()), int(comment_complete_end.timestamp())),
        'comment_late': (int(comment_late_start.timestamp()), int(comment_late_end.timestamp())),
        'total_period': (int(last_thursday.timestamp()), int(this_thursday.timestamp())),
    }

@sleep_and_retry
@limits(calls=50, period=60)
def get_user_activity(user_ids, channel_id):
    time_ranges = get_time_ranges()
    total_oldest = time_ranges['total_period'][0]
    total_latest = time_ranges['total_period'][1]

    user_posts = {user_id: [] for user_id in user_ids}
    user_comments = {user_id: [] for user_id in user_ids}

    # 채널의 메시지 가져오기 (페이징 처리)
    messages = []
    has_more = True
    next_cursor = None

    while has_more:
        response = client.conversations_history(
            channel=channel_id,
            oldest=total_oldest,
            latest=total_latest,
            limit=1000,
            cursor=next_cursor
        )
        messages.extend(response.get('messages', []))
        has_more = response.get('has_more', False)
        next_cursor = response.get('response_metadata', {}).get('next_cursor')

    for message in messages:
        user = message.get('user')
        ts = float(message.get('ts'))
        if user in user_ids:
            user_posts[user].append(ts)

        # 스레드 내 댓글 가져오기
        if message.get('reply_count', 0) > 0:
            has_more_replies = True
            next_reply_cursor = None

            while has_more_replies:
                replies_response = client.conversations_replies(
                    channel=channel_id,
                    ts=message['ts'],
                    oldest=total_oldest,
                    latest=total_latest,
                    inclusive=True,
                    limit=1000,
                    cursor=next_reply_cursor
                )
                replies = replies_response.get('messages', [])
                has_more_replies = replies_response.get('has_more', False)
                next_reply_cursor = replies_response.get('response_metadata', {}).get('next_cursor')

                for reply in replies[1:]:
                    reply_user = reply.get('user')
                    reply_ts = float(reply.get('ts'))
                    # 댓글 작성자가 자신의 메시지에 댓글을 단 것이 아닌지 확인
                    if reply_user in user_ids and reply_user != user:
                        user_comments[reply_user].append(reply_ts)

    return user_posts, user_comments

def calculate_post_status(post_times, time_ranges):
    status = 2  # 기본은 결석(2)
    for ts in post_times:
        if time_ranges['post_complete'][0] <= ts <= time_ranges['post_complete'][1]:
            return 0  # 완료(0)
        elif time_ranges['post_late'][0] <= ts <= time_ranges['post_late'][1]:
            status = min(status, 1)  # 지각(1)
    return status

def calculate_comment_status(comment_times, time_ranges):
    complete_comments = 0
    late_comments = 0

    for ts in comment_times:
        if time_ranges['comment_complete'][0] <= ts <= time_ranges['comment_complete'][1]:
            complete_comments += 1
        elif time_ranges['comment_late'][0] <= ts <= time_ranges['comment_late'][1]:
            late_comments += 1

    total_comments = complete_comments + late_comments

    if total_comments >= 2:
        if complete_comments >= 2:
            return 0  # 완료(0)
        elif complete_comments == 1:
            return 1  # 1개 지각(1)
        else:
            return 2  # 2개 지각(2)
    elif total_comments == 1:
        return 3  # 1개 결석(3)
    else:
        return 4  # 2개 결석(4)

def update_spreadsheet(user_posts, user_comments, user_id_name, group_number):
    time_ranges = get_time_ranges()

    # 사용자 ID를 이름 순서로 정렬
    sorted_user_ids = sort_user_ids_by_name(user_id_name)

    # 데이터 행 준비
    data_rows = []
    for user_id in sorted_user_ids:
        name = user_id_name.get(user_id, 'Unknown')
        post_status = calculate_post_status(user_posts.get(user_id, []), time_ranges)
        comment_status = calculate_comment_status(user_comments.get(user_id, []), time_ranges)
        row = [f'{group_number}조', name, post_status, comment_status]
        data_rows.append(row)

    # 데이터 행을 한 번에 추가
    worksheet.append_rows(data_rows)
    print(f"{group_number}조의 데이터가 스프레드시트에 업데이트되었습니다.")
