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

st.set_page_config(page_title="수질 오염물질 데이터 분석", layout="wide")

st.title("수질 오염물질 데이터 분석 플랫폼")
st.write("""
하천, 호수, 해양 등에서 측정되는 중금속(납, 카드뮴 등), 영양염류(질소, 인 등)와 같은 주요 오염물질의 농도 변화와 주요 배출원을 데이터로 추적·분석하여, 수질 오염의 현황과 원인을 쉽게 파악할 수 있습니다.
""")

# 1. 데이터 업로드
st.sidebar.header("1. 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 파일을 업로드하세요", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"데이터를 읽는 중 오류 발생: {e}")
        st.stop()

    st.success("데이터 업로드 완료!")
    st.write("데이터 미리보기:")
    st.dataframe(df.head())

    # 2. 시기별·지점별 오염물질 농도 시각화
    st.header("2. 시기별/지점별 오염물질 농도 시각화")
    columns = df.columns.tolist()
    col_date = st.selectbox("날짜 컬럼 선택", columns)
    col_site = st.selectbox("측정지점 컬럼 선택", columns)
    col_pollutant = st.selectbox("오염물질 컬럼 선택", [c for c in columns if c not in [col_date, col_site]])

    if col_date and col_site and col_pollutant:
        try:
            fig = px.line(df, x=col_date, y=col_pollutant, color=col_site, title="오염물질 농도 추이")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"그래프 생성 오류: {e}")

    # 3. 지도상 주요 배출원 시각화
    st.header("3. 주요 배출원 위치 및 배출량 시각화")
    map_cols = {'위도', '경도', '배출원명', '배출량'}
    if map_cols.issubset(df.columns):
        m = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=10)
        for idx, row in df.iterrows():
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=5 + float(row['배출량']) / 10,
                popup=f"{row['배출원명']}<br>배출량: {row['배출량']}",
                color='red',
                fill=True,
                fill_opacity=0.7
            ).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.info("지도 시각화를 위해 '위도', '경도', '배출원명', '배출량' 컬럼이 필요합니다.")

    # 4. 농도 변화 추이 및 초과 지점 자동 탐지(알림)
    st.header("4. 농도 초과 지점 자동 탐지")
    try:
        threshold = st.number_input("기준치(예: 환경기준) 입력", value=float(df[col_pollutant].mean()))
        exceed = df[df[col_pollutant] > threshold]
        if not exceed.empty:
            st.warning(f"기준치 초과 지점 {len(exceed)}건 발견!")
            st.dataframe(exceed[[col_date, col_site, col_pollutant]])
        else:
            st.success("기준치 초과 지점이 없습니다.")
    except Exception as e:
        st.info("오염물질 컬럼의 값이 숫자가 아닐 수 있습니다. 데이터 타입을 확인하세요.")

    # 5. 오염물질별 상관관계 분석 및 리포트 생성
    st.header("5. 오염물질별 상관관계 분석")
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    pollutant_cols = st.multiselect("상관관계 분석할 오염물질 컬럼 선택", numeric_cols)
    if len(pollutant_cols) >= 2:
        corr = df[pollutant_cols].corr()
        st.write("상관계수 행렬:")
        st.dataframe(corr)
        fig_corr, ax = plt.subplots()
        sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
        st.pyplot(fig_corr)

    # 6. 데이터 요약 리포트 다운로드
    st.header("6. 데이터 요약 리포트 다운로드")
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


