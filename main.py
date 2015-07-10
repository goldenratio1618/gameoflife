from gameoflife import *
from gui import GUI
from gridtools import cluster, countLiveCells
from sys import stdout
from copy import deepcopy
from cmdline import run, run_GPU
from timeit import default_timer as timer
import numpy as np
import argparse

parser = argparse.ArgumentParser(description="Game of Life Analysis Frontend",
                                 epilog="")

parser.add_argument('-f', '--frac', help="Fraction of cells alive at beginning",
                    type=float, default=0.5)

parser.add_argument('-r', '--rows', help="Number of rows of the grid",
                    type=int, default=128)

parser.add_argument('-c', "--cols", help="Number of columns of the grid",
                    type=int, default=256)

parser.add_argument('-e', "--extraspace",
                    help="Amount of extra space to add to adjacency grid",
                    type=int, default=5)

parser.add_argument('-v', "--visible", help="Number of steps to show grid",
                    type=int, default=-1)

parser.add_argument('-n', "--niters", help=("Number of times to run simulation "
                                            "per each value of small world "
                                            "coefficient"),
                    type=int, default=1)

parser.add_argument('-l', "--simlength", help="Length of each simulation",
                    type=int, default=1000)

parser.add_argument('-ms', "--minswc", help="Minimum small world coefficient",
                    type=float, default=0)

parser.add_argument('-xs', "--maxswc", help="Maximum small world coefficient",
                    type=float, default=0)

parser.add_argument('-ss', "--stepswc", help="Step for small world coefficient",
                    type=float, default=1)

parser.add_argument('-o', "--output",
                    help=("Specify output format. Options:\n"
                           "0: do not output to file\n"
                           "1: output averages of final values across all "
                           "simulations per given small world coefficient\n"
                           "2: output final values for every simulation\n"
                           "3: output values for every step in every "
                           "simulation\n"
                           "4: output grid state at every step in every "
                           "simulation"),
                    type=int, default=1)

parser.add_argument('-d', "--debug", help="Enter debug mode",
                    action='store_true', default=False)

args = parser.parse_args()

print(args)


def main():
    #grid = []
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

    dim = np.array([128,256])
    #game = Game(genRandGrid(dim, prob=0.5), dim, lambda d, pos, currTuple,
    #dist:
    #            smallWorldAdjFunc(torusAdjFunc, d, pos, currTuple, dist, 1))
    start = timer()
    grid = genRandGrid(dim, prob=0.5)
    dt = timer() - start
    print("Time to generate grid: %f" % dt)
    game = Game(grid, dim, torusAdjFunc, 5)
    start = timer()
    smallWorldIfy(game.adjGrid,0.25)
    dt = timer() - start
    print("Time to smallWorldIfy: %f" % dt)
    #print(game.adjGrid)
    """
    for i in range(1000):
        print(i)
        sys.stdout.flush()
        game.evolve2D()
    """
    #GUI(game, delay=100)
    steps = 2000

    start = timer()
    grid = run_GPU(game.grid, game.adjGrid, steps, 0, 0, 2, -1)
    dt = timer() - start
    print(str(steps) + " evolve steps created in %f s on GPU" % dt)
    #start = timer()
    #run(game, steps, 0, 0, 1, -1)
    #dt = timer() - start
    #print(str(steps) + " evolve steps created in %f s on CPU" % dt)

    f = open("output71015.txt", "w")
    f.writelines(gridToStr2D(grid))
    f.writelines("\n\n\n")
    f.writelines("# Live Cells = " + str(countLiveCells(grid)) + "\n")
    f.writelines("Cluster = " + str(cluster(grid, game.adjGrid)))
    f.close()

    """
if __name__ == '__main__':
    main()
    """