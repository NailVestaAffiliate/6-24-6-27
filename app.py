import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NailVesta GMV Channel Analysis", layout="wide")

st.title("NailVesta｜GMV Channel Analysis")
st.caption("6/24–6/27 店舖 GMV、Creator Content、Seller Content、Shop Tab 分析")

data = {
    "Date": ["2026-06-24", "2026-06-25", "2026-06-26", "2026-06-27"],
    "Shop GMV": [8079.80, 9670.46, 9672.34, 6394.94],
    "Creator GMV": [2310.44, 2539.16, 3983.20, 2652.14],
    "Creator %": [28.6, 26.3, 41.2, 41.5],
    "Seller GMV": [3399.10, 4704.54, 3542.73, 2095.35],
    "Seller %": [42.1, 48.6, 36.6, 32.8],
    "Shop Tab %": [29.3, 25.1, 22.2, 25.8],
    "Orders": [214, 239, 264, 168],
    "Items Sold": [319, 398, 395, 256],
}

df = pd.DataFrame(data)
df["Date"] = pd.to_datetime(df["Date"])

st.subheader("1. 核心數據")

col1, col2, col3, col4 = st.columns(4)

col1.metric("最高 Shop GMV", f"${df['Shop GMV'].max():,.2f}")
col2.metric("最高 Creator GMV", f"${df['Creator GMV'].max():,.2f}")
col3.metric("最高 Creator 占比", f"{df['Creator %'].max():.1f}%")
col4.metric("最低 Seller 占比", f"{df['Seller %'].min():.1f}%")

st.dataframe(df, use_container_width=True)

st.subheader("2. Shop GMV vs Creator GMV")

fig1 = px.line(
    df,
    x="Date",
    y=["Shop GMV", "Creator GMV", "Seller GMV"],
    markers=True,
    title="GMV Trend by Channel"
)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("3. GMV 占比變化")

share_df = df.melt(
    id_vars="Date",
    value_vars=["Creator %", "Seller %", "Shop Tab %"],
    var_name="Channel",
    value_name="Contribution %"
)

fig2 = px.line(
    share_df,
    x="Date",
    y="Contribution %",
    color="Channel",
    markers=True,
    title="Channel Contribution % Trend"
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("4. 每日 GMV 組成")

gmv_breakdown = df[["Date", "Creator GMV", "Seller GMV"]].melt(
    id_vars="Date",
    var_name="Channel",
    value_name="GMV"
)

fig3 = px.bar(
    gmv_breakdown,
    x="Date",
    y="GMV",
    color="Channel",
    barmode="stack",
    title="Daily GMV Breakdown"
)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("5. 自動分析結論")

creator_change = df.loc[2, "Creator %"] - df.loc[1, "Creator %"]
seller_change = df.loc[2, "Seller %"] - df.loc[1, "Seller %"]

st.markdown(f"""
### 主要發現

6/25 到 6/26 之間，Shop GMV 幾乎持平：

- 6/25 Shop GMV：${df.loc[1, "Shop GMV"]:,.2f}
- 6/26 Shop GMV：${df.loc[2, "Shop GMV"]:,.2f}

但 GMV 來源發生明顯變化：

- Creator Content 占比從 **{df.loc[1, "Creator %"]:.1f}%** 提升到 **{df.loc[2, "Creator %"]:.1f}%**
- Seller Content 占比從 **{df.loc[1, "Seller %"]:.1f}%** 下降到 **{df.loc[2, "Seller %"]:.1f}%**

這代表店舖總 GMV 並不是大幅增加，而是成交來源從 Seller Content 轉移到 Creator Content。

### 判斷

目前更像是 TikTok 在重新分配 Buyer Flow，而不是直播組與 Affiliate 同步成長。

6/24–6/25：流量偏向 Seller Content / 直播側。  
6/26–6/27：流量偏向 Creator Content / Affiliate 側。

### 建議

後續需要持續觀察 7–14 天：

1. Creator Content 是否穩定維持在 40% 左右。
2. Seller Content 是否持續下降。
3. Shop Tab 是否被 Creator Content 取代。
4. Live GMV 是否和 Creator GMV 呈現此消彼長。
""")

st.subheader("6. 初步結論")

st.info(
    "目前數據顯示，NailVesta 的 Shop GMV 並沒有明顯失控或下滑，真正的變化是 TikTok 將成交來源從 Seller Content 重新分配到 Creator Content。"
)
