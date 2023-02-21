# Dataset Loader
# Univariate Datasets: KDD Cup'21 UCR, Yahoo S5, Power-demand, IoT_fridge
# Multivariate Datasets: NASA, ECG, 2D Gesture, SMD, UNSW, IoT_modbus

import os
import numpy as np
import pandas as pd
import simdjson
from tqdm import tqdm

import pywt
from itertools import groupby
from operator import itemgetter

import holidays
from datetime import datetime, timedelta

from sklearn.preprocessing import MinMaxScaler
from decomposition import load_STL_results, decompose_model

# Generated training sequences for use in the model.
def _create_sequences(values, seq_length, stride, historical=False):
    seq = []
    if historical:
        for i in range(seq_length, len(values) + 1, stride):
            seq.append(values[i-seq_length:i])
    else:
        for i in range(0, len(values) - seq_length + 1, stride):
            seq.append(values[i : i + seq_length])
   
    return np.stack(seq)

def _decreate_sequences(seq):
    temp = []
    for i in range(len(seq)):
        if i == len(seq)-1:
            for x in range(len(seq[i])):
                temp.append(seq[i][x])
        else:
            temp.append(seq[i][0])
    return temp

def _count_anomaly_segments(values):
    values = np.where(values == 1)[0]
    anomaly_segments = []
    
    for k, g in groupby(enumerate(values), lambda ix : ix[0] - ix[1]):
        anomaly_segments.append(list(map(itemgetter(1), g)))
    return len(anomaly_segments), anomaly_segments

def _wavelet(signal):
    (cA, cD) = pywt.dwt(signal, "haar")
    cat = pywt.threshold(cA, np.std(cA), mode="soft")
    cdt = pywt.threshold(cD, np.std(cD), mode="soft")
    return pywt.idwt(cat, cdt, "haar")

####################################################################################################################
######################################################TEMPORAL######################################################
def convert_datetime(unixtime):
    date = datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')
    return date # format : str

def get_dummies(df, column, name):
    columns = pd.get_dummies(column, prefix=name)
    df = df.merge(columns, left_index=True, right_index=True)
    df.drop([name], axis=1, inplace=True)
    return df

def add_temporal_info(dataset_name, df, timestamp):
    # Off the SettingWithCopyWarning
    pd.set_option('mode.chained_assignment', None)

    # Deep copy
    temporal_df = df.copy()

    timestamp = pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S')
    # Time(24)
    temporal_df['hour'] = pd.to_datetime(timestamp).dt.hour
    temporal_df['hour_sin'] = np.sin(temporal_df['hour'] * (2 * np.pi / 24))
    temporal_df['hour_cos'] = np.cos(temporal_df['hour'] * (2 * np.pi / 24))
    # temporal_df = get_dummies(temporal_df, temporal_df['hour'], 'hour')
    temporal_df.drop(['hour'], axis=1, inplace=True)

    # Day of week(7), Weekend(1)
    temporal_df['day_of_week'] = pd.to_datetime(timestamp).dt.weekday
    temporal_df['is_weekend'] = temporal_df['day_of_week'].isin([5,6]).astype(int)
    # temporal_df['day_of_week_sin'] = np.sin(temporal_df['day_of_week'] * (2 * np.pi / 7))
    # temporal_df['day_of_week_cos'] = np.cos(temporal_df['day_of_week'] * (2 * np.pi / 7))
    # temporal_df = get_dummies(temporal_df, temporal_df['day_of_week'], 'day_of_week')
    # temporal_df.drop(['day_of_week'], axis=1, inplace=True)
    
    # # Month(12), Season(4)
    # temporal_df['month'] = pd.to_datetime(timestamp).dt.month
    # temporal_df['spring'] = temporal_df['month'].isin([3,4,5]).astype(int)
    # temporal_df['summer'] = temporal_df['month'].isin([6,7,8]).astype(int)
    # temporal_df['fall'] = temporal_df['month'].isin([9,10,11]).astype(int)
    # temporal_df['winter'] = temporal_df['month'].isin([12,1,2]).astype(int)
    # temporal_df['month_sin'] = np.sin(temporal_df['month'] * (2 * np.pi / 12))
    # temporal_df['month_cos'] = np.cos(temporal_df['month'] * (2 * np.pi / 12))
    # temporal_df.drop(['month'], axis=1, inplace=True)
    
    ### datasets: IoT_fridge ###
    if dataset_name in ['kpi', 'unsw', 'IoT_fridge', 'IoT_modbus']:
        # Holiday(1), Previous holiday(1)
        holidays_list = []
        year = pd.to_datetime(timestamp.iloc[0]).year
        for date in holidays.UnitedStates(years=year).items():
            holidays_list.append(str(date[0]))
        holidays_list = pd.to_datetime(holidays_list, format='%Y-%m-%d')
        temporal_df['holiday'] = pd.to_datetime(timestamp.dt.date).isin(holidays_list).astype(int)
        delta = timedelta(hours=24)
        previous_holiday = holidays_list - delta
        temporal_df['previous_holiday'] = pd.to_datetime(timestamp.dt.date).isin(previous_holiday).astype(int)
    
    ### datasets: samsung, energy ###
    elif dataset_name in ['samsung', 'energy']:
        # Holiday(1), Previous holiday(1)
        holidays_list = []
        year = pd.to_datetime(timestamp[0]).year
        for date in holidays.Korea(years=year).items():
            holidays_list.append(str(date[0]))
        holidays_list = pd.to_datetime(holidays_list, format='%Y-%m-%d')
        temporal_df['holiday'] = pd.to_datetime(timestamp.dt.date).isin(holidays_list).astype(int)
        delta = timedelta(hours=24)
        previous_holiday = holidays_list - delta
        temporal_df['previous_holiday'] = pd.to_datetime(timestamp.dt.date).isin(previous_holiday).astype(int)

    # Change columns order
    temporal_df.insert(len(temporal_df.columns)-1, 'label', temporal_df.pop('label'))
    return temporal_df
