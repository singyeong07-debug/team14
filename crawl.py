# crawl.py
# 역할: 다이소몰 리뷰 크롤링 → 감성분석 → CSV/엑셀 저장

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import pandas as pd
import time
import re


# ============================================================
# 분석할 제품 목록 (URL을 실제 주소로 교체)
# ============================================================
PRODUCTS = [
    # 스킨케어 (판매량 상위 3개)
    {"카테고리": "스킨케어", "제품명": "스킨케어 1등(앰플)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1049275&recmYn=N"},
    {"카테고리": "스킨케어", "제품명": "스킨케어 2등(토너)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1044553&recmYn=N"},
    {"카테고리": "스킨케어", "제품명": "스킨케어 3등(앰플)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1061918&recmYn=N"},

    # 메이크업 (판매량 상위 3개)
    {"카테고리": "메이크업", "제품명": "메이크업 1등(팩트)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1061379&recmYn=N"},
    {"카테고리": "메이크업", "제품명": "메이크업 2등(프라이머)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1064166&recmYn=N"},
    {"카테고리": "메이크업", "제품명": "메이크업 3등(브로우펜슬)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1045431&recmYn=N"},

    # 뷰티소품 (판매량 상위 3개)
    {"카테고리": "뷰티소품", "제품명": "뷰티소품 1등(퍼프)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1039628&recmYn=N"},
    {"카테고리": "뷰티소품", "제품명": "뷰티소품 2등(쿨링스틱)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1048910&recmYn=N"},
    {"카테고리": "뷰티소품", "제품명": "뷰티소품 3등(퍼프)", "url": "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1066897&recmYn=N"},
]

MAX_REVIEWS = 150  # 제품당 최대 수집 리뷰 수


# ============================================================
# 감성 키워드 사전
# ============================================================
POSITIVE_KEYWORDS = [
    "좋아요", "좋음", "만족", "대박", "최고", "강추", "추천", "괜찮", "훌륭",
    "촉촉", "부드럽", "효과", "효과적", "발림", "흡수", "산뜻",
    "가성비", "저렴", "합리적", "싸다", "가격대비",
    "재구매", "또살", "계속살", "단골",
]

NEGATIVE_KEYWORDS = [
    "별로", "실망", "최악", "안좋", "아쉽", "후회", "불만",
    "끈적", "백탁", "각질", "트러블",
    "다시는", "환불", "반품",
]

# 속성별 키워드 (핵심 질문: 가격 vs 품질)
ATTRIBUTE_KEYWORDS = {
    "가격/가성비": ["가성비", "저렴", "싸다", "합리적", "가격", "착한"],
    "효과/품질":   ["효과", "촉촉", "흡수", "부드럽", "발림", "개선"],
    "텍스처":      ["끈적", "가볍다", "산뜻", "묽다", "진하다"],
    "재구매의사":  ["재구매", "또살", "단골", "계속", "다시는", "환불"],
    "패키징":      ["용량", "패키지", "디자인", "뚜껑", "휴대"],
}


