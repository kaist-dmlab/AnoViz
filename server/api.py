import firebase_admin, time
import numpy as np
import pandas as pd

from math import floor, ceil
from typing import List

from scipy.stats import pearsonr
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from dtaidistance import dtw

from firebase_admin import credentials
from firebase_admin import firestore

from configs import service_account


def stats(length:int, start_date:str, end_date:str):
    """
    :param length: the length of timestamps to calculate percent changes
    :return: the count and percent change of anomalies
    """
    print('computing stats...')
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    query = db.collection('prediction_results').where('date', '>=', start_date).where('date', '<', end_date)
    reference_data = [doc.to_dict() for doc in query.stream()]
        
    query = db.collection('prediction_results').where('date', '<', start_date).order_by('date', direction=firestore.Query.DESCENDING).limit(length)
    comparison_data =[doc.to_dict() for doc in query.stream()]

    if len(reference_data) > 0:
        current_df = pd.DataFrame(reference_data)
        past_df = pd.DataFrame(comparison_data)
        var_columns = [c for c in current_df.columns if (not c.startswith('label') and not c.startswith('score') and c not in ['date'])]
        result = {var: current_df[f'label_{var}'].sum() for var in sorted(var_columns)}

        variable_wise = [
            {'name': k, 'n': int(v), 
            'percent': float((current_df[f'label_{k}'].sum() - past_df[f'label_{k}'].sum()) / past_df[f'label_{k}'].sum() * 100) if past_df[f'label_{k}'].sum() else float((current_df[f'label_{k}'].sum() - past_df[f'label_{k}'].sum()) * 100)} for k, v in result.items()
        ]

        current_var_sum = int(current_df[[c for c in sorted(current_df.columns) if c.startswith('label_')]].sum().sum())
        past_var_sum = int(past_df[[c for c in sorted(past_df.columns) if c.startswith('label_')]].sum().sum())
        total = {
            'n': int(current_df['label'].sum()),
            'percent': float((current_df['label'].sum() - past_df['label'].sum()) / past_df['label'].sum() * 100) if past_df['label'].sum() else float((current_df['label'].sum() - past_df['label'].sum()) * 100),
            'n_var': current_var_sum,
            'percent_var': float((current_var_sum - past_var_sum) / past_var_sum * 100) if past_var_sum else float((current_var_sum - past_var_sum) * 100)
        }
        return { 'total': total, 'variables': variable_wise}

    return {
            'total': {'n': 0, 'percent': 0, 'n_var': 0, 'percent_var': 0},
            'variables': [
                {'name': 'N/A', 'n':0, 'percent': 0}
            ]
        }


def hourly_chart(length:int, start_date:str, end_date:str):
    """
    :param length: length of data in timestamps to calculate
    :return: the hourly count of anomalies
    """
    print('computing hourly charts...')
    results = [{"time": f'{str(t).zfill(2)}:00', "value": 0} for t in range(24)]
    
    # firestore = Firestore()
    # df = firestore.get_full_data()
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()    
    query = db.collection('prediction_results').where('date', '>=', start_date).where('date', '<=', end_date)
    data = [doc.to_dict() for doc in query.stream()]    
    
    if len(data) > 0:
        df = pd.DataFrame(data)
        # if length:
        #     df = df.tail(length)
        df = df[df['label'] == 1]
        df['date'] = pd.to_datetime(df['date'])
        df['hour'] = df['date'].dt.hour
        result = df['hour'].value_counts()
        
        for k, v in result.to_dict().items():
            for r in results:
                if r['time'] == f'{str(k).zfill(2)}:00':
                    r['value'] = v
                    break
#         result = [{'time': f'{k}:00', 'value': v} for k, v in result.to_dict().items()]
    return results


def weekly_chart(length:int, start_date:str, end_date:str):
    """
    :param length: length of data in timestamps to calculate
    :return: the weekly count of anomalies
    """
    print('computing weekly charts...')
    results = [
        {"time": "Monday", "value": 0},
        {"time": "Tuesday", "value": 0},
        {"time": "Wednesday", "value": 0},
        {"time": "Thursday", "value": 0},
        {"time": "Friday", "value": 0},
        {"time": "Saturday", "value": 0},
        {"time": "Sunday", "value": 0}
    ]
    
    # firestore = Firestore()
    # df = firestore.get_full_data()
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()    
    query = db.collection('prediction_results').where('date', '>=', start_date).where('date', '<=', end_date)
    data = [doc.to_dict() for doc in query.stream()]       
    
    if len(data) > 0:
        df = pd.DataFrame(data)
        # if length:
        #     df = df.tail(length)
        df = df[df['label'] == 1]
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.day_name()
        result = df['day_of_week'].value_counts()
        
        for k, v in result.to_dict().items():
            for r in results:
                if r['time'] == k:
                    r['value'] = v
                    break
