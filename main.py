from gameoflife import Game, genRandGrid, torusAdjFunc, convAdjGrid
from gui import GUI
from sys import stdout
from copy import deepcopy
from cmdline import CmdInterface
from timeit import default_timer as timer
import numpy as np


grid = []
size = 192
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
grid[size//2 + 1][size//2] = 1

dim = np.array([size,size])
game = Game(genRandGrid(dim, prob=0.5), dim, torusAdjFunc)
game.smallWorldIfy(1)
game.adjGrid = convAdjGrid(game.adjGrid, game.dim)
#print(game.adjGrid)
"""
for i in range(1000):
    print(i)
    sys.stdout.flush()
    game.evolve2D()
"""
#GUI(game, delay=100)
cmd = CmdInterface(game)
steps = 1000
start = timer()
cmd.run(steps, 0, 0, False)
dt = timer() - start
print(str(steps) + " evolve steps created in %f s" % dt)
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

UPDATE 4 
"""