####################################################################################################################
####################################################################################################################
                
def load_samsung(seq_length, stride, weight, wavelet_num, historical=False, temporal=False, decomposition=False, segmentation=False):
    # interval: 10 min
    # seq. length: 36:1 (i.e., 6 hour)
    # source: SAMSUNG
    data_path = './datasets/samsung/September'
    datasets = sorted([f for f in os.listdir(f'{data_path}/train') if os.path.isfile(os.path.join(f'{data_path}/train', f))])
    
    x_train, x_test, y_test = [], [], []
    y_segment_test = []
    x_train_resid, x_test_resid = [], []
    
    label_seq, test_seq = [], []
    for data in tqdm(datasets):
        train_df = pd.read_csv(f'{data_path}/train/{data}')
        test_df = pd.read_csv(f'{data_path}/test/{data}')
        if temporal == True:
            train_df = np.array(add_temporal_info('samsung', train_df, train_df.date))
            train_df = train_df[:, 6:-1].astype(float)
            test_df = np.array(add_temporal_info('samsung', test_df, test_df.date))
            test_df = test_df[:, 6:-1].astype(float)
        else:
            if decomposition == True:
                train_holiday = np.array(add_temporal_info('samsung', train_df, train_df.date)['holiday'])
                test_holiday = np.array(add_temporal_info('samsung', test_df, test_df.date)['holiday'])
                train_weekend = np.array(add_temporal_info('samsung', train_df, train_df.date)['is_weekend'])
                test_weekend = np.array(add_temporal_info('samsung', test_df, test_df.date)['is_weekend'])
                train_temporal = (train_holiday + train_weekend).reshape(-1, 1)
                test_temporal = (test_holiday + test_weekend).reshape(-1, 1)
            train_df = np.array(train_df)
            train_df = train_df[:, 1:-1].astype(float)
            test_df = np.array(test_df)
            labels = test_df[:, -1].astype(int)
            test_df = test_df[:, 1:-1].astype(float)

            scaler = MinMaxScaler()
            train_df = scaler.fit_transform(train_df)
            test_df = scaler.transform(test_df)

        if decomposition == True:
            stl_loader = load_STL_results(train_df, test_df)

            train_seasonal, test_seasonal = stl_loader['train_seasonal'], stl_loader['test_seasonal']
            train_trend, test_trend = stl_loader['train_trend'], stl_loader['test_trend']
            train_normal = train_seasonal + train_trend
            test_normal = test_seasonal + test_trend
            x_train_normal = _create_sequences(train_normal, seq_length, stride, historical)
            x_test_normal = _create_sequences(test_normal, seq_length, stride, historical)      

            print("#"*10, "Deep Decomposer Generating...", "#"*10)
            deep_pattern = decompose_model(x_train_normal, x_test_normal)
            deep_train, deep_test = deep_pattern['rec_train'], deep_pattern['rec_test']
            deep_train_pattern, deep_test_pattern = _decreate_sequences(deep_train), _decreate_sequences(deep_test)

            train_resid = (train_df - deep_train_pattern) * (1 + weight * train_temporal)
            test_resid = (test_df - deep_test_pattern) * (1 + weight * test_temporal)

            # Wavelet transformation
            train_resid_wav = _wavelet(train_resid)
            test_resid_wav = _wavelet(test_resid)

            train_resid_wavelet = _wavelet(train_resid_wav)
            test_resid_wavelet = _wavelet(test_resid_wav)

            for iter in range(wavelet_num):
                train_resid_wavelet = _wavelet(train_resid_wavelet)
                test_resid_wavelet = _wavelet(test_resid_wavelet)

        if temporal == True:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))            
            else:
                x_train.append(train_df)
                x_test.append(test_df)
        else:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))
                y_test.append(_create_sequences(labels, seq_length, stride, historical))
            else:
                x_train.append(train_df)
                x_test.append(test_df)
                y_test.append(labels)
            
            if decomposition == True:
                x_train_resid.append(_create_sequences(train_resid_wavelet, seq_length, stride, historical))
                x_test_resid.append(_create_sequences(test_resid_wavelet, seq_length, stride, historical))
            
            y_segment_test.append(_count_anomaly_segments(labels)[1])
            label_seq.append(labels)

            # For plot traffic raw data
            test_seq.append(test_df)

    # Only return temporal auxiliary information
    if temporal == True:
        return {'x_train': x_train, 'x_test': x_test}
    
    # There are four cases.
    # 1) Decompose time series and evaluate through traditional metrics
    if (decomposition == True) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test, 
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid,
                'label_seq': label_seq, 'test_seq': test_seq}
    # 2) Decompose time series and evalutate new metrics
    elif (decomposition == True) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test,
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid}
    # 3) Evaluate through new metrics with common methods
    elif (decomposition == False) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test}                
    # 4) Evaluate through traditional metrics with common methods
    elif (decomposition == False) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test,
                'label_seq': label_seq, 'test_seq': test_seq}