#         result = [{'time': k, 'value': v} for k, v in result.to_dict().items()]
    return results



def close_pattern_chart(variable_name: str, anomaly_timestamp: str, interval: int, count: int) -> List[dict]:
    """
    :param variable_name: name of the variable to search for
    :param anomaly_timestamp: timestamp of the anomaly to find similar patterns for
    :param interval: length of each pattern found
    :param count: the number of similar patterns to find
    :return: an array of similar patterns as a list of rows
    """
    print('computing close pattern charts...')

    # firestore = Firestore()
    # df = firestore.get_full_data()
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()    
    query = db.collection('prediction_results')
    data = [doc.to_dict() for doc in query.stream()]
    df = pd.DataFrame(data)
    
    df = df[['date', variable_name, f'label_{variable_name}']]

    anomaly_idx = df.index[df['date'] == anomaly_timestamp][0]
    anomaly_range = [anomaly_idx - floor((interval - 1) / 2), anomaly_idx + ceil((interval - 1) / 2)]
    if anomaly_range[0] < 0:
        anomaly_range[1] = anomaly_range[1] - anomaly_range[0]
        anomaly_range[0] = max(0, anomaly_range[0])
    elif anomaly_range[1] >= len(df):
        anomaly_range[0] = anomaly_range[0] - (anomaly_range[1] - len(df) + 1)
        anomaly_range[1] = min(anomaly_range[1], len(df) - 1)
    anomaly = df.loc[anomaly_range[0]:anomaly_range[1]].copy()
    
    # df['corr'] = df[variable_name].rolling(interval).apply(lambda r: pearsonr(r, anomaly[variable_name])[0])
    # df['corr'] = df[variable_name].rolling(interval).apply(lambda r: cosine_similarity(r.values.reshape(-1, 1), anomaly[variable_name].values.reshape(-1, 1))[0][0])
    df['corr'] = df[variable_name].rolling(interval).apply(lambda r: 1 - dtw.distance_fast(r.values.astype(np.double), anomaly[variable_name].values.astype(np.double)))

    order = np.argsort(df['corr'].tolist())[::-1]
    order = order[interval:interval + count]

    result = []

    anomaly['range'] = 'range with anomaly'
    anomaly['name'] = variable_name
    anomaly['date'] = range(len(anomaly))
    anomaly.rename(columns={variable_name: 'value', f'label_{variable_name}': 'label'}, inplace=True)
    data = anomaly.to_dict('records')
    result.extend(data)

    for idx in order:
        match = df[idx - interval + 1: idx + 1].copy()
        match['range'] = f'{match["date"].iloc[0]}-{match["date"].iloc[-1]}'
        match['name'] = variable_name
        match['date'] = range(len(match))
        match.rename(columns={variable_name: 'value', f'label_{variable_name}': 'label'}, inplace=True)
        match.drop('corr', axis=1, inplace=True)
        data = match.to_dict('records')
        result.extend(data)
    return result


def past_close_patterns(anomaly_timestamp: str, interval: int) -> List[dict]:
    """
    :param anomaly_timestamp: timestamp of the anomaly to find close patterns for
    :param interval: length of each pattern found
    :return: a list of points in the close pattern
    """
    print('computing past close pattern charts...')
    # firestore = Firestore()
    # df = firestore.get_full_data()
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()    
    query = db.collection('prediction_results')
    data = [doc.to_dict() for doc in query.stream()]
    df = pd.DataFrame(data)    

    anomaly_idx = df.index[df['date'] == anomaly_timestamp][0]
    anomaly_range = [anomaly_idx - floor((interval - 1) / 2), anomaly_idx + ceil((interval - 1) / 2)]
    if anomaly_range[0] < 0:
        anomaly_range[1] = anomaly_range[1] - anomaly_range[0]
        anomaly_range[0] = max(0, anomaly_range[0])
    elif anomaly_range[1] >= len(df):
        anomaly_range[0] = anomaly_range[0] - (anomaly_range[1] - len(df) + 1)
        anomaly_range[1] = min(anomaly_range[1], len(df) - 1)
    var_columns = [c for c in sorted(df.columns) if (not c.startswith('label') and not c.startswith('score') and c not in ['date'])]
    anomaly = df.loc[anomaly_range[0]:anomaly_range[1], sorted(var_columns)]

    for var in var_columns:
        # df[f'corr_{var}'] = df[var].rolling(interval).apply(lambda r: pearsonr(r, anomaly[var])[0])
        # df[f'corr_{var}'] = df[var].rolling(interval).apply(lambda r: cosine_similarity(r.values.reshape(-1, 1), anomaly[var].values.reshape(-1, 1))[0][0])
        df[f'corr_{var}'] = df[var].rolling(interval).apply(lambda r: 1 - dtw.distance_fast(r.values.astype(np.double), anomaly[var].values.astype(np.double)))
        
    # correlation is the mean of the correlations for each variable
    df['corr'] = df[[f'corr_{var}' for var in sorted(var_columns)]].mean(axis=1)

    order = np.argsort(df['corr'].tolist())[::-1]
    order = order[interval:]  # ignore first few nans
    order = [idx for idx in order if idx < anomaly_range[0]]  # only take the patterns before the anomaly

    result = []

    max_idx = order[0]
    match = df[max_idx - interval + 1: max_idx + 1].copy()
    match['range'] = f'{match["date"].iloc[0]}-{match["date"].iloc[-1]}'

    for var in sorted(var_columns):
        var_df = match[[v for v in match.columns if v.endswith(var)] + ['date', 'range']].copy()
        var_df.drop(f'corr_{var}', axis=1, inplace=True)
        var_df.rename(columns={var: 'value', f'label_{var}': 'label', f'score_{var}': 'score'}, inplace=True)
        var_df['name'] = var
        data = var_df.to_dict('records')
        result.extend(data)

    return result


