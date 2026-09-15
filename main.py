import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
MIN_DAYS = 300  # 관측일이 적은 해(1907년, 한국전쟁기, 올해 등)는 평균이 왜곡되므로 제외

st.set_page_config(page_title="서울 100년 기온 변화", page_icon="🌡️", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str).str.strip())
    df["연도"] = df["날짜"].dt.year

    yearly = df.groupby("연도").agg(
        평균기온=("평균기온", "mean"),
        최저기온=("최저기온", "mean"),
        최고기온=("최고기온", "mean"),
        관측일수=("평균기온", "count"),
    )
    return yearly[yearly["관측일수"] >= MIN_DAYS].reset_index()


st.title("🌡️ 서울 100년 동안 연평균 기온 변화")
st.caption("자료: 기상청 서울(108) 관측소 일별 기온 · 관측일이 300일 미만인 해는 제외")

yearly = load_data()

first_year = int(yearly["연도"].min())
last_year = int(yearly["연도"].max())
default_start = max(first_year, last_year - 99)  # 기본값: 최근 100년

with st.sidebar:
    st.header("설정")
    start, end = st.slider("기간", first_year, last_year, (default_start, last_year))
    window = st.select_slider("이동평균 기간(년)", options=[1, 5, 10, 20, 30], value=10)
    show_minmax = st.checkbox("연평균 최저·최고기온도 보기", value=False)

data = yearly[(yearly["연도"] >= start) & (yearly["연도"] <= end)].copy()
data["이동평균"] = data["평균기온"].rolling(window, min_periods=1, center=True).mean()

# 선형 추세
slope, intercept = np.polyfit(data["연도"], data["평균기온"], 1)
data["추세"] = slope * data["연도"] + intercept

# 요약 지표: 처음 10년 평균 vs 마지막 10년 평균
early = data.head(10)["평균기온"].mean()
late = data.tail(10)["평균기온"].mean()
warmest = data.loc[data["평균기온"].idxmax()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("처음 10년 평균", f"{early:.1f}℃")
c2.metric(f"최근 10년 평균", f"{late:.1f}℃", f"{late - early:+.1f}℃", delta_color="inverse")
c3.metric("100년당 상승 추세", f"{slope * 100:+.1f}℃")
c4.metric("가장 더웠던 해", f"{int(warmest['연도'])}년", f"{warmest['평균기온']:.1f}℃", delta_color="off")

fig = go.Figure()

if show_minmax:
    fig.add_trace(go.Scatter(
        x=data["연도"], y=data["최고기온"], name="연평균 최고기온",
        line=dict(color="#e4572e", width=1), opacity=0.6,
        hovertemplate="%{x}년<br>최고 %{y:.1f}℃<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=data["연도"], y=data["최저기온"], name="연평균 최저기온",
        line=dict(color="#2e86de", width=1), opacity=0.6,
        hovertemplate="%{x}년<br>최저 %{y:.1f}℃<extra></extra>",
    ))

fig.add_trace(go.Scatter(
    x=data["연도"], y=data["평균기온"], name="연평균 기온",
    mode="lines+markers", line=dict(color="#aaaaaa", width=1), marker=dict(size=4),
    hovertemplate="%{x}년<br>평균 %{y:.2f}℃<extra></extra>",
))
if window > 1:
    fig.add_trace(go.Scatter(
        x=data["연도"], y=data["이동평균"], name=f"{window}년 이동평균",
        line=dict(color="#d62728", width=3),
        hovertemplate="%{x}년<br>이동평균 %{y:.2f}℃<extra></extra>",
    ))
fig.add_trace(go.Scatter(
    x=data["연도"], y=data["추세"], name="추세선",
    line=dict(color="#333333", width=2, dash="dash"), hoverinfo="skip",
))

fig.update_layout(
    title=f"서울 연평균 기온 ({start}–{end}년)",
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    height=550,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(t=80, b=40),
)
st.plotly_chart(fig, width="stretch")

st.info(
    f"선택한 {start}–{end}년 동안 서울의 연평균 기온은 10년마다 약 **{slope * 10:.2f}℃**씩 올랐습니다. "
    f"처음 10년과 최근 10년을 비교하면 **{late - early:+.1f}℃** 차이가 납니다."
)

with st.expander("연도별 데이터 보기"):
    table = data[["연도", "평균기온", "최저기온", "최고기온", "관측일수"]].round(2)
    st.dataframe(table, hide_index=True, width="stretch")
