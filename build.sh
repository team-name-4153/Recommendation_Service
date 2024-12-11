docker system prune
git pull
docker build -t rec_service .
docker run -p 5001:5000 rec_service