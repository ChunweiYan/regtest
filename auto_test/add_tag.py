#!/usr/bin/python
# Copyright (c) 2016 PaddlePaddle Authors. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Usage: add_tag.py -m [MONITORFILE] -l [LOGFILE] -o [OUTPUTMONITORFILE]

addTag to monitorFile. Here tag means "Batch=100" or "Pass=0" etc. As we just 
record the cpu, memory, GPU memory usage and time in monitorfile, we don't
know exactly the usage in a certain batch or pass. Thus We have to compare the
time between monitor file and  train.log.

Arguments:
    MONITORFILE             cpu, gpu and memory usage file collected by monitor.sh
    LOGFILE                 training log generated by train.sh 
    OUTPUTMONITORFILE       addTag to monitorFile and generate outputMonitorFile 

Options:
    -h      --help
    -m      monitorFile
    -l      logFile
    -o      outputMonitorFile

"""

from docopt import docopt
import sys
import datetime
import bisect


def read_monitor_file(monitorFile):
    """
        reaad Monitor file, the format is :
        ---------------------2016-11-23_07:33:53 BEGIN-----------------------------
        DATE	PID	%MEM	MEM	GPU_MEM	START	TIME
        2016-11-23_07:33:55	16698(PID)	0.0(%memory)	7028(KB memory)	 55 MiB_GPU_MEM	07:33(begin time)	0:00(run durning time)
        ....
    """
    monitorTime = []
    with open(monitorFile, 'r') as f:
        for line in f:
            if line[0] != '2':
                continue
            time = line.split()[0]
            dtime = datetime.datetime.strptime(time, "%Y-%m-%d_%H:%M:%S")
            monitorTime.append(dtime)
    return monitorTime


def locate_tag(logFile, monitorTime):
    """
        once we have a monitor file and a train log file, we have to identify the location of 
        each line of train.log in monitor log file. After this, we can get format like below:
        ---------------------2016-11-23_07:33:53 BEGIN-----------------------------
        DATE	PID	%MEM	MEM	GPU_MEM	START	TIME    TAG
        2016-11-23_07:34:22	16698(PID)	0.3(%memory)	717456(KB memory)	 766 MiB_GPU_MEM	07:33(begin time)	0:31(run durning time) Batch=300
    
        Here we use binary search algorithm, for each line in train.log, we use the time to
        search its location in monitor file. Thus we can know more about the resource usage, 
        for example, we can know that in pass 0 and batch 300, the memory usage is 717456KB.
    """
    tagList = {}
    with open(logFile, 'r') as f:
        for line in f:
            line_data = line.split()
            assert len(line_data) >= 3
            # before this parsing process, we use shell script to preprocess train.log
            t1, t2, tag = line_data[0:3]
            t1 = t1.replace('I', '').replace('.', '')
            dtime = datetime.datetime.strptime(
                str(datetime.datetime.now().year) + "-" + t1[:2] + "-" + t1[2:]
                + "_" + t2.split('.')[0], "%Y-%m-%d_%H:%M:%S")
            index = bisect.bisect(monitorTime, dtime)
            if index not in tagList.keys() or "Pass" not in tagList[index]:
                tagList[index] = tag
    return tagList


def add_tag_to_monitor(monitorTime, monitorFile, tagList, outMonitorFile):
    with open(monitorFile, 'r') as IN, open(outMonitorFile, 'w') as OUT:
        index = 0
        for line in IN:
            if index in tagList.keys():
                print >> OUT, line.strip(), tagList[index]
            else:
                print >> OUT, line.strip()
            index += 1


if __name__ == '__main__':
    arguments = docopt(__doc__)
    monitorFile = arguments['MONITORFILE']
    logFile = arguments['LOGFILE']
    outMonitorFile = arguments['OUTPUTMONITORFILE']
    monitorTime = read_monitor_file(monitorFile)
    tagList = locate_tag(logFile, monitorTime)
    add_tag_to_monitor(monitorTime, monitorFile, tagList, outMonitorFile)
