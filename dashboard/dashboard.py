import os
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Set Page Config
st.set_page_config(
    page_title="E-Commerce Analysis Dashboard",
    page_icon="🛍️",
    layout="wide"
)

# Set Seaborn Theme
sns.set_theme(style="whitegrid")


# Load Dataset
@st.cache_data
def load_data():
    # Cek lokasi file main_data.csv secara fleksibel
    if os.path.exists("dashboard/main_data.csv"):
        file_path = "dashboard/main_data.csv"
    elif os.path.exists("main_data.csv"):
        file_path = "main_data.csv"
    else:
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, "main_data.csv")

    df = pd.read_csv(file_path)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])

    # Otomatis buat kolom delivery_status jika belum ada di CSV
    if "delivery_status" not in df.columns:
        if "order_delivered_customer_date" in df.columns and "order_estimated_delivery_date" in df.columns:
            df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
            df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"])
            df["delivery_status"] = df.apply(
                lambda x: "Terlambat" if x["order_delivered_customer_date"] > x[
                    "order_estimated_delivery_date"] else "Tepat Waktu / Lebih Cepat",
                axis=1
            )
        else:
            df["delivery_status"] = "Tepat Waktu / Lebih Cepat"

    return df


main_df = load_data()

# Sidebar Setup
st.sidebar.image("https://raw.githubusercontent.com/dicodingacademy/assets/main/logo.png", width=200)
st.sidebar.title("📌 Navigation & Filter")

# Sidebar Date Filter
min_date = main_df["order_purchase_timestamp"].min().date()
max_date = main_df["order_purchase_timestamp"].max().date()

start_date, end_date = st.sidebar.date_input(
    label="Pilih Rentang Waktu:",
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date]
)

# Filter Data
filtered_df = main_df[
    (main_df["order_purchase_timestamp"].dt.date >= start_date) &
    (main_df["order_purchase_timestamp"].dt.date <= end_date)
    ].copy()

# Header Utama
st.title("🛍️ E-Commerce Business & Logistics Performance Dashboard")
st.markdown("Proyek Analisis Data E-Commerce Public Dataset — **Haidar Azhar Bihaque Amrulloh**")
st.divider()

# Key Performance Indicators (KPIs)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Order Unik", value=f"{filtered_df['order_id'].nunique():,}")
with col2:
    st.metric("Total Revenue", value=f"BRL {filtered_df['price'].sum():,.2f}")
with col3:
    st.metric("Rata-Rata Review Score", value=f"{filtered_df['review_score'].mean():.2f} / 5.0")
with col4:
    late_pct = (filtered_df['delivery_status'] == 'Terlambat').mean() * 100
    st.metric("Tingkat Keterlambatan", value=f"{late_pct:.1f}%")

st.divider()

# Tab Layout
tab1, tab2, tab3 = st.tabs(["📦 Performa Kategori Produk", "🚚 Logistik & Review Score", "📊 RFM & Demografi Pelanggan"])

