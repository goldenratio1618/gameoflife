from copy import deepcopy
from math import floor
from numbapro import cuda
from numba import *
import numpy as np

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
            arr += stdAdjFunc(dim[1:], rmFirst(pos), currTuple + (new_pos,), dist)
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
        arr += torusAdjFunc(dim[1:], rmFirst(pos),
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
    if np.random.random() < jumpProb:
        arr[np.random.randint(0, len(arr))] = getRandLoc(dim)
    return arr
  
  
  
  

""" Below are a variety of useful operations on the grid. """
def rmFirst(t):
    """ Removes the first element of a tuple. """
    return tuple(t[i] for i in range(1, len(t)))

def initAdjGrid(adjFunc, dim):
    """ Initializes a grid from an adjacency function.
    
        Elements of the grid are lists of coordinates of adjacent
        points, according to the adjacency function.
    """
    adjGrid = np.empty(tuple(dim), dtype=object)
    it = np.nditer(adjGrid, flags=['multi_index', 'refs_ok'],
        op_flags=['writeonly'])
    while not it.finished:
        adjGrid[it.multi_index] = adjFunc(it.multi_index)
        it.iternext()
    return adjGrid
    
def convAdjGrid(adjGrid, dim):
    """ Converts the adjacency grid from a Numpy object array to the much more
        efficient int16 array (which supports grids up to 32767 rows or columns)
        
        So as to enable Numpy to store this array as an array of integers,
        rather than objects (in particular, lists of tuples), "placeholder"
        values of [-1, -1] are inserted - this allows Numpy to use int8
        data-type, but the placeholder values have to be discounted.
        
        This method needs to be run after all adjGrid conversions have been
        completed.
    """
    # size of adjGrid, not including internal arrays
    size = adjGrid.shape
    # maximum length - this will be incorporated into the new shape
    maxLen = 0
    it = np.nditer(adjGrid, flags=['multi_index', 'refs_ok'],
        op_flags=['readonly'])
    while not it.finished:
        if maxLen < len(adjGrid[it.multi_index]):
            maxLen = len(adjGrid[it.multi_index])
        it.iternext()
    # number of elements in each tuple is the number of dimensions
    newGrid = np.full(size + (maxLen, len(dim)), -1, dtype=np.int16)
    it = np.nditer(adjGrid, flags=['multi_index', 'refs_ok'],
        op_flags=['readonly'])
    while not it.finished:
        for adjPos in range(len(adjGrid[it.multi_index])):
            for coord in range(len(dim)):
                # copy element over to new grid
                newGrid[it.multi_index][adjPos][coord] =\
                    adjGrid[it.multi_index][adjPos][coord]
        it.iternext()
    return newGrid
    
    
    
def getRandLoc(dim, loc=None):
    """ Generates a random location in the grid, that isn't loc. """
    newLoc = tuple(np.random.randint(0, dim[i]) for i in range(len(dim)))
    while newLoc == loc:
        newLoc = tuple(np.random.randint(0, dim[i]) for i in range(len(dim)))
    return newLoc
    
def genRandGrid(dim, prob=0.5):
    """ Generates a random grid, with each cell having a given probability
        of being alive. """
    grid = np.random.random(tuple(dim))
    alive = grid < prob
    intGrid = np.zeros(tuple(dim), dtype=np.int8) # make an integer grid
    intGrid[alive] = 1
    return intGrid
    
def addToTuple(tp, num):
    l = len(tp)
    newTp = np.array(tp)
    for i in range(l):
        newTp[i] += num
    return tuple(newTp)

def configure(grid, adjGrid):
    """ Configures grid and adjGrid for higher efficiency, i.e no using that
        troublesome if statement. """
    dim = addToTuple(grid.shape, 1)
    newGrid = np.zeros(dim, dtype=np.int8)
    it = np.nditer(grid, flags=['multi_index'], op_flags=['readonly'])
    while not it.finished:
        newGrid[addToTuple(it.multi_index, 1)] = grid[it.multi_index]
        it.iternext()
    
    newAdjGrid = np.empty_like(adjGrid)
    it = np.nditer(grid, flags=['multi_index'], op_flags=['readonly'])
    while not it.finished:
        newAdjGrid[it.multi_index] = adjGrid[it.multi_index] + 1
        it.iternext()
    return (newGrid, newAdjGrid)
    
    
""" Evolution methods. These are placed outside the class for clarity, and to
    enable easier compiling or parallelization."""
def evolve(dim, grid, adjGrid):
    """ The original evolve function of the game of life. 
        Works for grids of any dimension, but may be slower."""
    # copy the grid so that further changes aren't decided by previous ones
    newGrid = np.zeros(dim, dtype=np.int8)
    it = np.nditer(grid, flags=['multi_index'], op_flags=['readonly'])
    while not it.finished:
        numAlive = 0
        for adj in adjGrid[it.multi_index]:
            # avoid placeholder values
            if adj[0] != -1:
                numAlive += grid[tuple(adj)]
        if numAlive == 3 or (numAlive == 2 and grid[it.multi_index] == 1):
            newGrid[it.multi_index] = 1
        it.iternext()
    return newGrid
   
@autojit
def evolve2D(rows, cols, grid, adjGrid):
    """ Like evolve, but only compatible with 2D arrays. Uses loops rather than
        iterators, so hopefully easier to parallelize. Assumes grid and adjGrid
        are what they should be for dim = [rows, cols] (AND ARE CONFIGURED.)"""
    newGrid = np.zeros_like(grid)
    maxLen = len(adjGrid[0,0])
    # first row and column are 0s according to configure - they should stay that
    for i in range(1,rows+1):
        for j in range(1,cols+1):
            numAlive = 0
            for k in range(maxLen):
                # if adjGrid is configured, a placeholder value of (-1, -1) will
                # result in a 0 being looked up in grid.
                numAlive += grid[adjGrid[i-1,j-1,k,0], adjGrid[i-1,j-1,k,1]]

            if numAlive == 3 or (numAlive == 2 and grid[i,j] == 1):
                newGrid[i,j] = 1
    return newGrid
    
class Game:
    """ Initializes the  The grid will be a numpy array of Cell objects.
        It is possible to specify the grid, the dimension, and/or the adjacency
        function. """
    def __init__(self, grid=None, dim=np.array([10,10]), adjFunc=None):
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
    
    def evolve2D_self(self):
        self.grid = evolve2D(self.dim[0], self.dim[1], self.grid, self.adjGrid)
    
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
            changePos = np.random.randint(0, len(adj))
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