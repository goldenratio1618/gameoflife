import os
import sys
from time import sleep

class CmdInterface:
    def __init__(self, game):
        self.game = game
    
    def run(self, steps, delay):
        for step in range(steps):
            grid_str = "STEP: " + str(step) + "\n"
            for i in range(self.game.dim[0]):
                for j in range(self.game.dim[1]):
                    if self.game.grid[i][j].val:
                        grid_str += "X"
                    else:
                        grid_str += " "
                grid_str += "\n"
            # cross-platform way to clear command prompt, for the next round of
            # printing the grid
            os.system('cls' if os.name == 'nt' else 'clear')
            print(grid_str)
            sys.stdout.flush()
            self.game.evolve2D()
            sleep(delay)