import psycopg2

def get_db_conn():
    conn = psycopg2.connect(database="opentube", 
                        user="postgres", 
                        password="kI1{WB=\'ioBN", 
                        host="localhost", 
                        port="5433")
    return conn