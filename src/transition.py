class Transition():

    def __init__(self, state, machine, transition):
        # Every transition belongs to some machine and some state
        self.fsm = machine
        self.start_state = state

        # Transition specific parameters
        self.transition_name = transition["transition_name"]
        # Transition logic is a boolean combination of one or more health monitors (monitor_WAN1+!monitor_WAN2)
        self.logic_list = transition["transition_logic"].split("+")
        self.end_state = self.fsm.get_state_object(transition["end_state"])

        #print "Transition", self.fsm.name, self.start_state.name, self.transition_name, str(self.logic_list), "\n"

    def check_transition_logic(self, logic_list):
        for logic in logic_list:
            status  = True
            if logic.startswith('!'):
                # Convert !monitor_WAN1 to monitor_WAN1 with status=False
                logic = logic[1:]
                status = False
            result = self.fsm.do_health_check(logic, status)
        # A True in result indicates that a transition is required
        return result