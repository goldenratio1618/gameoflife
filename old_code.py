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
        
    
        
    def __str__(self):
        return str(self.val)
        
    def getColor(self):
        """ Returns the "color" of this object - black if 1, white if 0. """
        if self.val == 1:
            return "black"
        else:
            return "white"
            
        @staticmethod
    def genRandVal(pr):
        """ Returns a random value for a Cell object (with probability pr of
            being alive); the default is either a 0 or 1 """
        if rand.random() < pr:
            return 1
        else:
            return 0
            
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
     
    @staticmethod
    def rmFirst(t):
        """ Removes the first element of a tuple. """
        return tuple(t[i] for i in range(1, len(t)))
        
        
    
    @autojit
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
                    
                    
@cuda.jit(argtypes=[uint32, uint32, uint8[:,:], uint16[:,:,:,:]])
""" Like evolve, but only compatible with 2D arrays. Uses loops rather than
        iterators, so hopefully easier to parallelize. Assumes grid and adjGrid
        are what they should be for dim = dimArr[0:1] (AND ARE CONFIGURED.)
        dimArr is [rows, cols, maxLen]"""
    rows = grid.shape[0] - 1
    maxLen = adjGrid.shape[2]
    cols = grid.shape[1] - 1
    # we'll only parallelize two dimensions - the third for loop may be quite
    # short, and thus not worth parallelizing as some cores may be idle.
    startX, startY = cuda.grid
    gridX = cuda.gridDim.x * cuda.blockDim.x;
    gridY = cuda.gridDim.y * cuda.blockDim.y;
    for i in range(startX, rows, gridX):
        for j in range(startY, cols, gridY):
            numAlive = 0
            for k in range(maxLen):
                # if adjGrid is configured, a placeholder value of (-1, -1) will
                # result in a 0 being looked up in grid.
                numAlive += grid[adjGrid[i,j,k,0], adjGrid[i,j,k,1]]

            if numAlive == 3 or (numAlive == 2 and grid[i,j] == 1):
                newGrid[i+1,j+1] = 1
                
                
                
                
 

def countLiveCells(grid, adjGrid, i, j, maxLen):
    numAlive = 0
    for k in range(maxLen):
        # if adjGrid is configured, a placeholder value of (-1, -1) will
        # result in a 0 being looked up in grid.
        numAlive += grid[adjGrid[i,j,k,0], adjGrid[i,j,k,1]]
    return numAlive
    
countLiveCells_GPU = cuda.jit(restype=uint8, argtypes=[uint8[:,:], 
    uint16[:,:,:,:], uint16, uint16, uint16], device=True)(countLiveCells)