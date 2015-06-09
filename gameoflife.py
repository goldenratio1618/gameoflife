import random as rand
from copy import deepcopy
from math import floor

""" The basic element, representing the entity at each
    individual grid cell. Will be overridden to make other
    games of Life. """
class Cell:
    def __init__(self, val=None, pr=0.5):
        """ Initializes a cell with the specified value, or a random one if no
        value is provided."""
        if val == None:
            self.val = Cell.genRandVal(pr)
        else:
            self.val = val
        
    @staticmethod
    def genRandVal(pr):
        """ Returns a random value for a Cell object (with probability pr of
            being alive); the default is either a 0 or 1 """
        if rand.random() < pr:
            return 1
        else:
            return 0
        
    def __str__(self):
        return str(self.val)
        
    def getColor(self):
        """ Returns the "color" of this object - black if 1, white if 0. """
        if self.val == 1:
            return "black"
        else:
            return "white"
    
    
class Game:
    """ grid will be a list array of Cell objects. """
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
        self.adjGrid = Game.initAdjGrid(self.adjFunc, self.dim, ())
    
    @staticmethod
    def rmFirst(t):
        """ Removes the first element of a tuple. """
        return tuple(t[i] for i in range(1, len(t)))
        
    @staticmethod
    def initAdjGrid(adjFunc, dim, pos):
        if len(dim) == 0:
            return adjFunc(pos)
        else:
            adjGrid = []
            for i in range(dim[0]):
                adjGrid.append(Game.initAdjGrid(adjFunc, Game.rmFirst(dim),
                        pos + (i,)))
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
            adj = Game.arrOfTuple(self.adjGrid, loc)
            if len(adj) == 0:
                continue
            # this is the one we're switching
            changePos = rand.randint(0, len(adj) - 1)
            # remove the other edge to loc
            adjLoc = Game.arrOfTuple(self.adjGrid, adj[changePos])
            if loc in adjLoc:
                adjLoc.remove(loc)
            # switch edge in loc
            adj[changePos] = Game.getRandLoc(self.dim, loc)
            # now add the reverse edge
            Game.arrOfTuple(self.adjGrid, adj[changePos]).append(loc)
            

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
            Game.arrOfTuple(self.adjGrid, loc).append(randLoc)
            Game.arrOfTuple(self.adjGrid, randLoc).append(loc)
            
    
    @staticmethod
    def arrOfTuple(a, t):
        """ Returns the position in an array corresponding to a given tuple. """
        x = a
        for i in t:
            x = x[i]
        return x
        
    @staticmethod
    def smallWorldAdjFunc(prevAdjFunc, dim, pos, currTuple, dist, jumpProb):
        """ Implements the previous adjacency function, with a probability of
            the random jumps characteristic of small-world networks. """
        arr = prevAdjFunc(dim, pos, currTuple, dist)
        if rand.random() < jumpProb:
            arr[rand.randint(0, len(arr) - 1)] = Game.getRandLoc(dim)
        return arr
        
    @staticmethod
    def getRandLoc(dim, loc=None):
        """ Generates a random location in the grid, that isn't loc. """
        newLoc = tuple(rand.randint(0, dim[i] - 1) for i in range(len(dim)))
        while newLoc == loc:
            newLoc = tuple(rand.randint(0, dim[i] - 1) for i in range(len(dim)))
        return newLoc
        
    @staticmethod
    def genRandGrid(dim, prob=0.5):
        if len(dim) == 0:
            return Cell(pr=prob)
        arr = []
        for i in range(dim[0]):
            arr.append(Game.genRandGrid(Game.rmFirst(dim), prob))
        return arr
    
    @staticmethod
    def gridToStr(grid, dim):
        if len(dim) == 0:
            # only one cell left, so grid is a Cell, not a grid
            return str(grid)
        
        s = "["
        for i in range(dim[0]):
            s += Game.gridToStr(grid[i], Game.rmFirst(dim))
            if i != dim[0] - 1:
                # don't add a comma after the last array element
                s += ", "
        s += "]"
        return s
    
        
    def evolve2D(self):
        """ The original evolve function of the game of life. Assumes possible
            states are 0 (dead) and 1 (alive), and that the grid is 2D. """
        if len(self.dim) != 2:
            raise ValueError("ERROR: evolve2D only works with 2D grids.")
        # copy the grid so that further changes aren't decided by previous ones
        gr = deepcopy(self.grid)
        # pre-initialize zero and one cells
        zero = Cell(0)
        one = Cell(1)
        for i in range(self.dim[0]):
            for j in range(self.dim[1]):
                numAlive = 0
                for adj in self.adjGrid[i][j]:
                    numAlive += gr[adj[0]][adj[1]].val
                if numAlive < 2 or numAlive > 3:
                    self.grid[i][j] = zero
                elif numAlive == 3 and self.grid[i][j].val == 0:
                    self.grid[i][j] = one
                    
    
    def __str__(self):
        return Game.gridToStr(self.grid, self.dim)