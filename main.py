from Persons.Person import Person
from Persons.PersonManager import PersonManager
from Tasks.Task import Task
from Tasks.TaskManager import TaskManager
from Actions.Action import Action
from Actions.ActionManager import ActionManager
from Simulator.Simulator import Simulator
from DatabaseAdaptor.database_adaptor import loadPreferences, loadTasks, loadActions, loadProfessions, loadThresholds
from Random.string_generator import rands
from Random.normal_distribution import randni
import numpy as np
import random
import pickle
import sys
import os




def main():
    # fline = open("seed.txt").readline().rstrip()
    ranseed = int(sys.argv[1])
    print(ranseed)
    
    try:
        os.mkdir('Outputs')
    except:
        pass

    output_dirname = "Outputs/Seed_"+str(ranseed)
    try:
        os.mkdir(output_dirname)
    except:
        pass
    
    output_dirname_prefix = 'Outputs/Seed_'
    
    np.random.seed(ranseed)
    random.seed(ranseed)

    preferences_df = loadPreferences()
    thresholds_df = loadThresholds()
    profession_df = loadProfessions()
    actions_df = loadActions()
    tasks_df = loadTasks()

    trace_days = 2
    tracing_percentage = 0.3
    smartphone_owner_percentage = 0.6
    quarantine_days = 14


    timerun = 0 #0 if we want snapshots, any other value if we don'tc
    beginmodel = 27 #the day from which we want the simulation to start
    dayfinish = 120 #simulate upto which day. 90 or 120
    tracing_starts_on_day = 27 #from which day contact tracing implemented
    #snapdays = [10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120] #the days we want the snapshots of (index always from original day 1)
    snapdays = [90,120] #the days we want the snapshots of (index always from original day 1)
    
    #outfile = open("Outputarray.txt","w+")
    #outfile.write(str(snapdays))

    
    Simulator.start_simulation(trace_days, tracing_percentage, smartphone_owner_percentage, quarantine_days, preferences_df, profession_df, actions_df, tasks_df, thresholds_df,timerun,snapdays, beginmodel, dayfinish, tracing_starts_on_day, output_dirname_prefix, ranseed)

'''
Wash Hands,30,40,0.5,1,Work,0.1,0.7,0,0,-0.75,-0.1
Wash Hands,30,40,0.5,1,Stay Home,0.2,0.7,0,0,-0.75,-0.1
Wash Hands,30,40,0.4,1,Attend Event,0.1,0.7,0,0,-0.75,-0.1
Wash Hands,20,40,0.4,1,Treat Patients,0.2,0.7,0,0,-0.75,-0.1
'''
    

    
    

if __name__ == '__main__':

    main()