def load_energy(seq_length, stride, weight, wavelet_num, historical=False, temporal=False, decomposition=False, segmentation=False):
    # interval: 1 min
    # seq. length: 60:1 (i.e., 1 hour)
    # source: https://aihub.or.kr/aidata/30759
    data_path = './datasets/aihub'
    datasets = sorted([f for f in os.listdir(f'{data_path}/training') if os.path.isfile(os.path.join(f'{data_path}/training', f))])
    x_train, x_test, y_test = [], [], []
    y_segment_test = []
    x_train_resid, x_test_resid = [], []    

    label_seq, test_seq = [], []
    for data in tqdm(datasets):
        with open(f'{data_path}/training/{data}', 'rb') as f:
            raw_json = simdjson.loads(f.read())
        raw_df = pd.DataFrame(raw_json)['data']
        
        pre_dict = {}
        key_list = []
        print(f'----------------------{data} TRAIN DATA----------------------')
        for row in raw_df:
            pre_dict_key = row['TIMESTAMP']
            item_name = row['ITEM_NAME']
            item_value = row['ITEM_VALUE']
            label = row['LABEL_NAME']
            
            if not pre_dict_key in key_list:
                key_list.append(pre_dict_key)
                pre_dict[pre_dict_key] = {}
            pre_dict[pre_dict_key]['label'] = label
            pre_dict[pre_dict_key][item_name] = item_value
        
        train_df = pd.DataFrame(pre_dict)
        train_df = train_df.transpose()
        change_label_dict = {'경고':1, '주의':0, '정상':0}
        train_df = train_df.replace({'label': change_label_dict})
        train_df['date'] = pd.to_datetime(train_df.index, format='%Y-%m-%d %H:%M:%S')
        train_df = pd.concat([train_df['date'], train_df.iloc[:, 1:-1], train_df['label']], axis=1)
        train_df.drop(['역률평균'], axis=1, inplace=True)
        train_df.drop(['전류고조파평균'], axis=1, inplace=True)
        train_df.drop(['전압고조파평균'], axis=1, inplace=True)

        with open(f'{data_path}/validation/{data}', 'rb') as f:
            raw_json = simdjson.loads(f.read())
        raw_df = pd.DataFrame(raw_json)['data']
        
        pre_dict = {}
        key_list = []
        print(f'----------------------{data} VALIDATION DATA----------------------')
        for row in raw_df:
            pre_dict_key = row['TIMESTAMP']
            item_name = row['ITEM_NAME']
            item_value = row['ITEM_VALUE']
            label = row['LABEL_NAME']
            
            if not pre_dict_key in key_list:
                key_list.append(pre_dict_key)
                pre_dict[pre_dict_key] = {}
            pre_dict[pre_dict_key]['label'] = label
            pre_dict[pre_dict_key][item_name] = item_value
        
        test_df = pd.DataFrame(pre_dict)
        test_df = test_df.transpose()
        change_label_dict = {'경고':1, '주의':0, '정상':0}
        test_df = test_df.replace({'label': change_label_dict})
        test_df['date'] = pd.to_datetime(test_df.index, format='%Y-%m-%d %H:%M:%S')
        test_df = pd.concat([test_df['date'], test_df.iloc[:, 1:-1], test_df['label']], axis=1)
        test_df.drop(['역률평균'], axis=1, inplace=True)
        test_df.drop(['전류고조파평균'], axis=1, inplace=True)
        test_df.drop(['전압고조파평균'], axis=1, inplace=True)
        
        if temporal == True:
            train_df = np.array(add_temporal_info('energy', train_df, train_df.date))
            train_df = train_df[:, 1:-1].astype(float)
            test_df = np.array(add_temporal_info('energy', test_df, test_df.date))
            test_df = test_df[:, 1:-1].astype(float)
            labels = test_df[:, -1].astype(int)
        else:
            if decomposition == True:
                train_holiday = np.array(add_temporal_info('energy', train_df, train_df.date)['holiday'])
                test_holiday = np.array(add_temporal_info('energy', test_df, test_df.date)['holiday'])
                train_weekend = np.array(add_temporal_info('energy', train_df, train_df.date)['is_weekend'])
                test_weekend = np.array(add_temporal_info('energy', test_df, test_df.date)['is_weekend'])
                train_temporal = (train_holiday + train_weekend).reshape(-1, 1)
                test_temporal = (test_holiday + test_weekend).reshape(-1, 1)
            train_df = np.array(train_df)
            train_df = train_df[:, 1:-1].astype(float)
            test_df = np.array(test_df)
            labels = test_df[:, -1].astype(int)
            test_df = test_df[:, 1:-1].astype(float)

            scaler = MinMaxScaler()
            train_df = scaler.fit_transform(train_df)
            test_df = scaler.transform(test_df)

        if decomposition == True:
            stl_loader = load_STL_results(train_df, test_df)
            
            train_seasonal, test_seasonal = stl_loader['train_seasonal'], stl_loader['test_seasonal']
            train_trend, test_trend = stl_loader['train_trend'], stl_loader['test_trend']
            train_normal = train_seasonal + train_trend
            test_normal = test_seasonal + test_trend
            x_train_normal = _create_sequences(train_normal, seq_length, stride, historical)
            x_test_normal = _create_sequences(test_normal, seq_length, stride, historical)      

            print("#"*10, "Deep Decomposer Generating...", "#"*10)
            deep_pattern = decompose_model(x_train_normal, x_test_normal)
            deep_train, deep_test = deep_pattern['rec_train'], deep_pattern['rec_test']
            deep_train_pattern, deep_test_pattern = _decreate_sequences(deep_train), _decreate_sequences(deep_test)

            train_resid = (train_df - deep_train_pattern) * (1 + weight * train_temporal)
            test_resid = (test_df - deep_test_pattern) * (1 + weight * test_temporal)

            # Wavelet transformation
            train_resid_wav = _wavelet(train_resid)
            test_resid_wav = _wavelet(test_resid)

            train_resid_wavelet = _wavelet(train_resid_wav)
            test_resid_wavelet = _wavelet(test_resid_wav)

            for iter in range(wavelet_num):
                train_resid_wavelet = _wavelet(train_resid_wavelet)
                test_resid_wavelet = _wavelet(test_resid_wavelet)

        if temporal == True:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))            
            else:
                x_train.append(train_df)
                x_test.append(test_df)
        else:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))
                y_test.append(_create_sequences(labels, seq_length, stride, historical))
            else:
                x_train.append(train_df)
                x_test.append(test_df)
                y_test.append(labels)

            if decomposition == True:
                x_train_resid.append(_create_sequences(train_resid_wavelet, seq_length, stride, historical))
                x_test_resid.append(_create_sequences(test_resid_wavelet, seq_length, stride, historical))
            
            y_segment_test.append(_count_anomaly_segments(labels)[1])
            label_seq.append(labels)

            # For plot traffic raw data
            test_seq.append(test_df)

    # Only return temporal auxiliary information
    if temporal == True:
        return {'x_train': x_train, 'x_test': x_test}
    
    # There are four cases.
    # 1) Decompose time series and evaluate through traditional metrics
    if (decomposition == True) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test, 
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid,
                'label_seq': label_seq, 'test_seq': test_seq}
    # 2) Decompose time series and evalutate new metrics
    elif (decomposition == True) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test,
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid}
    # 3) Evaluate through new metrics with common methods
    elif (decomposition == False) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test}                
    # 4) Evaluate through traditional metrics with common methods
    elif (decomposition == False) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test,
                'label_seq': label_seq, 'test_seq': test_seq}

