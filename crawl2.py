# crawl.py
# 실행: python crawl.py
# 역할: 다이소몰 리뷰 크롤링 -> 감성분석 -> CSV/엑셀 저장

import time
import re
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================
# 설정값
# ============================================================
MAX_REVIEWS = 300  # 제품당 최대 수집 리뷰 수
WAIT_SEC = 10      # WebDriverWait 기본 타임아웃


# ============================================================
# 분석할 제품 목록 (URL은 실제 주소)
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


# ============================================================
# 감성/속성 키워드 (필요하면 여기만 계속 튜닝)
# ============================================================
POSITIVE_KEYWORDS = [
    "좋", "만족", "추천", "재구매", "가성비", "최고", "예쁘", "편하", "부드럽", "촉촉",
    "빠르", "깔끔", "탄탄", "유용", "잘", "괜찮", "향 좋"
]

NEGATIVE_KEYWORDS = [
    "별로", "실망", "불만", "최악", "비추", "후회", "안좋", "나쁘", "자극", "트러블",
    "건조", "끈적", "냄새", "냄새나", "깨짐", "부러", "불편", "오래", "느리", "작아"
]

ATTRIBUTE_KEYWORDS = {
    "가격": ["가성비", "가격", "저렴", "싸", "비싸"],
    "품질": ["품질", "퀄리티", "마감", "튼튼", "탄탄", "부러", "깨짐"],
    "사용감": ["부드럽", "편하", "불편", "끈적", "촉촉", "건조", "자극"],
    "디자인": ["예쁘", "디자인", "귀엽", "깔끔"],
    "휴대": ["휴대", "가볍", "작아", "파우치", "들고"],
    "용기": ["용기", "뚜껑", "펌프", "새", "샘", "누수"],
}


# ============================================================
# 크롤링
# ============================================================
def click_review_tab(driver):
    """리뷰/후기 탭 클릭 시도"""
    xpaths = [
        '//button[contains(text(), "리뷰")]',
        '//button[contains(text(), "후기")]',
        '//a[contains(text(), "리뷰")]',
        '//a[contains(text(), "후기")]',
    ]
    for xp in xpaths:
        try:
            el = WebDriverWait(driver, WAIT_SEC).until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].click();", el)
            time.sleep(2)
            return True
        except Exception:
            continue
    return False


def parse_reviews_from_page_source(product, page_source):
    soup = BeautifulSoup(page_source, "html.parser")
    items = soup.select("li.review-detail")
    results = []

    for item in items:
        # 리뷰 텍스트
        text_el = item.select_one(".review-desc .cont span")
        text = text_el.get_text(strip=True) if text_el else ""

        # 별점
        score_el = item.select_one(".hiddenText")
        score_raw = score_el.get_text(strip=True) if score_el else ""
        score_num = int(re.findall(r"\d+", score_raw)[0]) if re.findall(r"\d+", score_raw) else 0

        # 날짜
        date_el = item.select_one(".cw-bar-list span")
        date = date_el.get_text(strip=True) if date_el else ""

        if text.strip():
            results.append({
                "카테고리": product["카테고리"],
                "제품명": product["제품명"],
                "리뷰내용": text,
                "별점": score_num,
                "날짜": date,
            })

    return results


def go_next_page(driver, current_page):
    """
    다음 페이지 이동:
    1) el-pager 안의 숫자 버튼(current_page+1) 클릭 시도
    2) 실패 시 next 화살표 버튼(btn-next) 시도
    """
    next_page_num = current_page + 1

    # 1) 숫자 페이지 버튼
    try:
        next_btn = driver.find_element(
            By.XPATH,
            f'//ul[contains(@class,"el-pager")]//li[contains(@class,"number") and normalize-space(text())="{next_page_num}"]'
        )
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(2)
        return True
    except Exception:
        pass

    # 2) 다음 화살표
    try:
        arrow_btn = driver.find_element(By.XPATH, '//button[contains(@class,"btn-next")]')
        driver.execute_script("arguments[0].click();", arrow_btn)
        time.sleep(2)
        return True
    except Exception:
        return False


