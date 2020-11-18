from Persons.PersonManager import PersonManager
from Groups.GroupManager import GroupManager
from Simulator.DaySimulator import DaySimulator
from Simulator.HourSimulator import HourSimulator
from Simulator.GroupSimulator import GroupSimulator
from DatabaseAdaptor.utils import dfToInt
# import matplotlib.pyplot as plt
from tqdm import tqdm
import pickle
import multiprocessing as mp
from datetime import datetime
import numpy as np

class Simulator :

    def __init__(self):
        pass


    @staticmethod

    def start_simulation(trace_days, tracing_percentage, smartphone_owner_percentage, quarantine_days, preferences_df, profession_df, actions_df, tasks_df, thresholds_df, timerun, snapdays, beginmodel, dayfinish, tracing_starts_on_day, output_dirname_prefix, ranseed):
        output_dirname = output_dirname_prefix + str(ranseed) + '/'

        myLogFile = open(output_dirname+"myLogFile.txt","w+")
        n_persons = dfToInt(preferences_df,"n_persons")
        n_infected_init = dfToInt(preferences_df,"n_infected_init")
        quarantine_start = dfToInt(preferences_df, "quarantine_start")

        #dayinit = 1
        dayinit = beginmodel

        myLogFile.write('Person loading starts at '+ str(datetime.now()) + '\n')

        #print('Person loading starts at '+ str(datetime.now()) + '\n')
        if (beginmodel==1):
            persons = PersonManager.generatePersons(n_persons,profession_df,preferences_df, smartphone_owner_percentage)
            #print("before initial")
            PersonManager.initialInfection(persons, n_infected_init)
            #print("after initial")

            infections = [n_infected_init]
        else:
            #dayinit = beginmodel + 1
            load_day = beginmodel - 1
            personname = 'persons_snapshot' + str(load_day) + '.p'
            infectname = 'infections_snapshot' + str(load_day) + '.p'
            personfile = open(personname,'rb') #not using output_dirname assuming common start for every seed
            persons = pickle.load(personfile)
            infectfile = open(infectname,'rb') # ^^
            infections = pickle.load(infectfile)
            personfile.close()
            infectfile.close()
        myLogFile.write('Person loaded at '+ str(datetime.now()) + '\n')
        #print('Person loaded at '+ str(datetime.now()) + '\n')
        track = 0
        
        cpu_cnt = mp.cpu_count()
        myLogFile.write("CPU count: %s \n" % cpu_cnt)

        for day in tqdm(range(dayinit,dayfinish+1),desc='Days'):
        #for day in range(dayinit,dayfinish+1):
            
            # Typical tracing
            if (day == tracing_starts_on_day):
                smartphone_owner_cnt = 0
                for pers in persons:
                    rnd = np.random.rand()
                    if(rnd < smartphone_owner_percentage):
                        pers.is_traceable = True
                        smartphone_owner_cnt += 1

                #print("smartphone owner count: " + str(smartphone_owner_cnt))


            DaySimulator.dayStart(persons, day, preferences_df)

            # Tracing non-quarantined people only 
            # if (day == tracing_starts_on_day):
            #     smartphone_owner_cnt = 0
            #     for pers in persons:
            #     	if pers.profession != "Unemployed":
            #             pers.is_traceable = True
            #             smartphone_owner_cnt += 1

            #     print("smartphone owner count: " + str(smartphone_owner_cnt))


            #tqdm.write('Day {}'.format(day))        

            #DaySimulator.generateDailyTasks(persons, tasks_df, day>=quarantine_start)
            per_cpu_persons = int(len(persons)/(cpu_cnt - 1))

            USE_MULTIPROCESSOR = True
            if (not USE_MULTIPROCESSOR):
                DaySimulator.generateDailyTasks(persons, tasks_df, day>=quarantine_start)

            else:
                pl = mp.Pool(mp.cpu_count())
                persons_cluster = []
                for cpu_i in range(cpu_cnt):
                    start_index = cpu_i*per_cpu_persons
                    persons_cluster.append(persons[start_index : min(len(persons), start_index + per_cpu_persons)])
                arglist = [(persons_subset,tasks_df, day>=quarantine_start) for persons_subset in persons_cluster]
                results = pl.starmap(DaySimulator.generateDailyTasks, arglist)
                pl.close()
                persons_cluster = results.copy()
                results = None
                
                start_index = 0
                for persons_subset in persons_cluster:
                    persons[start_index:start_index+len(persons_subset)] = persons_subset
                    start_index += len(persons_subset)


            daily_groups = []
            #print("Ready for hourly actions...")

            #for hour in tqdm(range(0,24),desc='Hour'):
            for hour in range(0,24):
                #print('\n\n')
                #print(1, '->', datetime.now().time())
                #beginning = datetime.now()
                for prsn in persons:

                    prsn.updateCurrentTask(hour)
                #print(2, '->', datetime.now().time())
                #HourSimulator.generateHourlyActions(persons,hour,actions_df,thresholds_df)
                

                USE_MULTIPROCESSOR = True
                if (not USE_MULTIPROCESSOR):
                    HourSimulator.generateHourlyActions(persons,hour,actions_df,thresholds_df, day)

                else:
                    per_cpu_persons = int(len(persons)/(cpu_cnt - 1))
                    pl = mp.Pool(mp.cpu_count())
                    persons_cluster = []
                    for cpu_i in range(cpu_cnt):
                        start_index = cpu_i*per_cpu_persons
                        persons_cluster.append(persons[start_index : min(len(persons), start_index + per_cpu_persons)])
                    arglist = [(persons_subset,hour,actions_df,thresholds_df, day) for persons_subset in persons_cluster]
                    results = pl.starmap(HourSimulator.generateHourlyActions, arglist)
                    pl.close()
                    persons_cluster = results.copy()
                    results = None
                    
                    start_index = 0
                    for persons_subset in persons_cluster:
                        persons[start_index:start_index+len(persons_subset)] = persons_subset
                        start_index += len(persons_subset)
                
                #print('\n Length of action list for person 100: ', len(persons[100].actions))

                #print(3, '->', datetime.now().time())
                
                #print('\nGenerated hourly actions ', datetime.now() - beginning)




                groups,person_group = GroupManager.assignGroups(persons, preferences_df, tracing_percentage, day)
                #print(4, '->', datetime.now().time())

                # event_cnt = 0
                # event_going_person_cnt = 0
                # for grp in groups:
                #     if((grp.group_name).startswith("E")):
                #         event_cnt+=1
                #         event_going_person_cnt += len(grp.persons)

                # if(event_going_person_cnt>400):
                #     print("\nHour: {} - Events: {} - Event going people: {}\n".format(hour, event_cnt, event_going_person_cnt))
                
                daily_groups.append(person_group)
                #store groups in pickle
                #print(5)

                
                
                for grp in groups:

                    grp.updateActions()

                    #GroupSimulator.groupInteraction(grp, thresholds_df)
                #print(6, '->', datetime.now().time())
                USE_MULTIPROCESSOR = True
                if (not USE_MULTIPROCESSOR):
                    for grp in groups:
                        GroupSimulator.groupInteraction(grp, thresholds_df)

                else:
                    pl = mp.Pool(mp.cpu_count())
                    arglist = [(grp, thresholds_df) for grp in groups]
                    results = pl.starmap(GroupSimulator.groupInteraction, arglist)
                    pl.close()
                    groups = results.copy()
                    results = None
                    for grp in groups:
                        for person in grp.persons:
                            persons[person.id] = person


                    #GroupSimulator.groupInteraction(grp, thresholds_df, preferences_df)
                #print(7, '->', datetime.now().time())


                #print(groups[0].persons[0])
                #map(GroupManager.updateActions, groups)
                #print(groups[0].persons[0])
                #args = [(grp, thresholds_df) for grp in groups]
                #map(GroupSimulator.groupInteraction, args)

            #store groups in pickle file
            pickle.dump(daily_groups,open(output_dirname + 'group_info_day_' + str(day) + '.p','wb'))

            DaySimulator.dayEnd(persons, thresholds_df, day, trace_days, quarantine_days, preferences_df, beginmodel, tracing_starts_on_day, output_dirname)

            cnt_infections = 0

            unemployed_cnt = 0
            isolated_cnt = 0

            for prsn in persons:

                if(prsn.is_infected):
                #if(prsn.state == 'contagious_symptomatic' or prsn.state == 'Dead'):
                    cnt_infections += 1
                if(prsn.profession == 'Unemployed'):
                    unemployed_cnt+=1
                if(prsn.profession == 'Isolated'):

                    #print("Isolated dude has {} tasks\n".format(len(prsn.tasks)))
                    isolated_cnt+=1
                    #print("{} is unemployed".format(prsn.id))

            #print("Total unemployed today: " + str(unemployed_cnt))
            #print("Total isolated today: " + str(isolated_cnt))

            
            

            #REMOVED THIS FOR SERVER
            #tqdm.write('Total Infections = {},\tNew Infections = {}'.format(cnt_infections,cnt_infections-infections[-1]))
            
            infections.append(cnt_infections)

            #print("Total Infection Array: "+ str(infections))
            

            if(timerun==0):
                if day in snapdays:
                    personname = 'persons_snapshot' + str(day) + '.p'
                    infectname = 'infections_snapshot' + str(day) + '.p'
                    pickle.dump(persons,open(output_dirname + personname,'wb'))
                    pickle.dump(infections,open(output_dirname + infectname,'wb'))
                    #break
                    #print(persons)


            if (cnt_infections-infections[-2] <= 5):
                #print("working")
                track += 1
            else:
                track = 0

            infction_perc = cnt_infections/len(persons)

            if (infction_perc >= 0.8):
                if (track >= 5):
                    break


            myLogFile.write('Day finishes at '+ str(datetime.now()) + '\n')
            #print('Day finishes at '+ str(datetime.now()) + '\n')
            





        pickle.dump(persons,open(output_dirname + 'persons.p','wb'))

        #plt.plot(infections[0:])


        #plt.show()
        myLogFile.write("%s \n" % infections)
        print("Output - " + str(infections))
        outfile = open(output_dirname + "Outputarray.txt","w+")
        outfile.write(str(infections))            
