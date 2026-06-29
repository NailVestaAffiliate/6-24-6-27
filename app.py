import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="NailVesta Weekly Dashboard", layout="wide")

START_DATE = pd.to_datetime("2026-06-19")
END_DATE = pd.to_datetime("2026-06-27")

SCENARIO_ORDER = ["S", "AK", "AS", "C", "BK1", "BK2", "BK3", "BK4", "BS1", "BS2", "Haul"]

def clean_scenario(value):
    if pd.isna(value):
        return None
    text = str(value).strip().replace("Scenario", "").replace("scenario", "").replace(" ", "")
    text_upper = text.upper()
    for s in SCENARIO_ORDER:
        if text_upper == s.upper():
            return s
    for s in SCENARIO_ORDER:
        if s.upper() in text_upper:
            return s
    return None

def prepare_video_data(df, group_name, date_col, scenario_col, handle_col=None, link_col=None):
    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data[(data[date_col] >= START_DATE) & (data[date_col] <= END_DATE)].copy()
    data["Group"] = group_name
    data["Date"] = data[date_col].dt.date
    data["Scenario"] = data[scenario_col].apply(clean_scenario)
    data["Handle"] = data[handle_col] if handle_col and handle_col in data.columns else None
    data["Video Link"] = data[link_col] if link_col and link_col in data.columns else None
    data = data[data["Scenario"].notna()].copy()
    return data[["Group", "Date", "Handle", "Scenario", "Video Link"]]

