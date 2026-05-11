import streamlit as st
import pandas as pd
import requests
import plotly.express as px # 用來畫更高級的圖表

# 1. 頁面設定
st.set_page_config(page_title="全球即時氣象觀測站", page_icon="🌡️", layout="wide")

# 2. 城市座標數據 (預設穩定數據源)
CITIES = {
    "台北 (Taipei)": {"lat": 25.03, "lon": 121.53},
    "東京 (Tokyo)": {"lat": 35.68, "lon": 139.69},
    "紐約 (New York)": {"lat": 40.71, "lon": -74.00},
    "倫敦 (London)": {"lat": 51.50, "lon": -0.12},
    "巴黎 (Paris)": {"lat": 48.85, "lon": 2.35},
    "雪梨 (Sydney)": {"lat": -33.86, "lon": 151.20}
}

# 3. Data Pipeline: 抓取氣象資料
@st.cache_data(ttl=3600) # 氣象資料一小時更新一次即可
def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m&current_weather=true"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"數據抓取失敗：{e}")
        return None

# --- UI 介面 ---
st.title("🌡️ 全球主要城市即時氣象 Dashboard")
st.markdown("本系統透過 **Open-Meteo API** 進行即時數據介接，分析全球各大城市之氣溫趨勢。")

# 側邊欄：選擇城市
st.sidebar.header("📍 觀測設定")
selected_city = st.sidebar.selectbox("選擇觀測城市", list(CITIES.keys()))
city_coords = CITIES[selected_city]

data = get_data = get_weather_data(city_coords["lat"], city_coords["lon"])

if data:
    # 4. Data Wrangling: 解析資料
    current = data["current_weather"]
    hourly_df = pd.DataFrame({
        "時間": pd.to_datetime(data["hourly"]["time"]),
        "氣溫 (°C)": data["hourly"]["temperature_2m"],
        "濕度 (%)": data["hourly"]["relative_humidity_2m"]
    })

    # 5. Visualization: 關鍵指標卡片
    col1, col2, col3 = st.columns(3)
    col1.metric("當前氣溫", f"{current['temperature']} °C")
    col2.metric("風速", f"{current['windspeed']} km/h")
    col3.metric("觀測緯度", f"{city_coords['lat']}")

    st.divider()

    # 6. Visualization: 氣溫趨勢圖 (Plotly 版，比內建更強)
    st.subheader(f"📅 {selected_city} 未來一週氣溫預測趨勢")
    fig = px.line(hourly_df, x="時間", y="氣溫 (°C)", title="溫度變化曲線")
    st.plotly_chart(fig, use_container_width=True)

    # 7. 地圖顯示
    st.subheader("🗺️ 觀測站地理位置")
    map_df = pd.DataFrame([city_coords]).rename(columns={"lat": "latitude", "lon": "longitude"})
    st.map(map_data = map_df)

    # 8. 原始資料檢視
    with st.expander("🔍 檢視 168 小時原始數據預測表"):
        st.dataframe(hourly_df, use_container_width=True)

# 刷新機制
if st.sidebar.button("同步最新氣象數據"):
    st.cache_data.clear()
    st.rerun()
