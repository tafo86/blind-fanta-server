import csv
import sqlite3

csv_file = "Lista-FantaAsta-Fantacalcio.csv"


def record_iterator(reader):
    for row in reader:
        yield (row[1], row[2], row[14][:10], row[3], row[15], row[9])


db_conn = sqlite3.connect("fanta_db.db3")

cursor = db_conn.cursor()

with open(csv_file, mode="r", encoding="utf-8") as csv_file:
    reader = csv.reader(csv_file, delimiter=",")
    cursor.executemany(
        "INSERT INTO player (name, full_name, birth_date, role, img, real_team) VALUES(?, ?, ?, ?, ?, ?)",
        record_iterator(reader),
    )

db_conn.commit()
