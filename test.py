from numpy import *

def adjFunc(pos):
        arr = [(1,0), (-1,0), (0,1), (0,-1)]
        return [tuple(pos[j] + arr[i][j] for j in range(len(arr[i]))) for i in range(len(arr))]
        