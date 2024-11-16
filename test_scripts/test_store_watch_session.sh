curl -X POST http://localhost:5000/store_watch_session \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": 3,
        "session_id": 12,
        "duration": 10
    }'