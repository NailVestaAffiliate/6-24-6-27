import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="NailVesta Weekly GMV Dashboard", layout="wide")

SCENARIO_ORDER = ["S", "AK", "AS", "C", "BK1", "BK2", "BK3", "BK4", "BS1", "BS2", "Haul"]

st.title("NailVesta Weekly GMV Dashboard")
st.caption("GMV × Creator Content × 廣達 / 深達內容結構摘要")

st.sidebar.title("資料設定")

affiliate_file = st.sidebar.file_uploader("上傳廣達 Excel", type=["xlsx"])
deep_file = st.sidebar.file_uploader("上傳深達 Excel", type=["xlsx"])

start_date = st.sidebar.date_input("開始日期", pd.to_datetime("2026-06-19"))
end_date = st.sidebar.date_input("結束日期", pd.to_datetime("2026-06-27"))

START_DATE = pd.to_datetime(start_date)
END_DATE = pd.to_datetime(end_date)
END_DATE_INCLUSIVE = END_DATE + pd.Timedelta(days=1)


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

    text = str(value).upper()
    text = text.replace("SCENARIO", "")
    text = text.replace("：", ":")
    text = text.replace("，", ",")
    text = text.replace(" ", "")
    text = text.replace(".", "")
    text = text.replace("（", "(").replace("）", ")")

    if "BK1" in text:
        return "BK1"
    if "BK2" in text:
        return "BK2"
    if "BK3" in text:
        return "BK3"
    if "BK4" in text:
        return "BK4"
    if "BS1" in text:
        return "BS1"
    if "BS2" in text:
        return "BS2"
    if "HAUL" in text:
        return "Haul"
    if "AK" in text:
        return "AK"
    if "AS" in text:
        return "AS"

    if text in ["S", "S,速投", "S,可深达", "可深达,S", "可深达,S,速投"]:
        return "S"

    if text in ["C", "C,速投"]:
        return "C"

    return None


def filter_by_date(df, date_col):
    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    return data[
        (data[date_col] >= START_DATE) &
        (data[date_col] < END_DATE_INCLUSIVE)
    ].copy()


def summarize_content(df, group_name, date_col, feedback_col):
    data = filter_by_date(df, date_col)
    total_count = len(data)

    data["Scenario"] = data[feedback_col].apply(clean_scenario)
    classified = data[data["Scenario"].notna()].copy()

    summary = (
        classified.groupby("Scenario")
        .size()
        .reset_index(name=group_name)
    )

    return total_count, summary


def make_summary_table(affiliate_summary, deep_summary):
    base = pd.DataFrame({"Scenario": SCENARIO_ORDER})

    table = base.merge(affiliate_summary, on="Scenario", how="left")
    table = table.merge(deep_summary, on="Scenario", how="left")

    for col in ["廣達", "深達"]:
        if col not in table.columns:
            table[col] = 0
        table[col] = table[col].fillna(0).astype(int)

    table["Total"] = table["廣達"] + table["深達"]

    return table[["Scenario", "廣達", "深達", "Total"]]


# =========================
# 固定 GMV 數據
# =========================

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


# =========================
# 讀取內容資料
# =========================

content_ready = False
summary_table = pd.DataFrame()
affiliate_total = 0
deep_total = 0

if affiliate_file and deep_file:
    affiliate_raw = read_excel_auto(affiliate_file, preferred_sheet="Affiliate List")
    deep_raw = read_excel_auto(deep_file, preferred_sheet="深度达人List")

    affiliate_date_col = find_col(affiliate_raw, ["视频发布日期", "發布日期", "Video Publish Date"])
    affiliate_feedback_col = find_col(affiliate_raw, ["内容反馈", "內容反饋"])

    deep_date_col = find_col(deep_raw, ["视频发布日期", "發布日期", "Video Publish Date"])
    deep_feedback_col = find_col(deep_raw, ["视频反馈", "視頻反饋"])

    missing = []

    if not affiliate_date_col:
        missing.append("廣達：找不到日期欄位")
    if not affiliate_feedback_col:
        missing.append("廣達：找不到內容反饋欄位")
    if not deep_date_col:
        missing.append("深達：找不到日期欄位")
    if not deep_feedback_col:
        missing.append("深達：找不到視頻反饋欄位")

    if missing:
        st.error("欄位缺失：\n" + "\n".join(missing))
        st.write("廣達欄位：", list(affiliate_raw.columns))
        st.write("深達欄位：", list(deep_raw.columns))
        st.stop()

    affiliate_total, affiliate_summary = summarize_content(
        affiliate_raw,
        "廣達",
        affiliate_date_col,
        affiliate_feedback_col
    )

    deep_total, deep_summary = summarize_content(
        deep_raw,
        "深達",
        deep_date_col,
        deep_feedback_col
    )

    summary_table = make_summary_table(affiliate_summary, deep_summary)
    content_ready = True


# =========================
# GMV Dashboard
# =========================

st.header("1. GMV Overview")

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

