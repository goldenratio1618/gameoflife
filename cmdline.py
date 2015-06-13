import os
import sys
from time import sleep
from numba import autojit


class CmdInterface:
    def __init__(self, game):
        self.game = game
    
    @autojit
    def run(self, steps, delay, initDelay, printFlag, indSteps):
        """ Runs the Command-Line interface for a specified number of steps,
            or forever if the number of steps is specified to be -1."""
        step = 0
        while step < steps or steps == -1:
            if printFlag:
                grid_str = "STEP: " + str(step) + "\n"
                grid_str += CmdInterface.horizontalLine(self.game.dim[1])
                for i in range(self.game.dim[0]):
                    grid_str += "|"
                    for j in range(self.game.dim[1]):
                        # add 1 to support configured grids
                        if self.game.grid[i+1][j+1]:
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
            if indSteps is not -1 and step % indSteps is 0:
                print("Step = " + str(step))
            self.game.evolve2D_self()
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