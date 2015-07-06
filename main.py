from gameoflife import *
from gui import GUI
from gridtools import cluster, countLiveCells
from sys import stdout
from copy import deepcopy
from cmdline import run, run_GPU
from timeit import default_timer as timer
import numpy as np

#grid = []
size = 192
"""
for a in range(size):
    row = []
    for b in range(size):
        row.append(0)
    grid.append(row)

# Makes an R-pentomino
grid[size//2 - 1][size//2] = 1
grid[size//2 - 1][size//2 + 1] = 1
grid[size//2][size//2 - 1] = 1
grid[size//2][size//2] = 1
grid[size//2 + 1][size//2] = 1"""

dim = np.array([size,size])
#game = Game(genRandGrid(dim, prob=0.5), dim, lambda d, pos, currTuple, dist:
#            smallWorldAdjFunc(torusAdjFunc, d, pos, currTuple, dist, 1))
start = timer()
grid = genRandGrid(dim, prob=0.5)
dt = timer() - start
print("Time to generate grid: %f" % dt)
game = Game(grid, dim, torusAdjFunc)
#print(game.adjGrid)
"""
for i in range(1000):
    print(i)
    sys.stdout.flush()
    game.evolve2D()
"""
#GUI(game, delay=100)
steps = 500

start = timer()
grid = run_GPU(game.grid, game.adjGrid, steps, 0, 0, 1, -1)
dt = timer() - start
print(str(steps) + " evolve steps created in %f s on GPU" % dt)
#start = timer()
#run(game, steps, 0, 0, 1, -1)
#dt = timer() - start
#print(str(steps) + " evolve steps created in %f s on CPU" % dt)

f = open("output7615.txt", "w")
f.writelines(gridToStr2D(grid))
f.writelines("\n\n\n")
f.writelines("# Live Cells = " + str(countLiveCells(grid)) + "\n")
f.writelines("Cluster = " + str(cluster(grid, game.adjGrid)))
f.close()

"""
ORIGINAL (before Numpy refactoring):
45.74s for only printing
94.28s for only evolving the game (no printing)

UPDATE 1 (after Numpy refactoring, before CPU compilation with Accelerate):
100.59s for only evolving the game (no printing)

UPDATE 2 (after Numpy refactoring for adjGrid as well, no Accelerate):
169.77s

UPDATE 3 (after Numpy refactoring, including int8 for adjGrid, still no Accelerate):
1120.25s

UPDATE 4 (code tweak)
490.39s

UPDATE 5 ("configuring" grid and AdjGrid to remove IF statement - still no Accelerate):
469.4s

UPDATE 6 (add AUTOJIT acceleration):
1.32s

**FASTER PERFORMANCE => MORE TESTS. FROM NOW ON, USING 5000 ITERATIONS**
5.77s

UPDATE 7 (with GPU enabled, Phase 1):
8.24s

UPDATE 8 (GPU enabled, Phase 2):
4.99s
"""