def load_kpi(seq_length, stride, weight, wavelet_num, historical=False, temporal=False, decomposition=False, segmentation=False):
    # interval: 1 miniute (60 secs)
    # seq. length: 60:1 (i.e., 1 hour)
    # source: http://iops.ai/competition_detail/?competition_id=5&flag=1
    
    data_path = f'./datasets/KPI/finals'
    f_names = sorted([f for f in os.listdir(f'{data_path}') if os.path.isfile(os.path.join(f'{data_path}', f))])

    x_train, x_test, y_test = [], [], []
    y_segment_test = []
    x_train_resid, x_test_resid = [], []
    
    label_seq, test_seq = [], []
    for f_name in f_names:
        df = pd.read_csv(f'{data_path}/{f_name}')
        # for avoid RuntimeWarning: invalid value encountered in true_divide (wavelet)
        df['value'] = df['value'] * 1e+6
        test_idx = int(df.shape[0] * 0.4) # train 60% test 40%
        
        if temporal == True:
            train_df = df[['timestamp', 'value', 'label']].iloc[:-test_idx]
            train_df['timestamp'] = pd.to_datetime(train_df['timestamp'], unit='s')
            train_df = np.array(add_temporal_info('kpi', train_df, train_df.timestamp))
            train_df = train_df[:, 2:-1].astype(float)

            test_df = df[['timestamp', 'value', 'label']].iloc[-test_idx:]
            test_df['timestamp'] = pd.to_datetime(test_df['timestamp'], unit='s')
            test_df = np.array(add_temporal_info('kpi', test_df, test_df.timestamp))
            test_df = test_df[:, 2:-1].astype(float)

        else:
            if decomposition == True:
                train_df = df[['timestamp', 'value', 'label']].iloc[:-test_idx]
                train_df['timestamp'] = pd.to_datetime(train_df['timestamp'], unit='s')
                test_df = df[['timestamp', 'value', 'label']].iloc[-test_idx:]
                test_df['timestamp'] = pd.to_datetime(test_df['timestamp'], unit='s')
                train_holiday = np.array(add_temporal_info('kpi', train_df, train_df.timestamp)['holiday'])
                test_holiday = np.array(add_temporal_info('kpi', test_df, test_df.timestamp)['holiday'])
                train_weekend = np.array(add_temporal_info('kpi', train_df, train_df.timestamp)['is_weekend'])
                test_weekend = np.array(add_temporal_info('kpi', test_df, test_df.timestamp)['is_weekend'])
                train_temporal = (train_holiday + train_weekend).reshape(-1, 1)
                test_temporal = (test_holiday + test_weekend).reshape(-1, 1)
            train_df = df['value'].iloc[:-test_idx].values.reshape(-1, 1)
            test_df = df['value'].iloc[-test_idx:].values.reshape(-1, 1)
            labels = df['label'].iloc[-test_idx:].values.astype(int)

            scaler = MinMaxScaler()
            train_df = scaler.fit_transform(train_df)
            test_df = scaler.transform(test_df)

        if decomposition == True:
            stl_loader = load_STL_results(train_df, test_df)

            train_seasonal, test_seasonal = stl_loader['train_seasonal'], stl_loader['test_seasonal']
            train_trend, test_trend = stl_loader['train_trend'], stl_loader['test_trend']
            train_normal = train_seasonal + train_trend
            test_normal = test_seasonal + test_trend
            x_train_normal = _create_sequences(train_normal, seq_length, stride, historical)
            x_test_normal = _create_sequences(test_normal, seq_length, stride, historical)      

            print("#"*10, "Deep Decomposer Generating...", "#"*10)
            deep_pattern = decompose_model(x_train_normal, x_test_normal)
            deep_train, deep_test = deep_pattern['rec_train'], deep_pattern['rec_test']
            deep_train_pattern, deep_test_pattern = _decreate_sequences(deep_train), _decreate_sequences(deep_test)

            train_resid = (train_df - deep_train_pattern) * (1 + weight * train_temporal)
            test_resid = (test_df - deep_test_pattern) * (1 + weight * test_temporal)

        if temporal == True:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))            
            else:
                x_train.append(train_df)
                x_test.append(test_df)
        else:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))
                y_test.append(_create_sequences(labels, seq_length, stride, historical))
            else:
                x_train.append(train_df)
                x_test.append(test_df)
                y_test.append(labels)
            
            if decomposition == True:
                x_train_resid.append(_create_sequences(train_resid, seq_length, stride, historical))
                x_test_resid.append(_create_sequences(test_resid, seq_length, stride, historical))
            
            y_segment_test.append(_count_anomaly_segments(labels)[1])
            label_seq.append(labels)

            # For plot traffic raw data
            test_seq.append(test_df)

    # Only return temporal auxiliary information
    if temporal == True:
        return {'x_train': x_train, 'x_test': x_test}
    
    # There are four cases.
    # 1) Decompose time series and evaluate through traditional metrics
    if (decomposition == True) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test, 
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid,
                'label_seq': label_seq, 'test_seq': test_seq}
    # 2) Decompose time series and evalutate new metrics
    elif (decomposition == True) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test,
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid}
    # 3) Evaluate through new metrics with common methods
    elif (decomposition == False) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test}                
    # 4) Evaluate through traditional metrics with common methods
    elif (decomposition == False) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test,
                'label_seq': label_seq, 'test_seq': test_seq}


