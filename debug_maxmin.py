#!/usr/bin/env python3
"""
Debug script to check max/min processing
"""
import pandas as pd
from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers
from powertech_tools.data.processor import compute_maxmin_template

# Load your merged file
print("Loading file...")
file_path = input("Enter path to your merged file: ").strip()

df = load_table_allow_duplicate_headers(file_path)

print(f"\n✓ File loaded successfully!")
print(f"  Rows: {len(df)}")
print(f"  Columns: {list(df.columns)}")

# Check cycle column
print("\n--- CYCLE COLUMN ANALYSIS ---")
cycle_col = input("Which column is the Cycle column? (e.g., 'Cycle'): ").strip()

if cycle_col in df.columns:
    unique_cycles = df[cycle_col].unique()
    print(f"  Unique cycles found: {len(unique_cycles)}")
    print(f"  Cycle values: {sorted(unique_cycles)}")

    # Count rows per cycle
    cycle_counts = df[cycle_col].value_counts().sort_index()
    print(f"\n  Rows per cycle:")
    for cyc, count in cycle_counts.head(10).items():
        print(f"    Cycle {cyc}: {count} rows")
    if len(cycle_counts) > 10:
        print(f"    ... and {len(cycle_counts) - 10} more cycles")
else:
    print(f"  ERROR: Column '{cycle_col}' not found!")
    exit(1)

# Check time column
print("\n--- TIME COLUMN ANALYSIS ---")
time_col = input("Which column is the Time column? (e.g., 'Time' or 'Date  Time'): ").strip()

if time_col in df.columns:
    print(f"  ✓ Time column '{time_col}' found")
    print(f"  Sample values: {df[time_col].head(3).tolist()}")
else:
    print(f"  ERROR: Column '{time_col}' not found!")
    print(f"  Available columns: {list(df.columns)}")
    exit(1)

# Run the max/min computation
print("\n--- RUNNING MAX/MIN COMPUTATION ---")
result = compute_maxmin_template(df, time_col, cycle_col)

print(f"\n✓ Max/Min computation complete!")
print(f"  Output rows: {len(result)}")
print(f"  Output columns: {len(result.columns)}")
print(f"\nFirst few rows:")
print(result.head(10))

# Save option
save = input("\nSave output? (y/n): ").strip().lower()
if save == 'y':
    out_path = input("Enter output path: ").strip()
    result.to_csv(out_path, sep='\t', index=False)
    print(f"✓ Saved to {out_path}")
