from agent import Agent

# Device (switch) has an agent

class Device:

    def __init__(self):
        self.agent = Agent.create_agent(self)

    def start_agent(self):
        self.agent.launch()