def crawl_product(product, driver, max_reviews):
    """제품 한 개의 리뷰를 크롤링하여 리스트로 반환"""
    reviews = []
    print(f"\n[수집 시작] {product['카테고리']} - {product['제품명']}")
    driver.get(product["url"])
    time.sleep(3)

    # 리뷰 탭 클릭 (있으면)
    try:
        review_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(text(), "리뷰") or contains(text(), "후기")]')
            )
        )
        review_tab.click()
        time.sleep(2)
    except Exception:
        print("  -> 리뷰 탭 클릭 실패(또는 리뷰 탭 없음), 계속 진행합니다.")

    page = 1
    while len(reviews) < max_reviews:
        print(f"  -> {page}페이지 수집 중... (현재 {len(reviews)}개)")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("li.review-detail")
        if not items:
            print("  -> 리뷰를 찾지 못했습니다(셀렉터 변경 가능).")
            break

        for item in items:
            if len(reviews) >= max_reviews:
                break

            try:
                # 리뷰 텍스트
                text_el = item.select_one(".review-desc .cont span")
                text = text_el.get_text(strip=True) if text_el else ""

                # 별점 (숫자만 추출)
                score_el = item.select_one(".hiddenText")
                score_raw = score_el.get_text(strip=True) if score_el else "0"
                nums = re.findall(r"\d+", score_raw)
                score_num = int(nums[0]) if nums else 0

                # 날짜
                date_el = item.select_one(".cw-bar-list span")
                date = date_el.get_text(strip=True) if date_el else ""

                if text:
                    reviews.append({
                        "카테고리": product["카테고리"],
                        "제품명": product["제품명"],
                        "리뷰내용": text,
                        "별점": score_num,
                        "날짜": date,
                    })
            except Exception:
                continue

        # 다음 페이지 이동 시도
        moved = False
        try:
            next_btn = driver.find_element(
                By.XPATH, '//button[contains(@class,"next") or contains(text(),"다음")]'
            )
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(2)
            page += 1
            moved = True
        except Exception:
            pass

        if not moved:
            try:
                next_page = driver.find_element(By.XPATH, f'//button[text()="{page + 1}"]')
                driver.execute_script("arguments[0].click();", next_page)
                time.sleep(2)
                page += 1
                moved = True
            except Exception:
                print("  -> 마지막 페이지 도달.")
                break

    print(f"  -> 수집 완료: {len(reviews)}개")
    return reviews


def analyze_sentiment(text: str) -> str:
    """긍정/부정/중립 분류"""
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

    if pos > neg:
        return "긍정"
    elif neg > pos:
        return "부정"
    return "중립"


def analyze_attributes(text: str) -> dict:
    """속성별 키워드 포함 여부 반환"""
    return {attr: any(kw in text for kw in kws) for attr, kws in ATTRIBUTE_KEYWORDS.items()}


def save_results(df: pd.DataFrame):
    """분석 결과를 CSV와 엑셀로 저장"""
    # CSV 저장 (한글 깨짐 방지: utf-8-sig)
    df.to_csv("daiso_reviews.csv", index=False, encoding="utf-8-sig")
    print("[저장] daiso_reviews.csv")

    # 엑셀 저장 (시트 3개)
    with pd.ExcelWriter("daiso_reviews.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="전체리뷰", index=False)

        df.groupby("카테고리")["감성"].value_counts().unstack(fill_value=0).to_excel(
            writer, sheet_name="카테고리별감성"
        )

        df.groupby("카테고리")["별점"].mean().round(2).to_frame("평균별점").to_excel(
            writer, sheet_name="카테고리별평균별점"
        )

    print("[저장] daiso_reviews.xlsx")


if __name__ == "__main__":
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    all_reviews = []
    for product in PRODUCTS:
        all_reviews.extend(crawl_product(product, driver, MAX_REVIEWS))

    driver.quit()

    df = pd.DataFrame(all_reviews)
    print(f"\n전체 수집 리뷰: {len(df)}개")

    if df.empty:
        print("수집된 리뷰가 없습니다. URL/셀렉터를 확인하세요.")
        raise SystemExit(1)

    # 전처리: 빈 리뷰 및 중복 제거
    df = df[df["리뷰내용"].astype(str).str.strip() != ""].drop_duplicates(subset=["리뷰내용"])
    print(f"전처리 후 리뷰: {len(df)}개")

    # 감성 분석
    df["감성"] = df["리뷰내용"].apply(analyze_sentiment)

    # 속성별 분석
    attr_df = df["리뷰내용"].apply(analyze_attributes).apply(pd.Series)
    df = pd.concat([df, attr_df], axis=1)

    save_results(df)
    print("\n분석 완료. 이제 streamlit run dashboard.py 실행하세요.")