#!/usr/bin/env python3
"""Create shareholders table + insert initial data."""
import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import execute, query

# Create table
execute("""
CREATE TABLE IF NOT EXISTS shareholders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  role VARCHAR(50) DEFAULT 'Shareholder',
  capital_contribution DECIMAL(15,0) DEFAULT 0,
  ownership_pct DECIMAL(5,2) DEFAULT 0,
  notes TEXT DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
""")
print('Table created')

# Check if data exists
rows = query("SELECT COUNT(*) as c FROM shareholders")
if rows and rows[0]['c'] == 0:
    execute("""
    INSERT INTO shareholders (name, role, capital_contribution, ownership_pct, notes)
    VALUES (%s, %s, %s, %s, %s)
    """, ('Aung Chan Myint', 'Founder', 300000000, 100.00, 'Initial capital from KBZ Bank'))
    print('Initial data inserted')
else:
    print(f'Data exists ({rows[0]["c"]} rows), skipping insert')

# Verify
rows = query("SELECT * FROM shareholders")
for r in rows:
    print(f'  #{r["id"]}: {r["name"]} ({r["role"]}) - {r["capital_contribution"]:,} Ks @ {r["ownership_pct"]}%')
