import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import folium
from streamlit_folium import folium_static
import plotly.express as px
from io import BytesIO
import base64

st.set_page_config(page_title="수질 오염 분석", layout="wide")

st.title("📊 수질 오염 분석 대시보드")

# -------------------------------
# 1. 데이터 업로드
# -------------------------------
st.header("1. 데이터 업로드")
uploaded_file = st.file_uploader("CSV 또는 Excel 파일 업로드", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("✅ 데이터 업로드 완료")
    st.dataframe(df.head())

    # -------------------------------
    # 2. 시기별·지점별 오염물질 농도 시각화
    # -------------------------------
    st.header("2. 시기별·지점별 오염물질 농도 시각화")

    date_col = st.selectbox("📅 날짜 컬럼 선택", df.columns)
    loc_col = st.selectbox("📍 지점 컬럼 선택", df.columns)
    value_col = st.selectbox("🧪 오염물질 농도 컬럼 선택", df.columns)

    fig = px.line(df, x=date_col, y=value_col, color=loc_col, title="농도 변화 추이")
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # 3. 지도에서 배출원 시각화
    # -------------------------------
    st.header("3. 주요 배출원 위치 시각화")

    if {'위도', '경도', '배출량', '배출원명'}.issubset(df.columns):
        m = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=8)
        for i, row in df.iterrows():
            folium.CircleMarker(
                location=(row['위도'], row['경도']),
                radius=row['배출량'] / 10,
                color='red',
                fill=True,
                fill_opacity=0.6,
                popup=f"{row['배출원명']} (배출량: {row['배출량']})"
            ).add_to(m)
        folium_static(m)
    else:
        st.warning("⚠️ '위도', '경도', '배출량', '배출원명' 컬럼이 필요합니다.")

    # -------------------------------
    # 4. 농도 초과 지점 탐지 및 알림
    # -------------------------------
    st.header("4. 농도 초과 지점 자동 탐지")

    threshold = st.slider("🔔 초과 기준값 설정", min_value=0.0, max_value=500.0, value=50.0, step=0.1)

    exceeded = df[df[value_col] > threshold]
    st.write(f"🚨 초과 지점 수: {len(exceeded)}개")
    st.dataframe(exceeded)

    # -------------------------------
    # 5. 오염물질 간 상관관계 분석
    # -------------------------------
    st.header("5. 오염물질 간 상관관계 분석")

    selected_cols = st.multiselect("상관관계를 분석할 수질 지표 선택", df.select_dtypes(include=np.number).columns)

    if len(selected_cols) >= 2:
        corr_matrix = df[selected_cols].corr()
        st.write("📌 상관계수 행렬:")
        st.dataframe(corr_matrix)

        fig_corr = sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
        st.pyplot(fig_corr.figure)

    # -------------------------------
    # 6. 리포트 생성 및 다운로드
    # -------------------------------
    st.header("6. 리포트 다운로드")

    def convert_df(df_report):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_report.to_excel(writer, index=False, sheet_name='Report')
        output.seek(0)
        b64 = base64.b64encode(output.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="report.xlsx">📥 리포트 다운로드</a>'
        return href

    if st.button("📄 리포트 생성"):
        st.markdown(convert_df(df), unsafe_allow_html=True)

else:
    st.info("📁 분석할 데이터를 먼저 업로드해주세요.")
