import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(
    page_title="NailVesta Weekly Dashboard",
    layout="wide"
)

# =========================
# Basic Config
# =========================

START_DATE = pd.to_datetime("2026-06-19")
END_DATE = pd.to_datetime("2026-06-27")

SCENARIO_ORDER = [
    "S", "AK", "AS", "C",
    "BK1", "BK2", "BK3", "BK4",
    "BS1", "BS2", "Haul"
]

AFFILIATE_FILE = "NailVesta_Affiliate List_Edric.xlsx"
DEEP_FILE = "NailVesta_深度达人List_Edric (1).xlsx"


# =========================
# Helper Functions
# =========================

def clean_scenario(value):
    """
    Clean scenario text like:
    - Scenario S -> S
    - scenario c -> C
    - 审美 AS -> AS
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    text = text.replace("Scenario", "").replace("scenario", "").strip()
    text = text.replace("：", ":").replace(" ", "")
    text_upper = text.upper()

    for s in SCENARIO_ORDER:
        if text_upper == s.upper():
            return s

    for s in SCENARIO_ORDER:
        if s.upper() in text_upper:
            return s

    return None


def safe_read_excel(file_path, sheet_name=0):
    if not Path(file_path).exists():
        st.error(f"找不到檔案：{file_path}")
        st.stop()

    return pd.read_excel(file_path, sheet_name=sheet_name)


def prepare_video_data(df, group_name, date_col, scenario_col, handle_col=None, link_col=None):
    data = df.copy()

    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data[
        (data[date_col] >= START_DATE) &
        (data[date_col] <= END_DATE)
    ].copy()

    data["Group"] = group_name
    data["Date"] = data[date_col].dt.date
    data["Scenario"] = data[scenario_col].apply(clean_scenario)

    if handle_col and handle_col in data.columns:
        data["Handle"] = data[handle_col]
    else:
        data["Handle"] = None

    if link_col and link_col in data.columns:
        data["Video Link"] = data[link_col]
    else:
        data["Video Link"] = None

    data = data[data["Scenario"].notna()].copy()

    return data[["Group", "Date", "Handle", "Scenario", "Video Link"]]


def make_count_table(video_df):
    count_table = (
        video_df
        .groupby(["Scenario", "Group"])
        .size()
        .reset_index(name="Count")
        .pivot(index="Scenario", columns="Group", values="Count")
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    for col in ["廣達", "深達"]:
        if col not in count_table.columns:
            count_table[col] = 0

    count_table["Total"] = count_table["廣達"] + count_table["深達"]
    count_table["Scenario"] = pd.Categorical(
        count_table["Scenario"],
        categories=SCENARIO_ORDER,
        ordered=True
    )

    count_table = (
        count_table
        .sort_values("Scenario")
        .reset_index(drop=True)
    )

    return count_table[["Scenario", "廣達", "深達", "Total"]]


def percent_change(current, previous):
    if previous == 0:
        return 0
    return (current - previous) / previous * 100


# =========================
# Load Excel Data
# =========================

affiliate_raw = safe_read_excel(AFFILIATE_FILE, sheet_name="Affiliate List")
deep_raw = safe_read_excel(DEEP_FILE, sheet_name="深度达人List")

affiliate_video = prepare_video_data(
    affiliate_raw,
    group_name="廣達",
    date_col="视频发布日期",
    scenario_col="内容反馈",
    handle_col="Handle🧑",
    link_col="带货视频Link"
)

deep_video = prepare_video_data(
    deep_raw,
    group_name="深達",
    date_col="视频发布日期",
    scenario_col="视频分类",
    handle_col="handle",
    link_col="视频链接"
)

video_df = pd.concat([affiliate_video, deep_video], ignore_index=True)
count_table = make_count_table(video_df)


# =========================
# GMV Data
# =========================

gmv_data = {
    "Date": [
        "2026-06-24",
        "2026-06-25",
        "2026-06-26",
        "2026-06-27",
    ],
    "Shop GMV": [8079.80, 9670.46, 9672.34, 6394.94],
    "Creator GMV": [2310.44, 2539.16, 3983.20, 2652.14],
    "Creator %": [28.6, 26.3, 41.2, 41.5],
    "Seller GMV": [3399.10, 4704.54, 3542.73, 2095.35],
    "Seller %": [42.1, 48.6, 36.6, 32.8],
    "Shop Tab %": [29.3, 25.1, 22.2, 25.8],
    "Orders": [214, 239, 264, 168],
    "Items Sold": [319, 398, 395, 256],
}

gmv_df = pd.DataFrame(gmv_data)
gmv_df["Date"] = pd.to_datetime(gmv_df["Date"])


# =========================
# Sidebar
# =========================

st.sidebar.title("NailVesta Dashboard")
page = st.sidebar.radio(
    "選擇頁面",
    [
        "📈 GMV Analysis",
        "📹 Video Analysis",
        "📊 Combined Analysis",
        "📋 Raw Data",
    ]
)

st.sidebar.markdown("---")
st.sidebar.write(f"分析日期：{START_DATE.date()} ~ {END_DATE.date()}")


# =========================
# Page 1: GMV Analysis
# =========================

if page == "📈 GMV Analysis":
    st.title("📈 NailVesta GMV Analysis")
    st.caption("6/24–6/27 店舖 GMV、Creator Content、Seller Content、Shop Tab 分析")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("最高 Shop GMV", f"${gmv_df['Shop GMV'].max():,.2f}")
    col2.metric("最高 Creator GMV", f"${gmv_df['Creator GMV'].max():,.2f}")
    col3.metric("最高 Creator 占比", f"{gmv_df['Creator %'].max():.1f}%")
    col4.metric("最低 Seller 占比", f"{gmv_df['Seller %'].min():.1f}%")

    st.subheader("GMV 數據表")
    st.dataframe(gmv_df, use_container_width=True)

    st.subheader("Shop GMV vs Creator GMV vs Seller GMV")

    gmv_melt = gmv_df.melt(
        id_vars="Date",
        value_vars=["Shop GMV", "Creator GMV", "Seller GMV"],
        var_name="Metric",
        value_name="GMV"
    )

    chart = (
        alt.Chart(gmv_melt)
        .mark_line(point=True)
        .encode(
            x="Date:T",
            y="GMV:Q",
            color="Metric:N",
            tooltip=["Date:T", "Metric:N", "GMV:Q"]
        )
        .properties(height=420)
    )

    st.altair_chart(chart, use_container_width=True)

    st.subheader("GMV 占比變化")

    share_df = gmv_df.melt(
        id_vars="Date",
        value_vars=["Creator %", "Seller %", "Shop Tab %"],
        var_name="Channel",
        value_name="Contribution %"
    )

    share_chart = (
        alt.Chart(share_df)
        .mark_line(point=True)
        .encode(
            x="Date:T",
            y="Contribution %:Q",
            color="Channel:N",
            tooltip=["Date:T", "Channel:N", "Contribution %:Q"]
        )
        .properties(height=420)
    )

    st.altair_chart(share_chart, use_container_width=True)

    st.info(
        "目前數據顯示，6/25 到 6/26 店舖總 GMV 幾乎持平，"
        "但 Creator Content 占比從 26.3% 提升到 41.2%，"
        "代表成交來源從 Seller Content 明顯轉移到 Creator Content。"
    )


# =========================
# Page 2: Video Analysis
# =========================

elif page == "📹 Video Analysis":
    st.title("📹 廣達 / 深達影片分類分析")
    st.caption("統計 6/19–6/27 發布影片中的 S、AK、AS、C、BK、BS、Haul 數量")

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

    st.subheader("Scenario Total Distribution")

    total_chart = (
        alt.Chart(count_table)
        .mark_bar()
        .encode(
            x=alt.X("Scenario:N", sort=SCENARIO_ORDER),
            y="Total:Q",
            tooltip=["Scenario:N", "Total:Q"]
        )
        .properties(height=400)
    )

    st.altair_chart(total_chart, use_container_width=True)

    st.subheader("廣達 vs 深達 Scenario 對比")

    group_chart_df = count_table.melt(
        id_vars="Scenario",
        value_vars=["廣達", "深達"],
        var_name="Group",
        value_name="Count"
    )

    group_chart = (
        alt.Chart(group_chart_df)
        .mark_bar()
        .encode(
            x=alt.X("Scenario:N", sort=SCENARIO_ORDER),
            y="Count:Q",
            color="Group:N",
            xOffset="Group:N",
            tooltip=["Scenario:N", "Group:N", "Count:Q"]
        )
        .properties(height=420)
    )

    st.altair_chart(group_chart, use_container_width=True)

    st.subheader("每日發布量")

    daily_df = (
        video_df
        .groupby(["Date", "Group"])
        .size()
        .reset_index(name="Videos")
    )

    daily_chart = (
        alt.Chart(daily_df)
        .mark_line(point=True)
        .encode(
            x="Date:T",
            y="Videos:Q",
            color="Group:N",
            tooltip=["Date:T", "Group:N", "Videos:Q"]
        )
        .properties(height=420)
    )

    st.altair_chart(daily_chart, use_container_width=True)

    st.subheader("自動分析")

    s_count = int(count_table.loc[count_table["Scenario"] == "S", "Total"].sum())
    ak_count = int(count_table.loc[count_table["Scenario"] == "AK", "Total"].sum())
    as_count = int(count_table.loc[count_table["Scenario"] == "AS", "Total"].sum())
    c_count = int(count_table.loc[count_table["Scenario"] == "C", "Total"].sum())

    s_rate = s_count / total_videos * 100 if total_videos else 0
    strong_count = s_count + ak_count + as_count
    strong_rate = strong_count / total_videos * 100 if total_videos else 0

    st.markdown(f"""
