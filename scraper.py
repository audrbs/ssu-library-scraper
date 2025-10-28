import requests
import pandas as pd
from datetime import datetime
import time
import os

# 1. 수집할 열람실 ID (우리의 목표는 리클라이너 '59')
TARGET_ROOM_ID = 59
TARGET_ROOM_NAME = '리클라이너(5F)'

# 2. API 기본 정보 (로그인 필요 없는 '요약' API 주소)
SUMMARY_API_URL = "https://oasis.ssu.ac.kr/pyxis-api/1/seat-rooms?smufMethodCode=PC&roomTypeId=2&branchGroupId=1"

# 3. 요청 헤더 (봇 차단 방지를 위해 추가)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
    'Referer': 'https://oasis.ssu.ac.kr/'
}

# 4. 데이터 저장 파일명
# (GitHub Actions 워크플로우(.yml)에서 이 이름을 사용하도록 설정했음)
CSV_FILENAME = 'recliner_seats_log.csv'

def scrape_summary_data(url, headers):
    """요약 API에서 리클라이너 좌석 현황만 추출합니다."""
    
    collected_data = []
    now_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # 5. 헤더를 포함하여 '요약 API'에 GET 요청
        response = requests.get(url, headers=headers)
        response.raise_for_status() # 200 OK가 아니면 오류 발생
        data = response.json()

        # 6. 'data' -> 'list' 구조로 접근 (이전 JSON 확인 완료)
        room_list = data['data']['list']
        
        found = False
        for room in room_list:
            # 7. 모든 열람실 중, 우리가 원하는 리클라이너(ID 59)만 필터링
            if room['id'] == TARGET_ROOM_ID:
                found = True
                seat_info = room['seats']
                
                collected_data.append({
                    'timestamp': now_timestamp,
                    'room_name': TARGET_ROOM_NAME,
                    'total': seat_info['total'],
                    'occupied': seat_info['occupied'],
                    'available': seat_info['available'] # 우리가 예측할 목표 값
                })
                break # 리클라이너 찾았으니 반복 중지
        
        if not found:
            print(f"  [실패] API 응답에서 'ID: {TARGET_ROOM_ID}'를 찾을 수 없습니다.")
            return None
            
        print(f"  [성공] '{TARGET_ROOM_NAME}' 요약 정보 수집 완료 (Available: {seat_info['available']})")
        return collected_data

    except requests.exceptions.RequestException as e:
        print(f"  [실패] API 요청 오류: {e}")
        return None
    except KeyError as e:
        print(f"  [실패] JSON 파싱 오류: 키 '{e}'를 찾을 수 없습니다.")
        print(f"  서버 응답: {response.text[:200]}...")
        return None

# --- 메인 스크립트 실행 ---
if __name__ == '__main__':
    
    print(f"--- 도서관 좌석 스크래핑 시작 ({datetime.now()}) ---")
    
    # 8. 헤더를 인수로 전달
    room_data = scrape_summary_data(SUMMARY_API_URL, HEADERS)

    if room_data:
        df = pd.DataFrame(room_data)
        file_exists = os.path.exists(CSV_FILENAME)
        
        try:
            # 9. CSV 파일 저장 (기존 파일에 이어쓰기)
            df.to_csv(
                CSV_FILENAME, 
                mode='a', 
                header=not file_exists, 
                index=False, 
                encoding='utf-8-sig', 
                lineterminator='\n'
            )
            print(f"--- 총 {len(room_data)}건 데이터 저장 완료. ({CSV_FILENAME}) ---")
        except IOError as e:
            print(f"CSV 파일 저장 중 오류 발생: {e}")
    else:
        print("--- 수집된 새 데이터가 없습니다. ---")
