from copy import deepcopy
from numpy import *
from math import floor
    
class Game:
    """ A list of useful static functions."""
    @staticmethod
    def rmFirst(t):
        """ Removes the first element of a tuple. """
        return tuple(t[i] for i in range(1, len(t)))
        
    @staticmethod
    def initAdjGrid(adjFunc, dim):
        adjGrid = empty(dim, dtype=object)
        it = nditer(adjGrid, flags=['multi_index', 'refs_ok'],
            op_flags=['writeonly'])
        while not it.finished:
            adjGrid[it.multi_index] = adjFunc(it.multi_index)
            it.iternext()
        return adjGrid
    
    @staticmethod
    def stdAdjFunc(dim, pos, currTuple, dist):
        """ Returns all adjacent locations to a given position. """
        if len(dim) == 0:
            return [currTuple]
        arr = []
        for j in range(-dist, dist + 1):
            new_pos = pos[0] + j
            if new_pos >= 0 and new_pos < dim[0]:
                arr += Game.stdAdjFunc(Game.rmFirst(dim), Game.rmFirst(pos),
                        currTuple + (new_pos,), dist)
        if len(currTuple) == 0:
            arr.remove(pos)
        return arr
        
    @staticmethod
    def torusAdjFunc(dim, pos, currTuple, dist):
        """ Returns all adjacent locations to a given position. """
        if len(dim) == 0:
            return [currTuple]
        arr = []
        for j in range(-dist, dist + 1):
            new_pos = pos[0] + j
            arr += Game.torusAdjFunc(Game.rmFirst(dim), Game.rmFirst(pos),
                    currTuple + (new_pos % dim[0],), dist)
        if len(currTuple) == 0: 
            arr.remove(pos)
        return arr
        
    @staticmethod
    def smallWorldAdjFunc(prevAdjFunc, dim, pos, currTuple, dist, jumpProb):
        """ Implements the previous adjacency function, with a probability of
            the random jumps characteristic of small-world networks. """
        arr = prevAdjFunc(dim, pos, currTuple, dist)
        if random.random() < jumpProb:
            arr[random.randint(0, len(arr))] = Game.getRandLoc(dim)
        return arr
        
    @staticmethod
    def getRandLoc(dim, loc=None):
        """ Generates a random location in the grid, that isn't loc. """
        newLoc = tuple(random.randint(0, dim[i]) for i in range(len(dim)))
        while newLoc == loc:
            newLoc = tuple(random.randint(0, dim[i]) for i in range(len(dim)))
        return newLoc
        
    @staticmethod
    def genRandGrid(dim, prob=0.5):
        """ Generates a random grid, with each cell having a given probability
            of being alive."""
        grid = random.random(dim)
        dead = grid >= prob
        alive = grid < prob
        grid[dead] = 0
        grid[alive] = 1
        return grid
    
    
    
    
    
    """ grid will be a numpy array of Cell objects. """
    def __init__(self, grid=None, dim=(10,10), adjFunc=None):
        if grid is None:
            self.grid = Game.genRandGrid(dim)
        else:
            self.grid = grid
        if adjFunc is None:
            self.adjFunc = lambda pos: Game.stdAdjFunc(self.dim, pos, (), 1)
        else:
            self.adjFunc = lambda pos: adjFunc(self.dim, pos, (), 1)
        self.dim = dim
        self.adjGrid = Game.initAdjGrid(self.adjFunc, self.dim)
    
    
    def smallWorldIfy(self, jumpFrac):
        """ Turns the adjacency grid into a small-world network.
            The number of random jumps inserted is a proportion of the total
            number of distinct grid values. Connections are removed."""
        prod = 1
        for i in range(len(self.dim)):
            prod *= self.dim[i]
        
        for _ in range(floor(prod * jumpFrac)):
            # get the location we're about to switch
            loc = Game.getRandLoc(self.dim)
            # get all adjacent locations
            adj = self.adjGrid[loc]
            if len(adj) == 0:
                continue
            # this is the one we're switching
            changePos = random.randint(0, len(adj))
            # remove the other edge to loc
            adjLoc = self.adjGrid[adj[changePos]]
            if loc in adjLoc:
                adjLoc.remove(loc)
            # switch edge in loc
            adj[changePos] = Game.getRandLoc(self.dim, loc)
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
            loc = Game.getRandLoc(self.dim)
            # append a random location to our adjacent locations, and vice versa
            randLoc = Game.getRandLoc(self.dim, loc)
            self.adjGrid[loc].append(randLoc)
            self.adjGrid[randLoc].append(loc)
            
    
    
        
    def evolve2D(self):
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
                    
    
    def __str__(self):
        return str(self.grid)