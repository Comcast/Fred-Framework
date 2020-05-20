import variables as names
from transition import Transition
import time

# OWNS TRANSITIONS

class State():

    def __init__(self, machine, state):
        # Every state belongs to a machine
        self.fsm = machine
        self.ovsdb_client = machine.ovsdb_client

        # State specific parameters
        self.name = state["state_name"]
        self.on_config = state["on_state_config"]
        self.off_config = state["off_state_config"]
        self.state_config = state["state_config"]

        # State transition happens when the transition logic (TL) is met
        # One start state can have multiple different transition based on the TL
        self.transitions_ready = False
        self.list_of_transitions = []

    def get_transitions(self):
        where_clause = [["fsm_name", "==", self.fsm.name],["start_state", "==", self.name]]
        kvargs = {"table_name": names.__FSM_TRANSITION_TABLE__, "where": where_clause,
                  "callback": self.get_transition_table_callback}
        self.ovsdb_client.get_fsm_table(**kvargs)

    def get_transition_table_callback(self, message):
        transitions = message["result"][0]["rows"]
        for transition in transitions:
            self.list_of_transitions.append(Transition(self, self.fsm, transition))
        self.transitions_ready = True
        return False

    def run(self):
        # apply on_state config #TODO what is off_state_config??
        self.apply_on_config()
        self.transitions_ready = False
        self.get_transitions() # Get any updated transitions every time -- needed? (impacts thread's performance)
        while not self.transitions_ready:
            continue # do nothing until transaction logic is ready
        # This will run only when the state is set to actve by the FSM
        print "\n","State THREAD READY", self.name, self.fsm.name, "\n"

        # Start monitoring state. Move to end_state if transition logic criterion is met.
        transition  = self.list_of_transitions[0]
        while not transition.check_transition_logic(transition.logic_list):
            #self.transitions_ready = False
            #self.get_transitions()  # Get any updated transitions every time -- needed? (impacts thread's performance)
            # Performance hack: Trigger the transaction with OVSdb before the state thread goes to sleep - new transactions will be ready when state thread becomes active
            time.sleep(names.__STATE_MONITOR_TIME__) # Monitor the state transition status periodically
            #while not self.transitions_ready:
            #    continue  # do nothing until transaction logic is ready

        new_state = transition.end_state         # Move to the end_state when the transition logic is met
        self.fsm.transition_to_new_state(new_state)
        print "\n","State THREAD DYING", self.name, self.fsm.name, "\n"
        # End of thread's life

    def apply_on_config(self):
        # TODO Call device's API to push configuration into switch's config table
        pass
    
    def apply_off_config(self):
        pass
