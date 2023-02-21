import os, time, datetime, threading, firebase_admin

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ['CUDA_VISIBLE_DEVICES']= "1"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
from detector import detect_anomaly
from decomposition import load_STL_results, decompose_model

from models import *
from data_loader import _create_sequences, _decreate_sequences, _count_anomaly_segments, _wavelet
from data_loader import convert_datetime, get_dummies, add_temporal_info

from tqdm import tqdm
from flask import Flask, flash, request, redirect, url_for, jsonify
from waitress import serve

from firebase_admin import credentials
from firebase_admin import firestore
from configs import var_names, threshold, service_account

dataset_name = 'energy'
stride = 1 
seq_length = 36

SEED = 13
MODEL = "Bi-GRU"
TEMPORAL = 0
DECOMPOSITION = 1 # 0
SEGMENTATION = 0
lamda_t = -0.7
wavelet_num = 3
aux_data = None

detector = tf.keras.models.load_model(f'pretrained_models/AD_{dataset_name}')

def preprocessor(df, seq_length, stride, weight, wavelet_num, historical=False, temporal=False, decomposition=False, segmentation=False):
    x_test = []
    x_test_resid = []
    
    test_df = df
    if temporal == True:
        test_df = np.array(add_temporal_info(dataset_name, test_df, test_df.date))
        test_df = test_df[:, 1:].astype(float)
    else:
        if decomposition == True:
            test_holiday = np.array(add_temporal_info(dataset_name, test_df, test_df.date)['holiday'])
            test_weekend = np.array(add_temporal_info(dataset_name, test_df, test_df.date)['is_weekend'])
            test_temporal = (test_holiday + test_weekend).reshape(-1, 1)
        test_df = np.array(test_df)
        test_df = test_df[:, 1:].astype(float)

        scaler = MinMaxScaler(feature_range=(0, 1))
        test_df = scaler.fit_transform(test_df)

    if decomposition == True:
        stl_loader = load_STL_results(test_df)

        test_seasonal = stl_loader['test_seasonal']
        test_trend = stl_loader['test_trend']
        test_normal = test_seasonal + test_trend
        x_test_normal = _create_sequences(test_normal, seq_length, stride, historical)      

        print("#"*10, "Deep Decomposer Generating...", "#"*10)
        deep_pattern = decompose_model(x_test_normal, dataset_name)
        deep_test = deep_pattern['rec_test']
        deep_test_pattern = _decreate_sequences(deep_test)

        test_resid = (test_df - deep_test_pattern) * (1 + weight * test_temporal)

        # Wavelet transformation
        test_resid_wav = _wavelet(test_resid)
        test_resid_wavelet = _wavelet(test_resid_wav)

        for _ in range(wavelet_num):
            test_resid_wavelet = _wavelet(test_resid_wavelet)
            
    if temporal == True:
        if seq_length > 0:
            x_test.append(_create_sequences(test_df, seq_length, stride, historical))            
        else:
            x_test.append(test_df)
    else:
        if seq_length > 0:
            x_test.append(_create_sequences(test_df, seq_length, stride, historical))
        else:
            x_test.append(test_df)
        
        if decomposition == True:
            x_test_resid.append(_create_sequences(test_resid_wavelet, seq_length, stride, historical))

    
    # Only return temporal auxiliary information
    if temporal == True:
        return {'x_test': x_test}
    
    # There are four cases.
    # 1) Decompose time series and evaluate through traditional metrics
    if (decomposition == True) and (segmentation == False):
        return {'x_test': x_test, 'x_test_resid': x_test_resid }
    # 2) Decompose time series and evalutate new metrics
    elif (decomposition == True) and (segmentation == True):
        return {'x_test': x_test, 'x_test_resid': x_test_resid}
    # 3) Evaluate through new metrics with common methods
    elif (decomposition == False) and (segmentation == True):
        return {'x_test': x_test}                
    # 4) Evaluate through traditional metrics with common methods
    elif (decomposition == False) and (segmentation == False):
        return {'x_test': x_test}    


saved_data = []
            
def run_prediction(data):
    global saved_data
    
    saved_data = saved_data + data
    
    if len(saved_data) == seq_length:
        print('running prediction...')
        test_df = pd.DataFrame(saved_data, columns=['date'] + var_names)
        saved_data = [] # clear for the next batch
        
        data = preprocessor(test_df, seq_length, stride, lamda_t, wavelet_num, decomposition=DECOMPOSITION, segmentation=SEGMENTATION)
        # preprocess file
        print('start detection phase')
        start_time = time.time()
        avg_scores, scores = detect_anomaly(data, aux_data, detector, detector, MODEL, TEMPORAL, DECOMPOSITION, SEGMENTATION)
        avg_scores = avg_scores.reshape(avg_scores.shape[1])
        print(f'dection phase taken {time.time() - start_time}')
        
        metric_scores = pd.DataFrame(scores, columns=[f'score_{name}' for name in var_names])
        metric_scores['score'] = avg_scores # metric_scores.mean(axis=1)
        predictions = pd.DataFrame((scores > threshold).astype(int) , columns=[f'label_{name}' for name in var_names])
        predictions['label'] = (avg_scores > threshold).astype(int)
        test_df = pd.concat([test_df, metric_scores, predictions], axis=1)
        
        for idx, row in test_df.iterrows():
            db.collection('prediction_results').document(row['date']).set(row.to_dict())
            time.sleep(1.1)
            print(f"saved {row['date']} prediction")
        print('prediction end')
        
        
app = Flask(__name__)
initial_run = True
if __name__ == "__main__":
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credentials.Certificate(service_account))

    db = firestore.client()

    callback_done = threading.Event()
    def on_snapshot(col_snapshot, changes, read_time):
        global initial_run
        new_data = []

        for change in changes:
            if change.type.name == 'ADDED' and not initial_run:
                new_data.append(change.document.to_dict())
                print(f'{change.document.id} is added')
                
        callback_done.set()
        run_prediction(new_data)
        initial_run = False

    stram_watch = db.collection('data_streams').on_snapshot(on_snapshot)    
    print('listening on: data_streams')
#     app.run(host='0.0.0.0', port=5775, debug=False)
    serve(app, host='0.0.0.0', port=5775)