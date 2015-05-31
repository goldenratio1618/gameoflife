from gameoflife import Game, Cell
from gui import GUI
from sys import stdout
from copy import deepcopy
from cmdline import CmdInterface

z = Cell(0)
o = Cell(1)
grid = []
size = 100
for a in range(size):
    row = []
    for b in range(size):
        row.append(z)
    grid.append(row)

# Makes an R-pentomino
grid[size//2 - 1][size//2] = o
grid[size//2 - 1][size//2 + 1] = o
grid[size//2][size//2 - 1] = o
grid[size//2][size//2] = o
grid[size//2 + 1][size//2] = o

game = Game(grid, dim=(size,size))
#print(game.adjGrid)
"""
for i in range(1000):
    print(i)
    sys.stdout.flush()
    game.evolve2D()
"""
#GUI(game, delay=100)
cmd = CmdInterface(game)
cmd.run(1000, 0)