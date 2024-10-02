#!/bin/bash

# Send a GET request to recommend resources based on a label
curl -X GET http://localhost:5001/labels/recommend/comedy
