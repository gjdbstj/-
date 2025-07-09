import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import folium
from streamlit_folium import st_folium
from scipy.stats import pearsonr
import io

# 1. 데이터 업로드
st.title("수질 오염물질 데이터 분석 플랫폼")
st.sidebar.header("데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 파일을 업로드하세요", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.success("데이터 업로드 완료!")
    st.write(df.head())

    # 2. 시기별·지점별 오염물질 농도 시각화
    st.header("시기별/지점별 오염물질 농도 시각화")
    col_date = st.selectbox("날짜 컬럼 선택", df.columns)
    col_site = st.selectbox("측정지점 컬럼 선택", df.columns)
    col_pollutant = st.selectbox("오염물질 컬럼 선택", [c for c in df.columns if c not in [col_date, col_site]])
    st.write(f"선택한 오염물질: {col_pollutant}")

    fig = px.line(df, x=col_date, y=col_pollutant, color=col_site, title="오염물질 농도 추이")
    st.plotly_chart(fig)

    # 3. 지도상 주요 배출원 시각화
    st.header("주요 배출원 위치 및 배출량 시각화")
    if {'위도', '경도', '배출원명', '배출량'}.issubset(df.columns):
        m = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=10)
        for idx, row in df.iterrows():
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=5 + row['배출량'] / 10,
                popup=f"{row['배출원명']}<br>배출량: {row['배출량']}",
                color='red'
            ).add_to(m)
        st_folium(m, width=700)
    else:
        st.info("지도 시각화를 위해 '위도', '경도', '배출원명', '배출량' 컬럼이 필요합니다.")

    # 4. 농도 변화 추이 및 초과 지점 자동 탐지(알림)
    st.header("농도 초과 지점 자동 탐지")
    threshold = st.number_input("기준치(예: 환경기준) 입력", value=float(df[col_pollutant].mean()))
    exceed = df[df[col_pollutant] > threshold]
    if not exceed.empty:
        st.warning(f"기준치 초과 지점 {len(exceed)}건 발견!")
        st.dataframe(exceed[[col_date, col_site, col_pollutant]])
    else:
        st.success("기준치 초과 지점이 없습니다.")

    # 5. 오염물질별 상관관계 분석 및 리포트 생성
    st.header("오염물질별 상관관계 분석")
    pollutant_cols = st.multiselect("상관관계 분석할 오염물질 컬럼 선택", [c for c in df.columns if df[c].dtype in [np.float64, np.int64]])
    if len(pollutant_cols) >= 2:
        corr = df[pollutant_cols].corr()
        st.write("상관계수 행렬:")
        st.dataframe(corr)
        fig_corr, ax = plt.subplots()
        sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
        st.pyplot(fig_corr)

    # 6. 데이터 요약 리포트 다운로드
    st.header("데이터 요약 리포트 다운로드")
    summary = df.describe()
    st.dataframe(summary)
    buf = io.BytesIO()
    summary.to_csv(buf)
    st.download_button(
        label="요약 리포트 다운로드(CSV)",
        data=buf.getvalue(),
        file_name="summary_report.csv",
        mime="text/csv"
    )

else:
    st.info("먼저 데이터를 업로드하세요.")

