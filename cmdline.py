import os
import sys
from time import sleep

class CmdInterface:
    def __init__(self, game):
        self.game = game
    
    def run(self, steps, delay, initDelay):
        """ Runs the Command-Line interface for a specified number of steps,
            or forever if the number of steps is specified to be -1."""
        step = 0
        while step < steps or steps == -1:
            grid_str = "STEP: " + str(step) + "\n"
            grid_str += CmdInterface.horizontalLine(self.game.dim[1])
            for i in range(self.game.dim[0]):
                grid_str += "|"
                for j in range(self.game.dim[1]):
                    if self.game.grid[i][j]:
                        grid_str += "X"
                    else:
                        grid_str += " "
                grid_str += "|\n"
            # cross-platform way to clear command prompt, for the next round of
            # printing the grid
            grid_str += CmdInterface.horizontalLine(self.game.dim[1])
            os.system('cls' if os.name == 'nt' else 'clear')
            print(grid_str)
            sys.stdout.flush()
            self.game.evolve2D()
            sleep(delay)
            if step == 0:
                # allow initial position to be more easily visible
                sleep(initDelay)
            step += 1
        
    @staticmethod
    def horizontalLine(dim):
        """Draws a horizontal line, with two vertical bars at either end."""
        line = "|"
        for _ in range(dim):
            line += "_"
        line += "|\n"
        return line