### 6/19–6/27 影片結構重點

本週共統計 **{total_videos}** 支影片。

其中：

- 廣達發布：**{affiliate_videos}** 支
- 深達發布：**{deep_videos}** 支
- S 類影片：**{s_count}** 支，占比 **{s_rate:.1f}%**
- S + AK + AS 強內容合計：**{strong_count}** 支，占比 **{strong_rate:.1f}%**
- C 類影片：**{c_count}** 支

### 初步判斷

如果 S / AK / AS 占比越高，代表本週高質量內容比例較高，後續更容易帶動 Creator GMV。

如果 C / BK / BS 類占比較高，代表影片數量雖然有，但內容質量可能不夠穩定，需要加強口播、露臉、上手展示、前三秒吸引力。
""")


# =========================
# Page 3: Combined Analysis
# =========================

elif page == "📊 Combined Analysis":
    st.title("📊 GMV × 影片數量綜合分析")
    st.caption("將 GMV 變化和 6/19–6/27 發布影片結構放在一起觀察")

    st.subheader("1. GMV 占比變化")

    share_df = gmv_df.melt(
        id_vars="Date",
        value_vars=["Creator %", "Seller %", "Shop Tab %"],
        var_name="Channel",
        value_name="Contribution %"
    )

    share_chart = (
        alt.Chart(share_df)
        .mark_line(point=True)
        .encode(
            x="Date:T",
            y="Contribution %:Q",
            color="Channel:N",
            tooltip=["Date:T", "Channel:N", "Contribution %:Q"]
        )
        .properties(height=360)
    )

    st.altair_chart(share_chart, use_container_width=True)

    st.subheader("2. 影片分類結構")

    st.dataframe(count_table, use_container_width=True)

    st.subheader("3. 強內容占比")

    strong_scenarios = ["S", "AK", "AS"]
    weak_scenarios = ["C", "BK1", "BK2", "BK3", "BK4", "BS1", "BS2", "Haul"]

    strong_total = int(count_table[count_table["Scenario"].isin(strong_scenarios)]["Total"].sum())
    weak_total = int(count_table[count_table["Scenario"].isin(weak_scenarios)]["Total"].sum())
    all_total = strong_total + weak_total

    strong_rate = strong_total / all_total * 100 if all_total else 0
    weak_rate = weak_total / all_total * 100 if all_total else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("強內容 S/AK/AS", strong_total, f"{strong_rate:.1f}%")
    col2.metric("其他內容", weak_total, f"{weak_rate:.1f}%")
    col3.metric("總影片數", all_total)

    pie_df = pd.DataFrame({
        "Type": ["Strong Content", "Other Content"],
        "Count": [strong_total, weak_total]
    })

    pie_chart = (
        alt.Chart(pie_df)
        .mark_arc()
        .encode(
            theta="Count:Q",
            color="Type:N",
            tooltip=["Type:N", "Count:Q"]
        )
        .properties(height=360)
    )

    st.altair_chart(pie_chart, use_container_width=True)

    st.subheader("4. 可報告結論")

    st.markdown(f"""
