import os
import pandas as pd


def load_recommendations():
    """CSV 파일에서 추천 데이터를 로드합니다."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "short.csv")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except FileNotFoundError:
        print(f"Error: CSV 파일을 찾을 수 없습니다. 경로 확인: {csv_path}")
        return {}
    except Exception as e:
        print(f"Error: CSV 파일 읽기 실패 - {str(e)}")
        return {}

    recommendation_map = {}
    for _, row in df.iterrows():
        key = (
            row["일정"].strip(),
            row["변화"].strip(),
            row["시간대"].strip(),
            row["혼자/함께"].strip(),
            row["감각유형"].strip()
        )
        recommendation_map[key] = [
            row["추천 활동 1"],
            row["추천 활동 2"],
            row["추천 활동 3"]
        ]
    return recommendation_map


def ask_user():
    """질문을 통해 사용자 입력을 받는다."""
    schedule = input("일정 스타일을 선택하세요 (루즈/타이트): ").strip()
    change = input("일정 변화에 적응하는 편인가요? (O/X): ").strip().upper()
    time = input("아침형인가요, 저녁형인가요? (아침/저녁): ").strip()
    social = input("혼자 하는 걸 선호하나요, 함께 하는 걸 선호하나요? (혼자/함께): ").strip()
    sensory = input("감각유형을 입력하세요 (감각 둔감형/감각 민감+추구형/감각 추구형/감각 민감+회피형/감각 회피형): ").strip()

    # 스트레스 해소 방법 입력 여부
    stress_input = input("스트레스 해소 방법이 있나요? (O/X): ").strip().upper()
    user_methods = []
    if stress_input == "O":
        print("\n[스트레스 해소 방법 입력] 최대 3가지 (종료: Enter)")
        for i in range(3):
            method = input(f"{i + 1}. ").strip()
            if not method:
                break
            user_methods.append(method)

    return {
        "schedule": schedule,
        "change": change,
        "time": time,
        "social": social,
        "sensory": sensory,
        "stress_input": stress_input,
        "user_methods": user_methods
    }


def get_recommendation(recommendation_map, user_input):
    key = (
        user_input["schedule"],
        user_input["change"],
        user_input["time"],
        user_input["social"],
        user_input["sensory"]
    )
    return recommendation_map.get(key, ["추천 활동이 없습니다."])


def main():
    recommendation_map = load_recommendations()
    if not recommendation_map:
        return

    user_input = ask_user()
    default_recommendations = get_recommendation(recommendation_map, user_input)

    # 최종 추천 생성
    if user_input["stress_input"] == "O":
        combined = user_input["user_methods"] + default_recommendations
        final_recommendations = combined[:3]
    else:
        final_recommendations = default_recommendations

    # 결과 출력
    print("\n✏️ 추천 활동:")
    for activity in final_recommendations:
        print(f"- {activity}")


if __name__ == "__main__":
    main()
