import streamlit as st
import pandas as pd
#from sqlalchemy import create_engine
import sqlite3
import urllib
import os

DB_PATH = "data.sqlite"
CLOUD_DB_URL = st.secrets['CLOUD_DB_URL']

if not os.path.exists(DB_PATH):
  with st.spinner("Downloading sales database from Hugging Face..."):
    try:
      urllib.request.urlretrieve(CLOUD_DB_URL, DB_PATH)
    except Exception as error:
      st.error(f"Failed to download database: {error}")

st.set_page_config(page_title="Product Drilldown", layout="wide")

DB_URI = r'sqlite:///C:/Users/DELL/Documents/PBI_assignment2/data.sqlite'
#engine = create_engine(DB_URI)

connection = sqlite3.connect(DB_PATH)
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
    df = pd.read_sql(query, con=connection)
    
    df['order_quantity'] = pd.to_numeric(df['order_quantity'], errors='coerce').fillna(0)
    df['product_price'] = pd.to_numeric(df['product_price'], errors='coerce').fillna(0.0)
    df['total_sales'] = df['order_quantity'] * df['product_price']
    return df

df = load_sales_data()

st.header("Product Level Drill-Down Table")
search_query = st.text_input("Search Product Name")

drill_df = df.groupby('product_name').agg(
    total_sales=('total_sales', 'sum'),
    total_orders=('order_quantity', 'sum')
).reset_index().sort_values(by='total_sales', ascending=False)

if search_query:
    drill_df = drill_df[drill_df['product_name'].str.contains(search_query, case=False, na=False)]

st.dataframe(drill_df, use_container_width=True)