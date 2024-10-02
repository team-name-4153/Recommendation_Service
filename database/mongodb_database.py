from dotenv import load_dotenv
import os
from typing import List
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dataclasses import asdict

load_dotenv()

class database:
    def __init__(self, collection_name="Comment_Service"):
        # CONNECTION_URI is the connection string you copied from mongodb tutorial
        uri = os.getenv('CONNECTION_URI')
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.collection = self.client[collection_name]


    # Input must be dataclasses object
    def add_data(self, data,table_name):
        print("br2")
        table = self.collection[table_name]
        data = asdict(data)
        print("br3")
        result = table.insert_one(data)
        return result
    
    def find_documents(self, table_name,**kwargs):
        results = self.collection[table_name].find(kwargs)
        documents = list(results)
        return documents
