import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Page Configuration
st.set_page_config(
    page_title="AdventureWorks Sales Dashboard",
    page_icon="📈",
    layout="wide"
)

# Database Connection
DB_URI = r'sqlite:///C:/Users/DELL/Documents/PBI_assignment2/data.sqlite'
engine = create_engine(DB_URI)

@st.cache_data
def load_sales_data():
    query = """
        SELECT 
            CAST(s.Year_col AS TEXT) AS calendar_year,
            s.OrderDate AS order_date,
            CAST(s.OrderQuantity AS INTEGER) AS order_quantity, 
            CAST(p.ProductPrice AS REAL) AS product_price,
            COALESCE(cat.SubcategoryName, 'Uncategorized') AS category_name,
            COALESCE(p.ProductName, 'Unknown Product') AS product_name
        FROM sales_data s 
        LEFT JOIN adventureworksproductlookup p ON s.ProductKey = p.ProductKey 
        LEFT JOIN adventureworksproductsubcategorieslookup cat ON p.ProductSubcategoryKey = cat.ProductSubcategoryKey
    """
    with engine.connect() as connection:
        df = pd.read_sql(query, con=connection)
    
    df['order_quantity'] = pd.to_numeric(df['order_quantity'], errors='coerce').fillna(0)
    df['product_price'] = pd.to_numeric(df['product_price'], errors='coerce').fillna(0.0)
    df['total_sales'] = df['order_quantity'] * df['product_price']
    df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    df['month'] = df['order_date'].dt.strftime('%b')
    return df

df = load_sales_data()

# App Title
st.title("📊 AdventureWorks Sales & Analytics Dashboard")
st.markdown("Explore revenue metrics, interactive slicers, visual trends, and detailed product drill-downs in a single view.")

# Sidebar Filters / Slicers
st.sidebar.header("Filter Slicers")
years = ['All'] + sorted(df['calendar_year'].unique().tolist())
categories = ['All'] + sorted(df['category_name'].unique().tolist())

selected_year = st.sidebar.selectbox("Year Filter", years)
selected_category = st.sidebar.selectbox("Category Filter", categories)

# Apply Filter Logic
filtered_df = df.copy()
if selected_year != 'All':
    filtered_df = filtered_df[filtered_df['calendar_year'] == selected_year]
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['category_name'] == selected_category]

# KPI Banner
st.markdown("---")
kpi1, kpi2 = st.columns(2)
total_sales_val = filtered_df['total_sales'].sum()
total_orders_val = filtered_df['order_quantity'].sum()

kpi1.metric("Total Revenue", f"${total_sales_val:,.2f}")
kpi2.metric("Total Order Quantity", f"{int(total_orders_val):,}")
st.markdown("---")

# Visual Charts Section
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Annual Sales Summary")
    annual_summary = filtered_df.groupby('calendar_year')['total_sales'].sum().reset_index()
    st.bar_chart(annual_summary.set_index('calendar_year'), color="#3b82f6")

with col_right:
    st.subheader("Monthly Revenue Trend")
    monthly_summary = filtered_df.dropna(subset=['month']).groupby('month')['total_sales'].sum().reset_index()
    st.line_chart(monthly_summary.set_index('month'), color="#10b981")

# Category Distribution Breakdown
st.subheader("Sales Share by Category")
cat_summary = filtered_df.groupby('category_name')['total_sales'].sum().reset_index().sort_values(by='total_sales', ascending=False)
st.dataframe(cat_summary, use_container_width=True)

# Product Drill-Down Section
st.subheader("Drill-Down View: Top Products")
search_query = st.text_input("Search Product Name for Detailed Inspection")

drill_df = filtered_df.groupby('product_name').agg(
    total_sales=('total_sales', 'sum'),
    total_orders=('order_quantity', 'sum')
).reset_index().sort_values(by='total_sales', ascending=False)

if search_query:
    drill_df = drill_df[drill_df['product_name'].str.contains(search_query, case=False, na=False)]

st.dataframe(drill_df, use_container_width=True)