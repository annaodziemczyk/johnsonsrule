import random
from enum import Enum
import datetime

import heapq
import cmocean
import matplotlib
import numpy as np

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
    #we're using dictionary in order to easily find the required job during gantt chart generation
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
        #setting piority to the execution time initally as the jobs need to be sorted first by the processing time
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

        #using a piority queue for each machine jobs to sort them by the processing time
        heapq.heapify(machine1Jobs)
        heapq.heapify(machine2Jobs)

        while len(self.schedule) < noOfJobs:
            #since we used piority queues the first job will have the lowest processing time
            minJob1 = machine1Jobs[0]
            minJob2 = machine2Jobs[0]
            scheduledJob = None
            pickRandom = None

            #according to Johnson't Rule if jobs have the same processing time we pick one at random
            if minJob1.executionTime == minJob2.executionTime:
                pickRandom = random.choice([highPiority, lowPiority])

            #if job on first machine has lower processing time it will have higher priority
            if minJob1 < minJob2 or pickRandom == highPiority:
                scheduledJob = minJob1
                scheduledJob.priority = highPiority
                highPiority += 1
                scheduledJob.executionMachine=self.machine1.name
            # if job on second machine has lower processing time it will have lower priority
            elif minJob1 > minJob2 or pickRandom == lowPiority:
                scheduledJob = minJob2
                scheduledJob.priority = lowPiority
                lowPiority -= 1
                scheduledJob.executionMachine = self.machine2.name

            #we remove selected job from both queues and adding it to the schedule
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
        enddate1 = None
        enddate2 = None
        numColors = len(self.schedule)
        colors = self.cmocean_to_plotly(cmocean.cm.haline, numColors)
        jobOrder= []

        while self.schedule:
            job = heapq.heappop(self.schedule)
            jobOrder.append(job.name)

            #create items for the gantt chart in the order specified
            job1 = self.machine1.jobs.get(job.name)
            job2 = self.machine2.jobs.get(job.name)
            enddate1 = self.calculateEndDate(startdate1, job1.executionTime)

            #same job on machine2 cannot start before the same job is finished on machine1
            if startdate2 is None or enddate2 < enddate1:
                startdate2 = enddate1
            else:
                startdate2 = enddate2

            enddate2 = self.calculateEndDate(startdate2, job2.executionTime)
            jobLabel = "Job " + (job.name if len(job.name)>1 else "0" + job.name)
            #add chart item for the job for both machines
            df.append(dict(Task=self.machine1.name, Start=startdate1.strftime('%Y-%m-%d %H:%M:%S'), Finish=enddate1.strftime('%Y-%m-%d %H:%M:%S'), Resource=jobLabel, Description=jobLabel))
            df.append(dict(Task=self.machine2.name, Start=startdate2.strftime('%Y-%m-%d %H:%M:%S'),
                           Finish=enddate2.strftime('%Y-%m-%d %H:%M:%S'), Resource=jobLabel, Description=jobLabel))
            startdate1 = enddate1


        #print the order of the jobs procecessed according to Johnson's Rule
        print("\n\n>>>>>>>>>>>>>>>>>> JOB ORDER <<<<<<<<<<<<<<<<<<<<<<<<<\n\n")
        print(">".join(jobOrder), end='')
        makespan = (enddate2 if enddate2 > enddate1 else enddate1) - self.startDate
        displayMakespan = self.displayMakeSpan(makespan)
        print(displayMakespan)

        #generate gantt chart
        fig = ff.create_gantt(df, title='Gantt Chart for Johnson\'s Rule' + ' <br>(' + ">".join(jobOrder) + " - " + displayMakespan + ')', colors=colors, index_col='Resource', height=900,
                              show_colorbar=True, group_tasks=True, showgrid_x=True, showgrid_y=True)
        py.offline.plot(fig, filename='johnsons-rule-gantt-chart.html')


        print("\n\nGantt chart has been generated to an html file in project dir. \nA web browser should open automatically. \nYou may need to allow bocked conent in IE to see the chart.\n\n")

    #calculate the end date for a single job based on the specified time unit
    def calculateEndDate(self, startdate, executiontime):
        if self.timeUnit == TimeUnit.SECOND:
            return startdate + datetime.timedelta(seconds=executiontime)
        elif self.timeUnit == TimeUnit.MINUTE:
            return startdate + datetime.timedelta(minutes=executiontime)
        elif self.timeUnit == TimeUnit.HOUR:
            return startdate + datetime.timedelta(hours=executiontime)
        elif self.timeUnit == TimeUnit.DAY:
            return startdate + datetime.timedelta(days=executiontime)
        elif self.timeUnit == TimeUnit.MONTH:
            return startdate + datetime.timedelta(executiontime*365/12)
        elif self.timeUnit == TimeUnit.YEAR:
            return startdate + datetime.timedelta(executiontime*365)

    def displayMakeSpan(self, delta):
        makespan = "\nMakespan: "
        if self.timeUnit == TimeUnit.SECOND:
            makespan += str(round(delta.days*24*60*60 + delta.seconds))
        elif self.timeUnit == TimeUnit.MINUTE:
            makespan += str(round(delta.days*24*60 + delta.seconds/60))
        elif self.timeUnit == TimeUnit.HOUR:
            makespan += str(round(delta.days*24 + delta.seconds/3600))
        elif self.timeUnit == TimeUnit.DAY:
            makespan += str(delta.days)
        elif self.timeUnit == TimeUnit.MONTH:
            makespan += str(round(delta.days/365*12))
        elif self.timeUnit == TimeUnit.YEAR:
            makespan += str(round(delta.days/365))
        return makespan

    #source https://plot.ly/python/cmocean-colorscales/
    #generates colors for the gantt chart
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

    #specify the time units and start date for the gantt chart
    schedule = Schedule(datetime.datetime.now(), TimeUnit.DAY)

    #initialzie jobs for both machines
    for jobCount in range(1, len(jobExecutionTimes[0]) + 1):
        schedule.addJob(str(jobCount), jobExecutionTimes[0][jobCount-1], jobExecutionTimes[1][jobCount - 1])

    schedule.displayMachineExecutionTimes()
    schedule.create()
    #display sequence and gantt chart
    schedule.display()







