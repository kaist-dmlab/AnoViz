from flask import Flask, flash, request, redirect, url_for, jsonify
from flask_cors import CORS, cross_origin
from waitress import serve
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

from hashlib import md5

from api import stats, hourly_chart, weekly_chart, close_pattern_chart, possible_outliers, score_heatmap, past_close_patterns
from simulator import run_append
from configs import var_names, threshold
# from simulator import run_simulation, run_delete

origin = 'https://time-cad.web.app/'
origin_localhost = 'http://localhost:3000/'

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
# CORS(app, resources={r"/*": {"origins": [origin, origin_localhost]}})
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

unauthorized_response = {
    'status': 401,
    'message': 'The service is called by an unauthorized user'
}

bad_response = {
    'status': 400,
    'message': 'Bad Request / Required arguments are not given.'
}


@app.route('/', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def index():
    return jsonify({'status': 200 , 'message': "Silence is golden 🏆"})


@app.route('/api/stats', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def get_stats():
    # length: (int) the length of timestamps to calculate percent changes
    condition = request.args.get('length') and request.args.get('minDate') and request.args.get('maxDate')
    if condition:
        length = int(request.args.get('length'))
        start_date = str(request.args.get('minDate'))
        end_date = str(request.args.get('maxDate'))
        return jsonify({'status': 200, 'data': stats(length, start_date, end_date )})
    
    return jsonify(bad_response)


@app.route('/api/hourly_chart', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def get_hourly_chart():
    condition = request.args.get('length') and request.args.get('minDate') and request.args.get('maxDate')
    if condition:
        length = int(request.args.get('length'))
        start_date = str(request.args.get('minDate'))
        end_date = str(request.args.get('maxDate'))
        return jsonify({'status': 200, 'data': hourly_chart(length, start_date, end_date)})


@app.route('/api/weekly_chart', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def get_weekly_chart():
    condition = request.args.get('length') and request.args.get('minDate') and request.args.get('maxDate')
    if condition:
        length = int(request.args.get('length'))
        start_date = str(request.args.get('minDate'))
        end_date = str(request.args.get('maxDate'))
        return jsonify({'status': 200, 'data': weekly_chart(length, start_date, end_date)})


@app.route('/api/close_pattern_chart', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def get_close_pattern_chart():
    # variable_name: (str) name of the variable to search for
    # anomaly_timestamp: (str) timestamp of the anomaly to find similar patterns for
    # interval: (int) length of each pattern found
    # count: (int) the number of similar patterns to find
    condition = request.args.get('variable_name') and request.args.get('anomaly_timestamp') and request.args.get('interval') and request.args.get('count')
    if condition:
        variable_name = str(request.args.get('variable_name'))
        anomaly_timestamp = str(request.args.get('anomaly_timestamp'))
        interval = int(request.args.get('interval'))
        count = int(request.args.get('count'))
        return jsonify({'status': 200, 'data': close_pattern_chart(variable_name, anomaly_timestamp, interval, count)})
    
    return jsonify(bad_response)


@app.route('/api/past_close_patterns', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def get_past_close_patterns():
    # anomaly_timestamp: (str) timestamp of the anomaly to find close patterns for
    # interval: (int) length of each pattern found
    condition = request.args.get('anomaly_timestamp') and request.args.get('interval')
    if condition:
        anomaly_timestamp = str(request.args.get('anomaly_timestamp'))
        interval = int(request.args.get('interval'))
        return jsonify({'status': 200, 'data': past_close_patterns(anomaly_timestamp, interval)})
    
    return jsonify(bad_response)


@app.route('/api/possible_outliers', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def get_possible_outliers():
    # anomaly_timestamp: (str) timestamp of the anomaly to calculate outliers for
    # interval: (int) length of the data for box/violin plot    
    if request.args.get('interval') and request.args.get('anomaly_timestamp'):
        anomaly_timestamp = str(request.args.get('anomaly_timestamp'))
        interval = int(request.args.get('interval'))
        return jsonify({'status': 200, 'data': possible_outliers(anomaly_timestamp, interval)})
    
    return jsonify(bad_response)


@app.route('/api/score_heatmap', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def get_score_heatmap():
    if request.args.get('interval') and request.args.get('anomaly_timestamp'):
        interval = int(request.args.get('interval'))
        anomaly_timestamp = str(request.args.get('anomaly_timestamp'))
        return jsonify({'status': 200, 'data': score_heatmap(anomaly_timestamp, interval)})
    
    return jsonify(bad_response)


@app.route('/init', methods=['GET'])
# @cross_origin(origin=origin_localhost, headers=['Content-Type','Authorization'])
def initialize_client():
    return jsonify({'status': 200, 'data': {
        'var_names':  sorted(var_names),
        'threshold': threshold
    }})
    
# @app.route('/simulator/collection/delete', methods=['POST'])
# def delete_collection():
#     if request.json['passcode'] == '88e4da800f37b8517f39b3017dd21fe1':
#         if request.json['collection_name']:
#             return run_delete(request.json['collection_name'])

#     return jsonify(unauthorized_response)

@app.route('/simulator/append', methods=['GET'])
def append_stream():
    if request.args.get('collection_name') and request.args.get('limit'):
        collection_name = str(request.args.get('collection_name'))
        limit = int(request.args.get('limit'))
        return jsonify({'status': 200, 
                        'data': run_append(collection_name, limit)
                       })
            
    return jsonify(unauthorized_response)

if __name__ == "__main__":
    # serve(app, host='0.0.0.0', port=5555, url_scheme='https', threads=24)
    app.run(host='0.0.0.0', port=5555, debug=True)