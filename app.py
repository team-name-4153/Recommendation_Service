import datetime
from flask import Flask, jsonify, request
from database.rds_database import rds_database
from models import Recommendation_Service_Model
from dataclasses import asdict
from util import * 
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
DB_NAME = os.getenv("RDS_DB_NAME")
BASEDIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
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



@app.route('/create_stream', methods=['POST'])
def create_stream():
    data = request.get_json()
    streamer_id = data.get('streamer_id')
    game = data.get('game')
    tags = data.get("tags")
    title = data.get('title', "")
    start_time = datetime.datetime.now()


    if not streamer_id or not game:
        return jsonify({
            'status': 'error',
            'message': 'streamer_id and game are required',
            "data": {}
        }), 400
 
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
    return jsonify({
        'status': 'success',
        'message': 'Store session',
        "data": {
            "session_id": session_id
        }
        }), 200

@app.route('/end_stream', methods=['POST'])
def end_stream():
    data = request.get_json()
    session_id = data.get('session_id')
    streamer_id = data.get('streamer_id')
    end_time = datetime.datetime.now()

    if not streamer_id or not session_id:
        return jsonify({
            'status': 'error',
            'message': 'streamer_id and session_id are required',
            "data": {}
        }), 400

    cur_database.update_data("stream_session",
                            {"end_time": end_time},
                            {"session_id": session_id,
                             "streamer_id": streamer_id},
                        )

    return jsonify({
        'status': 'success',
        'message': 'Updated',
        "data": {}
    }), 200


@app.route('/streams')
def list_streams():
    ITEMS_PER_PAGE = 10
    
    page = int(request.args.get('page', 1))
    
    total_count_query = "SELECT COUNT(*) FROM stream_session WHERE end_time is NULL"
    res = cur_database.custom_query_data(total_count_query)
    total_count = 0
    if res:
        total_count = res[0]['COUNT(*)']
    
    offset = (page - 1) * ITEMS_PER_PAGE
    
    query = f"""
        SELECT * FROM stream_session
        WHERE end_time is NULL
        LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
    """
    streams = cur_database.custom_query_data(query)
    
    base_url = request.base_url
    next_page = f"{base_url}?page={page + 1}" if offset + ITEMS_PER_PAGE < total_count else None
    previous_page = f"{base_url}?page={page - 1}" if page > 1 else None
    
    response = {
        "count": len(streams),
        "total_count": total_count,
        "current": f"{base_url}?page={page}",
        "next": next_page,
        "previous": previous_page,
        "results": streams
    }
    
    return jsonify(response, 200)


@app.route('/videos')
def list_videos():
    ITEMS_PER_PAGE = 10
    
    page = int(request.args.get('page', 1))
    
    total_count_query = "SELECT COUNT(*) FROM stream_session WHERE end_time is not NULL"
    res = cur_database.custom_query_data(total_count_query)
    total_count = 0
    if res:
        total_count = res[0]['COUNT(*)']
    
    offset = (page - 1) * ITEMS_PER_PAGE
    
    query = f"""
        SELECT * FROM stream_session
        WHERE end_time is not NULL
        LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
    """
    streams = cur_database.custom_query_data(query)
    
    base_url = request.base_url
    next_page = f"{base_url}?page={page + 1}" if offset + ITEMS_PER_PAGE < total_count else None
    previous_page = f"{base_url}?page={page - 1}" if page > 1 else None
    
    response = {
        "count": len(streams),
        "total_count": total_count,
        "current": f"{base_url}?page={page}",
        "next": next_page,
        "previous": previous_page,
        "results": streams
    }
    
    return jsonify(response, 200)




@app.route('/store_watch_session', methods=['POST'])
def store_watch_session():
    data = request.get_json()
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    watch_duration = data.get('duration')
    stop_watching_time = data.get('stop_watching_time')

    if not user_id or not session_id or not watch_duration:
        return jsonify({'error': 'user_id and session_id and duration are required'}), 400

    session_data = cur_database.query_data(
        "view_session", 
        ["user_id", "session_id", "watch_duration"], 
        {"user_id": user_id, "session_id": session_id}
    )

    if len(session_data) == 0:
        new_session = {
            "user_id": user_id,
            "session_id": session_id,
            "watch_duration": watch_duration,
            "stop_watching_time": stop_watching_time,
        }
        res = cur_database.bulk_insert_data("view_session", [new_session])
    else:
        watch_duration += session_data[0]['watch_duration']

        res = cur_database.update_data(
            "view_session",
            {
                "watch_duration": watch_duration,
                "stop_watching_time": stop_watching_time   
            },
            {
                "user_id": user_id,
                "session_id": session_id
            }
        )
    return jsonify({
        'status': 'success',
        'message': 'Store session',
        "data": {"result": res}
    }), 200


@app.route("/streams/recommend/<int:user_id>")
def recommend_streams(user_id):
    top_n = int(request.args.get('n', 10))
    query = f'''SELECT
            vs.user_id,
            ss.session_id,
            st.tag_name
        FROM
            stream_session ss
        LEFT JOIN
                view_session vs ON ss.session_id = vs.session_id
        LEFT JOIN
            stream_tag st ON ss.session_id = st.session_id
        WHERE ss.end_time is NULL
            '''
    streams = cur_database.custom_query_data(query)
    result_dict = {}
    for stream in streams:
        ui = stream["user_id"]
        si = stream["session_id"]
        if (ui, si) not in result_dict:
            result_dict[(ui, si)] = []
        result_dict[(ui, si)].append(stream["tag_name"])
    
    res = [[user_id, session_id, tags] for (user_id, session_id), tags in result_dict.items()]
    recommended_stream_ids = recommend_streams_for_user(res, user_id, top_n=top_n)
    formatted_streams = tuple(recommended_stream_ids)
    if len(formatted_streams) == 1:
        formatted_streams = (formatted_streams[0],)
    query = f"""
        SELECT * FROM stream_session
        WHERE session_id IN {formatted_streams}
    """
    recommended_streams = cur_database.custom_query_data(query)
    return jsonify({
        'status': 'success',
        'message': 'OK',
        "data": recommended_streams
    }), 200

@app.route("/videos/recommend/<int:user_id>")
def recommend_videos(user_id):
    top_n = int(request.args.get('n', 10))
    query = f'''SELECT
            vs.user_id,
            ss.session_id,
            st.tag_name
        FROM
            stream_session ss
        LEFT JOIN
                view_session vs ON ss.session_id = vs.session_id
        LEFT JOIN
            stream_tag st ON ss.session_id = st.session_id
        WHERE ss.end_time is not NULL
            '''
    streams = cur_database.custom_query_data(query)
    result_dict = {}
    for stream in streams:
        ui = stream["user_id"]
        si = stream["session_id"]
        if (ui, si) not in result_dict:
            result_dict[(ui, si)] = []
        result_dict[(ui, si)].append(stream["tag_name"])
    
    res = [[user_id, session_id, tags] for (user_id, session_id), tags in result_dict.items()]
    recommended_stream_ids = recommend_streams_for_user(res, user_id, top_n=top_n)
    formatted_streams = tuple(recommended_stream_ids)
    if len(formatted_streams) == 1:
        formatted_streams = (formatted_streams[0],)
    query = f"""
        SELECT * FROM stream_session
        WHERE session_id IN {formatted_streams}
    """
    recommended_streams = cur_database.custom_query_data(query)
    return jsonify({
        'status': 'success',
        'message': 'OK',
        "data": recommended_streams
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