def load_unsw(seq_length, stride, weight, wavelet_num, historical=False, temporal=False, decomposition=False, segmentation=False):
    # interval: 1 miniute (60 secs)
    # seq. length: 60:1 (i.e., 1 hour)
    # source: https://research.unsw.edu.au/projects/unsw-nb15-dataset
    
    data_path = './datasets/UNSW'
    f_names = sorted([f for f in os.listdir(f'{data_path}') if os.path.isfile(os.path.join(f'{data_path}', f))])

    x_train, x_test, y_test = [], [], []
    y_segment_test = []
    x_train_resid, x_test_resid = [], []
    
    label_seq, test_seq = [], []
    for f_name in tqdm(f_names):
        df = pd.read_csv(f'{data_path}/{f_name}', low_memory=False)
        drop_list = ['srcip', 'sport', 'dstip', 'dsport', 'proto', 'state', 'service', 'attack_cat', 'Dload', 'ct_ftp_cmd']
        df = df.drop(drop_list, axis=1)
        df.rename(columns = {'Label':'label'}, inplace=True)
        test_idx = int(df.shape[0] * 0.4) # train 60% test 40%
        
        if temporal == True:
            train_df = df.iloc[:-test_idx]
            train_df['timestamp'] = pd.to_datetime(train_df['Sload'], unit='s')
            train_df = add_temporal_info('unsw', train_df, train_df.timestamp)
            train_df.set_index(train_df['timestamp'], inplace=True)
            train_df = train_df.drop(['timestamp'], axis=1)
            train_df = np.array(train_df.astype(float))
            train_df = train_df[:, :-1].astype(float)

            test_df = df.iloc[-test_idx:]
            test_df['timestamp'] = pd.to_datetime(test_df['Sload'], unit='s')
            test_df = add_temporal_info('unsw', test_df, test_df.timestamp)
            test_df.set_index(test_df['timestamp'], inplace=True)
            test_df = test_df.drop(['timestamp'], axis=1)
            test_df = np.array(test_df.astype(float))
            test_df = test_df[:, :-1].astype(float)
            labels = df['label'].iloc[-test_idx:].values.astype(int)

        else:
            if decomposition == True:
                train_df = df.iloc[:-test_idx]
                train_df['timestamp'] = pd.to_datetime(train_df['Sload'], unit='s')
                test_df = df.iloc[-test_idx:]
                test_df['timestamp'] = pd.to_datetime(test_df['Sload'], unit='s')                             
                train_holiday = np.array(add_temporal_info('unsw', train_df, train_df.timestamp)['holiday'])
                test_holiday = np.array(add_temporal_info('unsw', test_df, test_df.timestamp)['holiday'])
                train_weekend = np.array(add_temporal_info('unsw', train_df, train_df.timestamp)['is_weekend'])
                test_weekend = np.array(add_temporal_info('unsw', test_df, test_df.timestamp)['is_weekend'])
                train_temporal = (train_holiday + train_weekend).reshape(-1, 1)
                test_temporal = (test_holiday + test_weekend).reshape(-1, 1)            
            train_df = df.iloc[:-test_idx]
            test_df = df.iloc[-test_idx:]
            labels = df['label'].iloc[-test_idx:].values.astype(int)

            scaler = MinMaxScaler(feature_range=(0, 1))
            train_df = scaler.fit_transform(train_df)
            test_df = scaler.transform(test_df)

        if decomposition == True:
            stl_loader = load_STL_results(train_df, test_df)

            train_seasonal, test_seasonal = stl_loader['train_seasonal'], stl_loader['test_seasonal']
            train_trend, test_trend = stl_loader['train_trend'], stl_loader['test_trend']
            train_normal = train_seasonal + train_trend
            test_normal = test_seasonal + test_trend
            x_train_normal = _create_sequences(train_normal, seq_length, stride, historical)
            x_test_normal = _create_sequences(test_normal, seq_length, stride, historical)      

            print("#"*10, "Deep Decomposer Generating...", "#"*10)
            deep_pattern = decompose_model(x_train_normal, x_test_normal)
            deep_train, deep_test = deep_pattern['rec_train'], deep_pattern['rec_test']
            deep_train_pattern, deep_test_pattern = _decreate_sequences(deep_train), _decreate_sequences(deep_test)

            train_resid = (train_df - deep_train_pattern) * (1 + weight * train_temporal)
            test_resid = (test_df - deep_test_pattern) * (1 + weight * test_temporal)

            # Wavelet transformation
            train_resid_wav = _wavelet(train_resid)
            test_resid_wav = _wavelet(test_resid)

            train_resid_wavelet = _wavelet(train_resid_wav)
            test_resid_wavelet = _wavelet(test_resid_wav)

            for iter in range(wavelet_num):
                train_resid_wavelet = _wavelet(train_resid_wavelet)
                test_resid_wavelet = _wavelet(test_resid_wavelet)

        if temporal == True:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))            
            else:
                x_train.append(train_df)
                x_test.append(test_df)
        else:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))
                y_test.append(_create_sequences(labels, seq_length, stride, historical))
            else:
                x_train.append(train_df)
                x_test.append(test_df)
                y_test.append(labels)

            if decomposition == True:
                x_train_resid.append(_create_sequences(train_resid_wavelet, seq_length, stride, historical))
                x_test_resid.append(_create_sequences(test_resid_wavelet, seq_length, stride, historical))

            y_segment_test.append(_count_anomaly_segments(labels)[1])
            label_seq.append(labels)

            # For plot traffic raw data
            test_seq.append(test_df)
    
    # Only return temporal auxiliary information
    if temporal == True:
        return {'x_train': x_train, 'x_test': x_test}
    
    # There are four cases.
    # 1) Decompose time series and evaluate through traditional metrics
    if (decomposition == True) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test, 
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid,
                'label_seq': label_seq, 'test_seq': test_seq}
    # 2) Decompose time series and evalutate new metrics
    elif (decomposition == True) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test,
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid}
    # 3) Evaluate through new metrics with common methods
    elif (decomposition == False) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test}                
    # 4) Evaluate through traditional metrics with common methods
    elif (decomposition == False) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test,
                'label_seq': label_seq, 'test_seq': test_seq}


