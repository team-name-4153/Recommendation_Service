import datetime
from flask import Flask, jsonify, request
from database.rds_database import rds_database
from models import Recommendation_Service_Model, WatchSession
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

@app.route("/start_watch", methods=['POST'])
def user_start_watch():
    data = request.get_json()
    user_id = data.get('user_id')
    stream_id = data.get('stream_id')

    if not user_id or not stream_id:
        return jsonify({'error': 'user_id and stream_id are required'}), 400

    existing_session = cur_database.query_data(
        "watch_session", 
        ["user_id", "stream_id"], 
        {"user_id": user_id, "stream_id": stream_id}
    )

    if len(existing_session) > 0:
        cur_database.update_data(
            "watch_session",
            {
                "watch_start_time": datetime.datetime.now(datetime.timezone.utc),
                "watch_end_time": None
            },
            {
                "user_id": user_id,
                "stream_id": stream_id
            }
        )
        message = "Session updated successfully."
    else:
        new_session = {
            "user_id": user_id,
            "stream_id": stream_id,
            "watch_start_time": datetime.datetime.now(datetime.timezone.utc),
            "watch_end_time": None,
            "duration": 0
        }
        cur_database.bulk_insert_data("watch_session", [new_session])
        message = "Session inserted successfully."

    return jsonify({"message": message}), 200



@app.route('/end_watch', methods=['POST'])
def end_watch():
    data = request.get_json()
    user_id = data.get('user_id')
    stream_id = data.get('stream_id')

    if not user_id or not stream_id:
        return jsonify({'error': 'user_id and stream_id are required'}), 400

    session_data = cur_database.query_data(
        "watch_session", 
        ["user_id", "stream_id", "watch_start_time"], 
        {"user_id": user_id, "stream_id": stream_id}
    )

    if len(session_data) == 0:
        return jsonify({'message': "session does not exist"}), 400

    # Retrieve watch_start_time and calculate duration
    watch_start_time = session_data[0]['watch_start_time']
    watch_end_time = datetime.datetime.now(datetime.timezone.utc)
    duration = (watch_end_time - watch_start_time).total_seconds()

    # Update the session with end time and duration
    cur_database.update_data(
        "watch_session",
        {
            "watch_end_time": watch_end_time,
            "duration": duration     
        },
        {
            "user_id": user_id,
            "stream_id": stream_id
        }
    )

    return jsonify({'message': 'Watch session ended', 'duration': duration}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
