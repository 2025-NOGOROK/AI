from flask import Flask, request, jsonify
import pandas as pd
import os
import numpy as np
import math
from sentence_transformers import SentenceTransformer
from geopy.distance import geodesic
from datetime import datetime, date

app = Flask(__name__)

# 루트 경로 추가 ✅
@app.route('/')
def home():
    return "Flask 추천 서버가 실행 중입니다. POST 요청을 /recommend로 보내주세요."

def load_recommendations():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "short.csv")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error: {e}")
        return None
    recommendation_map = {}
    for _, row in df.iterrows():
        key = (
            str(row["일정"]).strip(),
            str(row["변화"]).strip(),
            str(row["시간대"]).strip(),
            str(row["혼자/함께"]).strip(),
            str(row["감각유형"]).strip()
        )
        recommendation_map[key] = [
            str(row["추천 활동 1"]),
            str(row["추천 활동 2"]),
            str(row["추천 활동 3"])
        ]
    return recommendation_map

recommendation_map = load_recommendations()

@app.route('/recommend', methods=['POST'])
def recommend():
    if recommendation_map is None:
        return jsonify({"error": "추천 데이터가 없습니다."}), 500

    data = request.json

    # Java에서 Boolean이 올 경우 문자열로 변환
    change = data.get("change")
    if isinstance(change, bool):
        change = "O" if change else "X"
    elif change is None:
        change = "X"
    else:
        change = str(change).strip()

    key = (
        str(data.get("schedule", "")).strip(),
        change,
        str(data.get("time", "")).strip(),
        str(data.get("social", "")).strip(),
        str(data.get("sensory", "")).strip()
    )

    user_methods = data.get("user_methods", [])
    # user_methods가 None이면 빈 리스트로
    if user_methods is None:
        user_methods = []

    stress_input = data.get("stress_input", "X")
    if isinstance(stress_input, bool):
        stress_input = "O" if stress_input else "X"
    else:
        stress_input = str(stress_input).strip().upper()

    default_recommendations = recommendation_map.get(key, ["추천 활동이 없습니다."])

    if stress_input == "O":
        # 중복 제거, 최대 3개
        combined = user_methods + [act for act in default_recommendations if act not in user_methods]
        final_recommendations = combined[:3]
    else:
        final_recommendations = default_recommendations

    return jsonify(final_recommendations)

###########################################위 코드는 수정하지마시오#########################################################

# 1. long.csv 로드
df = pd.read_csv("long.csv")

# 2. 임베딩 모델 로드
model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')

def safe_json(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj

def cosine_similarity(a, b):
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_event_text(row):
    if pd.notnull(row.get('프로그램소개')):
        return f"{row['공연/행사명']} {row['프로그램소개']}"
    else:
        return row['공연/행사명']

def calc_score(sim, event_lat, event_lon, user_lat, user_lon, is_free):
    if user_lat and user_lon and not pd.isnull(event_lat) and not pd.isnull(event_lon):
        try:
            distance = geodesic((user_lat, user_lon), (event_lat, event_lon)).km
            distance_score = max(0, 1 - distance/10)
        except:
            distance_score = 0.5
    else:
        distance_score = 0.5
    price_score = 1.0 if is_free else 0.7
    return 0.7*sim + 0.2*distance_score + 0.1*price_score

def is_today_event(row):
    try:
        today = date.today()
        start_str = str(row.get('시작일', '')).strip()
        end_str = str(row.get('종료일', '')).strip()
        # '2025/06/02 0:00' 같은 형식 처리
        start_date = datetime.strptime(start_str, '%Y/%m/%d %H:%M').date()
        end_date = datetime.strptime(end_str, '%Y/%m/%d %H:%M').date()
        return start_date <= today <= end_date
    except Exception as e:
        print(f"날짜 파싱 오류: {e}, 행 데이터: {row}")
        return False


@app.route('/vector-recommend', methods=['POST'])
def vector_recommend():
    data = request.json
    user_title = data.get('title', '')
    user_label = data.get('label', '')
    stress = float(data.get('stress', 0.0))
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')

    # ★ 오늘 행사만 필터링
    today_df = df[df.apply(is_today_event, axis=1)]
    print(f"오늘 행사 개수: {len(today_df)}")  # 로깅 추가

    if stress >= 80:
        candidates = today_df[today_df['분류'].isin(["클래식", "국악", "전시/미술", "무용"])]
        user_vec = model.encode([user_title])[0]
    else:
        candidates = today_df
        user_vec = model.encode([f"{user_label} {user_title}"])[0]

    results = []
    for _, row in candidates.iterrows():
        event_text = get_event_text(row)
        event_vec = model.encode([event_text])[0]
        sim = cosine_similarity(user_vec, event_vec)
        event_lat = row.get('위도(Y좌표)')
        event_lon = row.get('경도(X좌표)')
        is_free = (row.get('유무료') == '무료')
        score = calc_score(sim, event_lat, event_lon, user_lat, user_lon, is_free)
        results.append((score, row))

    top2 = sorted(results, key=lambda x: x[0], reverse=True)[:2]

    output = []
    for score, row in top2:
        output.append({
            "title": row['공연/행사명'],
            "label": row['분류'],
            "description": safe_json(row.get('장소', '')),
            "program_intro": safe_json(row.get('프로그램소개', ''))
        })

    return jsonify(output)






################################################아래 코드 수정 금지#######################################################################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # 5000으로 통일

