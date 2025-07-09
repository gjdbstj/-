
import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from fpdf import FPDF

st.set_page_config(layout="wide")
st.title("💧 수질 오염 분석 대시보드")

# 파일 업로드
st.sidebar.header("📁 데이터 업로드")
uploaded_main = st.sidebar.file_uploader("✅ 측정 데이터 업로드 (CSV 또는 Excel)", type=['csv', 'xlsx'])
uploaded_sources = st.sidebar.file_uploader("🏭 배출원 데이터 업로드 (선택)", type=['csv', 'xlsx'])

# 데이터 로딩 함수
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

# 기본 실행 조건
if uploaded_main:
    df = load_data(uploaded_main)
    df['측정일자'] = pd.to_datetime(df['측정일자'])
    pollutants = [col for col in df.columns if col not in ['측정일자', '측정지점명', '위도', '경도']]

    # 측정 데이터 미리보기
    st.subheader("🧾 업로드된 측정 데이터")
    st.dataframe(df.head())

    # 필터 설정
    pollutant = st.sidebar.selectbox("🔬 분석할 오염물질", pollutants)
    start_date, end_date = st.sidebar.date_input("⏱️ 분석 기간", [df['측정일자'].min(), df['측정일자'].max()])
    threshold = st.sidebar.number_input("📉 기준치 설정", min_value=0.0, value=0.5)

    df_filtered = df[(df['측정일자'] >= pd.to_datetime(start_date)) & (df['측정일자'] <= pd.to_datetime(end_date))]

    # 시계열 그래프
    st.subheader("📈 오염물질 시계열 변화")
    fig = px.line(df_filtered, x='측정일자', y=pollutant, color='측정지점명', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # 지도 시각화
    st.subheader("🗺️ 측정 지점 지도 시각화")
    map_center = [df['위도'].mean(), df['경도'].mean()]
    fmap = folium.Map(location=map_center, zoom_start=8)
    marker_cluster = MarkerCluster().add_to(fmap)

    for _, row in df_filtered.iterrows():
        color = 'red' if row[pollutant] > threshold else 'green'
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=7,
            popup=f"{row['측정지점명']}<br>{pollutant}: {row[pollutant]:.2f}",
            color=color,
            fill=True,
            fill_opacity=0.6
        ).add_to(marker_cluster)

    st_folium(fmap, width=700, height=500)

    # 기준치 초과 탐지
    exceed = df_filtered[df_filtered[pollutant] > threshold]
    st.subheader(f"⚠️ 기준치 초과 측정값 ({len(exceed)}건)")
    st.dataframe(exceed[['측정일자', '측정지점명', pollutant]])

    # 상관관계 분석
    st.subheader("🔗 오염물질 간 상관관계 분석")
    corr = df[pollutants].corr()
    fig_corr, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
    st.pyplot(fig_corr)

    # 배출원 시각화
    if uploaded_sources:
        source_df = load_data(uploaded_sources)
        st.subheader("🏭 주요 배출원 위치")
        for _, row in source_df.iterrows():
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=f"{row['시설명']}<br>{row['배출물질']} {row['배출량(kg/일)']}kg",
                icon=folium.Icon(color='blue', icon='industry', prefix='fa')
            ).add_to(fmap)
        st_folium(fmap, width=700, height=500)

    # 리포트 PDF 생성
    if st.sidebar.button("📄 리포트 PDF 생성"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="수질 오염 리포트", ln=True, align='C')
        pdf.cell(200, 10, txt=f"분석 대상: {pollutant}", ln=True)
        pdf.cell(200, 10, txt=f"기간: {start_date} ~ {end_date}", ln=True)
        pdf.cell(200, 10, txt=f"기준치 초과 건수: {len(exceed)}건", ln=True)
        pdf.output("water_quality_report.pdf")
        st.success("PDF 리포트가 생성되었습니다. (로컬 환경에서 확인 가능)")

else:
    st.info("⬅️ 측정 데이터를 업로드해주세요.")
