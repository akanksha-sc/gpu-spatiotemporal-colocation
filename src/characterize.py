#!/usr/bin/env python

import argparse
import colorsys
import csv
import sys
import matplotlib.pyplot as plt
import matplotlib.colors as mc
from pathlib import Path
import datetime
import os
import math

class workload:

    def __init__(self,name,dram,fu):

        self.name = name
        self.dram = dram
        self.fu = fu

        self.mod = 1#math.sqrt((dram*dram) + (fu*fu))
        self.x = dram/self.mod
        self.y = fu/self.mod

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file', type=str, help='File containing '
                        'scheduling info from gem5 run')
    parser.add_argument('--output', type=str, default=None, help='Diectory containing Output')
    args = parser.parse_args()
    WORKLOAD = []

    with open(args.csv_file) as csvfile:
        reader = csv.reader(csvfile)
    
        for row in reader:
            # now = datetime.datetime.now()
            dram = float(row[1])
            fu = max(float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]),float(row[7]))
            WORKLOAD.append(workload(row[0].strip(),dram,fu))

    NAMES = [x.name for x in WORKLOAD]
    X = [temp.x for temp in WORKLOAD]
    Y = [temp.y for temp in WORKLOAD]

    fig, ax = plt.subplots()
    ax.scatter(X, Y)

    for i, txt in enumerate(NAMES):
        ax.annotate(txt, (X[i], Y[i]))

    OUTPUT_DIR = os.path.splitext(args.csv_file)[0]
    if(args.output):
        OUTPUT_DIR = args.output
    # ax.set_xlim([0, 1.0])
    # ax.set_ylim([0, 1.0])
    ax.set_title('Workload Characterization Graph', fontsize=12)
    ax.set_ylabel("FU Utilization (in %)")
    ax.set_xlabel("DRAM Utilization (in %)")
    ax.axline((0, 0), slope=1)
    plt.savefig('./similarity.png',dpi=300)

    # OUTPUT_DIR = os.path.splitext(args.csv_file)[0]
    # if(args.output):
    #     OUTPUT_DIR = args.output

    # if not os.path.exists(OUTPUT_DIR):
    #     os.makedirs(OUTPUT_DIR)

    # figure2, axis2 = plt.subplots(1, 1,constrained_layout=True)
    # axis2.plot(TIME_AXIS, VAL_TEMP,color='orange',linewidth=1,label="Temperature")
    # axis2.set_ylabel("Temperature (in C)")
    # axis2.set_xlabel("Time (in s)")
    # axis2.set_title('Temperature Analysis Graph', fontsize=12)
    # plt.savefig(os.path.join(OUTPUT_DIR,'temperature.png'),dpi=300)

    # figure, axis = plt.subplots(1, 1,constrained_layout=True)
    # axis.plot(TIME_AXIS, VAL_POW,color='red',linewidth=1,label="Power")
    # axis.set_ylabel("Power (in W)")
    # axis.set_xlabel("Time (in s)")
    # axis.set_title('Power Analysis Graph', fontsize=12)
    # plt.savefig(os.path.join(OUTPUT_DIR,'power.png'),dpi=300)

    # if PEAK_SM_FREQ != 0: 
    #     # axis3 = axis.twinx() 
    #     figure3, axis3 = plt.subplots(1, 1,constrained_layout=True)
    #     axis3.plot(TIME_AXIS, VAL_SM_FREQ,color='green',linewidth=1, label="Frequency")
    #     axis3.set_ylabel("Frequency (in MHz)")
    #     axis3.set_xlabel("Time (in s)")
    #     axis3.set_title('SM Frequency Analysis Graph', fontsize=12)
    #     plt.savefig(os.path.join(OUTPUT_DIR,'sm_frequency.png'),dpi=300)

    # if PEAK_GPU_UTILIZATION != 0: 
    #     figure4, axis4 = plt.subplots(1, 1,constrained_layout=True)
    #     axis4.plot(TIME_AXIS, VAL_GPU_UTIL,color='blue',linewidth=1,label="GPU Utilization")
    #     axis4.set_ylabel("GPU Utilization (in %)")
    #     axis4.set_xlabel("Time (in s)")
    #     axis4.set_title('GPU Utilization Analysis Graph', fontsize=12)
    #     plt.savefig(os.path.join(OUTPUT_DIR,'gpu_utilization.png'),dpi=300)

    # print("PEAK POWER IS: ", PEAK_POWER)
    # print("PEAK TEMPRETURE IS: ", PEAK_TEMP) 
    # print("PEAK SM FREQUENCY IS: ", PEAK_SM_FREQ) 
    # print("PEAK GPU UTILIZATION IS: ", PEAK_GPU_UTILIZATION) 
    
    # PROFILING_TIME = (TIME_AXIS[-1] - TIME_AXIS[0])
    # print("PROFILING TIME (in s): ", PROFILING_TIME)
if __name__ == '__main__':
    main()