def make_count_table(video_df):
    table = (
        video_df.groupby(["Scenario", "Group"])
        .size()
        .reset_index(name="Count")
        .pivot(index="Scenario", columns="Group", values="Count")
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    for col in ["廣達", "深達"]:
        if col not in table.columns:
            table[col] = 0
    table["Total"] = table["廣達"] + table["深達"]
    table["Scenario"] = pd.Categorical(table["Scenario"], categories=SCENARIO_ORDER, ordered=True)
    return table.sort_values("Scenario").reset_index(drop=True)[["Scenario", "廣達", "深達", "Total"]]

st.title("NailVesta Weekly Dashboard")
st.caption("GMV × 廣達 / 深達影片分類分析")

st.sidebar.title("上傳資料")
affiliate_file = st.sidebar.file_uploader("上傳廣達 Excel", type=["xlsx"])
deep_file = st.sidebar.file_uploader("上傳深達 Excel", type=["xlsx"])

page = st.sidebar.radio(
    "選擇頁面",
    ["📈 GMV Analysis", "📹 Video Analysis", "📊 Combined Analysis", "📋 Raw Data"]
)

gmv_df = pd.DataFrame({
    "Date": pd.to_datetime(["2026-06-24", "2026-06-25", "2026-06-26", "2026-06-27"]),
    "Shop GMV": [8079.80, 9670.46, 9672.34, 6394.94],
    "Creator GMV": [2310.44, 2539.16, 3983.20, 2652.14],
    "Creator %": [28.6, 26.3, 41.2, 41.5],
    "Seller GMV": [3399.10, 4704.54, 3542.73, 2095.35],
    "Seller %": [42.1, 48.6, 36.6, 32.8],
    "Shop Tab %": [29.3, 25.1, 22.2, 25.8],
    "Orders": [214, 239, 264, 168],
    "Items Sold": [319, 398, 395, 256],
})

if affiliate_file and deep_file:
    affiliate_raw = pd.read_excel(affiliate_file, sheet_name="Affiliate List")
    deep_raw = pd.read_excel(deep_file, sheet_name="深度达人List")

    affiliate_video = prepare_video_data(
        affiliate_raw, "廣達", "视频发布日期", "内容反馈", "Handle🧑", "带货视频Link"
    )

    deep_video = prepare_video_data(
        deep_raw, "深達", "视频发布日期", "视频分类", "handle", "视频链接"
    )

    video_df = pd.concat([affiliate_video, deep_video], ignore_index=True)
    count_table = make_count_table(video_df)
else:
    video_df = pd.DataFrame()
    count_table = pd.DataFrame()

if page == "📈 GMV Analysis":
    st.header("📈 GMV Analysis")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最高 Shop GMV", f"${gmv_df['Shop GMV'].max():,.2f}")
    col2.metric("最高 Creator GMV", f"${gmv_df['Creator GMV'].max():,.2f}")
    col3.metric("最高 Creator 占比", f"{gmv_df['Creator %'].max():.1f}%")
    col4.metric("最低 Seller 占比", f"{gmv_df['Seller %'].min():.1f}%")

    st.dataframe(gmv_df, use_container_width=True)

    gmv_melt = gmv_df.melt(
        id_vars="Date",
        value_vars=["Shop GMV", "Creator GMV", "Seller GMV"],
        var_name="Metric",
        value_name="GMV"
    )

    chart = alt.Chart(gmv_melt).mark_line(point=True).encode(
        x="Date:T",
        y="GMV:Q",
        color="Metric:N",
        tooltip=["Date:T", "Metric:N", "GMV:Q"]
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

    share_df = gmv_df.melt(
        id_vars="Date",
        value_vars=["Creator %", "Seller %", "Shop Tab %"],
        var_name="Channel",
        value_name="Contribution %"
    )

    share_chart = alt.Chart(share_df).mark_line(point=True).encode(
        x="Date:T",
        y="Contribution %:Q",
        color="Channel:N",
        tooltip=["Date:T", "Channel:N", "Contribution %:Q"]
    ).properties(height=400)

    st.altair_chart(share_chart, use_container_width=True)

elif page == "📹 Video Analysis":
    st.header("📹 Video Analysis")

    if video_df.empty:
        st.warning("請先在左側上傳廣達與深達兩個 Excel。")
        st.stop()

    total_videos = len(video_df)
    affiliate_videos = len(video_df[video_df["Group"] == "廣達"])
    deep_videos = len(video_df[video_df["Group"] == "深達"])
    s_total = int(count_table.loc[count_table["Scenario"] == "S", "Total"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總影片數", total_videos)
    col2.metric("廣達影片數", affiliate_videos)
    col3.metric("深達影片數", deep_videos)
    col4.metric("S 影片數", s_total)

    st.subheader("Scenario 數量統計")
    st.dataframe(count_table, use_container_width=True)

    chart = alt.Chart(count_table).mark_bar().encode(
        x=alt.X("Scenario:N", sort=SCENARIO_ORDER),
        y="Total:Q",
        tooltip=["Scenario:N", "Total:Q"]
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

    group_df = count_table.melt(
        id_vars="Scenario",
        value_vars=["廣達", "深達"],
        var_name="Group",
        value_name="Count"
    )

    group_chart = alt.Chart(group_df).mark_bar().encode(
        x=alt.X("Scenario:N", sort=SCENARIO_ORDER),
        y="Count:Q",
        color="Group:N",
        xOffset="Group:N",
        tooltip=["Scenario:N", "Group:N", "Count:Q"]
    ).properties(height=400)

    st.altair_chart(group_chart, use_container_width=True)

    daily_df = video_df.groupby(["Date", "Group"]).size().reset_index(name="Videos")

    daily_chart = alt.Chart(daily_df).mark_line(point=True).encode(
        x="Date:T",
        y="Videos:Q",
        color="Group:N",
        tooltip=["Date:T", "Group:N", "Videos:Q"]
    ).properties(height=400)

    st.altair_chart(daily_chart, use_container_width=True)

elif page == "📊 Combined Analysis":
    st.header("📊 Combined Analysis")

    if video_df.empty:
        st.warning("請先在左側上傳廣達與深達兩個 Excel。")
        st.stop()

    strong = int(count_table[count_table["Scenario"].isin(["S", "AK", "AS"])]["Total"].sum())
    total = int(count_table["Total"].sum())
    strong_rate = strong / total * 100 if total else 0

    st.metric("S / AK / AS 強內容占比", f"{strong_rate:.1f}%")

    st.markdown(f"""
### 綜合結論

6/24–6/27 的 GMV 數據顯示，店舖不是單純上升或下降，而是成交來源發生轉移。

6/25 到 6/26：

- Shop GMV 幾乎持平
- Creator Content 占比從 **26.3%** 提升到 **41.2%**
- Seller Content 占比從 **48.6%** 下降到 **36.6%**

同時，6/19–6/27 共發布 **{total}** 支影片，其中 S / AK / AS 強內容共 **{strong}** 支，占比 **{strong_rate:.1f}%**。

這代表 TikTok 可能正在重新分配 Buyer Flow，把更多高購買意圖流量導向 Creator Content。
""")

    st.subheader("Scenario 統計")
    st.dataframe(count_table, use_container_width=True)

elif page == "📋 Raw Data":
    st.header("📋 Raw Data")

    if video_df.empty:
        st.warning("請先在左側上傳廣達與深達兩個 Excel。")
        st.stop()

    st.subheader("整理後影片資料")
    st.dataframe(video_df, use_container_width=True)

    st.subheader("Scenario 統計表")
    st.dataframe(count_table, use_container_width=True)

    st.subheader("GMV 資料")
    st.dataframe(gmv_df, use_container_width=True)

    csv = count_table.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "下載 Scenario 統計 CSV",
        data=csv,
        file_name="scenario_count_20260619_20260627.csv",
        mime="text/csv"
    )
