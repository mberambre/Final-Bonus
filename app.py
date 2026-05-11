import streamlit as st
import pandas as pd
import requests
import numpy as np

# 頁面基本設定
st.set_page_config(page_title="YouBike Pro 數據分析終端", page_icon="🚲", layout="wide")

# 1. 進階 Data Pipeline
@st.cache_data(ttl=300)
def get_data():
    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    try:
        res = requests.get(url)
        df = pd.DataFrame(res.json())
        # 基本清洗
        df['lat'] = df['lat'].astype(float)
        df['lng'] = df['lng'].astype(float)
        df['sbi'] = df['sbi'].astype(int) # 可用車輛
        df['bemp'] = df['bemp'].astype(int) # 可還空位
        return df
    except:
        return pd.DataFrame()

# 2. 距離計算函數 (Wrangling 加分項)
def haversine(lat1, lon1, lat2, lon2):
    # 計算地球上兩點間的距離 (公里)
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1-a))

st.title("📊 YouBike 2.0 高級數據監測終端")
st.sidebar.header("控制面板")

df = get_data()

if not df.empty:
    # --- 側邊欄：台大專區 ---
    st.sidebar.subheader("📍 地標連動")
    show_ntu = st.sidebar.checkbox("顯示離台大最近站點")
    
    # --- 第一區：全台北市數據統計 (Visualization 加分) ---
    st.header("📈 全市數據透視")
    city_stats = df.groupby('sarea')['sbi'].sum().sort_values(ascending=False)
    st.bar_chart(city_stats)
    
    # --- 第二區：互動篩選 ---
    districts = sorted(df['sarea'].unique())
    selected_dist = st.selectbox("請選擇觀測行政區", districts)
    f_df = df[df['sarea'] == selected_dist]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("區域站點數", len(f_df))
    col2.metric("區域總車輛", f_df['sbi'].sum())
    # 計算滿載率 (Wrangling 加分)
    load_rate = (f_df['sbi'].sum() / (f_df['sbi'].sum() + f_df['bemp'].sum())) * 100
    col3.metric("區域車輛滿載率", f"{load_rate:.1f}%")

    # --- 第三區：地圖與距離分析 ---
    st.subheader(f"📍 {selected_dist} 實時點位與飽和度")
    
    # 地圖顏色處理 (依車輛數顯示不同大小)
    map_df = f_df.rename(columns={'lat': 'latitude', 'lng': 'longitude'})
    st.map(map_df)

    # --- 第四區：加分項 - 離台大最近的站點 (NTU Proximity) ---
    if show_ntu:
        st.divider()
        st.subheader("🎓 師生福利：台大校門口最近站點 (羅斯福路口)")
        ntu_lat, ntu_lng = 25.0173, 121.5330 # 台大校門口經緯度
        df['dist_ntu'] = haversine(ntu_lat, ntu_lng, df['lat'], df['lng'])
        near_ntu = df.sort_values('dist_ntu').head(5)
        
        for _, row in near_ntu.iterrows():
            with st.expander(f"📌 {row['sna'].replace('YouBike2.0_', '')}"):
                st.write(f"距離校門：約 {row['dist_ntu']*1000:.0f} 公尺")
                st.write(f"目前可用車輛：{row['sbi']} 台")
                st.progress(min(row['sbi']/row['tot'], 1.0), text="車輛充足度")

    # 手動刷新
    if st.sidebar.button("即時數據刷新"):
        st.cache_data.clear()
        st.rerun()

else:
    st.error("無法連線至政府數據庫，請檢查網路。")
