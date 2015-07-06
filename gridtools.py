import numpy as np
from gameoflife import addToTuple

def countLiveCells(grid):
    """ Returns the number of live cells in the grid.
        
        If the cells have multiple lives, returns the total number of lives. """
    count = 0
    for val in np.nditer(grid):
        count += val
    return count

def cluster(grid, adjGrid):
    """ Returns the probability that neighbors of live cells are live
   
        This can be used as a measure of "randomness" of the grid -- i.e. if the
        grid is completely random, then this should roughly equal 1 - 2f + 2f^2,
        where f is the fraction of live cells. """
    if countLiveCells(grid) == 0:
        return 0 # nothing is alive; cluster is 0
    it = np.nditer(grid, flags=['multi_index'])
    matches = 0 # number of cells that match their neighbors
    total = 0 # total number of cells
    while not it.finished:
        flag = False
        for x in it.multi_index:
            if x == 0:
                flag = True
        if flag:
            it.iternext()
            continue # do not record situations where we're in dead zone of grid
        
        # add -1 to coordinate, since first row/col of grid are 0
        for adj in adjGrid[addToTuple(it.multi_index, -1)]:
            # do not record situations where adjacent cell is in dead zone
            if adj[0] != 0:
                # we only care about live cell matches
                if grid[it.multi_index] == 1:
                    total+= 1
                    if grid[tuple(adj)] == 1:
                        matches += 1
        it.iternext()
    return matches/total
    