# #!/bin/bash

curl -X POST http://localhost:5000/create_stream \
    -H "Content-Type: application/json" \
    -d '{
        "streamer_id": 12345,
        "game": "Example Game",
        "tags": ["tag1", "tag2", "tag3"],
        "title": "Exciting Stream Title"
    }'