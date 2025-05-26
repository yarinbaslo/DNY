import mysql.connector
from datetime import datetime

# Replace with your actual RDS endpoint and credentials
db = mysql.connector.connect(
    host="dny-db.c5gkcuoaa00c.eu-north-1.rds.amazonaws.com",
    user="admin",
    password="Yarin218!",
    database="dns_logger"
)

cursor = db.cursor()

def log_dns_query(domain: str, client_ip: str):
    try:
        query = "INSERT INTO dns_logs (domain, client_ip, timestamp) VALUES (%s, %s, %s)"
        cursor.execute(query, (domain, client_ip, datetime.utcnow()))
        db.commit()
    except Exception as e:
        print(f"DB Logging Error: {e}")
