python stream/streaming_server.py > /dev/null & 
stream=$!
python stream/worker.py > /dev/null &
worker=$!
trap "kill $stream $worker" SIGINT
python application.py
