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