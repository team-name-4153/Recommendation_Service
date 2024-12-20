import sys
import pymysql
from dotenv import load_dotenv
import os
from pymysql import OperationalError, MySQLError, InternalError
from util import *



load_dotenv()
HOST = os.getenv("RDS_HOST")
PORT = os.getenv("RDS_PORT")
USER = os.getenv("RDS_USER")
PASSWORD = os.getenv("RDS_PASSWORD")

class rds_database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connect()

    
    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                db=self.db_name,
                port=3306,
            )
            print("Connection established successfully!")
        except MySQLError as e:
            print(f"Error connecting to the database: {e}", file=sys.stderr)
            sys.exit(1)

    def reconnect(self):
        try:
            self.conn.close()
        except:
            pass
        self.connect()


    def insert_data_return_id(self, table_name, record):
        if not record:
            return "No record to insert."

        columns = ', '.join(record.keys())
        placeholders = ', '.join(['%s'] * len(record))

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        values = tuple(record.values())

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, values)
                self.conn.commit()
                last_id = cursor.lastrowid

            print(f"Successfully inserted record into {table_name} with ID {last_id}.")
            return last_id
        except (OperationalError, InternalError) as e:
            print("Connection lost. Attempting to reconnect...", file=sys.stderr)
            self.reconnect()
            return self.insert_data_return_id(table_name, record)
        except Exception as e:
            print(f"Error inserting record: {e}")
            return str(e)

    # Example usage:
    # self.bulk_insert_data([{'username': 'alice', 'age': 30}, {'username': 'bob', 'age': 25}])
    def bulk_insert_data(self,table_name, records):
        if not records:
            return "No records to insert."
        columns = ', '.join(records[0].keys())
        placeholders = ', '.join(['%s'] * len(records[0]))

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        values = [tuple(record.values()) for record in records]

        try:
            with self.conn.cursor() as cursor:
                cursor.executemany(sql, values)
                self.conn.commit()
                print(f"Successfully inserted {len(records)} records into {table_name}.")
                return "Success"
        except (OperationalError, InternalError) as e:
            print("Connection lost. Attempting to reconnect...", file=sys.stderr)
            self.reconnect()
            return self.bulk_insert_data(table_name, records)
        except Exception as e:
            print(f"Error inserting records: {e}")
            return str(e)
        

    # Example usage:
    # self.update_data('users', {'age': 31}, {'username': 'alice'})
    def update_data(self, table_name ,set_values, conditions):
        set_clause = ', '.join([f"{key} = %s" for key in set_values.keys()])
        set_values_list = list(set_values.values())

        condition_clause = ' AND '.join([f"{key} = %s" for key in conditions.keys()])
        condition_values_list = list(conditions.values())

        values = set_values_list + condition_values_list

        sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition_clause}"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, values)
                self.conn.commit()
                print(f"Successfully updated records in {table_name}.")
                return "Success"
        except (OperationalError, InternalError) as e:
            print("Connection lost. Attempting to reconnect...", file=sys.stderr)
            self.reconnect()
            return self.update_data(table_name, set_values, conditions)
        except Exception as e:
            print(f"Error updating records: {e}")
            return str(e)

    # Example usage:
    # query results for all users with username 'alice' specifying desired columns
    # results = self.query_data('users', columns=['username', 'age'], conditions={'username': 'alice'})
    # print(results)

    # query all data from a table without conditions
    # all_users = self.query_data('users')
    # print(all_users)
    def query_data(self,table_name,columns=None, conditions=None):
        columns_clause = ', '.join(columns) if columns else '*'
        if conditions:
            condition_clauses = ' AND '.join([f"{key} = %s" for key in conditions.keys()])
            condition_values = list(conditions.values())
            sql = f"SELECT {columns_clause} FROM {table_name} WHERE {condition_clauses}"
        else:
            sql = f"SELECT {columns_clause} FROM {table_name}"

        # Executing the query
        try:
            with self.conn.cursor() as cursor:
                if conditions:
                    cursor.execute(sql, condition_values)
                else:
                    cursor.execute(sql)
                records = cursor.fetchall()
                res = []
                if records:
                    columns = [desc[0] for desc in cursor.description]
                    res = [dict(zip(columns, record)) for record in records]
                return res
        except (OperationalError, InternalError) as e:
            print("Connection lost. Attempting to reconnect...", file=sys.stderr)
            self.reconnect()
            return self.query_data(table_name, columns, conditions)
        except Exception as e:
            print(f"Error querying data: {e}")
            return []


    def custom_query_data(self, sql):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                records = cursor.fetchall()
                res = []
                if records:
                    columns = [desc[0] for desc in cursor.description]
                    res = [dict(zip(columns, record)) for record in records]

                return res
        except (OperationalError, InternalError) as e:
            print("Connection lost. Attempting to reconnect...", file=sys.stderr)
            self.reconnect()
            return self.custom_query_data(sql)
        except Exception as e:
            print(f"Error querying data: {e}", file=sys.stderr)
            return []



