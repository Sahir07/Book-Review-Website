import csv
import psycopg2

conn = psycopg2.connect("host=localhost dbname=postgres user=postgres password=raghuram771231")
cur = conn.cursor()

with open('books.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header row.
    for row in reader:
        cur.execute("INSERT INTO book VALUES (%s, %s, %s, %s)",row)
conn.commit()