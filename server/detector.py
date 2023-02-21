#%%
import os

import pandas as pd
import numpy as np
from tqdm import tqdm

from utils.evaluator import evaluate, set_thresholds
from utils.evaluator_seg import compute_anomaly_scores, compute_metrics


def _elements(array):
    return array.ndim and array.size

def detect_anomaly(datasets, datasets_auxiliary, AE_model, Temporal_AE_model, model_name, temporal=False, decomposition=False, segmentation=False):
    if temporal == True:
        # datasets_auxiliary = globals()[f'load_{dataset}'](window_size, stride, lamda_t, wavelet_num, temporal=temporal)
        ax_tests = datasets_auxiliary['x_test']
        
    if segmentation == False:
        # datasets = globals()[f'load_{dataset}'](window_size, stride, lamda_t, wavelet_num, decomposition=decomposition, segmentation=segmentation)
        x_tests = datasets['x_test']

        if decomposition == True:
            test_residual = datasets['x_test_resid']
        
        per_window_idx = []
        data_num = 0
        # 1) if decomposition == True
        if decomposition == True:
            X_test = x_tests[data_num]
            residual_X_test = test_residual[data_num]

            # 1-1) temporal=True, decomposition=True, Segmentation=False
            if temporal == True:
                X_test_ax = ax_tests[data_num]                    
                model = Temporal_AE_model # (X_train_ax, residual_X_train)
                rec_x = model.predict([X_test_ax, residual_X_test])
                thresholds = set_thresholds(residual_X_test, rec_x, is_reconstructed=True)
                test_scores = evaluate(thresholds, residual_X_test, rec_x, y_tests[data_num], is_reconstructed=True)
            # 2-1) temporal=False, decomposition=True, Segmentation=False
            else:
                if model_name == "MS-RNN":
                    model = AE_model # (residual_X_train)
                    rec_x = [np.flip(rec, axis=1) for rec in model.predict(residual_X_test)]
                    thresholds = set_thresholds(residual_X_test, rec_x, is_reconstructed=True, scoring='square_median')
                    test_scores = evaluate(thresholds, residual_X_test, rec_x, y_tests[data_num], is_reconstructed=True, scoring='square_median')
                else:
                    model = AE_model # (residual_X_train)
                    rec_x = model.predict(residual_X_test)
                    # thresholds = set_thresholds(residual_X_test, rec_x, is_reconstructed=True)
                    # test_scores = evaluate(thresholds, residual_X_test, rec_x, y_tests[data_num], is_reconstructed=True)
                    scores, metric_scores = compute_anomaly_scores(residual_X_test, rec_x)

        # 4) if decomposition == False
        else:
            X_test = x_tests[data_num]              
            
            # 1-4) temporal=True, decomposition=False, segmentation=False
            if temporal == True:
                X_test_ax = ax_tests[data_num]                    
                model = Temporal_AE_model # (X_train_ax, X_train)
                rec_x = model.predict([X_test_ax, X_test])
                thresholds = set_thresholds(X_test, rec_x, is_reconstructed=True)
                test_scores = evaluate(thresholds, X_test, rec_x, y_tests[data_num], is_reconstructed=True)                  
            # 2-4) temporal=False, decomposition=False, segmentation:False
            else:
                if model_name == "MS-RNN":
                    model = AE_model # (X_train)
                    rec_x = [np.flip(rec, axis=1) for rec in model.predict(X_test)]
                    thresholds = set_thresholds(X_test, rec_x, is_reconstructed=True, scoring='square_median')
                    test_scores = evaluate(thresholds, X_test, rec_x, y_tests[data_num], is_reconstructed=True, scoring='square_median')
                else:
                    model = AE_model # (X_train)
                    rec_x = model.predict(X_test)
                    thresholds = set_thresholds(X_test, rec_x, is_reconstructed=True)
                    test_scores = evaluate(thresholds, X_test, rec_x, y_tests[data_num], is_reconstructed=True)
            
#         th_index = test_scores['f1'].index(max(test_scores['f1'])) # int(np.median(np.where(test_scores['f1']==np.max(test_scores['f1']))[0]))
#         threshold = thresholds[th_index]
        
        # pred_anomal_idx = []
        # for t in range(len(X_test)):
        #     pred_anomalies = np.where(test_scores['rec_errors'][t] > thresholds[th_index])[0]
        #     isEmpty = (_elements(pred_anomalies) == 0)
        #     if isEmpty:
        #         pass
        #     else:
        #         if pred_anomalies[0] == 0:
        #             pred_anomal_idx.append(t)
        # per_window_idx.append(pred_anomal_idx)

    # 2) decomposition==True: Decompose time series and evalutate new metrics (Temporal+Seg_evaluation)
    # 3) decomposition==False: Evaluate through new metrics with common methods (Seg_evaluation)
    elif segmentation == True:
        # datasets = globals()[f'load_{dataset}'](window_size, stride, lamda_t, wavelet_num, decomposition=decomposition, segmentation=segmentation)
        x_tests = datasets['x_test']
#         y_tests, y_segment_tests = datasets['y_test'], datasets['y_segment_test']
        if decomposition == True:
            test_residual = datasets['x_test_resid']
        
        per_window_idx = []
        data_num = 0
        # 2) if decomposition == True
        if decomposition == True:
            residual_X_test = test_residual[data_num]

            # 1-2) temporal=True, decomposition=True, segmentation=True
            if temporal == True:
                X_test_ax = ax_tests[data_num]                    
                model = Temporal_AE_model # (X_train_ax, residual_X_train)
                scores, metric_scores = compute_anomaly_scores(residual_X_test, model.predict([X_test_ax, residual_X_test]))
#                 test_scores = compute_metrics(scores, y_tests[data_num], y_segment_tests[data_num])
            else:
            # 2-2) temporal=False, decomposition=True, segmentation=True
                if model_name == "MS-RNN":
                    model = AE_model # (residual_X_train)
                    rec_x = np.mean([np.flip(rec, axis=1) for rec in model.predict(residual_X_test)], axis=0)
                    scores, metric_scores = compute_anomaly_scores(residual_X_test, rec_x, scoring='square_median')
#                     test_scores = compute_metrics(scores, y_tests[data_num], y_segment_tests[data_num])
                else:                
                    model = AE_model # (residual_X_train)
                    scores, metric_scores = compute_anomaly_scores(residual_X_test, model.predict(residual_X_test))
#                     test_scores = compute_metrics(scores, y_tests[data_num], y_segment_tests[data_num])      
                           
#         th_index = test_scores['f1'].index(max(test_scores['f1']))
#         threshold = test_scores['thresholds'][th_index]            
                     
    return scores, metric_scores