def load_IoT_fridge(seq_length, stride, weight, wavelet_num, historical=False, temporal=False, decomposition=False, segmentation=False):
    # interval: 1 second
    # seq. length: 60:1 (i.e., 1 min)
    # source: https://research.unsw.edu.au/projects/toniot-datasets
    
    data_path = './datasets/IoT_fridge'
    f_names = sorted([f for f in os.listdir(f'{data_path}') if os.path.isfile(os.path.join(f'{data_path}', f))])

    x_train, x_test, y_test = [], [], []
    y_segment_test = []
    x_train_resid, x_test_resid = [], []
    
    label_seq, test_seq = [], []
    for f_name in tqdm(f_names):
        df = pd.read_csv(f'{data_path}/{f_name}')
        date_format = '%d-%b-%y'
        time_format = '%H:%M:%S'
        df['date'] = [datetime.strptime(date, date_format) for date in df['date']]
        df['date'] = df['date'].dt.date
        df['time'] = df['time'].str.strip()
        df['time'] = pd.to_datetime(df['time'], format=time_format).dt.time
        datetimes = ['date', 'time']
        df['timestamp'] =df[datetimes].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)
        df.insert(0, 'timestamp', df.pop('timestamp'))
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')
        df.sort_values('timestamp', inplace=True)
        df.reset_index(drop=True, inplace=True)

        drop_list = ['ts', 'date', 'time', 'temp_condition', 'type']
        df = df.drop(drop_list, axis=1)
        test_idx = int(df.shape[0] * 0.7) # train 30% test 70%
        
        if temporal == True:
            train_df = df.iloc[:-test_idx]
            train_df = add_temporal_info('IoT_fridge', train_df, train_df.timestamp)
            train_df.set_index(train_df['timestamp'], inplace=True)
            train_df = np.array(train_df.drop(['timestamp'], axis=1))
            train_df = train_df[:, 1:-1].astype(float)

            test_df = df.iloc[-test_idx:]
            test_df = add_temporal_info('IoT_fridge', test_df, test_df.timestamp)
            test_df.set_index(test_df['timestamp'], inplace=True)
            test_df = np.array(test_df.drop(['timestamp'], axis=1))
            test_df = test_df[:, 1:-1].astype(float)
            labels = test_df[:, -1].astype(int)

        else:
            if decomposition == True:
                train_df = df.iloc[:-test_idx]
                test_df = df.iloc[-test_idx:]
                train_holiday = np.array(add_temporal_info('IoT_fridge', train_df, train_df.timestamp)['holiday'])
                test_holiday = np.array(add_temporal_info('IoT_fridge', test_df, test_df.timestamp)['holiday'])
                train_weekend = np.array(add_temporal_info('IoT_fridge', train_df, train_df.timestamp)['is_weekend'])
                test_weekend = np.array(add_temporal_info('IoT_fridge', test_df, test_df.timestamp)['is_weekend'])
                train_temporal = (train_holiday + train_weekend).reshape(-1, 1)
                test_temporal = (test_holiday + test_weekend).reshape(-1, 1)            
            train_df = np.array(df.iloc[:-test_idx])
            train_df = train_df[:, 1:-1].astype(float)
            test_df = np.array(df.iloc[-test_idx:])
            labels = test_df[:, -1].astype(int)
            test_df = test_df[:, 1:-1].astype(float)

            scaler = MinMaxScaler(feature_range=(0, 1))
            train_df = scaler.fit_transform(train_df)
            test_df = scaler.transform(test_df)

        if decomposition == True:
            stl_loader = load_STL_results(train_df, test_df)

            train_seasonal, test_seasonal = stl_loader['train_seasonal'], stl_loader['test_seasonal']
            train_trend, test_trend = stl_loader['train_trend'], stl_loader['test_trend']
            train_normal = train_seasonal + train_trend
            test_normal = test_seasonal + test_trend
            x_train_normal = _create_sequences(train_normal, seq_length, stride, historical)
            x_test_normal = _create_sequences(test_normal, seq_length, stride, historical)      

            print("#"*10, "Deep Decomposer Generating...", "#"*10)
            deep_pattern = decompose_model(x_train_normal, x_test_normal)
            deep_train, deep_test = deep_pattern['rec_train'], deep_pattern['rec_test']
            deep_train_pattern, deep_test_pattern = _decreate_sequences(deep_train), _decreate_sequences(deep_test)

            train_resid = (train_df - deep_train_pattern) * (1 + weight * train_temporal)
            test_resid = (test_df - deep_test_pattern) * (1 + weight * test_temporal)

            # Wavelet transformation
            train_resid_wav = _wavelet(train_resid)
            test_resid_wav = _wavelet(test_resid)

            train_resid_wavelet = _wavelet(train_resid_wav)
            test_resid_wavelet = _wavelet(test_resid_wav)

            for iter in range(wavelet_num):
                train_resid_wavelet = _wavelet(train_resid_wavelet)
                test_resid_wavelet = _wavelet(test_resid_wavelet)

        if temporal == True:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))            
            else:
                x_train.append(train_df)
                x_test.append(test_df)
        else:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))
                y_test.append(_create_sequences(labels, seq_length, stride, historical))

            else:
                x_train.append(train_df)
                x_test.append(test_df)
                y_test.append(labels)

            if decomposition == True:
                x_train_resid.append(_create_sequences(train_resid_wavelet, seq_length, stride, historical))
                x_test_resid.append(_create_sequences(test_resid_wavelet, seq_length, stride, historical))

            y_segment_test.append(_count_anomaly_segments(labels)[1])
            label_seq.append(labels)

            # For plot traffic raw data
            test_seq.append(test_df)
    
    # Only return temporal auxiliary information
    if temporal == True:
        return {'x_train': x_train, 'x_test': x_test}
    
    # There are four cases.
    # 1) Decompose time series and evaluate through traditional metrics
    if (decomposition == True) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test, 
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid,
                'label_seq': label_seq, 'test_seq': test_seq}
    # 2) Decompose time series and evalutate new metrics
    elif (decomposition == True) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test,
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid}
    # 3) Evaluate through new metrics with common methods
    elif (decomposition == False) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test}                
    # 4) Evaluate through traditional metrics with common methods
    elif (decomposition == False) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test,
                'label_seq': label_seq, 'test_seq': test_seq}

