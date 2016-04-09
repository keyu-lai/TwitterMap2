python streaming_server.py > /dev/null & 
stream=$!
python worker.py > /dev/null &
worker=$!
trap "kill $stream $worker" SIGINT
python application.py
