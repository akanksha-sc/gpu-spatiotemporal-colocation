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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file', type=str, help='File containing '
                        'scheduling info from gem5 run')

    parser.add_argument('--timeout', type=float, default=None, help='Timeout after how much time')
    parser.add_argument('--output', type=str, default=None, help='Diectory containing Output')
    parser.add_argument('--window-size', type=int, default=1, help='Window Size for sampling')

    t_start = 0
    t_end = 0

    RUNTIMES = []
    args = parser.parse_args()

    START_TIME = 0
    WINDOW_SIZE = int(args.window_size)

    NUM_DATA_POINTS = 0

    VAL_POW = []
    VAL_TEMP = []
    VAL_SM_FREQ = []
    VAL_GPU_UTIL = []
    TIME_AXIS = []

    PEAK_POWER = 0
    PEAK_TEMP = 0
    PEAK_SM_FREQ = 0
    PEAK_GPU_UTILIZATION = 0

    AVG_POWER = 0
    AVG_TEMP = 0
    AVG_SM_FREQ = 0
    AVG_GPU_UTILIZATION = 0
    RM = 0
    WINDOW_PEAK_POWER = 0
    WINDOW_PEAK_TEMP = 0
    WINDOW_PEAK_FREQ = 0
    WINDOW_PEAK_UTILIZATION = 0

    WINDOW__POWER = []
    WINDOW__TEMP = []
    WINDOW__SM_FREQ = []
    WINDOW__UTILIZATION = []
    timestr = '00:04:23'

    ftr = [3600,60,1]


    TIME_STEP_PREV = 0
    PROFILING_TIME = 0
    with open(args.csv_file) as csvfile:
        reader = csv.reader(csvfile)
        cnt = 0
        for row in reader:
            # now = datetime.datetime.now()
            if row[0].strip() == 'timestamp':
                continue

            if(cnt%4)!=RM:
                cnt += 1
                continue
            else:
                cnt += 1

            t = float(row[2].split()[0].strip())
            t2 = float(row[1].split()[0].strip())
            t3 = 0
            t4 = 0

            #print(WINDOW__POWER)
            time =  sum([a*b for a,b in zip(ftr, map(float,row[0].split()[-1].split(':')))])#float(int(row[0].split()[-1].replace(':','').replace('.','')))

            if(len(row)>3):
                t3 = float(row[3].split()[0].strip())
                PEAK_SM_FREQ = max(t3,PEAK_SM_FREQ)

            if(len(row)>4):
                t4 = float(row[4].split()[0].strip())
                PEAK_GPU_UTILIZATION = max(t4,PEAK_GPU_UTILIZATION)

            PEAK_POWER = max(t,PEAK_POWER)
            PEAK_TEMP = max(t2,PEAK_TEMP)
            
            NUM_DATA_POINTS += 1

            WINDOW__POWER.append(t)

            if len(WINDOW__POWER) > WINDOW_SIZE:
                WINDOW__POWER.pop(0)

            WINDOW__TEMP.append(t2)

            if len(WINDOW__TEMP) > WINDOW_SIZE:
                WINDOW__TEMP.pop(0)

            WINDOW__SM_FREQ.append(t3)

            if len(WINDOW__SM_FREQ) > WINDOW_SIZE:
                WINDOW__SM_FREQ.pop(0)

            WINDOW__UTILIZATION.append(t4)

            if len(WINDOW__UTILIZATION) > WINDOW_SIZE:
                WINDOW__UTILIZATION.pop(0)

            WINDOW_PEAK_POWER = max(WINDOW__POWER)
            WINDOW_PEAK_TEMP = max(WINDOW__TEMP)
            WINDOW_PEAK_FREQ = max(WINDOW__SM_FREQ)
            WINDOW_PEAK_UTILIZATION = max(WINDOW__UTILIZATION)

            #print(WINDOW_PEAK_POWER,WINDOW_PEAK_TEMP,WINDOW_PEAK_FREQ,WINDOW_PEAK_UTILIZATION)
            VAL_POW.append(WINDOW_PEAK_POWER)
            VAL_TEMP.append(WINDOW_PEAK_TEMP)
            VAL_SM_FREQ.append(WINDOW_PEAK_FREQ)
            VAL_GPU_UTIL.append(WINDOW_PEAK_UTILIZATION)
        
            AVG_POWER += WINDOW_PEAK_POWER
            AVG_TEMP += WINDOW_PEAK_TEMP
            AVG_SM_FREQ += WINDOW_PEAK_FREQ
            AVG_GPU_UTILIZATION += WINDOW_PEAK_UTILIZATION

            if(WINDOW_PEAK_UTILIZATION < 70):
                runtime = t_end - t_start

                if(runtime > 1):
                    RUNTIMES.append(runtime)
                    t_start = time
            else:
                t_end = time

            # TIME_STEP_PREV = time
            if TIME_AXIS:
                TIME_AXIS.append(float(time)-START_TIME)
            else:
                START_TIME = float(time)
                t_start = float(time)
                t_end = float(time)
                TIME_AXIS.append(0)

            time_elapsed = time - TIME_AXIS[0]
            if args.timeout and (time_elapsed > args.timeout):
                break

    OUTPUT_DIR = os.path.splitext(args.csv_file)[0]
    if(args.output):
        OUTPUT_DIR = args.output

    OUTPUT_DIR += "GPU {}".format(RM)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    AVG_POWER /= NUM_DATA_POINTS
    AVG_GPU_UTILIZATION /= NUM_DATA_POINTS
    AVG_SM_FREQ /= NUM_DATA_POINTS
    AVG_TEMP /= NUM_DATA_POINTS

    figure2, axis2 = plt.subplots(1, 1,constrained_layout=True)
    axis2.plot(TIME_AXIS, VAL_TEMP,color='orange',linewidth=1,label="Temperature")
    axis2.set_ylabel("Temperature (in C) ")
    axis2.set_xlabel("Time (in s)")
    axis2.set_title('Temperature Analysis Graph (GPU {})'.format(RM), fontsize=12)
    plt.savefig(os.path.join(OUTPUT_DIR,'temperature.png'),dpi=300)

    figure, axis = plt.subplots(1, 1,constrained_layout=True)
    axis.plot(TIME_AXIS, VAL_POW,color='red',linewidth=1,label="Power")
    axis.set_ylabel("Power (in W)")
    axis.set_xlabel("Time (in s)")
    axis.set_title('Power Analysis Graph (GPU {})'.format(RM), fontsize=12)
    plt.savefig(os.path.join(OUTPUT_DIR,'power.png'),dpi=300)

    if PEAK_SM_FREQ != 0: 
        # axis3 = axis.twinx() 
        figure3, axis3 = plt.subplots(1, 1,constrained_layout=True)
        axis3.plot(TIME_AXIS, VAL_SM_FREQ,color='green',linewidth=1, label="Frequency")
        axis3.set_ylabel("Frequency (in MHz)")
        axis3.set_xlabel("Time (in s)")
        axis3.set_title('SM Frequency Analysis Graph (GPU {})'.format(RM), fontsize=12)
        plt.savefig(os.path.join(OUTPUT_DIR,'sm_frequency.png'),dpi=300)

    if PEAK_GPU_UTILIZATION != 0: 
        figure4, axis4 = plt.subplots(1, 1,constrained_layout=True)
        axis4.plot(TIME_AXIS, VAL_GPU_UTIL,color='blue',linewidth=1,label="GPU Utilization")
        axis4.set_ylabel("GPU Utilization (in %)")
        axis4.set_xlabel("Time (in s)")
        axis4.set_title('GPU Utilization Analysis Graph (GPU {})'.format(RM), fontsize=12)
        plt.savefig(os.path.join(OUTPUT_DIR,'gpu_utilization.png'),dpi=300)

    print("PEAK POWER IS: {} | AVG POWER IS: {:.2f}".format(PEAK_POWER, AVG_POWER))
    print("PEAK TEMPERATURE IS: {} | AVG TEMPERATURE IS: {:.2f}".format(PEAK_TEMP, AVG_TEMP))
    print("PEAK SM FREQUENCY IS: {} | AVG SM FREQUENCY IS: {:.2f}".format(PEAK_SM_FREQ, AVG_SM_FREQ)) 
    print("PEAK GPU UTILIZATION IS: {} | AVG GPU UTILIZATION IS: {:.2f}\n".format(PEAK_GPU_UTILIZATION, AVG_GPU_UTILIZATION))
    
    AVG = 0
    for i in range(len(RUNTIMES)):
        print("Job {} Runtime: {:.2F}".format(i,RUNTIMES[i]))
        AVG += float(RUNTIMES[i])

    if RUNTIMES:
        AVG /= (len(RUNTIMES))
    print("\nAVG JOB RUNTIME: ",AVG)
    PROFILING_TIME = (TIME_AXIS[-1] - TIME_AXIS[0])
    print("PROFILING TIME (in s): ", PROFILING_TIME)
if __name__ == '__main__':
    main()