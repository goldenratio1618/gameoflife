from copy import deepcopy
from math import floor
from numbapro import cuda
from numba import *
import numpy as np
from timeit import default_timer as timer

""" Below are a variety of adjacency functions, which can be used
    to generate grids of various topologies for the Game of Life. """
    
def stdAdjFunc(coord, dim):
    """ Returns all adjacent locations to a given position.
        Uses standard layout (with special edge/corner cases)"""
    ldim = len(dim)
    pos = coord[0:ldim]
    val = coord[ldim]
    # this adjacency function does not use this many adjacent locations
    if val >= 3 ** ldim - 1:
        return dim
    arr = dirFromNum(val, ldim)
    adj = np.add(arr, coord)

    for pos in adj:
        # position is not in grid; return "blank"
        if pos < 0 or pos >= ldim:
            return dim

    return adj
   
def torusAdjFunc(coord, dim):
    """ Returns all adjacent locations to a given position.
        Wraps around at edges and corners. """
    ldim = len(dim)
    pos = coord[0:ldim]
    # this adjacency function does not use this many adjacent locations
    val = coord[ldim]
    if val >= 3 ** ldim - 1:
        return np.full(ldim, ldim)
    arr = dirFromNum(val, ldim)
    adj = np.add(arr, pos)

    for i in range(ldim):
        if adj[i] < 0:
            adj[i] += dim[i]
        elif adj[i] >= dim[i]:
            adj[i] -= dim[i]

    return adj
    
def smallWorldAdjFunc(prevAdjFunc, dim, pos, currTuple, dist, jumpProb):
    """ Implements a small-world adjacency function.

        Implements the previous adjacency function, with a probability of
        the random jumps characteristic of small-world networks.
        Unlike smallWorldIfy, this does NOT generate bidirectional
        small-world networks, but instead introduces one-way "wormholes".
        Also, note that with this adjacency function, all outputs are of
        equal length - this means that every space has the same number of
        outgoing edges, but not necessarily the same number of incoming edges.
        The way the RNG works here is, for each edge there is a probability
        of it being replaced with a completely random edge.

        Note that "overrandom" networks, with more than 8 connections, can be
        created by using this function with a high jumpProb, and with extra 
        space (see initAdjGrid) """
    if np.random.random() < jumpProb:
        return np.array(getRandLoc(dim))
    else:
        return prevAdjFunc(dim, pos, currTuple, dist)
  
  
  
  

""" Below are a variety of useful operations on the grid. """
def dirFromNum(val, ldim):
    """ Returns the direction corresponding to an integer.

        Used to generate adjacency tables (i.e. the "space"). Operates using
        base 3, but excludes same point (0,0,...,0). Assumes the grid
        is Cartesian. Output will be a difference vector in the form of an
        array, which must be added to the current vector. """
    maxVal = 3 ** ldim - 1
    if val >= maxVal / 2:
        val += 1
    arr = np.zeros(ldim, dtype=np.int32)
    # convert to base 3, for the conversion
    for i in range(ldim):
        arr[ldim - i - 1] = val % 3 - 1
        val = val // 3
    return arr

def rmFirst(t):
    """ Removes the first element of a tuple. """
    return tuple(t[i] for i in range(1, len(t)))

def initAdjGrid(adjFunc, dim, extraSpace):
    """ Initializes a grid from an adjacency function.
    
        Elements of the grid are arrays of coordinates (in array form) 
        of adjacent points, according to the adjacency function. The amount
        of extra connections that can be added is specified by the extraSpace
        parameter. """
    
    ldim = len(dim)
    buffer = (3 ** ldim - 1) * extraSpace
    adjGrid = np.zeros(tuple(dim) + (buffer * extraSpace, ldim), dtype=np.int32)
    # the array we iterate over, to get the multi_index of the iterator
    iter_arr = np.empty(tuple(dim) + (buffer * extraSpace,), dtype=np.int8)
    it = np.nditer(iter_arr, flags=['multi_index'])
    while not it.finished:
        adjGrid[it.multi_index] = adjFunc(np.array(it.multi_index), dim)
        it.iternext()
    return adjGrid
    
