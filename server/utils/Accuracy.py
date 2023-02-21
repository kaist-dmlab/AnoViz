"""Scoring Function Design Principles I
Avoid complex and opaque scoring functions We want a scoring function that..
Is a single number, for easy comparisons.
Does not have spurious location precision. If the ground truth says the anomaly is at say 1250, and an algorithm reports 1247 or 1254, it should be counted as correct. This problem is compound by the fact that different algorithms report the leading edge, the center or the trailing edge of a sliding window.
Has a binary score for each example, that can be combined to a real number for the full collection. 
Reports a number close to zero for a “random dart” algorithm (i.e. the default rate) and close to one for a perfect algorithm.

My suggestion
Let length of anomaly be L, L = end – begin
Let the prediction of an algorithm be an integer P
P is labeled as correct if: min(begin-L , begin-100 )  <  P  <  max(end+L, end+100 )
Why the ‘100’ case? Some anomalies can be as short as a single point. 
the only meaningful score is something like “207 out of 250”
"""
from math import ceil

def compute_accuracy(pred_segments, anomaly_segments, delta):
    correct = 0
    for seg in anomaly_segments:
        L = seg[-1] - seg[0] # length of anomaly
        d = ceil(L * delta)
        for pred in pred_segments:
            P = pred[len(pred) // 2] # center location as an integer
            
            if min([seg[0] - L, seg[0] - d]) < P < max([seg[-1] + L, seg[-1] + d]):
                correct = correct + 1
                break
    
    return correct, correct / (len(anomaly_segments) + 1e-7)