import random
from enum import Enum
import datetime

import heapq
import cmocean
import matplotlib
import numpy as np
import copy

#https://plot.ly/python/gantt/
#pip install plotly --upgrade

import plotly as py
import plotly.figure_factory as ff

class TimeUnit(Enum):
    SECOND=1,
    MINUTE=2,
    HOUR=3,
    DAY=4,
    MONTH=5,
    YEAR=6


class Machine:

    name = ""
    jobs = None

    def __init__(self, name):
        self.name = name
        self.jobs = {}

    #add job to machine by specifying its execution time
    #we're using a piority queue where a shortest execution time has higher piority
    def addJob(self, name, executiontime):
        self.jobs[str(name)] = Job(str(name), executiontime)

    def __eq__(self, other):
        return self.name == other.name


class Job:
    name = ''
    executionTime = None
    priority = None
    executionMachine = ''

    def __init__(self, name, executiontime):
        self.name = name
        self.executionTime = executiontime
        self.priority = executiontime

    def __str__(self):
        return str(self.name)

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.name == other.name

    def __gt__(self, other):
        return self.priority > other.priority


class Schedule:

    timeUnit = TimeUnit.DAY
    startDate = datetime.datetime.now()
    machine1 = None
    machine2 = None
    schedule = []

    def __init__(self, startdate, timeunit):
        self.timeUnit = timeunit
        self.startDate = startdate
        self.machine1 = Machine("p1")
        self.machine2 = Machine("p2")

    def addJob(self, name, machine1ExecutionTime, machine2ExecutionTime):
        self.machine1.addJob(name, machine1ExecutionTime)
        self.machine2.addJob(name, machine2ExecutionTime)

    def create(self):
        noOfJobs = len(self.machine1.jobs)
        if noOfJobs==0 or len(self.machine2.jobs) != noOfJobs:
            raise Exception("Machine jobs not initialized correctly")

        highPiority=1
        lowPiority=noOfJobs
        machine1Jobs = list(self.machine1.jobs.values())
        machine2Jobs = list(self.machine2.jobs.values())

        heapq.heapify(machine1Jobs)
        heapq.heapify(machine2Jobs)

        copy.deepcopy(self.machine2.jobs)
        while len(self.schedule) < noOfJobs:
            minJob1 = machine1Jobs[0]
            minJob2 = machine2Jobs[0]
            scheduledJob = None
            pickRandom = None

            if minJob1.executionTime == minJob2.executionTime:
                pickRandom = random.choice([highPiority, lowPiority])

            if minJob1 < minJob2 or pickRandom == highPiority:
                scheduledJob = minJob1
                scheduledJob.priority = highPiority
                highPiority += 1
                scheduledJob.executionMachine=self.machine1.name
            elif minJob1 > minJob2 or pickRandom == lowPiority:
                scheduledJob = minJob2
                scheduledJob.priority = lowPiority
                lowPiority -= 1
                scheduledJob.executionMachine = self.machine2.name

            machine1Jobs.remove(scheduledJob)
            machine2Jobs.remove(scheduledJob)
            heapq.heappush(self.schedule, scheduledJob)


    def displayMachineExecutionTimes(self):
        print("\n\n\tJobs\t\t", end='')
        for jobName in self.machine1.jobs.keys():
            print(jobName + "\t\t", end='')

        print("\n\t" + self.machine1.name + "\t\t\t", end='')
        for job in self.machine1.jobs.values():
            print(str(job.executionTime) + "\t\t", end='')

        print("\n\t" + self.machine2.name + "\t\t\t", end='')
        for job in self.machine2.jobs.values():
            print(str(job.executionTime) + "\t\t", end='')

    def display(self):

        df = []
        startdate1 = self.startDate
        startdate2 = None
        numColors = len(self.schedule)
        colors = self.cmocean_to_plotly(cmocean.cm.haline, numColors)

        print("\n\n>>>>>>>>>>>>>>>>>> JOB ORDER <<<<<<<<<<<<<<<<<<<<<<<<<\n\n")


        while self.schedule:
            job = heapq.heappop(self.schedule)
            print(job.name + " > ", end='')
            job1 = self.machine1.jobs.get(job.name)
            job2 = self.machine2.jobs.get(job.name)
            enddate1 = self.calculateEndDate(startdate1, job1.executionTime)

            if startdate2 is None or enddate2 < enddate1:
                startdate2 = enddate1
            else:
                startdate2 = enddate2

            enddate2 = self.calculateEndDate(startdate2, job2.executionTime)
            jobLabel = "Job " + (job.name if len(job.name)>1 else "0" + job.name)
            df.append(dict(Task=self.machine1.name, Start=startdate1.strftime('%Y-%m-%d %H:%M:%S'), Finish=enddate1.strftime('%Y-%m-%d %H:%M:%S'), Resource=jobLabel, Description=jobLabel))
            df.append(dict(Task=self.machine2.name, Start=startdate2.strftime('%Y-%m-%d %H:%M:%S'),
                           Finish=enddate2.strftime('%Y-%m-%d %H:%M:%S'), Resource=jobLabel, Description=jobLabel))
            startdate1 = enddate1

        fig = ff.create_gantt(df, title='Gantt Chart for Johnson\'s Rule', colors=colors, index_col='Resource', height=900,
                              show_colorbar=True, group_tasks=True, showgrid_x=True, showgrid_y=True)
        py.offline.plot(fig, filename='johnsons-rule-gantt-chart.html')

        print("\n\nGantt chart has been generated to an html file in project dir. \nA web browser should open automatically. \nYou may need to allow bocked conent in IE to see the chart.\n\n")

    def calculateEndDate(self, startdate, executiontime):
        if self.timeUnit == TimeUnit.SECOND:
            return startdate + datetime.timedelta(seconds=executiontime)
        if self.timeUnit == TimeUnit.MINUTE:
            return startdate + datetime.timedelta(minutes=executiontime)
        if self.timeUnit == TimeUnit.HOUR:
            return startdate + datetime.timedelta(hours=executiontime)
        if self.timeUnit == TimeUnit.DAY:
            return startdate + datetime.timedelta(days=executiontime)
        elif self.timeUnit == TimeUnit.MONTH:
            return startdate + datetime.timedelta(executiontime*365/12)
        elif self.timeUnit == TimeUnit.YEAR:
            return startdate + datetime.timedelta(executiontime*365)

    #source https://plot.ly/python/cmocean-colorscales/
    def cmocean_to_plotly(self, cmap, pl_entries):
        h = 1.0 / (pl_entries - 1)
        pl_colorscale = []

        for k in range(pl_entries):
            C = list(map(np.uint8, np.array(cmap(k * h)[:3]) * 255))
            pl_colorscale.append('rgb' + str((C[0], C[1], C[2])))

        return pl_colorscale


if __name__ == "__main__":

    jobExecutionTimes = [
        [3, 6, 4, 3, 4, 2, 7, 5, 5, 6, 12],
        [4, 5, 5, 2, 3, 3, 6, 6, 4, 7, 2]
    ]

    schedule = Schedule(datetime.datetime.now(), TimeUnit.DAY)

    #initialzie jobs for both machines
    for jobCount in range(1, len(jobExecutionTimes[0]) + 1):
        schedule.addJob(str(jobCount), jobExecutionTimes[0][jobCount-1], jobExecutionTimes[1][jobCount - 1])

    schedule.displayMachineExecutionTimes()
    schedule.create()
    schedule.display()







