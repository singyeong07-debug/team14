# dashboard.py
# 실행: streamlit run dashboard.py
# 역할: crawl.py 실행 후 저장된 CSV를 불러와 시각화

import os
import platform
from collections import Counter

import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud


# ============================================================
# 한글 폰트 설정 (matplotlib)
# ============================================================
if platform.system() == "Windows":
    matplotlib.rc("font", family="Malgun Gothic")
elif platform.system() == "Darwin":
    matplotlib.rc("font", family="AppleGothic")
else:
    # Linux 등: 설치된 한글 폰트가 없다면 깨질 수 있음
    matplotlib.rc("font", family="DejaVu Sans")

matplotlib.rcParams["axes.unicode_minus"] = False


def get_font_path():
    """워드클라우드용 폰트 경로 자동 선택"""
    sysname = platform.system()
    candidates = []

    if sysname == "Windows":
        candidates = [
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/malgunbd.ttf",
        ]
    elif sysname == "Darwin":
        candidates = [
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        ]
    else:
        # Linux 예시(환경마다 다름)
        candidates = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]

    for p in candidates:
        if os.path.exists(p):
            return p
    return None


FONT_PATH = get_font_path()

# crawl.py에서 만들어지는 속성 컬럼명 기준
ATTR_COLS = ["가격", "품질", "사용감", "디자인", "휴대", "용기"]

# 워드클라우드 공통 불용어(토큰 기반)
STOPWORDS = {
    "이", "것", "수", "제", "좀", "때", "거", "점", "편", "분", "번",
    "도", "를", "은", "는", "가", "의", "에", "로", "으로", "와", "과",
    "그", "저", "더", "잘", "안", "이게", "이건", "이런", "그런",
    "너무", "정말", "진짜", "그냥", "항상", "계속", "매번", "자주",
    "저는", "저도", "저한테", "제가", "나는", "나도",
    "이거", "이제", "이번", "요거", "요즘",
    "사용", "사용해", "사용하고", "사용했", "사용중",
    "제품", "제품은", "제품이", "제품을", "상품", "구매", "구매했",
    "피부가", "피부에", "피부도", "피부는", "피부",
    "생각", "느낌", "정도", "조금", "약간", "살짝",
    "있어요", "없어요", "같아요", "해요", "해서", "하고", "하는",
    "그리고", "근데", "그래서", "그런데",
    "다이소", "뷰티",
    "좋아요", "좋고", "좋은", "좋습니다", "좋아서", "좋네요",
    "별로", "실망", "최악",
}


# ============================================================
# 데이터 로드
# ============================================================
def load_data():
    """저장된 CSV 파일 불러오기"""
    if not os.path.exists("daiso_reviews.csv"):
        st.error("데이터 파일이 없습니다. 먼저 `python crawl.py` 를 실행하세요.")
        st.stop()

    df = pd.read_csv("daiso_reviews.csv", encoding="utf-8-sig")

    # 혹시 모를 타입 정리
    if "별점" in df.columns:
        df["별점"] = pd.to_numeric(df["별점"], errors="coerce")
    return df


# ============================================================
# 상단 지표
# ============================================================
def show_metrics(df):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 리뷰 수", f"{len(df)}개")
    col2.metric("평균 별점", f"{df['별점'].mean():.2f}점" if len(df) else "-")
    col3.metric("긍정 비율", f"{(df['감성'] == '긍정').mean() * 100:.1f}%".replace("nan", "-"))
    col4.metric("부정 비율", f"{(df['감성'] == '부정').mean() * 100:.1f}%".replace("nan", "-"))


# ============================================================
# 시각화 함수들
# ============================================================
def plot_avg_star_category(df):
    avg = df.groupby("카테고리")["별점"].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    bars = ax.bar(
        avg.index, avg.values,
        color=["#FF6B6B", "#4ECDC4", "#FFD93D"],
        edgecolor="white", width=0.35
    )
    ax.set_ylim(0, 5.5)
    ax.set_ylabel("평균 별점")
    ax.set_title("카테고리별 평균 별점")

    for bar, val in zip(bars, avg.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.05, f"{val:.2f}", ha="center", fontsize=10)

    plt.tight_layout()
    return fig


