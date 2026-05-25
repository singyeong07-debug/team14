# dashboard.py
# 실행: streamlit run dashboard.py
# 역할: crawl.py 실행 후 저장된 CSV를 불러와 시각화

import os
import platform
from collections import Counter

import pandas as pd
import streamlit as st
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud


# ----------------------------
# 한글 폰트 설정
# ----------------------------
if platform.system() == "Windows":
    matplotlib.rc("font", family="Malgun Gothic")
    FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
elif platform.system() == "Darwin":  # macOS
    matplotlib.rc("font", family="AppleGothic")
    FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
else:
    # Linux 등: 시스템에 설치된 한글 폰트를 지정해야 워드클라우드가 정상 출력됩니다.
    # 예: /usr/share/fonts/truetype/nanum/NanumGothic.ttf
    matplotlib.rc("font", family="DejaVu Sans")
    FONT_PATH = None

matplotlib.rcParams["axes.unicode_minus"] = False


ATTR_COLS = ["가격/가성비", "효과/품질", "텍스처", "재구매의사", "패키징"]


def load_data() -> pd.DataFrame:
    """저장된 CSV 파일 불러오기"""
    if not os.path.exists("daiso_reviews.csv"):
        st.error("데이터 파일이 없습니다. 먼저 `python crawl.py` 를 실행해 주세요.")
        st.stop()

    df = pd.read_csv("daiso_reviews.csv", encoding="utf-8-sig")

    # 기본 컬럼 방어(혹시라도 누락되면 Streamlit이 터지는 것 방지)
    needed = ["카테고리", "제품명", "리뷰내용", "별점", "날짜", "감성"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        st.error(f"CSV에 필요한 컬럼이 없습니다: {missing}")
        st.stop()

    return df


def show_metrics(df: pd.DataFrame):
    """상단 요약 지표 4개"""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 리뷰 수", f"{len(df)}개")

    if len(df) > 0:
        col2.metric("평균 별점", f"{df['별점'].mean():.2f}점")
        col3.metric("긍정 비율", f"{(df['감성'] == '긍정').mean() * 100:.1f}%")
        col4.metric("부정 비율", f"{(df['감성'] == '부정').mean() * 100:.1f}%")
    else:
        col2.metric("평균 별점", "-")
        col3.metric("긍정 비율", "-")
        col4.metric("부정 비율", "-")


def plot_avg_star(df: pd.DataFrame):
    """카테고리별 평균 별점 막대그래프"""
    avg = df.groupby("카테고리")["별점"].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(
        avg.index,
        avg.values,
        color=["#FF6B6B", "#4ECDC4", "#FFD93D"],
        edgecolor="white",
    )
    ax.set_ylim(0, 5.5)
    ax.set_ylabel("평균 별점")
    ax.set_title("카테고리별 평균 별점")

    for bar, val in zip(bars, avg.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.05,
            f"{val:.2f}",
            ha="center",
            fontsize=10,
        )

    plt.tight_layout()
    return fig


def plot_sentiment(df: pd.DataFrame):
    """카테고리별 감성 비율 막대그래프"""
    counts = df.groupby(["카테고리", "감성"]).size().unstack(fill_value=0)
    for col in ["긍정", "부정", "중립"]:
        if col not in counts.columns:
            counts[col] = 0

    pct = counts[["긍정", "부정", "중립"]].div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(5, 3))
    pct.plot(
        kind="bar",
        ax=ax,
        color=["#4ECDC4", "#FF6B6B", "#C0C0C0"],
        edgecolor="white",
        width=0.6,
    )
    ax.set_ylabel("비율 (%)")
    ax.set_xlabel("")
    ax.set_title("카테고리별 감성 비율")
    plt.xticks(rotation=0)
    plt.tight_layout()
    return fig


def plot_star_hist(df: pd.DataFrame):
    """전체 별점 분포 히스토그램"""
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.hist(
        df["별점"],
        bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
        color="#FF6B6B",
        edgecolor="white",
        rwidth=0.8,
    )
    ax.set_xlabel("별점")
    ax.set_ylabel("리뷰 수")
    ax.set_title("별점 분포")
    ax.set_xticks([1, 2, 3, 4, 5])
    plt.tight_layout()
    return fig


