#!/usr/bin/env python

'''
    This script reads the topologies stored in the topologies directory
    and generates a serie of instances files for the RSA for each topology
    based on the data of the bibliography. It depends on the modulation level
    the optical fiber used, the graph density among other paramters.

    From the literature we obtained the most used data for the RSA problem:

    + The slot bandwith most of the cases is 12.5 GHz. However it could be
    smaller (sometimes 5 GHz) or larger, but not much larger, due to the fact
    that for the RWA problem with WDM, the minimum bandwidth of the slot is
    50 GHz and the main objective of RSA is to improve granularity.

    + The bandwidth of the optical fiber used on average is 4800 GHz,
    although the theoretical maximum bandwidth of the optical fiber is
    around 231 THz.
'''

import os
import random
import argparse
import numpy as np
import math

__author__ = "Marcelo Bianchetti"
__credits__ = ["Marcelo Bianchetti", "Ignacio Mariotti"]
__version__ = "1.0.0"
__maintainer__ = "Ignacio Mariotti"
__email__ = "mariotti.ignacio at dc.uba.ar"
__status__ = "Production"

line_enter = '{}\n'
sep = '\t'


def error(err):
    print("ERROR: {}".format(err))
    exit(1)


def getPair(n, used_dict=None):
    ''' Returns a pair of n different nodes. If a used_dict is given, the pair
    does not repeat any element.'''
    src, dst = random.sample(range(n), 2)
    if used_dict is None:
        return src, dst
    while dst in used_dict[src]:
        src, dst = random.sample(range(n), 2)
    return src, dst


def calculateGraphDensity(n, m):
    ''' Returns the density of the undirected graph '''
    return 2.*m/(n*(n-1))


def calculateMaxNumberOfDemands(n, m, S, max_sd):
    ''' Given a graph and the amount of slots per link
        it returns an estimative of the max amount of
        demands per instance.

        n: number of nodes
        m: number of undirected edges
        S: chosen number of slots per arc
        max_sd: chosen max value for slots by demand

        A tighter bound could be the min grade of the
        nodes but we want infeasible instances too.
    '''
    d = calculateGraphDensity(n, m)
    max_n_of_demands = int((n-1.) * d * S/(max_sd))
    return max_n_of_demands


