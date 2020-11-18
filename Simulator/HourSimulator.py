from Actions.ActionManager import ActionManager

class HourSimulator:

    def __init__(self):

        pass


    @staticmethod
    def generateHourlyActions(persons, hour, actions_df, thresholds_df, day, print_opt=False):
            

        for prsn in persons:

            current_task = prsn.current_task

            prsn.setActions(ActionManager.generateActions(prsn.id, actions_df[actions_df["task"]==current_task.name], thresholds_df, day, hour))

            if(print_opt):
                print('=== {} === {} === {} ==='.format(hour, prsn.profession, current_task))
                ActionManager.printActions(prsn.actions)
        return persons

