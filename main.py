import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from fpdf import FPDF

st.title("💧 수질 오염 데이터 분석")

# --------------------------------------------
# 1. 데이터 업로드 or 샘플
st.sidebar.title("📁 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 업로드", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.info("✅ 업로드한 파일로 분석 중입니다.")
else:
    st.info("⚠️ 데이터가 없으므로 샘플 데이터를 사용합니다.")
    # 샘플 데이터 생성
    sample_data = {
        '측정일자': pd.date_range(start='2024-01-01', periods=10).tolist() * 3,
        '측정지점명': ['한강A'] * 10 + ['중랑천B'] * 10 + ['탄천C'] * 10,
        '위도': [37.55]*10 + [37.58]*10 + [37.47]*10,
        '경도': [126.98]*10 + [127.04]*10 + [127.07]*10,
        '총인': np.random.uniform(0.2, 1.0, 30),
        'BOD': np.random.uniform(1.0, 3.5, 30),
        'COD': np.random.uniform(1.0, 5.0, 30),
    }
    df = pd.DataFrame(sample_data)

# --------------------------------------------
# 2. 데이터프레임 출력
st.subheader("📄 데이터 미리보기")
st.dataframe(df.head())

# --------------------------------------------
# 3. 시계열 그래프
pollutant = st.sidebar.selectbox("오염물질 선택", df.columns[4:])
date_col = '측정일자'
site_col = '측정지점명'

df[date_col] = pd.to_datetime(df[date_col])
start_date, end_date = st.sidebar.date_input("기간 선택", [df[date_col].min(), df[date_col].max()])
df_filtered = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]

fig = px.line(df_filtered, x=date_col, y=pollutant, color=site_col, markers=True)
st.subheader("📈 오염물질 시계열 변화")
st.plotly_chart(fig)

# --------------------------------------------
# 4. 지도 시각화
st.subheader("🗺️ 측정 지점 지도 보기")
map_center = [df['위도'].mean(), df['경도'].mean()]
map_ = folium.Map(location=map_center, zoom_start=11)
marker_cluster = MarkerCluster().add_to(map_)

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row['위도'], row['경도']],
        radius=7,
        popup=f"{row[site_col]}<br>{pollutant}: {row[pollutant]:.2f}",
        color="red" if row[pollutant] > 0.5 else "green",
        fill=True,
    ).add_to(marker_cluster)

st_folium(map_, width=700)

# --------------------------------------------
# 5. 기준 초과 탐지
threshold = st.sidebar.number_input("기준치 설정", min_value=0.0, value=0.5)
exceed = df[df[pollutant] > threshold]
st.subheader("📌 기준치 초과 탐지")
st.write(f"총 **{len(exceed)}건** 기준 초과")
st.dataframe(exceed[[date_col, site_col, pollutant]])

# --------------------------------------------
# 6. PDF 리포트 생성
if st.sidebar.button("리포트 생성"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"수질 오염 데이터 분석 리포트", ln=True, align='C')
    pdf.cell(200, 10, txt=f"오염물질: {pollutant}", ln=True)
    pdf.cell(200, 10, txt=f"기준치: {threshold}", ln=True)
    pdf.cell(200, 10, txt=f"기준 초과 건수: {len(exceed)}", ln=True)
    pdf.output("water_quality_report.pdf")
    st.success("리포트가 생성되었습니다.")
