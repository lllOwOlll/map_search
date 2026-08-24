import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from geopy.distance import geodesic

load_dotenv()

KAKAO_KEY = os.getenv("KAKAO_REST_API_KEY")

INPUT_FILE = r"D:\study\project_1\last_tast.xlsx"
OUTPUT_DIR = "output"

SHEETS_TO_RUN = [
    "강북구",
    "광진구",
    "도봉구",
    "동대문구",
    "종로구",
    "중랑구",
    "중구",
    "노원2차",
    "성북2차",
]

START_POINTS = {
    "광진구": ("영등포역", "서울 영등포구 경인로 846"),
    "종로구": ("영등포역", "서울 영등포구 경인로 846"),
    "중구": ("영등포역", "서울 영등포구 경인로 846"),
}

DEFAULT_START_NAME = "TGS강북센터"
DEFAULT_START_ADDRESS = "서울 성북구 월계로 30"


def get_start_info(sheet_name):
    return START_POINTS.get(sheet_name, (DEFAULT_START_NAME, DEFAULT_START_ADDRESS))


def kakao_address_search(query):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
    params = {"query": query}

    res = requests.get(url, headers=headers, params=params, timeout=10)

    if res.status_code != 200:
        print("카카오 API 오류:", res.status_code)
        print(res.text)
        raise Exception("카카오 주소 검색 실패")

    return res.json().get("documents", [])


def kakao_keyword_search(query):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
    params = {"query": query, "size": 10}

    res = requests.get(url, headers=headers, params=params, timeout=10)

    if res.status_code != 200:
        print("카카오 API 오류:", res.status_code)
        print(res.text)
        raise Exception("카카오 키워드 검색 실패")

    return res.json().get("documents", [])


def get_coord(address, keyword=None):
    docs = kakao_address_search(address)

    if docs:
        doc = docs[0]
        return {
            "주소": address,
            "위도": float(doc["y"]),
            "경도": float(doc["x"]),
            "검색상태": "주소검색성공",
        }

    if keyword:
        docs = kakao_keyword_search(keyword)
        if docs:
            doc = docs[0]
            return {
                "주소": doc.get("road_address_name") or doc.get("address_name"),
                "위도": float(doc["y"]),
                "경도": float(doc["x"]),
                "검색상태": "키워드검색성공",
            }

    return {
        "주소": address,
        "위도": None,
        "경도": None,
        "검색상태": "실패",
    }


def find_header_row(sheet_name):
    raw = pd.read_excel(INPUT_FILE, sheet_name=sheet_name, header=None)

    for idx in range(len(raw)):
        values = raw.iloc[idx].astype(str).str.strip().tolist()
        if "학교명" in values and "학교주소" in values:
            return idx

    raise ValueError(f"{sheet_name} 시트에서 헤더 행을 찾지 못했습니다.")


def load_sheet_data(sheet_name):
    header_row = find_header_row(sheet_name)
    df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name, header=header_row)

    df.columns = [str(col).strip() for col in df.columns]

    df = df.rename(columns={
        "주소": "구",
        "자치구": "구",
        "학교주소": "학교주소",
        "주소지": "학교주소",
        "보관함 장소": "무인함 위치",
        "무인함 위치": "무인함 위치",
        "설치위치": "무인함 위치",
    })

    if "학교명" not in df.columns:
        raise ValueError(f"{sheet_name} 시트에 '학교명' 컬럼이 없습니다.")

    if "학교주소" not in df.columns:
        raise ValueError(f"{sheet_name} 시트에 '학교주소' 컬럼이 없습니다.")

    if "구" not in df.columns:
        df["구"] = sheet_name

    if "무인함 위치" not in df.columns:
        df["무인함 위치"] = ""

    df = df.dropna(subset=["학교명", "학교주소"])

    df["학교명"] = df["학교명"].astype(str).str.replace("\n", "", regex=False).str.strip()
    df["구"] = df["구"].astype(str).str.strip()
    df["학교주소"] = df["학교주소"].astype(str).str.strip()
    df["무인함 위치"] = df["무인함 위치"].fillna("").astype(str).str.strip()

    df = df[df["학교명"] != ""]
    df = df[df["학교주소"] != ""]

    df = df.drop_duplicates(subset=["학교명", "학교주소"], keep="first")
    df = df.reset_index(drop=True)

    return df


def get_distance_km(a, b):
    return geodesic(
        (a["위도"], a["경도"]),
        (b["위도"], b["경도"])
    ).km


def calculate_route_distance(route, start):
    total = 0.0
    current = start

    for point in route:
        total += get_distance_km(current, point)
        current = point

    return total


