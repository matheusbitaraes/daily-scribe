#!/bin/bash

# Path to the database
DB_PATH="data/digest_history.db"

# Check if a file path is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_sql_file>"
  exit 1
fi

# Check if the provided file exists
if [ ! -f "$1" ]; then
  echo "Error: File not found: $1"
  exit 1
fi

# Execute the SQL query
sqlite3 "$DB_PATH" < "$1"
