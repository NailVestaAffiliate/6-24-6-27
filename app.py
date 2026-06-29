import re
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="NailVesta Weekly Dashboard", layout="wide")

SCENARIO_ORDER = ["S", "AK", "AS", "C", "BK1", "BK2", "BK3", "BK4", "BS1", "BS2", "Haul"]
MATCH_ORDER = ["BK1", "BK2", "BK3", "BK4", "BS1", "BS2", "HAUL", "AK", "AS", "S", "C"]

st.title("NailVesta Weekly Dashboard")
st.caption("GMV × 廣達 / 深達影片分類分析")

st.sidebar.title("上傳資料")
affiliate_file = st.sidebar.file_uploader("上傳廣達 Excel", type=["xlsx"])
deep_file = st.sidebar.file_uploader("上傳深達 Excel", type=["xlsx"])

start_date = st.sidebar.date_input("開始日期", pd.to_datetime("2026-06-19"))
end_date = st.sidebar.date_input("結束日期", pd.to_datetime("2026-06-27"))

START_DATE = pd.to_datetime(start_date)
END_DATE = pd.to_datetime(end_date)

page = st.sidebar.radio(
    "選擇頁面",
    ["📈 GMV Analysis", "📹 Video Analysis", "📊 Combined Analysis", "📋 Raw Data"]
)

def read_excel_auto(uploaded_file, preferred_sheet=None):
    sheets = pd.read_excel(uploaded_file, sheet_name=None)
    if preferred_sheet and preferred_sheet in sheets:
        return sheets[preferred_sheet]
    return list(sheets.values())[0]

def find_col(df, possible_cols):
    for col in possible_cols:
        if col in df.columns:
            return col
    return None

def clean_scenario(value):
    if pd.isna(value):
        return None

    text = str(value).strip().upper()
    text = text.replace("SCENARIO", "")
    text = text.replace("：", ":")
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("－", "-").replace("—", "-")

    pattern = r"(?<![A-Z0-9])(" + "|".join(MATCH_ORDER) + r")(?![A-Z0-9])"
    match = re.search(pattern, text)

    if not match:
        return None

    result = match.group(1)

    if result == "HAUL":
        return "Haul"

    return result

def prepare_video_data(df, group_name, date_col, feedback_col, handle_col=None, link_col=None):
    data = df.copy()

    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data[(data[date_col] >= START_DATE) & (data[date_col] <= END_DATE)].copy()

    data["Group"] = group_name
    data["Date"] = data[date_col].dt.date
    data["Raw Feedback"] = data[feedback_col]
    data["Scenario"] = data[feedback_col].apply(clean_scenario)

    data["Handle"] = data[handle_col] if handle_col and handle_col in data.columns else None
    data["Video Link"] = data[link_col] if link_col and link_col in data.columns else None

    data = data[data["Scenario"].notna()].copy()

    return data[["Group", "Date", "Handle", "Raw Feedback", "Scenario", "Video Link"]]