def readTopologyData(tops_dir, top_fname):
    ''' Returns the amount of nodes and edges of the graph '''
    with open(os.path.join(tops_dir, top_fname)) as f:
        for line in f:
            if line.startswith('#'):
                continue
            line = line.split()
            return int(line[0]), int(line[1])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-mdir", type=str, help="The main directory or path. "
                        "If no tdir or idir parameters are used, mdir must "
                        "contain the 'topologies' and/or 'instances' folder. "
                        "The default value is the location of this script")
    parser.add_argument("-tdir", type=str, help="The topologies directory or "
                        "path.")
    parser.add_argument("-idir", type=str, help="The directory or path for the"
                        " created instances.")
    parser.add_argument("-s", "--seed", type=int, default=1988, help="The "
                        "random seed. Default is 1988.")
    parser.add_argument("-S", "--slots", nargs='+', type=int, help="List of "
                        "amounts of available slots.")
    parser.add_argument("-p", "--percents", nargs='+', type=float,
                        help="List of maximum percentage of total available "
                             "slots that a demand can use. Must be in (0, 1].")
    parser.add_argument("-d", "--density", type=float, default=2.0,
                        help="Density factor. The maximum amount of demands is"
                        " multiplied by this factor. Default is 2.0.")
    parser.add_argument("-sp", "--spread", nargs='+', type=float, default=[1.0],
                        help="Spread factor. The higher the spread, the more "
                        "distributed are terminals between demands. "
                        "Must be in (0, 1]). Default is 1.0.")
    args = parser.parse_args()

    main_dir = (os.path.dirname(os.path.abspath(__file__))
                if args.mdir is None else args.mdir)

    topologies_dir = (os.path.join(main_dir, 'topologies')
                      if args.tdir is None
                      else os.path.abspath(args.tdir))

    instances_dir = (os.path.join(main_dir, 'instances')
                     if args.idir is None
                     else os.path.abspath(args.idir))

    # Check directories
    for d in [main_dir, topologies_dir]:
        if not os.path.exists(d):
            error("Directory '{}' not found.".format(d))

    instance_fname = 'instance_{}_{}_{}_{}_{}.txt'

    random.seed(args.seed)

    if not 0 < args.density < 10:
        error("Demands density must be in (0, 10)")

    # Available slots per fiber. Discarding non-positive values
    avaliable_S = ([10, 15, 20, 30, 40, 60, 80, 100, 150, 200, 300, 400, 600,
                    800, 1000] if args.slots is None else
                   [s for s in set(args.slots) if s > 0])

    # Default: From a lightly loaded network to a heavily loaded one.
    # Discarding values not in (0, 1]
    max_percentages_of_slots_by_demand = (np.arange(.1, .9, .1)
                                          if args.percents is None else
                                          [p for p in set(args.percents)
                                           if p > 0 and p <= 1])
    
    spreads = [sp for sp in set(args.spread) if 0 < sp <= 1]

    # Creation of instances directory if it does not exist
    if not os.path.exists(instances_dir):
        os.makedirs(instances_dir)

    for percentage in max_percentages_of_slots_by_demand:

        # The resulting instances are created in directories
        # acoording to their percentage and topologies
        percentage_dir = os.path.join(instances_dir,
                                      "{}".format(round(percentage, 2) * 100))

        # Creation of instance directory if it does not exist
        if not os.path.exists(percentage_dir):
            os.makedirs(percentage_dir)

        for top_fname in os.listdir(topologies_dir):
            top_name = os.path.splitext(top_fname)[0]
            n, m = readTopologyData(topologies_dir, top_fname)

            # The resulting instances are created in directories
            # acoording to their topologies
            top_dir = os.path.join(percentage_dir, top_name)

            # Creation of instance directory if it does not exist
            if not os.path.exists(top_dir):
                os.makedirs(top_dir)

            # Iterates over each available S
            for S, sp in [(S, sp) 
                          for S in avaliable_S 
                          for sp in spreads]:
                max_sd = math.ceil(percentage * S)

                nT = calculateMaxNumberOfDemands(n, m, S, max_sd)
                nT = int(max(1, nT * args.density))
                demand_f = os.path.join(
                    top_dir, instance_fname.format(
                        top_name, S, max_sd, nT, str(sp)))

                with open(demand_f, 'w') as out:
                    out.write('# Created by {}\n'.format(__author__))
                    out.write('# Version: {}\n'.format(__version__))
                    out.write('# Seed: {}\n'.format(args.seed))
                    out.write('# Format:\n')
                    out.write('#   First line: S  |D|\n')
                    out.write('#   Other lines: <src #dst dst_1 dst_2 ... dst_#dst #slots>\n')

                    remainingT = nT
                    spInv = math.pow(sp, -1)

                    lines = []
                    nD = 0
                    while remainingT > 0:
                        nD += 1
                        [src] = random.sample(range(n), 1)

                        nDst = 1
                        if spInv - 1 > 0.001:
                            nDst = math.ceil(random.uniform(0.5*spInv, 2*spInv))

                        nDst: int = min(remainingT, nDst)
                        nDst = min(n-1,nDst)
                        remainingT = remainingT - nDst
                        dsts = random.sample(
                            [dst for dst in range(n) if dst != src], 
                            nDst)

                        s = random.randint(math.floor(max_sd/2), max_sd)
                        s = max(1, s)
                        
                        line = '{src}{sep}{nDst}{sep}{dst}{sep}{s}'.format(
                            S=S, sep=sep, src=src, nDst=nDst, 
                            dst=sep.join(map(str, dsts)),
                            s=s)
                        lines.append(line_enter.format(line))
                    
                    line = '{}{}{}'.format(S, sep, nD)
                    out.write(line_enter.format(line))

                    for line in lines:
                        out.write(line)
