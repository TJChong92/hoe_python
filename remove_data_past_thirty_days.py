import mysql.connector as mariadb
from datetime import datetime, timedelta

# Connect to the database

def fetch_data_from_database():
    try:
        # Connect to MariaDB using username and password
        db = mariadb.connect(user='root', password='syswelliot', host='127.0.0.1', database='myhoepharma', port='3306')

        # Calculate the date threshold (1 month ago)
        one_month_ago = datetime.now() - timedelta(days=30)

        # Delete records older than one month
        delete_query = f"DELETE FROM pharma_table_new WHERE created_at < '{one_month_ago}'"
        db_cursor = db.cursor()
        db_cursor.execute(delete_query)
        db.commit()

# Close the database connection
        db_cursor.close()
        db.close()

    except mariadb.Error as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_data_from_database()