def possible_outliers(anomaly_timestamp: str, interval: int) -> List[dict]:
    """
    :param anomaly_timestamp: timestamp of the anomaly to calculate outliers for
    :param interval: length of the data for box/violin plot
    :return: the close pattern found as a list of rows
    """
    print('computing violin / outliers charts...')
    # firestore = Firestore()
    # df = firestore.get_full_data()
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()    
    query = db.collection('prediction_results')
    data = [doc.to_dict() for doc in query.stream()]
    df = pd.DataFrame(data)    
    
    anomaly_idx = df.index[df['date'] == anomaly_timestamp][0]
    anomaly_range = [anomaly_idx - floor((interval - 1) / 2), anomaly_idx + ceil((interval - 1) / 2)]
    if anomaly_range[0] < 0:
        anomaly_range[1] = anomaly_range[1] - anomaly_range[0]
        anomaly_range[0] = max(0, anomaly_range[0])
    elif anomaly_range[1] >= len(df):
        anomaly_range[0] = anomaly_range[0] - (anomaly_range[1] - len(df) + 1)
        anomaly_range[1] = min(anomaly_range[1], len(df) - 1)
    anomaly = df.loc[anomaly_range[0]:anomaly_range[1]]
    var_columns = [c for c in sorted(df.columns) if (not c.startswith('label') and not c.startswith('score') and c not in ['date'])]

    result = []
    for row in anomaly.to_dict('records'):
        for v in sorted(var_columns):
            if row[f'label_{v}'] == 1:
                data = {
                    'name': v,
                    'value': row[v]
                }
                result.append(data)
    return result


def score_heatmap(anomaly_timestamp: str, interval: int):
    """
    :param anomaly_timestamp: timestamp of the anomaly to calculate for
    :param interval: length of data in timestamps to request
    :return: most recent {length} timestamps of data
    """
    print('computing heatmap charts...')
    # firestore = Firestore()
    # df = firestore.get_full_data()
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()    
    query = db.collection('prediction_results')
    data = [doc.to_dict() for doc in query.stream()]
    df = pd.DataFrame(data)        

    anomaly_idx = df.index[df['date'] == anomaly_timestamp][0]
    anomaly_range = [anomaly_idx - floor((interval - 1) / 2), anomaly_idx + ceil((interval - 1) / 2)]
    if anomaly_range[0] < 0:
        anomaly_range[1] = anomaly_range[1] - anomaly_range[0]
        anomaly_range[0] = max(0, anomaly_range[0])
    elif anomaly_range[1] >= len(df):
        anomaly_range[0] = anomaly_range[0] - (anomaly_range[1] - len(df) + 1)
        anomaly_range[1] = min(anomaly_range[1], len(df) - 1)
    anomaly_df = df.loc[anomaly_range[0]:anomaly_range[1]].copy()

    var_columns = [c for c in sorted(df.columns) if (not c.startswith('label') and not c.startswith('score') and c not in ['date'])]

    anomaly_df['score_avg'] = anomaly_df[[f'score_{v}' for v in sorted(var_columns)]].mean(axis=1)

    result = []
    for row in anomaly_df.to_dict('records'):
        for v in sorted(var_columns):
            data = {
                'date': row['date'],
                'score': row[f'score_{v}'],
                'name': v
            }
            result.append(data)
        data = {
            'date': row['date'],
            'score': row['score_avg'],
            'name': 'Overall'
        }
        result.append(data)
    return result


def normalization(raw_data):
    df = raw_data 
    scaler = MinMaxScaler(feature_range=(0, 1))
    normalized_data = scaler.fit_transform(df)
    return normalized_data