### 綜合判斷

6/24–6/27 的 GMV 數據顯示，店舖總 GMV 並不是單純上升或下降，而是成交來源發生轉移。

6/25 到 6/26：

- Shop GMV 幾乎持平
- Creator Content 占比從 **26.3%** 提升到 **41.2%**
- Seller Content 占比從 **48.6%** 下降到 **36.6%**

這代表 TikTok 可能正在重新分配 Buyer Flow，把更多高購買意圖流量導向 Creator Content。

同時，6/19–6/27 共發布 **{all_total}** 支影片，其中 S / AK / AS 強內容共 **{strong_total}** 支，占比 **{strong_rate:.1f}%**。

如果 Creator Content 占比能持續維持在 40% 左右，代表平台可能開始更信任達人內容的轉化能力，後續應優先複製高質量 S / AK / AS 類型內容，並加強深達和廣達的內容標準化。
""")


# =========================
# Page 4: Raw Data
# =========================

elif page == "📋 Raw Data":
    st.title("📋 Raw Data")

    st.subheader("整理後影片資料")
    st.dataframe(video_df, use_container_width=True)

    st.subheader("Scenario 統計表")
    st.dataframe(count_table, use_container_width=True)

    st.subheader("GMV 資料")
    st.dataframe(gmv_df, use_container_width=True)

    csv = count_table.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="下載 Scenario 統計 CSV",
        data=csv,
        file_name="scenario_count_20260619_20260627.csv",
        mime="text/csv"
    )