def make_count_table(video_df):
    base = pd.DataFrame({"Scenario": SCENARIO_ORDER})

    pivot = (
        video_df.groupby(["Scenario", "Group"])
        .size()
        .reset_index(name="Count")
        .pivot(index="Scenario", columns="Group", values="Count")
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    table = base.merge(pivot, on="Scenario", how="left").fillna(0)

    for col in ["廣達", "深達"]:
        if col not in table.columns:
            table[col] = 0
        table[col] = table[col].astype(int)

    table["Total"] = table["廣達"] + table["深達"]

    return table[["Scenario", "廣達", "深達", "Total"]]

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

video_df = pd.DataFrame()
count_table = pd.DataFrame()

if affiliate_file and deep_file:
    affiliate_raw = read_excel_auto(affiliate_file, preferred_sheet="Affiliate List")
    deep_raw = read_excel_auto(deep_file, preferred_sheet="深度达人List")

    affiliate_date_col = find_col(affiliate_raw, ["视频发布日期", "發布日期", "Video Publish Date"])
    affiliate_feedback_col = find_col(affiliate_raw, ["内容反馈", "內容反饋"])
    affiliate_handle_col = find_col(affiliate_raw, ["Handle🧑", "handle", "Handle"])
    affiliate_link_col = find_col(affiliate_raw, ["带货视频Link", "视频链接", "Video Link"])

    deep_date_col = find_col(deep_raw, ["视频发布日期", "發布日期", "Video Publish Date"])
    deep_feedback_col = find_col(deep_raw, ["视频反馈", "視頻反饋"])
    deep_handle_col = find_col(deep_raw, ["handle", "Handle", "Handle🧑"])
    deep_link_col = find_col(deep_raw, ["视频链接", "带货视频Link", "Video Link"])

    missing = []

    if not affiliate_date_col:
        missing.append("廣達：找不到 视频发布日期")
    if not affiliate_feedback_col:
        missing.append("廣達：找不到 内容反馈")
    if not deep_date_col:
        missing.append("深達：找不到 视频发布日期")
    if not deep_feedback_col:
        missing.append("深達：找不到 视频反馈")

    if missing:
        st.error("欄位缺失：\n" + "\n".join(missing))
        st.write("廣達欄位：", list(affiliate_raw.columns))
        st.write("深達欄位：", list(deep_raw.columns))
        st.stop()

    affiliate_video = prepare_video_data(
        affiliate_raw,
        "廣達",
        affiliate_date_col,
        affiliate_feedback_col,
        affiliate_handle_col,
        affiliate_link_col
    )

    deep_video = prepare_video_data(
        deep_raw,
        "深達",
        deep_date_col,
        deep_feedback_col,
        deep_handle_col,
        deep_link_col
    )

    video_df = pd.concat([affiliate_video, deep_video], ignore_index=True)
    count_table = make_count_table(video_df)

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

    affiliate_s = int(count_table.loc[count_table["Scenario"] == "S", "廣達"].sum())
    deep_s = int(count_table.loc[count_table["Scenario"] == "S", "深達"].sum())
    total_s = affiliate_s + deep_s

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總影片數", total_videos)
    col2.metric("廣達影片數", affiliate_videos)
    col3.metric("深達影片數", deep_videos)
    col4.metric("S 影片數", total_s)

    st.subheader("Scenario 數量統計（分開計算）")
    st.dataframe(count_table, use_container_width=True)

    st.info(f"廣達 S 影片：{affiliate_s} 支｜深達 S 影片：{deep_s} 支｜合計 S：{total_s} 支")

    group_df = count_table.melt(
        id_vars="Scenario",
        value_vars=["廣達", "深達"],
        var_name="Group",
        value_name="Count"
    )

    st.subheader("廣達 vs 深達 Scenario 對比")

    group_chart = alt.Chart(group_df).mark_bar().encode(
        x=alt.X("Scenario:N", sort=SCENARIO_ORDER),
        y="Count:Q",
        color="Group:N",
        xOffset="Group:N",
        tooltip=["Scenario:N", "Group:N", "Count:Q"]
    ).properties(height=420)

    st.altair_chart(group_chart, use_container_width=True)

    st.subheader("Scenario Total Distribution")

    total_chart = alt.Chart(count_table).mark_bar().encode(
        x=alt.X("Scenario:N", sort=SCENARIO_ORDER),
        y="Total:Q",
        tooltip=["Scenario:N", "Total:Q"]
    ).properties(height=400)

    st.altair_chart(total_chart, use_container_width=True)

    st.subheader("每日發布量")

    daily_df = video_df.groupby(["Date", "Group"]).size().reset_index(name="Videos")

    daily_chart = alt.Chart(daily_df).mark_line(point=True).encode(
        x="Date:T",
        y="Videos:Q",
        color="Group:N",
        tooltip=["Date:T", "Group:N", "Videos:Q"]
    ).properties(height=400)

    st.altair_chart(daily_chart, use_container_width=True)

    st.subheader("分類明細資料")
    st.dataframe(video_df, use_container_width=True)

elif page == "📊 Combined Analysis":
    st.header("📊 Combined Analysis")

    if video_df.empty:
        st.warning("請先在左側上傳廣達與深達兩個 Excel。")
        st.stop()

    strong = int(count_table[count_table["Scenario"].isin(["S", "AK", "AS"])]["Total"].sum())
    total = int(count_table["Total"].sum())
    strong_rate = strong / total * 100 if total else 0

    affiliate_total = int(count_table["廣達"].sum())
    deep_total = int(count_table["深達"].sum())

    affiliate_strong = int(count_table[count_table["Scenario"].isin(["S", "AK", "AS"])]["廣達"].sum())
    deep_strong = int(count_table[count_table["Scenario"].isin(["S", "AK", "AS"])]["深達"].sum())

    affiliate_strong_rate = affiliate_strong / affiliate_total * 100 if affiliate_total else 0
    deep_strong_rate = deep_strong / deep_total * 100 if deep_total else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("全部強內容占比", f"{strong_rate:.1f}%")
    col2.metric("廣達強內容占比", f"{affiliate_strong_rate:.1f}%")
    col3.metric("深達強內容占比", f"{deep_strong_rate:.1f}%")

    st.markdown(f"""
### 綜合結論

6/19–6/27 共發布 **{total}** 支影片。

其中：

- 廣達：**{affiliate_total}** 支
- 深達：**{deep_total}** 支
- S / AK / AS 強內容：**{strong}** 支，占比 **{strong_rate:.1f}%**
- 廣達強內容占比：**{affiliate_strong_rate:.1f}%**
- 深達強內容占比：**{deep_strong_rate:.1f}%**

6/24–6/27 的 GMV 數據顯示，Creator Content 占比從 6/25 的 **26.3%** 提升到 6/26 的 **41.2%**，代表 TikTok 可能正在重新分配 Buyer Flow，把更多高購買意圖流量導向 Creator Content。
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
