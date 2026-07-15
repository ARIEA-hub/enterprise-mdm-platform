import pandas as pd
import recordlinkage
from recordlinkage.index import Block

def clean_data(df):
    """Standardizes incoming text fields to ensure reliable comparisons."""
    # Convert text columns to uppercase, remove leading/trailing spaces
    for col in ['first_name', 'last_name', 'email', 'company']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            
    # Clean phone numbers: remove dashes, spaces, and parentheses
    if 'phone' in df.columns:
        df['phone'] = df['phone'].astype(str).str.replace(r'[\s\-\(\)\+]', '', regex=True)
        
    return df

def find_duplicate_clusters(df):
    """Analyzes a dataframe to find records that likely belong to the same person."""
    if df.empty:
        return []

    # 1. Clean data first
    df = clean_data(df)

    # 2. Indexing (Blocking): Only compare records with the exact same first letter of last name
    # This prevents the algorithm from wasting performance comparing everyone against everyone
    df['ln_initial'] = df['last_name'].str[0]
    indexer = Block('ln_initial')
    candidate_pairs = indexer.index(df)

    # 3. Setting up Comparison Weights
    compare = recordlinkage.Compare()
    # Exact match on email
    compare.exact('email', 'email', label='email_score')
    # Fuzzy match on names (accounts for typos like 'Jon' vs 'John')
    compare.string('first_name', 'first_name', method='jarowinkler', threshold=0.85, label='first_name_score')
    compare.string('last_name', 'last_name', method='jarowinkler', threshold=0.85, label='last_name_score')

    # Compute similarity scores across all candidate pairs
    features = compare.compute(candidate_pairs, df)

    # 4. Filter duplicates (records with a total score of 1.85 or higher out of 3.0)
    potential_matches = features[features.sum(axis=1) >= 1.85]
    
    return potential_matches