def plot_attribute(df: pd.DataFrame):
    """속성별 키워드 언급 비율 막대그래프 (핵심 질문 직접 답변)"""
    existing = [c for c in ATTR_COLS if c in df.columns]
    if not existing:
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.text(0.5, 0.5, "속성 컬럼이 없습니다.\n(crawl.py에서 속성 분석 결과가 저장되어야 합니다.)",
                ha="center", va="center")
        ax.axis("off")
        return fig

    ratio = df[existing].mean() * 100

    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(
        ratio.index,
        ratio.values,
        color=["#FF6B6B", "#4ECDC4", "#FFD93D", "#A29BFE", "#FD79A8"][: len(ratio)],
        edgecolor="white",
    )
    ax.set_ylabel("언급 비율 (%)")
    ax.set_title("속성별 언급 비율 (가격 vs 품질)")
    plt.xticks(rotation=15, fontsize=9)

    for bar, val in zip(bars, ratio.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.3,
            f"{val:.1f}%",
            ha="center",
            fontsize=9,
        )

    plt.tight_layout()
    return fig


def plot_wordcloud(df: pd.DataFrame):
    """전체 리뷰 키워드 워드클라우드"""
    stopwords = {
        "이", "것", "수", "제", "좀", "때", "거", "점", "편", "분", "번",
        "도", "를", "은", "는", "가", "의", "에", "로", "으로", "와", "과",
        "그", "저", "너무", "정말", "진짜", "그냥", "더", "잘", "안"
    }

    text = " ".join(df["리뷰내용"].dropna().astype(str).tolist())
    words = text.split()
    words = [w for w in words if len(w) > 1 and w not in stopwords]
    freq = Counter(words)

    if not freq:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "워드클라우드를 만들 단어가 없습니다.", ha="center", va="center")
        ax.axis("off")
        return fig

    # Linux 등에서 폰트 경로가 없으면 워드클라우드 한글이 깨질 수 있음
    wc_kwargs = dict(
        background_color="white",
        width=800,
        height=350,
        max_words=80,
        colormap="RdYlGn",
    )
    if FONT_PATH:
        wc_kwargs["font_path"] = FONT_PATH

    wc = WordCloud(**wc_kwargs).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("전체 리뷰 키워드 워드클라우드")
    plt.tight_layout()
    return fig


def main():
    st.set_page_config(page_title="다이소 뷰티 리뷰 분석", layout="wide")
    st.title("다이소 뷰티 소비자 리뷰 분석")
    st.markdown("**핵심 질문: 다이소 뷰티 제품은 가격뿐 아니라 품질까지도 소비자에게 인정받고 있는가?**")
    st.divider()

    df = load_data()

    # 사이드바 필터
    st.sidebar.header("필터")
    selected = st.sidebar.multiselect(
        "카테고리 선택",
        options=df["카테고리"].dropna().unique(),
        default=df["카테고리"].dropna().unique(),
    )
    df = df[df["카테고리"].isin(selected)]

    # 요약 지표
    show_metrics(df)
    st.divider()

    # 그래프 2x2 배치
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("카테고리별 평균 별점")
        st.pyplot(plot_avg_star(df))

    with col2:
        st.subheader("카테고리별 감성 비율")
        st.pyplot(plot_sentiment(df))

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("별점 분포")
        st.pyplot(plot_star_hist(df))

    with col4:
        st.subheader("속성별 언급 비율 (가격 vs 품질)")
        st.pyplot(plot_attribute(df))

    st.divider()

    # 워드클라우드
    st.subheader("전체 리뷰 키워드 워드클라우드")
    st.pyplot(plot_wordcloud(df))
    st.divider()

    # 전체 리뷰 테이블
    st.subheader("수집된 리뷰 데이터")
    show_cols = [c for c in ["카테고리", "제품명", "별점", "감성", "리뷰내용", "날짜"] if c in df.columns]
    st.dataframe(df[show_cols], use_container_width=True)


if __name__ == "__main__":
    main()