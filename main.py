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
    #game = Game(genRandGrid(dim, prob=0.5), dim, lambda d, pos, currTuple, dist:
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

if __name__ == '__main__':
    main()
