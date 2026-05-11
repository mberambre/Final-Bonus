import streamlit as st
import pandas as pd
import requests

# 1. Data Pipeline: 抓取政府 Open Data
@st.cache_data(ttl=600) # Data Refresh: 每 10 分鐘自動更新一次快取
def get_data():
    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    response = requests.get(url)
    data = response.json()
    return pd.DataFrame(data)

st.title("🚲 台北市 YouBike 2.0 即時監測 Dashboard")

# 獲取資料
df = get_data()

# 2. Data Wrangling (簡單處理): 轉換經緯度格式並重新命名欄位供地圖使用
df['latitude'] = df['lat'].astype(float)
df['longitude'] = df['lng'].astype(float)
df['available_bikes'] = df['sbi'].astype(int)

# 3. Sidebar Interaction (互動功能)
district = st.sidebar.selectbox("選擇行政區", df['sarea'].unique())
filtered_df = df[df['sarea'] == district]

# 4. Visualization: 數值指標與地圖
col1, col2 = st.columns(2)
col1.metric("總站點數", len(filtered_df))
col2.metric("該區可用車輛", filtered_df['available_bikes'].sum())

st.subheader(f"{district} 站點分布地圖")
st.map(filtered_df) # Streamlit 內建地圖，自動讀取 latitude/longitude

# 5. Data Refresh Button
if st.button('手動重新整理數據'):
    st.cache_data.clear()
    st.rerun()