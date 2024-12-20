import datetime
from flask import Flask, jsonify, make_response, request
from database.rds_database import rds_database
from middleware import token_required
from models import Recommendation_Service_Model
from dataclasses import asdict
from util import * 
import os
from dotenv import load_dotenv
from flask_cors import CORS

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
DB_NAME = os.getenv("RDS_DB_NAME")
BASEDIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": "*",
    }
}, supports_credentials=True)
# CORS(app, resources={
#     r"/*": {
#         "origins": [
#         "https://user-home.d27vaquqa87q60.amplifyapp.com",
#         "https://main.d27vaquqa87q60.amplifyapp.com",
#         "http://localhost:3000",
#     ],
#     }
# }, supports_credentials=True)

cur_database = rds_database(db_name=DB_NAME)

def send_email(to_email, subject, body):
    """Send an email notification."""
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))  # Default to 587 for TLS
    
    try:
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.route('/create_stream', methods=['POST'])
# @token_required
def create_stream():
    data = request.get_json()
    streamer_id = data.get('streamer_id')
    streamer_email = data.get('streamer_email') 
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
        "hls_folder": "",
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
    if streamer_email:
        subject = "Stream Created Successfully!"
        body = f"Your stream '{title}' for the game '{game}' has been successfully created and is now live!"
        send_email(streamer_email, subject, body)
    else:
        print("No email found in cookies, skipping notification.")


    return jsonify({
        'status': 'success',
        'message': 'Store session',
        "data": {
            "session_id": session_id
        }
        })

@app.route('/end_stream', methods=['POST'])
# @token_required
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


@app.route('/games')
def list_games():
    data = request.args
    limit = data.get('limit', 10)
    query = f'''
    select game
    from stream_session
    group by game
    limit {str(limit)}
    '''
    res = cur_database.custom_query_data(query)
    games = []
    for row in res:
        games.append(row["game"])
    
    return jsonify({"games": games}), 200

@app.route('/streams')
def list_streams():
    ITEMS_PER_PAGE = 8
    
    data = request.args
    page = int(data.get('page', 1))
    game = data.get('game', None)
    
    total_count_query = f'''
    SELECT COUNT(*)
    FROM stream_session
    WHERE end_time IS NULL
    {f"and game = '{game}'" if game else ""}
    '''
    res = cur_database.custom_query_data(total_count_query)
    total_count = 0
    if res:
        total_count = res[0]['COUNT(*)']
    
    offset = (page - 1) * ITEMS_PER_PAGE
    
    query = f"""
        SELECT * FROM stream_session
        WHERE end_time IS NULL
        {f"and game = '{game}'" if game else ""}
        LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
    """
    streams = cur_database.custom_query_data(query)
    
    base_url = request.base_url
    current = f"{base_url}?page={page}"
    next_page = f"{base_url}?page={page + 1}" if offset + ITEMS_PER_PAGE < total_count else None
    previous_page = f"{base_url}?page={page - 1}" if page > 1 else None
    if game:
        current += "&game=" + game
        if next_page:
            next_page += "&game=" + game
        if previous_page:
            previous_page += "&game=" + game
    
    response = {
        "count": len(streams),
        "total_count": total_count,
        "current": current,
        "next": next_page,
        "previous": previous_page,
        "results": streams
    }
    
    return jsonify(response), 200



@app.route('/videos')
def list_videos():
    ITEMS_PER_PAGE = 8
    
    data = request.args
    page = int(data.get('page', 1))
    game = data.get('game', None)
    
    total_count_query = f'''
    SELECT COUNT(*)
    FROM stream_session
    WHERE end_time IS NOT NULL
    {f"and game = '{game}'" if game else ""}
    '''
    res = cur_database.custom_query_data(total_count_query)
    total_count = 0
    if res:
        total_count = res[0]['COUNT(*)']
    
    offset = (page - 1) * ITEMS_PER_PAGE
    
    query = f"""
        SELECT * FROM stream_session
        WHERE end_time IS NOT NULL
        {f"and game = '{game}'" if game else ""}
        LIMIT {ITEMS_PER_PAGE} OFFSET {offset}
    """
    streams = cur_database.custom_query_data(query)
    
    base_url = request.base_url
    current = f"{base_url}?page={page}"
    next_page = f"{base_url}?page={page + 1}" if offset + ITEMS_PER_PAGE < total_count else None
    previous_page = f"{base_url}?page={page - 1}" if page > 1 else None
    if game:
        current += "&game=" + game
        if next_page:
            next_page += "&game=" + game
        if previous_page:
            previous_page += "&game=" + game
    
    response = {
        "count": len(streams),
        "total_count": total_count,
        "current": current,
        "next": next_page,
        "previous": previous_page,
        "results": streams
    }
    
    return jsonify(response), 200




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



@app.route("/videos/recommend")
def recommend_videos():
    data = request.args
    user_id = data.get('user_id', None)
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'user_id not given',
            "data": []
        }), 400
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
