from flask import Flask, jsonify, request
from database.rds_database import rds_database
from models import Recommendation_Service_Model
from dataclasses import asdict
from util import * 
import os
from dotenv import load_dotenv
from flask_socketio import SocketIO

load_dotenv()
DB_NAME = os.getenv("RDS_DB_NAME")
BASEDIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
cur_database = rds_database(db_name=DB_NAME)
socketio = SocketIO(app, cors_allowed_origins="*")

''' 
# Route to add new labels for a resource
@app.route('/labels/add', methods=['POST'])
def add_label():
    resource_id = request.headers.get('resource_id')
    label = request.headers.get('label') # Assuming just one label per resource_id for now...
    # label_list = [label.strip() for label in labels.split(',')]
    # label_entries = [asdict(Recommendation_Service_Model.Label(resource_id=int(resource_id), label=label)) for label in label_list]
    # result = cur_database.bulk_insert_data("labels", label_entries)
    label_entry = asdict(Recommendation_Service_Model.Label(resource_id=int(resource_id), label=label.strip()))
    result = cur_database.bulk_insert_data("labels", [label_entry])  # Pass as a list
    return jsonify({"Message": result})
'''


# Route to recommend resources based on a label
@app.route("/labels/recommend/<string:keyword>")
def recommend_resources(keyword):
    result = cur_database.query_data('labels', columns=['resource_id'], conditions={'label': keyword})
    result = serialize_data(result)
    if not result:
        return jsonify({"message": "No matching resources found."})
    resource_ids = [entry['resource_id'] for entry in result]
    return jsonify(resource_ids)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