gmv_chart = alt.Chart(gmv_melt).mark_line(point=True).encode(
    x="Date:T",
    y="GMV:Q",
    color="Metric:N",
    tooltip=["Date:T", "Metric:N", "GMV:Q"]
).properties(height=380)

st.altair_chart(gmv_chart, use_container_width=True)

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
).properties(height=380)

st.altair_chart(share_chart, use_container_width=True)


# =========================
# Content Summary
# =========================

st.header("2. 廣達 / 深達內容結構摘要")

if not content_ready:
    st.warning("請先在左側上傳廣達與深達兩個 Excel。")
else:
    total_content = affiliate_total + deep_total

    s_total = int(summary_table.loc[summary_table["Scenario"] == "S", "Total"].sum())
    ak_total = int(summary_table.loc[summary_table["Scenario"] == "AK", "Total"].sum())
    as_total = int(summary_table.loc[summary_table["Scenario"] == "AS", "Total"].sum())
    c_total = int(summary_table.loc[summary_table["Scenario"] == "C", "Total"].sum())

    strong_total = s_total + ak_total + as_total
    classified_total = int(summary_table["Total"].sum())

    strong_rate_total = strong_total / total_content * 100 if total_content else 0
    strong_rate_classified = strong_total / classified_total * 100 if classified_total else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("廣達內容數", affiliate_total)
    c2.metric("深達內容數", deep_total)
    c3.metric("總內容數", total_content)
    c4.metric("已分類內容數", classified_total)

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("S 內容", s_total)
    c6.metric("AK 內容", ak_total)
    c7.metric("AS 內容", as_total)
    c8.metric("C 內容", c_total)

    st.subheader("Scenario Summary")
    st.dataframe(summary_table, use_container_width=True)

    chart_data = summary_table.melt(
        id_vars="Scenario",
        value_vars=["廣達", "深達"],
        var_name="Group",
        value_name="Count"
    )

    scenario_chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Scenario:N", sort=SCENARIO_ORDER),
        y="Count:Q",
        color="Group:N",
        xOffset="Group:N",
        tooltip=["Scenario:N", "Group:N", "Count:Q"]
    ).properties(height=400)

    st.altair_chart(scenario_chart, use_container_width=True)


    # =========================
    # AI Weekly Report
    # =========================

    st.header("3. AI Weekly Report")

    st.markdown(f"""
### 核心結論

6/19–6/27 共統計 **{total_content}** 條內容。

其中：

- 廣達：**{affiliate_total}** 條
- 深達：**{deep_total}** 條
- 已完成 Scenario 分類：**{classified_total}** 條
- S 內容：**{s_total}** 條
- AK 內容：**{ak_total}** 條
- AS 內容：**{as_total}** 條
- C 內容：**{c_total}** 條
- S / AK / AS 強內容合計：**{strong_total}** 條
- 強內容占總內容比例：**{strong_rate_total:.1f}%**
- 強內容占已分類內容比例：**{strong_rate_classified:.1f}%**

### GMV 端觀察

6/25 到 6/26，Shop GMV 幾乎持平：

- 6/25 Shop GMV：**${gmv_df.loc[1, "Shop GMV"]:,.2f}**
- 6/26 Shop GMV：**${gmv_df.loc[2, "Shop GMV"]:,.2f}**

但成交來源發生明顯轉移：

- Creator Content 占比從 **{gmv_df.loc[1, "Creator %"]:.1f}%** 提升到 **{gmv_df.loc[2, "Creator %"]:.1f}%**
- Seller Content 占比從 **{gmv_df.loc[1, "Seller %"]:.1f}%** 下降到 **{gmv_df.loc[2, "Seller %"]:.1f}%**
- Shop Tab 占比從 **{gmv_df.loc[1, "Shop Tab %"]:.1f}%** 下降到 **{gmv_df.loc[2, "Shop Tab %"]:.1f}%**

### 判斷

這代表店舖 GMV 不是單純放大，而是 TikTok 正在重新分配 Buyer Flow。

6/24–6/25 流量更偏向 Seller Content / Shop Tab，  
6/26–6/27 流量更偏向 Creator Content。

因此，直播組與 Affiliate 不一定會每天同步成長。  
當平台把高購買意圖流量分配給 Seller 側時，Creator 占比可能下降；  
當平台重新判定 Creator Content 效率更高時，Creator 占比就會快速提升。

### 建議

接下來建議持續追蹤：

1. Creator Content 占比是否能穩定維持在 **40% 左右**
2. Seller Content 是否持續下降
3. Shop Tab 是否被 Creator Content 分流
4. S / AK / AS 強內容占比是否與 Creator GMV 提升同步

如果 Creator Content 占比連續一週維持高位，代表 TikTok 可能開始更信任達人內容的轉化能力，後續應優先複製 S / AK / AS 類型內容。
""")

    csv = summary_table.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "下載 Scenario Summary CSV",
        data=csv,
        file_name="scenario_summary_20260619_20260627.csv",
        mime="text/csv"
    )