def two_opt(route, start):
    best = route[:]
    improved = True

    while improved:
        improved = False
        best_distance = calculate_route_distance(best, start)

        for i in range(len(best) - 1):
            for j in range(i + 2, len(best)):
                new_route = (
                    best[:i + 1]
                    + best[i + 1:j + 1][::-1]
                    + best[j + 1:]
                )

                new_distance = calculate_route_distance(new_route, start)

                if new_distance + 0.0001 < best_distance:
                    best = new_route
                    improved = True
                    break

            if improved:
                break

    return best


def make_route(points, start):
    unvisited = points.copy()
    route = []
    current = start

    while unvisited:
        next_point = min(
            unvisited,
            key=lambda p: get_distance_km(current, p)
        )

        route.append(next_point)
        unvisited.remove(next_point)
        current = next_point

    before = calculate_route_distance(route, start)
    route = two_opt(route, start)
    after = calculate_route_distance(route, start)

    print(f"2-opt: {before:.2f}km → {after:.2f}km / 절감 {before - after:.2f}km")

    return route


def make_route_df(sheet_name):
    start_name, start_address = get_start_info(sheet_name)

    print("\n==============================")
    print("대상 시트:", sheet_name)
    print("출발지:", start_name)
    print("==============================")

    df = load_sheet_data(sheet_name)

    print(f"{sheet_name} 학교 수:", len(df))

    rows = []

    for _, row in df.iterrows():
        school_name = row["학교명"]
        gu = row["구"]
        address = row["학교주소"]
        locker = row["무인함 위치"]

        coord = get_coord(address, school_name)

        rows.append({
            "구역": sheet_name,
            "구": gu,
            "학교명": school_name,
            "무인함 위치": locker,
            "주소": coord["주소"],
            "위도": coord["위도"],
            "경도": coord["경도"],
            "검색상태": coord["검색상태"],
        })

        print(school_name, coord["검색상태"])
        time.sleep(0.1)

    point_df = pd.DataFrame(rows)

    failed = point_df[point_df["검색상태"] == "실패"]

    if not failed.empty:
        failed_file = f"{OUTPUT_DIR}/{sheet_name}_주소확인필요.xlsx"
        failed.to_excel(failed_file, index=False)
        print("주소 검색 실패:", failed_file)
        return None, point_df

    start_coord = get_coord(start_address, start_name)

    start = {
        "학교명": start_name,
        "주소": start_address,
        "위도": start_coord["위도"],
        "경도": start_coord["경도"],
    }

    points = point_df.to_dict("records")
    route = make_route(points, start)

    final_rows = []

    final_rows.append({
        "구역": sheet_name,
        "순서": 0,
        "학교명": start_name,
    })

    for idx, point in enumerate(route, start=1):
        final_rows.append({
            "구역": sheet_name,
            "순서": idx,
            "학교명": point["학교명"],
        })

    route_df = pd.DataFrame(final_rows)

    return route_df, point_df


def save_all_outputs(all_route_rows):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    txt_file = f"{OUTPUT_DIR}/전체_방문순서.txt"
    excel_file = f"{OUTPUT_DIR}/전체_방문순서.xlsx"

    txt_lines = []

    for sheet_name, route_df in all_route_rows.items():
        txt_lines.append(f"[{sheet_name}]")

        for _, row in route_df.iterrows():
            txt_lines.append(f"{row['순서']}. {row['학교명']}")

        txt_lines.append("")

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))

    excel_rows = []

    for _, route_df in all_route_rows.items():
        for _, row in route_df.iterrows():
            excel_rows.append({
                "구역": row["구역"],
                "순서": row["순서"],
                "학교명": row["학교명"],
            })

    pd.DataFrame(excel_rows).to_excel(excel_file, index=False)

    print("\n저장 완료")
    print("TXT:", txt_file)
    print("Excel:", excel_file)


def main():
    if not KAKAO_KEY:
        raise ValueError(".env 파일에 KAKAO_REST_API_KEY가 없습니다.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("카카오 키 확인:", KAKAO_KEY[:6] + "******")

    all_route_rows = {}

    for sheet_name in SHEETS_TO_RUN:
        route_df, point_df = make_route_df(sheet_name)

        point_file = f"{OUTPUT_DIR}/{sheet_name}_주소좌표목록.xlsx"
        point_df.to_excel(point_file, index=False)

        if route_df is None:
            continue

        all_route_rows[sheet_name] = route_df

        route_file = f"{OUTPUT_DIR}/{sheet_name}_방문순서.xlsx"
        route_df.to_excel(route_file, index=False)

        print(f"\n[{sheet_name}] 방문 순서")
        for _, row in route_df.iterrows():
            print(f"{row['순서']}. {row['학교명']}")

    save_all_outputs(all_route_rows)


if __name__ == "__main__":
    main()