def plot_avg_star_product(df):
    avg = df.groupby(["카테고리", "제품명"])["별점"].mean().reset_index()
    avg = avg.sort_values(["카테고리", "별점"], ascending=[True, False])

    colors = {"스킨케어": "#FF6B6B", "메이크업": "#4ECDC4", "뷰티소품": "#FFD93D"}
    bar_colors = [colors.get(cat, "#aaa") for cat in avg["카테고리"]]

    fig, ax = plt.subplots(figsize=(9.5, 4))
    bars = ax.bar(avg["제품명"], avg["별점"], color=bar_colors, edgecolor="white", width=0.55)
    ax.set_ylim(0, 5.5)
    ax.set_ylabel("평균 별점")
    ax.set_title("제품별 평균 별점 비교")

    plt.xticks(rotation=20, fontsize=8, ha="right")
    for bar, val in zip(bars, avg["별점"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.05, f"{val:.2f}", ha="center", fontsize=8)

    from matplotlib.patches import Patch
    legend = [Patch(color=v, label=k) for k, v in colors.items()]
    ax.legend(handles=legend, loc="lower right", fontsize=8)

    plt.tight_layout()
    return fig


def plot_sentiment(df):
    counts = df.groupby(["카테고리", "감성"]).size().unstack(fill_value=0)

    for col in ["긍정", "부정", "중립"]:
        if col not in counts.columns:
            counts[col] = 0

    pct = counts[["긍정", "부정", "중립"]].div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    pct.plot(
        kind="bar", ax=ax,
        color=["#4ECDC4", "#FF6B6B", "#C0C0C0"],
        edgecolor="white", width=0.42
    )
    ax.set_ylabel("비율 (%)")
    ax.set_xlabel("")
    ax.set_title("카테고리별 감성 비율")
    plt.xticks(rotation=0)
    plt.tight_layout()
    return fig


def plot_attribute(df):
    existing = [c for c in ATTR_COLS if c in df.columns]
    if not existing:
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        ax.text(0.5, 0.5, "속성 컬럼이 없습니다.\n(crawl.py에서 속성 분석 컬럼 생성 여부 확인)",
                ha="center", va="center")
        ax.axis("off")
        return fig

    ratio = df[existing].mean() * 100

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    palette = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#A29BFE", "#FD79A8", "#74B9FF"]
    bars = ax.bar(ratio.index, ratio.values, color=palette[:len(ratio)], edgecolor="white", width=0.45)

    ax.set_ylabel("언급 비율 (%)")
    ax.set_title("속성별 언급 비율")
    plt.xticks(rotation=15, fontsize=9)

    for bar, val in zip(bars, ratio.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3, f"{val:.1f}%", ha="center", fontsize=9)

    plt.tight_layout()
    return fig


# ============================================================
# 워드클라우드
# ============================================================
def make_wordcloud(text_series, colormap):
    if FONT_PATH is None:
        return None, "워드클라우드용 한글 폰트를 찾지 못했습니다. (FONT_PATH 설정 필요)"

    # 단순 토큰화(공백 기준). 한글은 형태소 분석이 더 좋지만, 동작 우선으로 구현.
    text = " ".join(text_series.dropna().astype(str).tolist())
    tokens = text.split()
    tokens = [t.strip() for t in tokens if len(t.strip()) > 1 and t.strip() not in STOPWORDS]

    freq = Counter(tokens)
    if not freq:
        return None, "키워드가 부족합니다."

    wc = WordCloud(
        font_path=FONT_PATH,
        background_color="white",
        width=450,
        height=320,
        max_words=80,
        colormap=colormap,
    ).generate_from_frequencies(freq)

    return wc, None


def plot_wordclouds_by_category(df):
    categories = ["스킨케어", "메이크업", "뷰티소품"]
    for cat in categories:
        st.markdown(f"**{cat}**")
        col_pos, col_neg = st.columns(2)

        with col_pos:
            pos_df = df[(df["카테고리"] == cat) & (df["감성"] == "긍정")]
            wc, err = make_wordcloud(pos_df["리뷰내용"], colormap="Greens")
            if wc is not None:
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                ax.set_title(f"{cat} - 긍정 키워드", fontsize=11)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info(err or "긍정 리뷰 데이터가 부족합니다.")

        with col_neg:
            neg_df = df[(df["카테고리"] == cat) & (df["감성"] == "부정")]
            wc, err = make_wordcloud(neg_df["리뷰내용"], colormap="Reds")
            if wc is not None:
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                ax.set_title(f"{cat} - 부정 키워드", fontsize=11)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info(err or "부정 리뷰 데이터가 부족합니다.")


# ============================================================
# 메인 앱
# ============================================================
def main():
    st.set_page_config(page_title="다이소 뷰티 리뷰 분석", layout="wide")
    st.title("다이소 뷰티 소비자 리뷰 분석")
    st.markdown("**핵심 질문: 다이소 뷰티 제품은 가격뿐 아니라 품질까지도 소비자에게 인정받고 있는가?**")
    st.divider()

    df = load_data()

    st.sidebar.header("필터")
    options = list(df["카테고리"].dropna().unique())
    selected = st.sidebar.multiselect("카테고리 선택", options=options, default=options)

    df = df[df["카테고리"].isin(selected)].copy()

    if df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        st.stop()

    show_metrics(df)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("카테고리별 평균 별점")
        st.pyplot(plot_avg_star_category(df))
    with col2:
        st.subheader("카테고리별 감성 비율")
        st.pyplot(plot_sentiment(df))

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("제품별 평균 별점 비교")
        st.pyplot(plot_avg_star_product(df))
    with col4:
        st.subheader("속성별 언급 비율")
        st.pyplot(plot_attribute(df))

    st.divider()

    st.subheader("카테고리별 긍정 / 부정 키워드 워드클라우드")
    st.caption("긍정(초록) / 부정(빨강) 리뷰에서 자주 나오는 키워드")
    plot_wordclouds_by_category(df)

    st.divider()

    st.subheader("수집된 리뷰 데이터")
    show_cols = [c for c in ["카테고리", "제품명", "별점", "감성", "리뷰내용", "날짜"] if c in df.columns]
    st.dataframe(df[show_cols], use_container_width=True)


if __name__ == "__main__":
    main()