import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.title("💧 수질 오염 데이터 분석 & 지도 시각화")

# 기본 folium 지도 예시 (서울)
st.subheader("🗺️ 서울 마커 클러스터 예시")
m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
marker_cluster = MarkerCluster().add_to(m)
folium.Marker([37.5665, 126.9780], popup="서울").add_to(marker_cluster)
st_folium(m, width=700, height=500)

# 데이터 업로드
st.sidebar.title("📁 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 업로드", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 날짜 컬럼 체크 및 변환 시도
    date_col = '측정일자'
    site_col = '측정지점명'
    lat_col = '위도'
    lon_col = '경도'

    if date_col not in df.columns:
        st.error(f"'{date_col}' 컬럼이 데이터에 없습니다. 컬럼명을 확인해주세요.")
        st.stop()
    else:
        try:
            df[date_col] = pd.to_datetime(df[date_col])
        except Exception as e:
            st.error(f"'{date_col}' 컬럼을 날짜 형식으로 변환할 수 없습니다: {e}")
            st.stop()

    # 오염물질 후보 (날짜, 지점명, 위도, 경도 제외)
    pollutant_cols = [col for col in df.columns if col not in [date_col, site_col, lat_col, lon_col]]

    if len(pollutant_cols) == 0:
        st.error("분석할 오염물질 컬럼이 없습니다.")
        st.stop()

    st.subheader("📊 업로드된 데이터 미리보기")
    st.dataframe(df.head())

    pollutant = st.sidebar.selectbox("오염물질 선택", pollutant_cols)

    # 기간 선택
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    start_date, end_date = st.sidebar.date_input("기간 선택", [min_date, max_date], min_value=min_date, max_value=max_date)

    # 기간 필터링
    df_filtered = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]

    if df_filtered.empty:
        st.warning("선택한 기간 내 데이터가 없습니다.")
    else:
        # 시계열 그래프
        fig = px.line(df_filtered, x=date_col, y=pollutant, color=site_col, markers=True)
        st.subheader("📈 오염물질 시계열 변화")
        st.plotly_chart(fig, use_container_width=True)

        # 기준치 입력 (시계열 필터 후)
        threshold = st.sidebar.number_input("기준치 설정", min_value=0.0, value=0.5, step=0.1)

        # 지도 생성
        st.subheader("📍 측정 지점 지도")
        map_center = [df_filtered[lat_col].mean(), df_filtered[lon_col].mean()]
        map_ = folium.Map(location=map_center, zoom_start=11)
        marker_cluster = MarkerCluster().add_to(map_)

        for _, row in df_filtered.iterrows():
            color = "red" if row[pollutant] > threshold else "green"
            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]],
                radius=7,
                popup=f"{row[site_col]}<br>{pollutant}: {row[pollutant]:.2f}",
                color=color,
                fill=True,
                fill_opacity=0.7
            ).add_to(marker_cluster)

        st_folium(map_, width=700, height=500)

        # 기준치 초과 데이터
        exceed = df_filtered[df_filtered[pollutant] > threshold]
        st.subheader(f"⚠️ 기준치({threshold}) 초과 데이터: 총 {len(exceed)}건")
        st.dataframe(exceed[[date_col, site_col, pollutant]])

        # PDF 리포트 생성
        if st.sidebar.button("📄 리포트 생성"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=14)
            pdf.cell(200, 10, txt="수질 오염 데이터 분석 리포트", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"분석 기간: {start_date} ~ {end_date}", ln=True)
            pdf.cell(200, 10, txt=f"선택 오염물질: {pollutant}", ln=True)
            pdf.cell(200, 10, txt=f"기준치: {threshold}", ln=True)
            pdf.cell(200, 10, txt=f"기준치 초과 건수: {len(exceed)}", ln=True)
            pdf.output("water_quality_report.pdf")
            st.success("✅ 리포트가 생성되었습니다. (로컬 환경에서 저장됨)")

else:
    st.info("⬅️ 좌측 사이드바에서 데이터를 업로드하세요.")
