import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import base64
import tempfile

st.set_page_config(page_title="수질 오염 분석", layout="wide")

st.title("💧 수질 오염 데이터 분석")

# -------------------------
# 1. 데이터 업로드 또는 샘플
st.sidebar.title("📁 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 업로드", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.info("✅ 업로드한 파일로 분석 중입니다.")
else:
    st.info("⚠️ 파일이 없으므로 샘플 데이터를 사용합니다.")
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

    # 샘플 CSV 다운로드
    st.sidebar.download_button(
        label="💾 샘플 CSV 다운로드",
        data=df.to_csv(index=False).encode('utf-8-sig'),
        file_name="sample_water_quality.csv",
        mime='text/csv'
    )

# -------------------------
# 2. 데이터프레임 출력
st.subheader("📄 데이터 미리보기")
st.dataframe(df.head())

# -------------------------
# 3. 시계열 그래프
pollutant = st.sidebar.selectbox("오염물질 선택", df.columns[4:])
date_col = '측정일자'
site_col = '측정지점명'

df[date_col] = pd.to_datetime(df[date_col])
start_date, end_date = st.sidebar.date_input("📅 기간 선택", [df[date_col].min(), df[date_col].max()])
df_filtered = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]

fig = px.line(df_filtered, x=date_col, y=pollutant, color=site_col, markers=True)
st.subheader("📈 오염물질 시계열 변화")
st.plotly_chart(fig)

# -------------------------
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

# -------------------------
# 5. 기준 초과 탐지
threshold = st.sidebar.number_input("📌 기준치 설정", min_value=0.0, value=0.5)
exceed = df[df[pollutant] > threshold]
st.subheader("📍 기준치 초과 탐지 결과")
st.write(f"총 **{len(exceed)}건** 기준 초과")
st.dataframe(exceed[[date_col, site_col, pollutant]])

# -------------------------
# 6. PDF 리포트 생성 (matplotlib 그래프 포함)
if st.sidebar.button("📄 PDF 리포트 생성"):
    # 1. matplotlib 그래프 이미지 저장
    fig_, ax = plt.subplots(figsize=(8, 4))
    for name, group in df_filtered.groupby(site_col):
        ax.plot(group[date_col], group[pollutant], marker='o', label=name)
    ax.set_title(f"{pollutant} 시계열 변화")
    ax.set_xlabel("날짜")
    ax.set_ylabel(pollutant)
    ax.legend()
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # 2. PDF 작성
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="수질 오염 데이터 분석 리포트", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"선택 오염물질: {pollutant}", ln=True)
    pdf.cell(200, 10, txt=f"기준치: {threshold}", ln=True)
    pdf.cell(200, 10, txt=f"기준 초과 건수: {len(exceed)}건", ln=True)

    # 이미지 삽입
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        tmpfile.write(buf.read())
        tmpfile.flush()
        pdf.image(tmpfile.name, x=10, y=60, w=180)

    # 저장 및 다운로드
    pdf_path = "water_quality_report.pdf"
    pdf.output(pdf_path)
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="{pdf_path}">📥 리포트 다운로드</a>'
    st.markdown(href, unsafe_allow_html=True)
    st.success("PDF 리포트가 생성되었습니다.")
