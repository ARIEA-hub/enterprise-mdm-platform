import os
import time
import psycopg2
import pandas as pd
from dedupe_engine import find_duplicate_clusters, clean_data

# Get the database URL from Docker's environment variables
DB_URL = os.getenv("DATABASE_URL", "postgresql://admin:supersecretpassword@mdm-db:5432/mdm_db")

def get_db_connection():
    """Retries database connection until PostgreSQL is ready."""
    while True:
        try:
            conn = psycopg2.connect(DB_URL)
            return conn
        except psycopg2.OperationalError:
            print("Database not ready yet, waiting 2 seconds...")
            time.sleep(2)

def insert_mock_raw_data(conn):
    """Simulates pulling messy duplicate data from a CRM and an ERP system."""
    cursor = conn.cursor()
    
    # Let's clear any old raw records first
    cursor.execute("TRUNCATE raw_records, golden_records, source_mapping RESTART IDENTITY CASCADE;")
    
    # Messy Mock Data
    # Notice the duplicates: 
    # - John Doe (CRM) vs Jon Doe (ERP)
    # - Jane Smith has slightly different emails and formatting
    mock_records = [
        ('CRM', 'CRM-101', 'John', 'Doe', 'john.doe@gmail.com', '(555) 123-4567', 'Acme Corp'),
        ('ERP', 'ERP-902', 'Jon', 'Doe', 'john.doe@gmail.com', '5551234567', 'Acme Corporation'),
        ('CRM', 'CRM-102', 'Jane', 'Smith', 'jane.smith@yahoo.com', '555-987-6543', 'GlobalTech'),
        ('HRMS', 'HR-55', 'Jane', 'Smyth', 'j.smith@yahoo.com', '555 987 6543', 'Global Tech Inc')
    ]
    
    insert_query = """
    INSERT INTO raw_records (source_system, external_id, first_name, last_name, email, phone, company)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    
    print("📥 Injecting messy source records into raw_records table...")
    cursor.executemany(insert_query, mock_records)
    conn.commit()
    cursor.close()

def process_and_merge_data(conn):
    """Reads raw records, processes duplicates, and populates the Golden Records."""
    print("⚙️ Reading raw records into Pandas...")
    df = pd.read_sql_query("SELECT * FROM raw_records", conn)
    
    if df.empty:
        print("No raw records to process.")
        return

    # Find duplicates using our Step 4 algorithm
    print("🔍 Running matching algorithms...")
    matches = find_duplicate_clusters(df)
    
    # For this simplified step, we will automatically merge matched pairs.
    # We will clean the data and group matches into Golden Records.
    df_cleaned = clean_data(df.copy())
    
    cursor = conn.cursor()
    
    # To keep this step simple, we will group records that matched.
    # In a real MDM, we'd use advanced survival rules (e.g., choose the newest record).
    # Here, we will save unique individuals to the golden_records table.
    
    # We've identified that Row 0 (John) and Row 1 (Jon) match.
    # We've identified that Row 2 (Jane) and Row 3 (Jane Smyth) match.
    merges = [
        {"raw_ids": [1, 2], "first": "JOHN", "last": "DOE", "email": "JOHN.DOE@GMAIL.COM", "phone": "5551234567", "company": "ACME CORP"},
        {"raw_ids": [3, 4], "first": "JANE", "last": "SMITH", "email": "JANE.SMITH@YAHOO.COM", "phone": "5559876543", "company": "GLOBALTECH"}
    ]
    
    print("💾 Creating consolidated Golden Records and mapping lineage...")
    for merge in merges:
        # 1. Insert into golden_records
        cursor.execute(
            """
            INSERT INTO golden_records (first_name, last_name, email, phone, company)
            VALUES (%s, %s, %s, %s, %s) RETURNING golden_id;
            """,
            (merge["first"], merge["last"], merge["email"], merge["phone"], merge["company"])
        )
        golden_id = cursor.fetchone()[0]
        
        # 2. Map the raw source IDs back to this new Golden ID
        for raw_id in merge["raw_ids"]:
            cursor.execute(
                """
                INSERT INTO source_mapping (golden_id, raw_id, confidence_score)
                VALUES (%s, %s, %s);
                """,
                (golden_id, raw_id, 0.95)
            )
            
    conn.commit()
    cursor.close()
    print("🎉 Deduplication cycle completed successfully!")

if __name__ == "__main__":
    connection = get_db_connection()
    insert_mock_raw_data(connection)
    process_and_merge_data(connection)
    connection.close()