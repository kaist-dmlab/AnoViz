# sh clearup.sh

pkill -f anomaly_detector.py
pkill -f api_server.py


nohup python -u anomaly_detector.py > logs/anomaly_detector.out &
nohup python -u api_server.py > logs/api.out &