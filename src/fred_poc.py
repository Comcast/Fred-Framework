from device import Device
# The external driver

# For any device, before spinning off the agent, define its states, default_state,
# But the default state can be / should be obtained from the scema???
# POC just need to start the agent, the details of the state will be pulled from the OVSdb database

# When a new device object is created, an agent for the device is automatically created.
switch1 = Device()
# Start the agent
switch1.start_agent()

#switch2 = Device()