import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import altair as alt

st.set_page_config(page_title="Sales Analysis", layout="wide")

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
    return df

df = load_sales_data()

st.sidebar.header("Filter Slicers")
years = ['All'] + sorted(df['calendar_year'].unique().tolist())
categories = ['All'] + sorted(df['category_name'].unique().tolist())

selected_year = st.sidebar.selectbox("Year Filter", years)
selected_category = st.sidebar.selectbox("Category Filter", categories)

filtered_df = df.copy()
if selected_year != 'All':
    filtered_df = filtered_df[filtered_df['calendar_year'] == selected_year]
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['category_name'] == selected_category]
    
if 'month' not in filtered_df.columns:
    filtered_df['order_date'] = pd.to_datetime(filtered_df.get('order_date'), errors='coerce')
    filtered_df['month_num'] = filtered_df['order_date'].dt.month
    filtered_df['month'] = filtered_df['order_date'].dt.strftime('%b').fillna('Unknown')

st.header("Sales Performance Overview")

# Layout columns for visuals
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Annual Sales Summary")
    annual_summary = filtered_df.groupby('calendar_year')['total_sales'].sum().reset_index()
    st.bar_chart(annual_summary.set_index('calendar_year'), color="#3b82f6")
    
with col_right:
    st.subheader("Monthly Revenue Trend")
    monthly_summary = (
        filtered_df.dropna(subset=['month'])
        .groupby(['month_num', 'month'])['total_sales']
        .sum()
        .reset_index()
        .sort_values('month_num')
    )
    
    # Altair chart configuration enabling interactive tooltips and point markers
    chart = alt.Chart(monthly_summary).mark_line(point=True, color="#10b981", strokeWidth=3).encode(
        x=alt.X('month:N', sort=list(monthly_summary['month']), title='Month'),
        y=alt.Y('total_sales:Q', title='Total Sales ($)'),
        tooltip=['month:N', alt.Tooltip('total_sales:Q', format="$,.2f", title='Revenue')]
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)

category_summary = filtered_df.groupby('category_name')['total_sales'].sum().reset_index()
st.subheader("Category Distribution")
st.dataframe(category_summary, use_container_width=True)