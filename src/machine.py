import variables as names
import logging
import threading, time
from state import State
from monitor import Monitor

# OWNS STATES, MONITORS
# TODO Why maintain list of monitors when they are updated on runtime everytime?
class Machine:

    def __init__(self, agent, machine):
        # A machine objects belongs to an agent
        self.agent = agent
        self.ovsdb_client = agent.ovsdb_client

        # Machine specific parameters
        self.name = machine["fsm_name"]
        self.default_state = machine["default_state"]
        self.status = machine["enable"]
        self.state_thread = None
        self.monitor_ready = False
        self.list_of_monitors = {}
        # If FSM's status is enabled, initialize states and monitors
        if self.status:
            # Every machine has a list of possible states
            self.list_of_states = []
            self.get_all_states()
            # Every machine owns the monitors that run within
            #self.list_of_monitors = {}
            #self.get_all_monitors()

    def get_all_states(self):
        where_clause = [["fsm_name", "==", self.name]]
        kvargs = {"table_name": names.__FSM_STATE_TABLE__, "where": where_clause,
                  "callback": self.get_states_table_callback}
        self.ovsdb_client.get_fsm_table(**kvargs)

    def get_states_table_callback(self, message):
        states = message["result"][0]["rows"]
        for state in states:
            new_state = State(self, state)
            self.list_of_states.append(new_state)
            # Check if the state is the default state and start it
            if new_state.name == self.default_state:
                self.state_thread = threading.Thread(target=new_state.run)
                self.state_thread.start()
            #logging.debug(state["state_name"])
        return False

    def get_monitor(self, monitor_name):
        where_clause = [["fsm_name", "==", self.name],["monitor_name", "==", monitor_name]]
        kvargs = {"table_name": names.__FSM_MONITOR_TABLE__, "where": where_clause,
                  "callback": self.get_monitor_table_callback}
        self.ovsdb_client.get_fsm_table(**kvargs)

    def get_monitor_table_callback(self, message):
        # TODO add error check here if ovsdb returns nothing
        monitors = message["result"][0]["rows"]

        # Ideally I expect only one monitor to be returned by FSM_NAME and MONITOR_NAME index key combination
        if len(monitors) != 1:
            logging.error("Undesired number of monitors %d returned", len(monitors))

        for monitor in monitors:
            if not monitor["monitor_name"] in self.list_of_monitors:
                self.list_of_monitors[monitor["monitor_name"]] = Monitor(self, monitor)
            else: # The monitor exist -> update the monitor
                old_monitor = self.list_of_monitors.get(monitor["monitor_name"])
                old_monitor.update_monitor(monitor)

        self.monitor_ready = True
        return False

    def do_health_check(self, monitor_name, status):
        self.monitor_ready = False
        self.get_monitor(monitor_name) # this is done every healthcheck interval for every FSM as the monitors can change real-time
        while not self.monitor_ready:
            continue  # do nothing until new monitors are ready

        monitor = self.list_of_monitors.get(monitor_name)
        if not monitor:
            logging.error("Monitor %s not found!! Check the FSM_MONITOR_TABLE", monitor_name)
            return
        # Run the heath check for the monitor
        return monitor.do_health_check(status)

    def transition_to_new_state(self, new_state):
        try:
            time.sleep(1)
            self.state_thread = threading.Thread(target=new_state.run)
            self.state_thread.start()
            logging.debug("Starting fsm [%s] state: [%s] state: [%s]", self.name,
                              str(self.state_thread.is_alive()), new_state.name)
        except Exception as e:
            logging.exception("exception [%s] while handling fsm [%s] state: [%s] state: [%s]", e.message, self.name, str(self.state_thread.is_alive()), new_state.name)
        pass

    def get_state_object(self, state_name):
        state = None
        for state in self.list_of_states:
            if state.name == state_name:
                found = True
                break
        if not found:
            logging.error("Error! State not found!! Check the FSM_STATE_TABLE")
            return None
        return state

    # Every FSM has a default state
    def get_default_state(self):
        # Get schema for state from OVSdb schema
        pass

    # Every FSM has a default state
    def add_state(self):
        # Get schema for state from OVSdb schema
        pass

    def start_machine(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def set_default_state(self):
        pass

    def load_default_state(self):
        pass

    def state_transition(self):
        pass

    def monitor_current_state(self):
        pass

    def machine_clean_up(self):
        pass