def crawl_product(product, driver, max_reviews):
    """제품 한 개의 리뷰를 크롤링하여 리스트로 반환"""
    reviews = []
    print(f"\n[수집 시작] {product['카테고리']} - {product['제품명']}")
    driver.get(product["url"])
    time.sleep(3)

    clicked = click_review_tab(driver)
    if not clicked:
        print("  -> 리뷰 탭 클릭 실패(또는 탭 없음). 그래도 페이지에서 리뷰 탐색 시도합니다.")

    page = 1
    while len(reviews) < max_reviews:
        print(f"  -> {page}페이지 수집 중... (현재 {len(reviews)}개)")

        page_reviews = parse_reviews_from_page_source(product, driver.page_source)
        if not page_reviews:
            print("  -> 현재 페이지에서 리뷰를 찾지 못했습니다. 종료합니다.")
            break

        # 누적
        for r in page_reviews:
            if len(reviews) >= max_reviews:
                break
            reviews.append(r)

        # 다음 페이지
        moved = go_next_page(driver, page)
        if not moved:
            print("  -> 마지막 페이지(또는 다음 페이지 버튼 없음).")
            break

        page += 1

    print(f"  -> 수집 완료: {len(reviews)}개")
    return reviews


# ============================================================
# 분석
# ============================================================
def analyze_sentiment(text):
    """긍정/부정/중립 분류 (간단 규칙 + 부정어 처리)"""
    negation_patterns = ["지 않", "지않", "안 ", "없어", "아니", "못 "]

    pos_count = 0
    neg_count = 0

    for kw in POSITIVE_KEYWORDS:
        if kw in text:
            pos_count += 1

    for kw in NEGATIVE_KEYWORDS:
        if kw in text:
            kw_index = text.find(kw)
            before_kw = text[max(0, kw_index - 6):kw_index]  # 부정어 탐지 범위 살짝 확대
            if any(neg in before_kw for neg in negation_patterns):
                pos_count += 1  # "안 별로" 같은 케이스를 단순 보정
            else:
                neg_count += 1

    if pos_count > neg_count:
        return "긍정"
    elif neg_count > pos_count:
        return "부정"
    return "중립"


def analyze_attributes(text):
    """속성별 키워드 포함 여부 반환"""
    return {attr: any(kw in text for kw in kws) for attr, kws in ATTRIBUTE_KEYWORDS.items()}


# ============================================================
# 저장
# ============================================================
def save_results(df):
    """분석 결과를 CSV와 엑셀로 저장 (한글 깨짐 방지)"""
    df.to_csv("daiso_reviews.csv", index=False, encoding="utf-8-sig")
    print("[저장] daiso_reviews.csv")

    with pd.ExcelWriter("daiso_reviews.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="전체리뷰", index=False)

        # 카테고리별 감성 분포
        df.groupby("카테고리")["감성"].value_counts().unstack(fill_value=0).to_excel(
            writer, sheet_name="카테고리별감성"
        )

        # 카테고리별 평균 별점
        df.groupby("카테고리")["별점"].mean().round(2).to_frame("평균별점").to_excel(
            writer, sheet_name="카테고리별평균별점"
        )

    print("[저장] daiso_reviews.xlsx")


# ============================================================
# 메인
# ============================================================
if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    # 필요 시 헤드리스:
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    all_reviews = []
    try:
        for product in PRODUCTS:
            all_reviews.extend(crawl_product(product, driver, MAX_REVIEWS))
    finally:
        driver.quit()

    df = pd.DataFrame(all_reviews)
    print(f"\n전체 수집 리뷰: {len(df)}개")

    if df.empty:
        print("수집된 리뷰가 없습니다. URL/페이지 구조(선택자)를 확인하세요.")
        raise SystemExit(1)

    # 전처리: 빈 리뷰 및 중복 제거
    df = df[df["리뷰내용"].astype(str).str.strip() != ""].drop_duplicates(subset=["리뷰내용"]).reset_index(drop=True)
    print(f"전처리 후 리뷰: {len(df)}개")

    # 감성 분석
    df["감성"] = df["리뷰내용"].apply(analyze_sentiment)

    # 속성 분석
    attr_df = df["리뷰내용"].apply(analyze_attributes).apply(pd.Series)
    df = pd.concat([df, attr_df], axis=1)

    save_results(df)
    print("\n완료: 이제 (있다면) streamlit run dashboard.py 를 실행하세요.")