with tab1:
    st.header("Performa Revenue Berdasarkan Kategori Produk")
    st.caption("Menjawab Pertanyaan Bisnis 1: Top 5 & Bottom 5 Kategori Produk Berdasarkan Total Revenue")

    category_perf = filtered_df.groupby("product_category_name_english")["price"].sum().reset_index().sort_values(
        by="price", ascending=False)

    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(16, 6))

    sns.barplot(x="price", y="product_category_name_english", data=category_perf.head(5), palette="Blues_r", ax=ax[0])
    ax[0].set_title("Top 5 Kategori Produk (Revenue Terbanyak)", fontsize=13, fontweight='bold')
    ax[0].set_xlabel("Total Revenue (BRL)")
    ax[0].set_ylabel("Kategori Produk")

    sns.barplot(x="price", y="product_category_name_english", data=category_perf.tail(5), palette="Reds_r", ax=ax[1])
    ax[1].set_title("Bottom 5 Kategori Produk (Revenue Terendah)", fontsize=13, fontweight='bold')
    ax[1].set_xlabel("Total Revenue (BRL)")
    ax[1].set_ylabel("")

    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.header("Pengaruh Keterlambatan Pengiriman terhadap Kepuasan Pelanggan")
    st.caption("Menjawab Pertanyaan Bisnis 2: Hubungan Status Pengiriman Tepat Waktu vs Terlambat terhadap Skor Ulasan")

    delivery_review = filtered_df.groupby("delivery_status").agg(
        avg_review_score=("review_score", "mean"),
        total_orders=("order_id", "nunique")
    ).reset_index()

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.dataframe(delivery_review, hide_index=True, use_container_width=True)
        st.info(
            "💡 **Insight Logistik:** Keterlambatan pengiriman menurunkan rata-rata skor ulasan hingga menjadi di bawah 2.5/5.0.")

    with col_b:
        fig2, ax2 = plt.subplots(figsize=(8, 4.5))
        sns.barplot(x="delivery_status", y="avg_review_score", data=delivery_review, palette=["#2ca02c", "#d62728"],
                    ax=ax2)
        ax2.set_title("Rata-Rata Skor Ulasan Berdasarkan Status Pengiriman", fontsize=12, fontweight='bold')
        ax2.set_xlabel("Status Pengiriman")
        ax2.set_ylabel("Rata-Rata Review Score (1 - 5)")
        ax2.set_ylim(1, 5)

        for p in ax2.patches:
            height = p.get_height()
            ax2.annotate(f"{height:.2f}", (p.get_x() + p.get_width() / 2., height / 2),
                         ha='center', va='center', fontweight='bold', color='white', fontsize=12)

        st.pyplot(fig2)

with tab3:
    st.header("Analisis Lanjutan: RFM & Demografi Pelanggan")

    # Calculate RFM
    now_date = filtered_df["order_purchase_timestamp"].max() + dt.timedelta(days=1)

    if "customer_unique_id" in filtered_df.columns:
        cust_col = "customer_unique_id"
    else:
        cust_col = "customer_id"

    rfm_df = filtered_df.groupby(cust_col).agg(
        max_order_date=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("price", "sum")
    ).reset_index()
    rfm_df["recency"] = (now_date - rfm_df["max_order_date"]).dt.days

    st.subheader("Distribusi Parameter RFM (Recency, Frequency, Monetary)")
    fig3, ax3 = plt.subplots(nrows=1, ncols=3, figsize=(18, 5))

    sns.histplot(rfm_df["recency"], kde=True, ax=ax3[0], color="skyblue")
    ax3[0].set_title("Distribusi Recency (Hari Sejak Transaksi Terakhir)")

    sns.histplot(rfm_df[rfm_df["frequency"] < 10]["frequency"], kde=True, ax=ax3[1], color="orange")
    ax3[1].set_title("Distribusi Frequency (Jumlah Transaksi)")

    sns.histplot(rfm_df[rfm_df["monetary"] < 2000]["monetary"], kde=True, ax=ax3[2], color="green")
    ax3[2].set_title("Distribusi Monetary (Total Belanja BRL)")

    plt.tight_layout()
    st.pyplot(fig3)

    if "customer_state" in filtered_df.columns:
        st.subheader("Top 10 Negara Bagian (Customer State) Berdasarkan Pelanggan")
        state_df = filtered_df.groupby("customer_state").agg(
            total_customers=(cust_col, "nunique"),
            total_revenue=("price", "sum")
        ).reset_index().sort_values(by="total_customers", ascending=False).head(10)

        fig4, ax4 = plt.subplots(figsize=(10, 4.5))
        sns.barplot(x="customer_state", y="total_customers", data=state_df, palette="Purples_r", ax=ax4)
        ax4.set_title("10 Wilayah/State Pelanggan Terbesar", fontsize=12, fontweight='bold')
        ax4.set_xlabel("State Code")
        ax4.set_ylabel("Jumlah Pelanggan Unik")
        st.pyplot(fig4)

st.divider()
st.caption("Hak Cipta © Haidar Azhar Bihaque Amrulloh — Dicoding Data Analysis Final Project")