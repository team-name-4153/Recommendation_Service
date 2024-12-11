
import json
import sys
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
import pandas as pd
import random
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


def recommendation_setup(watch_sessions):
    watch_sessions_df = pd.DataFrame(watch_sessions, columns=['user_id', 'session_id', 'tags'])
    
    # Convert tags to tuple, handle empty or None tags
    watch_sessions_df['tags'] = watch_sessions_df['tags'].apply(lambda x: tuple(x) if x else ())
    
    tag_data = watch_sessions_df[['session_id', 'tags']].drop_duplicates()
    if tag_data.empty or tag_data['tags'].isnull().all():
        raise ValueError("Tags data is missing or empty.")
    
    # Clean tags: set to None if empty or first tag is None
    tag_data['tags'] = tag_data['tags'].apply(
        lambda tags: None if (not tags or tags[0] is None) else tags
    )
    
    # Ensure alignment by dropping rows where 'tags' is None
    non_null_tag_data = tag_data.dropna(subset=['tags'])
    
    if non_null_tag_data.empty:
        raise ValueError("No tags were provided to compute similarities.")
    # Use MultiLabelBinarizer for one-hot encoding
    mlb = MultiLabelBinarizer()
    tag_vectorized = pd.DataFrame(mlb.fit_transform(non_null_tag_data['tags']),
                                  columns=mlb.classes_,
                                  index=non_null_tag_data['session_id'])
    # Handle sessions without tags by assigning zero vectors
    all_session_ids = tag_data['session_id']
    sessions_without_tags = tag_data[tag_data['tags'].isnull()]['session_id']
    
    # Create zero vectors for sessions without tags
    zero_vectors = pd.DataFrame(0, index=sessions_without_tags, columns=mlb.classes_)
    
    # Combine tag_vectorized with zero_vectors
    tag_vectorized = pd.concat([tag_vectorized, zero_vectors])
    
    # Sort the tag_vectorized index to match stream_similarity_df later
    tag_vectorized = tag_vectorized.sort_index()
    
    if tag_vectorized.empty:
        raise ValueError("No tags were provided to compute similarities.")
    
    # Compute tag similarity using cosine similarity
    tag_similarity_matrix = cosine_similarity(tag_vectorized)
    
    tag_similarity_df = pd.DataFrame(
        tag_similarity_matrix,
        index=tag_vectorized.index,
        columns=tag_vectorized.index
    )
    
    # Create user-stream interaction matrix
    user_stream_matrix = watch_sessions_df.pivot_table(
        index='user_id', 
        columns='session_id', 
        aggfunc='size', 
        fill_value=0
    )
    if len(user_stream_matrix) == 0:
        raise ValueError("No view sessions.")
    
    # Compute stream similarity based on user interactions
    user_stream_array = user_stream_matrix.to_numpy()
    stream_similarity_matrix = cosine_similarity(user_stream_array.T)
    stream_similarity_df = pd.DataFrame(
        stream_similarity_matrix, 
        index=user_stream_matrix.columns, 
        columns=user_stream_matrix.columns
    )
    
    # Align indices before combining
    common_sessions = stream_similarity_df.index.intersection(tag_similarity_df.index)
    stream_similarity_df = stream_similarity_df.loc[common_sessions, common_sessions]
    tag_similarity_df = tag_similarity_df.loc[common_sessions, common_sessions]
    
    # Combine similarities
    combined_similarity_df = (stream_similarity_df + tag_similarity_df) / 2
    
    return user_stream_matrix, combined_similarity_df



def get_top_similar_streams(stream_similarity_df, stream_id, n=5):
    """Get top N similar streams to a given stream_id."""
    similar_streams = stream_similarity_df[stream_id].sort_values(ascending=False)
    top_similar = similar_streams[1:n+1].index
    return top_similar


def recommend_streams_for_user(watch_sessions, user_id, top_n=5):

    """Recommend streams for a user based on streams they've interacted with."""
    recommended_streams_ids = []
    try:
        user_stream_matrix, stream_similarity_df = recommendation_setup(watch_sessions)
        if user_id in user_stream_matrix.index:
            watched_streams = user_stream_matrix.loc[user_id]
            watched_streams = watched_streams[watched_streams > 0].index

            recommendation_scores = {}

            for stream_id in watched_streams:
                similar_streams = get_top_similar_streams(stream_similarity_df, stream_id)
                for sim_stream in similar_streams:
                    if sim_stream not in watched_streams:
                        recommendation_scores[sim_stream] = recommendation_scores.get(sim_stream, 0) + stream_similarity_df.loc[stream_id, sim_stream]

            recommended_streams = sorted(recommendation_scores, key=recommendation_scores.get, reverse=True)
            recommended_streams_ids = recommended_streams[:top_n]

    except:
        pass

    remaining_slots = top_n - len(recommended_streams_ids)
    if remaining_slots > 0:
        all_stream_ids = set(s[1]for s in watch_sessions)
        selected_streams = set(recommended_streams_ids)
        not_selected = all_stream_ids.difference(selected_streams)
        random_recommendations = random.sample(not_selected, min(len(not_selected), remaining_slots))
        recommended_streams_ids.extend(random_recommendations)


    return recommended_streams_ids
