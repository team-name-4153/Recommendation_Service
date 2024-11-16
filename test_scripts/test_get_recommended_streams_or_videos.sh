# #!/bin/bash

# if user_id exists and has view session, then return recommended based on item-based collaborate filters
# if user_id does not exist, or no view session, or recommended streams/videos are less than n
# return random recommendations (if has k recommendations, the last n-k will be random)
curl -X GET http://localhost:5000/streams/recommend/<user_id>?n=10

curl -X GET http://localhost:5000/videos/recommend/<user_id>
  