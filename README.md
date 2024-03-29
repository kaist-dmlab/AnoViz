# AnoViz: A Visual Inspection Tool of Anomalies in Multivariate Time Series

This is the implementation of a paper published in AAAI 2023 (Demonstration Track) [[Paper](https://ojs.aaai.org/index.php/AAAI/article/view/27088)] [[Video](https://www.youtube.com/watch?v=fOHZO3xiMAA)] [[Poster](https://time-cad.web.app/files/AnoViz_AAAI23_Poster.pdf)] [[Live Demo](https://time-cad.web.app)]

## Citation
```
@inproceedings{AnoVizAAAI,
  title={{AnoViz}: A Visual Inspection Tool of Anomalies in Multivariate Time Series},
  author={Trirat, Patara, and Nam, Youngeun, and Kim, Taeyoon and Lee, Jae-Gil},
  booktitle={Proceedings of the 37th AAAI Conference on Artificial Intelligence},
  pages={16489-16490},
  year={2023}
}
```

## Basic Requirements
### Web Client
- Nodejs v16+ with npm v8+ (See https://nodejs.org/en/)
- Firebase **Web** app (See https://firebase.google.com/docs/firestore/quickstart, *you may use other real-time database services for the stream mode.*)
### API Server
- Python 3.9 with pip v21+ (See https://www.python.org/downloads/)
- Anoconda or Miniconda (See https://www.anaconda.com/products/distribution)

## Installation & Running
### Web Client
```bash
cd client
npm install
# the web application will be accessible at: http://localhost:3000
npm run start
```
#### For self-hosting: 
```bash
npm run build
```
> Then, upload everything in `client/build/` to your web server.
### API Server
```bash
cd server
conda create --name AnoViz python=3.9
conda activate AnoViz
pip install -r requirements.txt
```
#### For running the servers:
```bash
bash startup.sh
```
or
```bash
# to run "Anomaly Detector" server
python -u anomaly_detector.py
# to run "Computation API" server, the api server will be accessible at: http://localhost:5555
python -u api_server.py
```
#### For stream simulation:
```bash
# from scratch, i.e., first batch of data stream
python -u simulator.py --action run --collection data_streams --limit 360
# after the run command, use append instead
python -u simulator.py --action append --collection data_streams --limit 36
```
> These commands are for **Firebase**-based services. You may modify the code depending on your use cases.



## Acknowledgments
<img src="https://time-cad.web.app/static/media/samsung_logo.27a04fee8d4a4d941f86.png"  width="128">
This work was supported by Mobile eXperience Business, Samsung Electronics Co., Ltd. (Real-time Service Incident Prediction Development).
