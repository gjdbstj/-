import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from fpdf import FPDF

st.set_page_config(layout="wide")
st.title("💧 수질 오염 데이터 분석 & 지도 시각화")

# 1. 데이터 업로드
st.sidebar.title("📁 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 업로드", type=['csv', 'xlsx'])

# 샘플 데이터 함수 (업로드 없을 때 보여주기용)
@st.cache_data
def load_sample_data():
    data = {
        '측정일자': pd.date_range(start='2024-01-01', periods=5),
        '측정지점명': ['A', 'B', 'C', 'D', 'E'],
        '위도': [37.56, 37.55, 37.57, 37.54, 37.58],
        '경도': [126.97, 126.98, 126.99, 126.96, 127.00],
        '총인': [0.3, 0.7, 0.2, 0.6, 0.8],
        'BOD': [2.0, 3.5, 1.8, 2.5, 4.0],
        'COD': [5.0, 6.0, 4.5, 5.5, 7.0],
    }
    df = pd.DataFrame(data)
    return df

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
else:
    st.info("샘플 데이터로 예시를 보여드립니다. 실제 데이터로 분석하려면 좌측에서 업로드하세요.")
    df = load_sample_data()

# 컬럼명 날짜 변환
date_col = '측정일자'
df[date_col] = pd.to_datetime(df[date_col])

# 오염물질 선택 (날짜, 지점명, 위도, 경도 제외)
possible_pollutants = [col for col in df.columns if col not in ['측정일자', '측정지점명', '위도', '경도']]
pollutant = st.sidebar.selectbox("오염물질 선택", possible_pollutants)

# 기간 선택
min_date = df[date_col].min()
max_date = df[date_col].max()
start_date, end_date = st.sidebar.date_input("기간 선택", [min_date, max_date], min_value=min_date, max_value=max_date)

# 기준치 설정
threshold = st.sidebar.number_input("기준치 설정", min_value=0.0, value=0.5, step=0.1)

@st.cache_data
def filter_data(df, start_date, end_date, date_col):
    return df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]

filtered_df = filter_data(df, start_date, end_date, date_col)

# Plotly 라인 차트 생성 (각 지점별 농도 시간 변화)
@st.cache_data
def create_line_chart(data, date_col, pollutant, site_col):
    # site_col별로 시간 순으로 그리도록
    fig = px.line(
        data.sort_values(by=[site_col, date_col]),
        x=date_col,
        y=pollutant,
        color=site_col,
        markers=True,
        title=f"{pollutant} 농도 시계열 변화"
    )
    fig.update_layout(autosize=True, xaxis_title="측정일자", yaxis_title=f"{pollutant} 농도")
    return fig

fig = create_line_chart(filtered_df, date_col, pollutant, '측정지점명')
st.subheader("📈 시계열 오염물질 농도 변화 (지점별)")
st.plotly_chart(fig, use_container_width=True)

# Folium 지도 생성 - 각 지점 위치 표시 및 농도 표시
@st.cache_resource
def create_folium_map(data, lat_col='위도', lon_col='경도', pollutant_col='총인', threshold=0.5):
    center = [data[lat_col].mean(), data[lon_col].mean()]
    m = folium.Map(location=center, zoom_start=11)
    marker_cluster = MarkerCluster().add_to(m)

    # 중복 지점이 있을 수 있으므로, 측정지점별 최근 데이터나 평균 데이터 선택 가능
    # 여기선 각 지점의 평균 농도 사용
    grouped = data.groupby(['측정지점명', lat_col, lon_col])[pollutant_col].mean().reset_index()

    for _, row in grouped.iterrows():
        color = 'red' if row[pollutant_col] > threshold else 'green'
        folium.CircleMarker(
            location=[row[lat_col], row[lon_col]],
            radius=10,
            popup=folium.Popup(f"{row['측정지점명']}<br>{pollutant_col}: {row[pollutant_col]:.2f}", max_width=200),
            color=color,
            fill=True,
            fill_opacity=0.7
        ).add_to(marker_cluster)
    return m

st.subheader("🗺️ 측정 지점 지도 시각화 (평균 농도 기준)")
map_ = create_folium_map(filtered_df, pollutant_col=pollutant, threshold=threshold)
st_folium(map_, width=700, height=500, key="map_folium")

# 기준치 초과 데이터 표출
exceed = filtered_df[filtered_df[pollutant] > threshold]
st.subheader(f"⚠️ 기준치({threshold}) 초과 데이터: 총 {len(exceed)}건")
st.dataframe(exceed[[date_col, '측정지점명', pollutant]])

# PDF 리포트 생성 (간단 예시)
if st.sidebar.button("리포트 생성"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="수질 오염 데이터 분석 리포트", ln=True, align='C')
    pdf.cell(200, 10, txt=f"분석기간: {start_date} ~ {end_date}", ln=True)
    pdf.cell(200, 10, txt=f"선택 오염물질: {pollutant}", ln=True)
    pdf.cell(200, 10, txt=f"기준치 초과 건수: {len(exceed)}건", ln=True)
    pdf.output("water_quality_report.pdf")
    st.success("리포트가 생성되었습니다. (water_quality_report.pdf)")

