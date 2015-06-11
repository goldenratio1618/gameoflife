from copy import deepcopy
from numpy import *
from math import floor
from numba import autojit # compile code to execute faster

""" Below are a variety of adjacency functions, which can be used
    to generate grids of various topologies for the Game of Life. """
    
def stdAdjFunc(dim, pos, currTuple, dist):
    """ Returns all adjacent locations to a given position.
        Uses standard layout (with special edge/corner cases)"""
    if len(dim) == 0:
        return [currTuple]
    arr = []
    for j in range(-dist, dist + 1):
        new_pos = pos[0] + j
        if new_pos >= 0 and new_pos < dim[0]:
            arr += stdAdjFunc(rmFirst(dim), rmFirst(pos),
                    currTuple + (new_pos,), dist)
    if len(currTuple) == 0:
        arr.remove(pos)
    return arr
    
def torusAdjFunc(dim, pos, currTuple, dist):
    """ Returns all adjacent locations to a given position.
        Wraps around at edges and corners. """
    if len(dim) == 0:
        return [currTuple]
    arr = []
    for j in range(-dist, dist + 1):
        new_pos = pos[0] + j
        arr += torusAdjFunc(rmFirst(dim), rmFirst(pos),
                currTuple + (new_pos % dim[0],), dist)
    if len(currTuple) == 0: 
        arr.remove(pos)
    return arr
    
def smallWorldAdjFunc(prevAdjFunc, dim, pos, currTuple, dist, jumpProb):
    """ Implements the previous adjacency function, with a probability of
        the random jumps characteristic of small-world networks.
        Unlike smallWorldIfy, this does NOT generate bidirectional
        small-world networks, but instead introduces one-way "wormholes"."""
    arr = prevAdjFunc(dim, pos, currTuple, dist)
    if random.random() < jumpProb:
        arr[random.randint(0, len(arr))] = getRandLoc(dim)
    return arr
  
  
  
  

""" Below are a variety of useful operations on the grid. """
def rmFirst(t):
    """ Removes the first element of a tuple. """
    return tuple(t[i] for i in range(1, len(t)))

def initAdjGrid(adjFunc, dim):
    """ Initializes a grid from an adjacency function.
    
        Elements of the grid are lists of coordinates (tuples) of adjacent
        points, according to the adjacency function.
    """
    adjGrid = empty(dim, dtype=object)
    it = nditer(adjGrid, flags=['multi_index', 'refs_ok'],
        op_flags=['writeonly'])
    while not it.finished:
        adjGrid[it.multi_index] = adjFunc(it.multi_index)
        it.iternext()
    return adjGrid

def getRandLoc(dim, loc=None):
    """ Generates a random location in the grid, that isn't loc. """
    newLoc = tuple(random.randint(0, dim[i]) for i in range(len(dim)))
    while newLoc == loc:
        newLoc = tuple(random.randint(0, dim[i]) for i in range(len(dim)))
    return newLoc
    
def genRandGrid(dim, prob=0.5):
    """ Generates a random grid, with each cell having a given probability
        of being alive. """
    grid = random.random(dim)
    alive = grid < prob
    intGrid = zeros(dim, dtype=int8) # make an integer grid
    intGrid[alive] = 1
    return intGrid
    
    
    
    
""" Evolution methods. These are placed outside the class for clarity, and to
    enable easier compiling or parallelization."""
def evolve(dim, grid, adjGrid):
    """ The original evolve function of the game of life. """
    # copy the grid so that further changes aren't decided by previous ones
    newGrid = zeros(dim, dtype=int8)
    it = nditer(grid, flags=['multi_index', 'refs_ok'],
        op_flags=['readonly'])
    while not it.finished:
        numAlive = 0
        for adj in adjGrid[it.multi_index]:
            numAlive += grid[adj]
        if numAlive == 3 or (numAlive == 2 and grid[it.multi_index] == 1):
            newGrid[it.multi_index] = 1
        it.iternext()
    return newGrid

