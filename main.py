from gameoflife import Game
from gui import GUI
from sys import stdout
from copy import deepcopy
from cmdline import CmdInterface
from timeit import default_timer as timer


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

game = Game(Game.genRandGrid((size, size), prob=0.5), dim=(size,size), adjFunc=Game.torusAdjFunc)
game.smallWorldIfy(1)
#print(game.adjGrid)
"""
for i in range(1000):
    print(i)
    sys.stdout.flush()
    game.evolve2D()
"""
#GUI(game, delay=100)
cmd = CmdInterface(game)
start = timer()
cmd.run(1000, 0, 0)
dt = timer() - start
print("1000 evolve steps created in %f s" % dt)
"""
ORIGINAL (before Numpy refactoring):
45.74s for only printing
94.28s for only evolving the game (no printing)

UPDATE 1 (after Numpy refactoring, before CPU compilation with Accelerate):
100.59s for only evolving the game (no printing)


"""