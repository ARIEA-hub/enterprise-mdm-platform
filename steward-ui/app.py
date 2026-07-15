import streamlit as pd_st
import pandas as pd
import psycopg2
import os

# Get the database URL from Docker's environment variables
DB_URL = os.getenv("DATABASE_URL", "postgresql://admin:supersecretpassword@mdm-db:5432/mdm_db")

def get_data(query):
    """Connects to the DB, runs a query, and returns a Pandas DataFrame."""
    try:
        conn = psycopg2.connect(DB_URL)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        pd_st.error(f"Error connecting to database: {e}")
        return pd.DataFrame()

# Set up the webpage header
pd_st.set_page_config(layout="wide", page_title="MDM Data Steward Portal")
pd_st.title("🛡️ Enterprise Master Data Management (MDM) Portal")
pd_st.subheader("Data Steward & Business Analyst Command Center")

# Create navigation tabs
tab1, tab2, tab3 = pd_st.tabs(["✨ Golden Records (Master)", "📥 Raw Ingested Records", "🔗 Data Lineage Maps"])

with tab1:
    pd_st.header("Unified Golden Records")
    pd_st.write("This table shows the single source of truth for customer profiles.")
    
    # Query the clean master table
    df_golden = get_data("SELECT golden_id, first_name, last_name, email, phone, company, updated_at FROM golden_records")
    if not df_golden.empty:
        pd_st.dataframe(df_golden, use_container_width=True)
    else:
        pd_st.warning("No Golden Records generated yet. Run the matching engine first!")

with tab2:
    pd_st.header("Raw Staged Records")
    pd_st.write("This represents messy, unfiltered input data from ERP, CRM, and HRMS systems.")
    
    df_raw = get_data("SELECT raw_id, source_system, external_id, first_name, last_name, email, phone, company FROM raw_records")
    if not df_raw.empty:
        pd_st.dataframe(df_raw, use_container_width=True)
    else:
        pd_st.warning("Raw records staging table is currently empty.")

with tab3:
    pd_st.header("System Lineage Mapping")
    pd_st.write("Understand which source systems contributed to each Golden Record.")
    
    # Query to join the tables and show lineage
    lineage_query = """
        SELECT 
            g.golden_id,
            g.first_name || ' ' || g.last_name AS golden_name,
            r.source_system,
            r.external_id AS original_system_id,
            r.first_name || ' ' || r.last_name AS raw_name,
            m.confidence_score
        FROM source_mapping m
        JOIN golden_records g ON m.golden_id = g.golden_id
        JOIN raw_records r ON m.raw_id = r.raw_id
        ORDER BY g.golden_id;
    """
    df_lineage = get_data(lineage_query)
    if not df_lineage.empty:
        pd_st.dataframe(df_lineage, use_container_width=True)
    else:
        pd_st.warning("No lineage mapping paths found.")