def convAdjGrid(adjGrid, dim):
    """ Converts the adjacency grid from a Numpy object array to the much more
        efficient int32 array (which supports grids up to 32767 rows or columns)
        
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
    newGrid = np.full(size + (maxLen, len(dim)), -1, dtype=np.int32)
    it = np.nditer(adjGrid, flags=['multi_index', 'refs_ok'],
        op_flags=['readonly'])
    while not it.finished:
        for adjPos in range(len(adjGrid[it.multi_index])):
            for coord in range(len(dim)):
                # copy element over to new grid
                newGrid[it.multi_index][adjPos][coord] = \
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
    """ Generates a random grid with a given cell density. """
    grid = np.random.random(tuple(dim))
    alive = grid < prob
    intGrid = np.zeros(tuple(dim + 1), dtype=np.int8) # make an integer grid
    intGrid[alive] = 1
    return intGrid


def gridToStr2D(grid):
    """ Returns a string representation of grid, ignoring first row and column. """
    dim = grid.shape
    s = ""
    for i in range(1,dim[0]):
        s += "["
        for j in range(1,dim[1]):
            s += str(grid[i,j])
            if j is not dim[1] - 1:
                s += ", "
        s += "]\n"
    return s

    
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
             numAlive += grid[tuple(adj)]
        if numAlive == 3 or (numAlive == 2 and grid[it.multi_index] == 1):
            newGrid[it.multi_index] = 1
        it.iternext()
    return newGrid
   
@autojit
def evolve2D(rows, cols, grid, adjGrid, newGrid):
    """ Like evolve, but only compatible with 2D arrays. Uses loops rather than
        iterators, so hopefully easier to parallelize. Assumes grid and adjGrid
        are what they should be for dim = [rows, cols] (AND ARE CONFIGURED.)"""
    maxLen = len(adjGrid[0,0])
    for i in range(rows):
        for j in range(cols):
            numAlive = 0
            for k in range(maxLen):
                numAlive += grid[adjGrid[i,j,k,0], adjGrid[i,j,k,1]]

            if numAlive == 3 or (numAlive == 2 and grid[i,j] == 1):
                newGrid[i,j] = 1


@cuda.jit(argtypes=[uint8[:,:], uint32[:,:,:,:], uint8[:,:]])
def evolve2D_kernel(grid, adjGrid, newGrid):
    """ Like evolve, but only compatible with 2D arrays. Uses loops rather than
        iterators, so hopefully easier to parallelize. Assumes grid and adjGrid
        are what they should be for dim = dimArr[0:1] (AND ARE CONFIGURED.)
        dimArr is [rows, cols, maxLen] """
    rows = grid.shape[0] - 1
    maxLen = adjGrid.shape[2]
    cols = grid.shape[1] - 1
    startX, startY = cuda.grid(2)
    gridX = cuda.gridDim.x * cuda.blockDim.x
    gridY = cuda.gridDim.y * cuda.blockDim.y
    for i in range(startX, rows, gridX):
        for j in range(startY, cols, gridY):
            numAlive = 0
            for k in range(maxLen):
                # if adjGrid is configured, a placeholder value of (-1, -1)
                # will
                # result in a 0 being looked up in grid.
                numAlive += grid[adjGrid[i,j,k,0], adjGrid[i,j,k,1]]
            if numAlive == 3 or (numAlive == 2 and grid[i,j] == 1):
                newGrid[i,j] = 1
    
class Game:
    """ Initializes the game of life.
        The grid will be a numpy array of int8s, i.e. the alive/dead state,
        such that the last row and column are all 0s, and will always remain 0
        (this is so direct array indexing is possible, without having
        conditional statements). The specified dimension must be the dimension
        of the "real" grid, i.e. not including that last row and column.
        The adjacency function can be used to specify the geometry of the
        grid. """
    def __init__(self, grid=None, dim=np.array([10,10]),
                 adjFunc=stdAdjFunc, extraSpace=1):
        if grid is None:
            self.grid = genRandGrid(dim)
        else:
            self.grid = grid
        self.dim = dim
        start = timer()
        self.adjGrid = initAdjGrid(adjFunc, self.dim, extraSpace)
        dt = timer() - start
        print("Time to generate adjGrid: %f" % dt)

    def evolve2D_self(self):
        newGrid = np.zeros_like(self.grid)
        evolve2D(self.dim[0], self.dim[1], self.grid, self.adjGrid, newGrid)
        self.grid = newGrid
    
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
            # append a random location to our adjacent locations, and vice
            # versa
            randLoc = getRandLoc(self.dim, loc)
            self.adjGrid[loc].append(randLoc)
            self.adjGrid[randLoc].append(loc)
            
    def __str__(self):
        return str(self.grid)