def evolve2D(dim, grid, adjGrid):
    """ Like evolve, but only compatible with 2D arrays. Uses loops rather than
        iterators, so hopefully easier to parallelize. """
    if len(dim) != 2:
        raise ValueError("ERROR: evolve2D only works with 2D grids.")
    newGrid = zeros(dim, dtype=int8)
    rows = dim[0]
    cols = dim[1]
    for i in range(rows):
        for j in range(cols):
            numAlive = 0
            for adj in adjGrid[i,j]:
                numAlive += grid[adj]
            if numAlive == 3 or (numAlive == 2 and grid[i,j] == 1):
                newGrid[i,j] = 1
    return newGrid
    
class Game:
    """ Initializes the  The grid will be a numpy array of Cell objects.
        It is possible to specify the grid, the dimension, and/or the adjacency
        function. """
    def __init__(self, grid=None, dim=(10,10), adjFunc=None):
        if grid is None:
            self.grid = genRandGrid(dim)
        else:
            self.grid = grid
        if adjFunc is None:
            self.adjFunc = lambda pos: stdAdjFunc(self.dim, pos, (), 1)
        else:
            self.adjFunc = lambda pos: adjFunc(self.dim, pos, (), 1)
        self.dim = dim
        self.adjGrid = initAdjGrid(self.adjFunc, self.dim)
    
    """def evolve2D_self(self):
        self.grid = evolve2D(self.dim, self.grid, self.adjGrid)"""
        
    def evolve2D_self(self):
        """ The original evolve function of the game of life. Assumes possible
            states are 0 (dead) and 1 (alive), and that the grid is 2D. """
        if len(self.dim) != 2:
            raise ValueError("ERROR: evolve2D only works with 2D grids.")
        # copy the grid so that further changes aren't decided by previous ones
        gr = deepcopy(self.grid)
        for i in range(self.dim[0]):
            for j in range(self.dim[1]):
                numAlive = 0
                for adj in self.adjGrid[i,j]:
                    numAlive += gr[adj]
                if numAlive < 2 or numAlive > 3:
                    self.grid[i,j] = 0
                elif numAlive == 3 and self.grid[i,j] == 0:
                    self.grid[i,j] = 1
    
    def smallWorldIfy(self, jumpFrac):
        """ Turns the adjacency grid into a small-world network.
            The number of random jumps inserted is a proportion of the total
            number of distinct grid values. Connections are removed."""
        prod = 1
        for i in range(len(self.dim)):
            prod *= self.dim[i]
        
        for _ in range(floor(prod * jumpFrac)):
            # get the location we're about to switch
            loc = getRandLoc(self.dim)
            # get all adjacent locations
            adj = self.adjGrid[loc]
            # if we don't have any neighbors, abort since we can't switch
            if len(adj) == 0:
                continue
            # get new location that we're going to make adjacent to loc
            newLoc = getRandLoc(self.dim, loc)
            # if they're already neighbors, or equal, abort operation
            if (loc in self.adjGrid[newLoc]) or (newLoc in self.adjGrid[loc])\
                or loc == newLoc:
                continue
            # this is the location we're going to swap
            changePos = random.randint(0, len(adj))
            # remove the other edge to loc
            adjToChangeLoc = self.adjGrid[adj[changePos]]
            if loc in adjToChangeLoc:
                adjToChangeLoc.remove(loc)
            # switch edge in loc
            adj[changePos] = newLoc
            # now add the reverse edge
            self.adjGrid[adj[changePos]].append(loc)
            

    def smallWorldIfy_noremove(self, jumpFrac):
        """ Turns the adjacency grid into a small-world network.
            The number of random jumps inserted is a proportion of the total
            number of distinct grid values. Note that no connections are
            removed, so using this method increases overall connectivity of the
            grid (in slight deviation with Strogatz & Watts's model)."""
        prod = 1
        for i in range(len(self.dim)):
            prod *= self.dim[i]
        
        for _ in range(floor(prod * jumpFrac)):
            # get the location we're about to switch
            loc = getRandLoc(self.dim)
            # append a random location to our adjacent locations, and vice versa
            randLoc = getRandLoc(self.dim, loc)
            self.adjGrid[loc].append(randLoc)
            self.adjGrid[randLoc].append(loc)
            
    def __str__(self):
        return str(self.grid)