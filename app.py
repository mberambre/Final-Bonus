import streamlit as st
import pandas as pd
import requests

# 設定網頁標題與圖示
st.set_page_config(page_title="YouBike 監測站", page_icon="🚲")

# 1. Data Pipeline: 抓取政府 Open Data (使用 Cache 確保效能)
@st.cache_data(ttl=600)  # 數據每 10 分鐘自動過期更新
def get_data():
    # 台北市 YouBike 2.0 即時 JSON
    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    try:
        response = requests.get(url)
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"資料抓取失敗: {e}")
        return pd.DataFrame()

st.title("🚲 台北市 YouBike 2.0 即時監測 Dashboard")
st.markdown("此 Dashboard 串接台北市政府 Open Data，提供即時站點資訊。")

# 獲取資料
df = get_data()

if not df.empty:
    # 2. Data Wrangling: 自動偵測欄位名稱 (修正 KeyError 問題)
    # 處理經緯度與車輛數
    lat_col = next((col for col in ['lat', 'latitude'] if col in df.columns), None)
    lng_col = next((col for col in ['lng', 'longitude'] if col in df.columns), None)
    bike_col = next((col for col in ['sbi', 'available_rent_bikes'] if col in df.columns), None)
    station_col = next((col for col in ['sna', 'station_name'] if col in df.columns), None)

    if lat_col and lng_col and bike_col:
        # 轉換資料型態
        df['latitude'] = df[lat_col].astype(float)
        df['longitude'] = df[lng_col].astype(float)
        df['available_bikes'] = df[bike_col].astype(int)
        
        # 3. Sidebar: 互動式篩選
        st.sidebar.header("篩選條件")
        all_districts = sorted(df['sarea'].unique())
        selected_district = st.sidebar.selectbox("選擇行政區", all_districts)
        
        filtered_df = df[df['sarea'] == selected_district]

        # 4. Visualization: 數值看板
        col1, col2, col3 = st.columns(3)
        col1.metric("該區總站點數", len(filtered_df))
        col2.metric("該區可用車輛", filtered_df['available_bikes'].sum())
        col3.metric("資料更新頻率", "10 min/次")

        # 5. Visualization: 地圖
        st.subheader(f"📍 {selected_district} 站點分布地圖")
        st.map(filtered_df[['latitude', 'longitude']])

        # 6. Data Refresh: 手動更新按鈕
        if st.sidebar.button('手動刷新數據'):
            st.cache_data.clear()
            st.rerun()

        # 顯示原始資料表格 (加分項：增加透明度)
        with st.expander("查看詳細站點資料"):
            st.write(filtered_df[[station_col, 'available_bikes', 'ar', 'mday']])
    else:
        st.warning("API 欄位格式變動，請檢查欄位對照表。")
else:
    st.info("目前無法讀取資料，請稍後再試。")
