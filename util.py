from bson import ObjectId
import json
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

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


def recommendation_setup(watch_sessions):
    watch_sessions_df = pd.DataFrame(watch_sessions)
    user_stream_matrix = watch_sessions_df.pivot_table(
        index='user_id', 
        columns='session_id', 
        values='watch_duration', 
        fill_value=0
    )

    user_stream_array = user_stream_matrix.to_numpy()

    stream_similarity_matrix = cosine_similarity(user_stream_array.T)  # Transpose to get stream-based similarity
    stream_similarity_df = pd.DataFrame(
        stream_similarity_matrix, 
        index=user_stream_matrix.columns, 
        columns=user_stream_matrix.columns
    )
    return user_stream_matrix, stream_similarity_df

def get_top_similar_streams(stream_similarity_df, stream_id, n=5):
    """Get top N similar streams to a given stream_id."""
    similar_streams = stream_similarity_df[stream_id].sort_values(ascending=False)
    top_similar = similar_streams[1:n+1].index
    return top_similar

def recommend_streams_for_user(watch_sessions, user_id, top_n=5):
    """Recommend streams for a user based on streams they've watched."""
    user_stream_matrix, stream_similarity_df = recommendation_setup(watch_sessions)
    watched_streams = user_stream_matrix.loc[user_id]
    watched_streams = watched_streams[watched_streams > 0].index

    recommendation_scores = {}

    for stream_id in watched_streams:
        similar_streams = get_top_similar_streams(stream_similarity_df, stream_id)
        for sim_stream in similar_streams:
            if sim_stream not in watched_streams:
                recommendation_scores[sim_stream] = recommendation_scores.get(sim_stream, 0) + stream_similarity_df.loc[stream_id, sim_stream]

    recommended_streams = sorted(recommendation_scores, key=recommendation_scores.get, reverse=True)
    return recommended_streams[:top_n]