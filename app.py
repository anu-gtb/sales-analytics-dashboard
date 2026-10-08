import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(
    page_title="AdventureWorks Analytics Portal",
    page_icon="📊",
    layout="wide"
)

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

st.title("AdventureWorks Enterprise Analytics Portal")
st.markdown("Select a page from the sidebar navigation panel to explore detailed visualizations and metrics.")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Revenue", f"${df['total_sales'].sum():,.2f}")
with col2:
    st.metric("Total Order Quantity", f"{int(df['order_quantity'].sum()):,}")