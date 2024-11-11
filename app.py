import datetime
from flask import Flask, jsonify, request
from database.rds_database import rds_database
from models import Recommendation_Service_Model
from dataclasses import asdict
from util import * 
import os
from dotenv import load_dotenv

load_dotenv()
DB_NAME = os.getenv("RDS_DB_NAME")
BASEDIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
cur_database = rds_database(db_name=DB_NAME)

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
# @app.route("/labels/recommend/<string:keyword>")
# def recommend_resources(keyword):
#     result = cur_database.query_data('labels', columns=['resource_id'], conditions={'label': keyword})
#     result = serialize_data(result)
#     if not result:
#         return jsonify({"message": "No matching resources found."})
#     resource_ids = [entry['resource_id'] for entry in result]
#     return jsonify(resource_ids)


@app.route('/create_stream', methods=['POST'])
def create_stream():
    data = request.get_json()
    streamer_id = data.get('streamer_id')
    game = data.get('game')
    tags = data.get("tags")
    title = data.get('title', "")
    start_time = datetime.datetime.now()


    if not streamer_id or not game:
        return jsonify({'error': 'streamer_id and game are required'}), 400
 
    new_session = {
        "streamer_id": streamer_id,
        "game": game,
        "title": title,
        "start_time": start_time,
        "hls_folder": "", # a placeholder...
    }
    session_id = cur_database.insert_data_return_id("stream_session", new_session)

    hls_folder = f"storage/videos/{streamer_id}/{session_id}"
    cur_database.update_data("stream_session", {"hls_folder": hls_folder}, {"session_id": session_id, "streamer_id": streamer_id})

    new_tags_session = []
    for tag in tags:
        new_session = {
            "session_id": session_id,
            "tag_name": tag,
        }
        new_tags_session.append(new_session)
    cur_database.bulk_insert_data("stream_tag", new_tags_session)
    return jsonify({'message': 'Store session', "session_id": session_id}), 200

@app.route('/end_stream', methods=['POST'])
def create_stream():
    data = request.get_json()
    session_id = data.get('session_id')
    streamer_id = data.get('streamer_id')
    end_time = datetime.datetime.now()

    cur_database.update_data("stream_session",
                            {"end_time": end_time},
                            {"session_id": session_id,
                             "streamer_id": streamer_id},
                        )

    return jsonify({'message': 'Updated'}), 200


@app.route('/streams')
def list_streams():
    streams = cur_database.custom_query_data("SELECT * FROM stream_session WHERE end_time is NULL")
    return {'streams': streams}

@app.route('/videos')
def list_videos():
    streams = cur_database.custom_query_data("SELECT * FROM stream_session WHERE end_time is not NULL")
    return {'videos': streams}



@app.route('/store_watch_session', methods=['POST'])
def store_watch_session():
    data = request.get_json()
    user_id = data.get('user_id')
    session_id = data.get('stream_id')
    watch_duration = data.get('duration')
    stop_watching_time = data.get('stop_watching_time')

    if not user_id or not session_id or not watch_duration:
        return jsonify({'error': 'user_id and stream_id and duration are required'}), 400

    session_data = cur_database.query_data(
        "view_session", 
        ["user_id", "session_id", "watch_duration"], 
        {"user_id": user_id, "session_id": session_id}
    )

    if len(session_data) == 0:
        new_session = {
            "user_id": user_id,
            "session_id": session_id,
            "duration": watch_duration,
            "stop_watching_time": stop_watching_time,
        }
        cur_database.bulk_insert_data("watch_session", [new_session])
    else:
        watch_duration += session_data[0]['watch_duration']

        cur_database.update_data(
            "watch_session",
            {
                "watch_duration": watch_duration,
                "stop_watching_time": stop_watching_time   
            },
            {
                "user_id": user_id,
                "session_id": session_id
            }
        )
    return jsonify({'message': 'Store session', 'duration': watch_duration}), 200


@app.route("/streams/recommend/<int:user_id>")
def recommend_streams(user_id):
    res = cur_database.query_data("watch_session", ["user_id", "session_id", "watch_duration"])
    recommended_streams = recommend_streams_for_user(res, user_id)
    return jsonify(recommended_streams)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
