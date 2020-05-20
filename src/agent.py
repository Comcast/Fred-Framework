import json
from ovsdb_client import OVSDBConnection
from machine import Machine
import variables as names
import logging
# Singleton class: A device can have only one agent
# Agent is owner of different states that are part of machines in device
# Agent is also an owner of actions (methods) that can be applied to different states.

# OWNS MACHINES

class Agent:
    __agent = None
    _name = "FRED"

    @staticmethod
    def create_agent(device):
        if Agent.__agent is None:
            return Agent(device)
        return Agent.__agent

    def __init__(self, dev):
        if Agent.__agent is not None:
            raise Exception("Singleton Class: Agent can be created only with createAgent() method")
        else:
            Agent.__agent = self

        # Agent is a part of some device, dev
        self.device = dev

        # Agent can contain more than one FSM
        self.list_of_fsm = []

        # Agent owns the ovsdb client (OVSdb server runs independently inside switch)
        self.ovsdb_client = OVSDBConnection(names.__OVSDB_IP__, names.__OVSDB_PORT__)

    def launch(self):
        # Reset and fill the tables in OVSdb using the fsm.ovsschema
        self.ovsdb_client.init_fsm_tables()

        # Get FSMs for this device from database (This can be done by reading YAML files too)
        kvargs = {"table_name": names.__FSM_NAME_TABLE__, "where": [],
                  "callback": self.get_fsm_table_callback}
        self.ovsdb_client.get_fsm_table(**kvargs)

    # TODO This callback does not look good here
    # Callback to wait and receive the transaction output
    def get_fsm_table_callback(self, message):
        machines = message["result"][0]["rows"]
        for machine in machines:
            # Initialize an object for every fsm
            fsm = Machine(self, machine)
            # Add the new FSM to the FSMs owned by this agent
            self.list_of_fsm.append(fsm)
        # Signal the OVSdb client that this callback will not persist
        return False

    def enable_fsm(self, fsm_name):
        pass

    def report_to_controller(self):
        pass
