﻿from gameoflife import *
from cmdline import *
from gui import GUI
from gridtools import cluster, countLiveCells
from sys import stdout
from copy import deepcopy
from timeit import default_timer as timer
import numpy as np
import argparse
import datetime

parser = argparse.ArgumentParser(description="Game of Life Analysis Frontend",
                                 epilog="")

parser.add_argument('-f', '--frac', help="Fraction of cells alive at beginning",
                    type=float, default=0.5) #
parser.add_argument('-r', '--rows', help="Number of rows of the grid",
                    type=int, default=128) #
parser.add_argument('-c', "--cols", help="Number of columns of the grid",
                    type=int, default=256) #
parser.add_argument('-e', "--extraspace",
                    help="Amount of extra space to add to adjacency grid",
                    type=int, default=5) #
parser.add_argument('-v', "--visible", help="Number of steps to show grid",
                    type=int, default=-1) #
parser.add_argument('-n', "--niters", help=("Number of times to run simulation "
                                            "per each value of small world "
                                            "coefficient"),
                    type=int, default=1) #
parser.add_argument('-l', "--simlength", help="Length of each simulation",
                    type=int, default=1000) #
parser.add_argument('-ms', "--minswc", help="Minimum small world coefficient",
                    type=float, default=0) #
parser.add_argument('-xs', "--maxswc", help="Maximum small world coefficient",
                    type=float, default=0) #
parser.add_argument('-ss', "--stepswc", help="Step for small world coefficient",
                    type=float, default=1) #
parser.add_argument('-o', "--output",
                    help=("Specify output format. Options:\n"
                           "0: do not output to file\n"
                           "1: output averages of final values across all "
                           "simulations per given small world coefficient\n"
                           "2: output final values for every simulation\n"
                           "3: output values for every step in every "
                           "simulation\n"
                           "4: output grid state at every step in every "
                           "simulation\n"
                           "Higher numbers also output everything for all lower"
                           " numbers, e.g. 3 will also output 2\n"),
                    type=int, default=1)

parser.add_argument('-d', "--debug", help="Enter debug mode",
                    action='store_true', default=False)

parser.add_argument('-s', "--sample", help="When using output modes 3 or 4, how often should the grid be sampled?",
                    type=int, default=10)

args = parser.parse_args()

start = datetime.datetime.now()
# this will be appended to the beginning of all datafiles to avoid overwriting
datestr = start.strftime("%m-%d-%Y_%H-%M-%S")
# add extra parameters
datestr += "_frac=" + str(args.frac) + "_rows=" + str(args.rows) + "_cols=" + \
    str(args.cols) + "_extraspace=" + str(args.extraspace) + "_niters=" + \
    str(args.niters) + "_simlength=" + str(args.simlength)

if args.output >= 1:
    # this file stores averages of final values across all simulations per swc
    outfile_avg = open("data1/" + datestr + ".txt", "w")
    # will be structured as a table with these 3 columns
    outfile_avg.writelines("SWC  LiveCells  Cluster\n")

def main():
    start = timer()
    dim = np.array([args.rows,args.cols])
    grid = genRandGrid(dim, prob=args.frac)
    game = Game(grid, dim, torusAdjFunc, args.extraspace)
    if args.debug:
        print("Initialized game. Time elapsed: " + str(timer() - start))
    # original torus adjacency grid, to be used as fresh template for
    # smallworld
    origAdjGrid = np.copy(game.adjGrid)
    # amount of small-world-ification to do
    swc = args.minswc
    # "fudge factor" needed because decimals are weird
    while swc <= args.maxswc + 0.0000000001:
        # changing small-world-ification; need to re-do smallWorldIfy
        game.adjGrid = np.copy(origAdjGrid)
        strswc = str(round(swc, 6))
        if args.debug:
            print("SWC = " + strswc + ". Time elapsed: " + str(timer() - start))
        smallWorldIfy(game.adjGrid,swc)
        if args.debug:
            print("Grid smallworldified. Time elapsed: " + str(timer() - start))
        # these will be arrays of the values for every simulation
        livecells = np.zeros(args.niters)
        cl = np.zeros(args.niters)
        # run the simulation on this many different, random grids
        for sim in range(args.niters):
            if args.debug:
                print("Sim = " + str(sim) + ". Time elapsed: " + str(timer() - start))
            # make file to output live cell count and cluster every step
            if args.output >= 3:
                outfile_steps = open("data3/" + datestr + "_swc=" + strswc +\
                    "_sim=" + str(sim) + ".txt", "w")
                outfile_steps.writelines("Step  LiveCells Mean Std  Cluster Mean Std\n")
            # reset grid to fresh state
            game.grid = genRandGrid(dim, prob=args.frac)
            if args.debug:
                print("Grid reset. Time elapsed: " + str(timer() - start))
            steps = args.simlength
            if args.output < 3:
                grid = run_GPU(game.grid, game.adjGrid, steps, 0, 0,
                               args.visible, -1)
            else:
                for step in range(steps//args.sample + 1):
                    if args.debug:
                        print("Step = " + str(step) + " Time elapsed: " + str(timer() - start))
                    # output data to file
                    outfile_steps.writelines(str(step * args.sample) + "    " + str(countLiveCells(grid)) + "    " + str(cluster(grid, game.adjGrid)) + "\n")
                    # step once
                    grid = run_GPU(game.grid, game.adjGrid, args.sample, 0, 0, args.visible, -1)
                    game.grid = grid
                    # make file, and output grid to that file
                    if args.output >= 4:
                        outfile_grids = open("data4/" + datestr + "_swc=" + strswc + "_sim=" + str(sim) + "_step=" + str(step * args.sample), "w")
                        printGrid(grid, -1, grid.shape, outfile_grids)
                        outfile_grids.close()

                outfile_steps.close()

            if args.debug:
                print("Simulation finished. Time elapsed: " + str(timer() - start))

            livecells[sim] = countLiveCells(grid)
            cl[sim] = cluster(grid, game.adjGrid)
            
            if args.debug:
                print("Finished computing live cells and clustering. Time elapsed: " + str(timer() - start))

        avglc = round(np.mean(livecells), 3)
        avgcl = round(np.mean(cl), 6)
        stdlc = round(np.std(livecells), 3)
        stdcl = round(np.std(cl), 6)
        if args.output >= 1:
            outfile_avg.writelines(strswc + "    " + str(avglc) + "    " + str(stdlc) + "    " + str(avgcl) + "    " + str(stdcl) + "\n")

        # make and output file of range of different final values in
        # simulations
        if args.output >= 2:
            outfile_final = open("data2/" + datestr + "_swc=" + strswc + ".txt", "w")
            outfile_final.writelines("Run  LiveCells  Cluster\n")
            for i in range(len(livecells)):
                outfile_final.writelines(str(i) + "    " + str(livecells[i]) + "    " + str(round(cl[i], 6)) + "\n")
            outfile_final.close()
        swc += args.stepswc

        if args.debug:
            print("Finished outputting everything to files. Time elapsed: " + str(timer() - start))

    outfile_avg.close()

if __name__ == '__main__':
    main()
