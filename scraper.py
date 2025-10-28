import requests
import pandas as pd
from datetime import datetime
import time
import os # CSV 파일 존재 여부 확인을 위해 import

# 1. 수집할 열람실 ID 목록 (전체 반영)
ROOMS_TO_SCRAPE = {
    # '53': '숭실스퀘어ON(2F)',
    # '54': '오픈열람실(2F)',
    # '60': '숭실멀티라운지(5F)',
    '59': '리클라이너(5F)',
    # '57': '마루열람실(6F)',
    # '58': '대학원열람실(6F)',
    # '15': '1열람실(B1F)'
}

# 2. API 기본 정보
BASE_API_URL = "https://oasis.ssu.ac.kr/pyxis-api/1/api/rooms/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
    'Referer': 'https://oasis.ssu.ac.kr/library-services/smuf/reading-rooms/53' # Referer는 어떤 ID로 고정해도 무방합니다.
}

# 3. 데이터 저장 파일명
CSV_FILENAME = 'recliner_seats_log.csv'

def scrape_room_data(room_id, room_name, headers):
    """지정된 열람실 ID의 좌석 데이터를 스크래핑합니다."""
    
    url = f"{BASE_API_URL}{room_id}/seats"
    collected_data = []
    
    # 데이터 수집 시각 (모든 좌석에 동일하게 적용)
    now_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # 4. 헤더를 포함하여 API에 GET 요청
        response = requests.get(url, headers=headers)
        
        # 200 OK 상태가 아니면 오류 발생
        response.raise_for_status() 
        
        # JSON 데이터 파싱
        data = response.json()

        # 5. 우리가 확인한 'data' -> 'list' 구조로 접근
        seat_list = data['data']['list']
        
        for seat in seat_list:
            seat_number = seat['code']      # 좌석 번호
            is_occupied = seat['isOccupied']  # 점유 여부 (True/False)
            
            collected_data.append({
                'timestamp': now_timestamp,
                'room_name': room_name,
                'seat_number': seat_number,
                'is_occupied': 1 if is_occupied else 0  # 1 (점유) / 0 (비어있음)
            })
            
        print(f"  [성공] '{room_name}'에서 {len(collected_data)}개 좌석 정보 수집 완료.")
        return collected_data

    except requests.exceptions.RequestException as e:
        print(f"  [실패] '{room_name}' 수집 중 API 요청 오류: {e}")
        return None
    except KeyError as e:
        print(f"  [실패] '{room_name}' 수집 중 JSON 파싱 오류: 키 '{e}'를 찾을 수 없습니다.")
        print(f"  서버 응답: {response.text[:200]}...") # 응답 내용 일부 출력
        return None
    except Exception as e:
        print(f"  [실패] '{room_name}' 수집 중 알 수 없는 오류: {e}")
        return None

# --- 메인 스크립트 실행 ---
if __name__ == '__main__':
    
    print(f"--- 도서관 좌석 스크래핑 시작 ({datetime.now()}) ---")
    
    all_rooms_data = []
    
    for room_id, room_name in ROOMS_TO_SCRAPE.items():
        print(f"-> '{room_name}' (ID: {room_id}) 수집 시도...")
        room_data = scrape_room_data(room_id, room_name, HEADERS)
        
        if room_data:
            all_rooms_data.extend(room_data)
        
        # 서버에 부담을 주지 않기 위해 각 열람실 요청 사이에 1초 대기
        time.sleep(1)

    # 6. 수집한 데이터가 있을 경우 CSV 파일로 저장
    if all_rooms_data:
        df = pd.DataFrame(all_rooms_data)
        
        # 파일이 이미 존재하는지 확인
        file_exists = os.path.exists(CSV_FILENAME)
        
        try:
            # 'a' (append) 모드로 저장
            # header=not file_exists: 파일이 없었을 때만 헤더(컬럼명)를 씀
            df.to_csv(
                CSV_FILENAME, 
                mode='a', 
                header=not file_exists, 
                index=False, 
                encoding='utf-8-sig', 
                lineterminator='\n'
            )
            print(f"--- 총 {len(all_rooms_data)}건 데이터 저장 완료. ({CSV_FILENAME}) ---")
            
        except IOError as e:
            print(f"CSV 파일 저장 중 오류 발생: {e}")
            
    else:
        print("--- 수집된 새 데이터가 없습니다. ---")