def load_IoT_modbus(seq_length, stride, weight, wavelet_num, historical=False, temporal=False, decomposition=False, segmentation=False):
    # interval: 1 second
    # seq. length: 60:1 (i.e., 1 min)
    # source: https://research.unsw.edu.au/projects/toniot-datasets
    
    data_path = './datasets/IoT_modbus'
    f_names = sorted([f for f in os.listdir(f'{data_path}') if os.path.isfile(os.path.join(f'{data_path}', f))])

    x_train, x_test, y_test = [], [], []
    y_segment_test = []
    x_train_resid, x_test_resid = [], []
    
    label_seq, test_seq = [], []
    for f_name in tqdm(f_names):
        df = pd.read_csv(f'{data_path}/{f_name}')
        date_format = '%d-%b-%y'
        time_format = '%H:%M:%S'
        df['date'] = [datetime.strptime(date, date_format) for date in df['date']]
        df['date'] = df['date'].dt.date
        df['time'] = df['time'].str.strip()
        df['time'] = pd.to_datetime(df['time'], format=time_format).dt.time
        datetimes = ['date', 'time']
        df['timestamp'] =df[datetimes].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)
        df.insert(0, 'timestamp', df.pop('timestamp'))
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')
        df.sort_values('timestamp', inplace=True)
        df.reset_index(drop=True, inplace=True)

        drop_list = ['ts', 'date', 'time', 'type']
        df = df.drop(drop_list, axis=1)
        test_idx = int(df.shape[0] * 0.7) # train 30% test 70%
        
        if temporal == True:
            train_df = df.iloc[:-test_idx]
            train_df = add_temporal_info('IoT_modbus', train_df, train_df.timestamp)
            train_df.set_index(train_df['timestamp'], inplace=True)
            train_df = np.array(train_df.drop(['timestamp'], axis=1))
            train_df = train_df[:, 3:-1].astype(float)

            test_df = df.iloc[-test_idx:]
            test_df = add_temporal_info('IoT_modbus', test_df, test_df.timestamp)
            test_df.set_index(test_df['timestamp'], inplace=True)
            test_df = np.array(test_df.drop(['timestamp'], axis=1))
            test_df = test_df[:, 3:-1].astype(float)
            labels = test_df[:, -1].astype(int)

        else:
            if decomposition == True:
                train_df = df.iloc[:-test_idx]
                test_df = df.iloc[-test_idx:]
                train_holiday = np.array(add_temporal_info('IoT_modbus', train_df, train_df.timestamp)['holiday'])
                test_holiday = np.array(add_temporal_info('IoT_modbus', test_df, test_df.timestamp)['holiday'])
                train_weekend = np.array(add_temporal_info('IoT_modbus', train_df, train_df.timestamp)['is_weekend'])
                test_weekend = np.array(add_temporal_info('IoT_modbus', test_df, test_df.timestamp)['is_weekend'])
                train_temporal = (train_holiday + train_weekend).reshape(-1, 1)
                test_temporal = (test_holiday + test_weekend).reshape(-1, 1)               
            train_df = np.array(df.iloc[:-test_idx])
            train_df = train_df[:, 1:-1].astype(float)
            test_df = np.array(df.iloc[-test_idx:])
            labels = test_df[:, -1].astype(int)
            test_df = test_df[:, 1:-1].astype(float)

            scaler = MinMaxScaler(feature_range=(0, 1))
            train_df = scaler.fit_transform(train_df)
            test_df = scaler.transform(test_df)

        if decomposition == True:
            stl_loader = load_STL_results(train_df, test_df)

            train_seasonal, test_seasonal = stl_loader['train_seasonal'], stl_loader['test_seasonal']
            train_trend, test_trend = stl_loader['train_trend'], stl_loader['test_trend']
            train_normal = train_seasonal + train_trend
            test_normal = test_seasonal + test_trend
            x_train_normal = _create_sequences(train_normal, seq_length, stride, historical)
            x_test_normal = _create_sequences(test_normal, seq_length, stride, historical)      

            print("#"*10, "Deep Decomposer Generating...", "#"*10)
            deep_pattern = decompose_model(x_train_normal, x_test_normal)
            deep_train, deep_test = deep_pattern['rec_train'], deep_pattern['rec_test']
            deep_train_pattern, deep_test_pattern = _decreate_sequences(deep_train), _decreate_sequences(deep_test)

            train_resid = (train_df - deep_train_pattern) * (1 + weight * train_temporal)
            test_resid = (test_df - deep_test_pattern) * (1 + weight * test_temporal)

            # Wavelet transformation
            train_resid_wav = _wavelet(train_resid)
            test_resid_wav = _wavelet(test_resid)

            train_resid_wavelet = _wavelet(train_resid_wav)
            test_resid_wavelet = _wavelet(test_resid_wav)

            # Wavelet transformation
            train_resid_wav = _wavelet(train_resid)
            test_resid_wav = _wavelet(test_resid)

            train_resid_wavelet = _wavelet(train_resid_wav)
            test_resid_wavelet = _wavelet(test_resid_wav)

            for iter in range(wavelet_num):
                train_resid_wavelet = _wavelet(train_resid_wavelet)
                test_resid_wavelet = _wavelet(test_resid_wavelet)

        if temporal == True:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))            
            else:
                x_train.append(train_df)
                x_test.append(test_df)
        else:
            if seq_length > 0:
                x_train.append(_create_sequences(train_df, seq_length, stride, historical))
                x_test.append(_create_sequences(test_df, seq_length, stride, historical))
                y_test.append(_create_sequences(labels, seq_length, stride, historical))

            else:
                x_train.append(train_df)
                x_test.append(test_df)
                y_test.append(labels)

            if decomposition == True:
                x_train_resid.append(_create_sequences(train_resid_wavelet, seq_length, stride, historical))
                x_test_resid.append(_create_sequences(test_resid_wavelet, seq_length, stride, historical))

            y_segment_test.append(_count_anomaly_segments(labels)[1])
            label_seq.append(labels)

            # For plot traffic raw data
            test_seq.append(test_df)
    
    # Only return temporal auxiliary information
    if temporal == True:
        return {'x_train': x_train, 'x_test': x_test}
    
    # There are four cases.
    # 1) Decompose time series and evaluate through traditional metrics
    if (decomposition == True) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test, 
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid,
                'label_seq': label_seq, 'test_seq': test_seq}
    # 2) Decompose time series and evalutate new metrics
    elif (decomposition == True) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test,
                'x_train_resid': x_train_resid, 'x_test_resid': x_test_resid}
    # 3) Evaluate through new metrics with common methods
    elif (decomposition == False) and (segmentation == True):
        return {'x_train': x_train, 'x_test': x_test,
                'y_test': label_seq, 'y_segment_test': y_segment_test}                
    # 4) Evaluate through traditional metrics with common methods
    elif (decomposition == False) and (segmentation == False):
        return {'x_train': x_train, 'x_test': x_test, 'y_test': y_test,
                'label_seq': label_seq, 'test_seq': test_seq}