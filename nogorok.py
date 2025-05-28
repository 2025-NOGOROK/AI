from flask import Flask, request, jsonify
import pandas as pd
import os
import numpy as np
import math

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

def safe_json(obj):
    # NaN, None, nan 등은 모두 null로
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj

# 2. 벡터화(임베딩) 함수 예시 (실제 서비스에서는 더 정교한 임베딩 사용)
def simple_vector(text):
    return np.array([sum(ord(c) for c in str(text))])

def cosine_similarity(a, b):
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@app.route('/vector-recommend', methods=['POST'])
def vector_recommend():
    data = request.json
    user_title = data.get('title', '')
    user_label = data.get('label', '')
    stress = float(data.get('stress', 0.0))

    # 1) 스트레스 80 이상: 특정 라벨만 필터링
    if stress >= 80:
        candidates = df[df['분류'].isin(["클래식", "국악", "전시/미술", "무용"])]
        user_vec = simple_vector(user_title)
    else:
        # 2) 80 미만: 전체에서 라벨+타이틀 벡터화
        candidates = df
        user_vec = simple_vector(f"{user_label} {user_title}")

    # 후보별 유사도 계산
    candidates = candidates.copy()
    candidates['sim'] = candidates['공연/행사명'].apply(
        lambda x: cosine_similarity(user_vec, simple_vector(x))
    )

    # 유사도 내림차순 정렬 후 상위 2개 추출
    top2 = candidates.sort_values(by='sim', ascending=False).head(2)

    # 추천 결과 포맷 (Spring DTO와 맞추기)
    results = []
    for _, row in top2.iterrows():
        results.append({
            "title": row['공연/행사명'],
            "label": row['분류'],
            "description": safe_json(row.get('프로그램소개', ''))
        })

    return jsonify(results)





################################################아래 코드 수정 금지#######################################################################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # 5000으로 통일

