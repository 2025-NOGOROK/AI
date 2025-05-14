from flask import Flask, request, jsonify
import pandas as pd
import os

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # 5000으로 통일

