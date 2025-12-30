import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="admin",
    password="*******",
    database="servicess_ftth"
)

cursor = db.cursor()
cursor.execute("CALL sync_ftth_table();")
db.commit()
print("✅ Vista aggiornata correttamente.")