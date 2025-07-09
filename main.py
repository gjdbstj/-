import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from fpdf import FPDF

# 1. 데이터 업로드
st.sidebar.title("📁 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 업로드", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.title("💧 수질 오염 데이터 분석")
    st.dataframe(df.head())

    # -------------------------------
    # 2. 시계열 그래프
    pollutant = st.sidebar.selectbox("오염물질 선택", df.columns[4:])
    date_col = '측정일자'
    site_col = '측정지점명'
    
    df[date_col] = pd.to_datetime(df[date_col])
    start_date, end_date = st.sidebar.date_input("기간 선택", [df[date_col].min(), df[date_col].max()])
    df_filtered = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]

    fig = px.line(df_filtered, x=date_col, y=pollutant, color=site_col, markers=True)
    st.plotly_chart(fig)

    # -------------------------------
    # 3. 지도 시각화
    st.subheader("🗺️ 측정 지점 지도 보기")
    map_center = [df['위도'].mean(), df['경도'].mean()]
    map_ = folium.Map(location=map_center, zoom_start=7)
    marker_cluster = MarkerCluster().add_to(map_)

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=7,
            popup=f"{row[site_col]}: {row[pollutant]}",
            color="red" if row[pollutant] > 0.5 else "green",
            fill=True,
        ).add_to(marker_cluster)

    st_folium(map_, width=700)

    # -------------------------------
    # 4. 농도 초과 탐지
    threshold = st.sidebar.number_input("기준치 설정", min_value=0.0, value=0.5)
    exceed = df[df[pollutant] > threshold]
    st.write(f"총 {len(exceed)}건 기준 초과")
    st.dataframe(exceed[[date_col, site_col, pollutant]])

    # -------------------------------
    # 5. PDF 리포트 생성
    if st.sidebar.button("리포트 생성"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"수질 오염 데이터 분석 리포트", ln=True, align='C')
        pdf.output("water_quality_report.pdf")
        st.success("리포트가 생성되었습니다.")

else:
    st.info("좌측 사이드바에서 데이터를 업로드하세요.")

import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.title("서울 마커 클러스터 지도")

# folium 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
marker_cluster = MarkerCluster().add_to(m)

# 마커 추가
folium.Marker([37.5665, 126.9780], popup="서울").add_to(marker_cluster)

# Streamlit 앱에 지도 표시
st_folium(m, width=700, height=500)
