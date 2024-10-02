from bson import ObjectId
import json

def serialize_data(data):
    """
    Serializes a list of dictionaries containing MongoDB ObjectId to a JSON serializable format.
    """
    results = []
    for entry in data:
        # Convert each entry to a serializable form
        if '_id' in entry:
            entry['_id'] = str(entry['_id'])  # Convert ObjectId to string
        results.append(entry)
    return results

def build_INSERTION_sql(table_name, **kwargs):
    # Extracting column names and corresponding values from kwargs
    columns = ', '.join(kwargs.keys())
    values = tuple(kwargs.values())
    
    # Creating placeholders for the values in the SQL statement
    placeholders = ', '.join(['%s'] * len(kwargs))
    
    # Constructing the SQL statement
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    # Here you would execute the SQL statement with a cursor
    # Assuming `cursor` is a cursor object connected to your database
    # cursor.execute(sql, values)
    # You may need to handle or log exceptions, and commit the transaction

    # For demonstration, let's print the sql and values that would be used
    print("SQL Statement:", sql)
    print("Values:", values)
    return sql, values