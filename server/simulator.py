import firebase_admin, time, argparse
import pandas as pd

from flask import jsonify
from tqdm import tqdm
from firebase_admin import credentials
from firebase_admin import firestore
from configs import service_account


def run_delete(collection_name, date_reference):
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()        
    
    docs = db.collection(collection_name).stream()
    for doc in tqdm(docs):
        if doc.id <= date_reference:
            print(f'Deleting doc {doc.id}')
            doc.reference.delete()


def run_simulation(data_name, limit:100):
    df = pd.read_csv(f'datasets/{data_name}.csv').drop(['label'], axis=1).sort_values(by='date', ascending=True)
    # df = df[df['date'] >= '2022-01-01 00:00:00']
    
    try:
        print('try to connect firebase...')
        firebase_admin.get_app()
    except ValueError:
        print('set firebase credentials...')
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    print('firestore db connected!')
    
    collection_name = 'data_streams'
    
    for _, data in tqdm(df.iloc[:limit].iterrows(), total=limit):
        db.collection(collection_name).document(data['date']).set(data.to_dict())
        time.sleep(1.75)


def run_append(data_name, limit:100):
    df = pd.read_csv(f'datasets/{data_name}.csv').drop(['label'], axis=1).sort_values(by='date', ascending=True)
    
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()
    
    collection_name = 'data_streams'
    result = db.collection(collection_name).order_by("date", direction=firestore.Query.DESCENDING).limit(1).get()[0].to_dict()
    recent_date = result['date']
    
    print('running append stream...')
    for _, data in tqdm(df[df['date'] > recent_date].iloc[:limit].iterrows(), total=limit):
        db.collection(collection_name).document(data['date']).set(data.to_dict())
        time.sleep(1.75)
        
    return True

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', type=str, required=True)
    parser.add_argument('--action', type=str, required=True)
    parser.add_argument('--limit', type=int, required=False, default=100)
    parser.add_argument('--date_reference', type=str, required=False, default='2020-01-01 00:00:00')

    args = parser.parse_args()

    collection_name = args.collection.lower()
    date_reference = str(args.date_reference)
    action = args.action.lower()
    limit = int(args.limit)
    
    if action == 'delete':
        run_delete(collection_name, date_reference)
    elif action == 'run':
        run_simulation(collection_name, limit)
    elif action == 'append':
        run_append(collection_name, limit)