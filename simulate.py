﻿from copy import deepcopy
from math import floor
import cmath
from numbapro import cuda
from numba import *
import numpy as np
from timeit import default_timer as timer
from random import randrange

""" Code for initializing fitness values for each location in grid."""
def initFitnesses(dim, payoffMatrix, adjGrid, grid):

def computeFitness(dim, payoffMatrix, adjGrid, grid, loc):
    """ Computes the fitness of the individual at location loc. """
    payoff = 0
    for adjLoc in adjGrid[loc]:
        payoff += grid[adjLoc]

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
        return dim
    arr = dirFromNum(val, ldim)
    adj = np.add(arr, pos)

    for i in range(ldim):
        if adj[i] < 0:
            adj[i] += dim[i]
        elif adj[i] >= dim[i]:
            adj[i] -= dim[i]

    return adj
    
def randomizedAdjFunc(prevAdjFunc, dim, pos, currTuple, dist, jumpProb):
    """ Implements a randomized adjacency function.

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
  
  
def dirFromNum(val, ldim):
    """ Returns the direction corresponding to an integer.

        Used to generate adjacency tables (i.e. the "space"). Operates using
        base 3, but excludes same point (0,0,...,0). Assumes the grid
        is Cartesian. Output will be a difference vector in the form of an
        array, which must be added to the current vector. Assumes val does
        not exceed maximum value (3^ldim-1). """
    maxVal = 3 ** ldim - 1
    if val >= maxVal / 2:
        val += 1
    arr = np.zeros(ldim, dtype=np.int32)
    # convert to base 3, for the conversion
    for i in range(ldim):
        arr[ldim - i - 1] = val % 3 - 1
        val = val // 3
    return arr  
  

""" Below are a variety of useful operations on the grid. """





def initAdjGrid(adjFunc, dim, extraSpace):
    """ Initializes a grid from an adjacency function.
    
        Elements of the grid are arrays of coordinates (in array form) 
        of adjacent points, according to the adjacency function. The amount
        of extra connections that can be added is specified by the extraSpace
        parameter. """
    
    ldim = len(dim)
    buffer = (3 ** ldim - 1) * extraSpace
    adjGrid = np.zeros(tuple(dim) + (buffer, ldim), dtype=np.int32)
    # the array we iterate over, to get the multi_index of the iterator
    iter_arr = np.empty(tuple(dim) + (buffer,), dtype=np.int8)
    it = np.nditer(iter_arr, flags=['multi_index'])
    while not it.finished:
        adjGrid[it.multi_index] = adjFunc(np.array(it.multi_index), dim)
        it.iternext()
    return adjGrid

@autojit
def getHubs(numHubs, ldim, adjGridShape):
    hubs = np.empty((len(numHubs), ldim))
    
    filled = 0
    count = 0
    allVertices = np.empty(adjGridShape[0:ldim])
    it = np.nditer(allVertices, flags=['multi_index'])
    while not it.finished:
        if count in numHubs:
            hubs[filled] = np.array(it.multi_index)
            filled += 1
        count += 1
        it.iternext()

    if filled != len(hubs):
        print("WARNING: Incorrect number of hubs.")
    
    return hubs

@autojit
def smallWorldIfyHeterogeneous(adjGrid, jumpProb, heterogeneity=0, replace=True):
    """ Turns the adjacency grid into a small-world network.
        This works as follows: for each edge, we rewire it into
        a random edge (with the same starting vertex) with a given
        probability, if replace. Otherwise, we simply add extra edges.
        The SWN will have tunable heterogeneity. Unlike other method,
        new edges are COMPLETELY random - they do not have same starting vertex.
        Assumes initial adjGrid is torus-like."""
    # we need to iterate over this to keep tuples intact
    ldim = len(adjGrid.shape) - 2
    dim = adjGrid.shape[0:ldim]
    iter_arr = np.empty(adjGrid.shape[0:ldim+1], dtype=np.int8)
    dim = np.array(dim)
    it = np.nditer(iter_arr, flags=['multi_index'])
    maxIndex = 3 ** ldim - 1
    
    numVertices = np.prod(adjGrid.shape[0:ldim])
    hubs = getHubs(np.random.choice(numVertices, (1 - heterogeneity) * numVertices, replace=False), ldim, adjGrid.shape)
    
    
    print("Number of hubs: " + len(hubs))

    while not it.finished:
        # only consider left-facing edges (plus down) - that way we
        # count each edge exactly once (the other edges will be counted
        # when we iterate to the corresponding neighbor vertices).
        if it.multi_index[ldim] >= maxIndex / 2:
            it.iternext()
            continue

        # do not change this edge
        if np.random.random() > jumpProb:
            it.iternext()
            continue

        # the edge we are about to remove
        loc = it.multi_index[0:ldim]
        adjLoc = tuple(adjGrid[it.multi_index])

        
        # an edge already exists bewtween the two new locations (i.e. we need to resample)
        edgeExists = True
        # new, random locations for the new edge
        while edgeExists:
            # one of the locations must be a hub
            newLocPos = randrange(0, len(hubs))
            newLoc = tuple(hubs[newLocPos])
            newAdjLoc = getRandLoc(dim, newLoc)
            edgeExists = False
            # check if an edge already exists between these two vertices
            for i in range(len(adjGrid[newLoc])):
                if (adjGrid[newLoc + (i,)] == newAdjLoc).all():
                    edgeExists = True
        
        
        
        # add edge from newLoc to newAdjLoc
        # to do this we replace first available blank space
        added = False
        for i in range(len(adjGrid[newLoc])):
            if (adjGrid[newLoc + (i,)] == dim).all():
                adjGrid[newLoc + (i,)] = np.array(newAdjLoc)
                added = True
                break
        
        # add reverse edge from newAdjLoc to newLoc
        addedRev = False
        for i in range(len(adjGrid[newAdjLoc])):
            if (adjGrid[newAdjLoc + (i,)] == dim).all():
                adjGrid[newAdjLoc + (i,)] = np.array(newLoc)
                addedRev = True
                break
        
        # we never added edge: print warning message and continue
        # to next location
        if not added:
            print("WARNING: Failed to write edge from " + str(newLoc) + " to " +
                  str(tuple(newAdjLoc)) + ". Try adding more extra space.")
            it.iternext()
            continue

        if not addedRev:
            print("WARNING: Failed to write edge from " + str(newAdjLoc) + " to " +
                  str(tuple(newLoc)) + ". Try adding more extra space.")
            it.iternext()
            continue
           
        # remove original edges
        if replace:
            # delete original forwards edge from loc to adjLoc
            adjGrid[it.multi_index] = dim

            # remove backwards edge from adjLoc to loc
            for i in range(len(adjGrid[adjLoc])):
                if (adjGrid[adjLoc + (i,)] == np.array(loc)).all():
                    adjGrid[adjLoc + (i,)] = dim
                    break

        it.iternext()
    
@autojit
def smallWorldIfy(adjGrid, jumpProb):
    """ Turns the adjacency grid into a small-world network.
        This works as follows: for each edge, we rewire it into
        a random edge (with the same starting vertex) with a given
        probability. Assumes initial adjGrid is torus-like."""
    # we need to iterate over this to keep tuples intact
    ldim = len(adjGrid.shape) - 2
    dim = adjGrid.shape[0:ldim]
    iter_arr = np.empty(adjGrid.shape[0:ldim+1], dtype=np.int8)
    dim = np.array(dim)
    it = np.nditer(iter_arr, flags=['multi_index'])
    maxIndex = 3 ** ldim - 1

    while not it.finished:
        # only consider left-facing edges (plus down) - that way we
        # count each edge exactly once (the other edges will be counted
        # when we iterate to the corresponding neighbor vertices).
        if it.multi_index[ldim] >= maxIndex / 2:
            it.iternext()
            continue

        # do not change this edge
        if np.random.random() > jumpProb:
            it.iternext()
            continue

        # the location in question, and the adjacent location
        loc = it.multi_index[0:ldim]
        adjLoc = tuple(adjGrid[it.multi_index])

        # new, random location that the edge will connect to
        newLoc = getRandLoc(dim, loc)
        
        # add backwards edge from newLoc to loc
        # to do this we replace first available blank space
        added = False
        for i in range(len(adjGrid[newLoc])):
            if (adjGrid[newLoc + (i,)] == dim).all():
                adjGrid[newLoc + (i,)] = np.array(loc)
                added = True
                break
        
        # we never added edge: print warning message and continue
        # to next location
        if not added:
            print("WARNING: Failed to write edge from " + str(loc) + " to " +
                  str(tuple(newLoc)) + ". Try adding more extra space.")
            it.iternext()
            continue


        # replace forwards edge with random edge (not to same vertex)
        adjGrid[it.multi_index] = np.array(newLoc)

        # remove backwards edge from adjLoc to loc
        for i in range(len(adjGrid[adjLoc])):
            if (adjGrid[adjLoc + (i,)] == np.array(loc)).all():
                adjGrid[adjLoc + (i,)] = dim
                break

        it.iternext()


    
def getRandLoc(dim, loc=None):
    """ Generates a random location in the grid, that isn't loc. """
    newLoc = tuple(np.random.randint(0, dim[i]) for i in range(len(dim)))
    while newLoc == loc:
        newLoc = tuple(np.random.randint(0, dim[i]) for i in range(len(dim)))
    return newLoc



    
def getRandEdge(adjGrid, dim):
    """ Gets a random edge in the adjacency grid. """
    loc = getRandLoc(dim)
    # we need a location that has an edge from it
    while len(adjGrid[loc]) is 0:
        loc = genRandLoc(dim)
    loc2 = adjGrid[loc][np.random.randint(0,len(adjGrid[loc]))]
    return [loc, loc2]



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
                # if adjGrid is configured, a placeholder value of dim
                # will result in a 0 being looked up (as desired)
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