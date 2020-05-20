from pysnmp.entity.rfc3413.oneliner import cmdgen

class Monitor:

    def __init__(self, machine, monitor):
        # Every monitor belong to some machine
        self.fsm = machine
        self.ovsdb_client = machine.ovsdb_client
        # Monitor specific parameters
        self.monitor_name = monitor["monitor_name"]
        self.run_period = monitor["run_period"]
        self.monitor_code = monitor["snmp_mib"]
        self.monitor_val = monitor["desired_mib_value"]
        self.upper_bound = monitor["upper_bound"]

        self.cmdGen = cmdgen.CommandGenerator()

    def update_monitor(self, monitor):
        self.monitor_name = monitor["monitor_name"]
        self.run_period = monitor["run_period"]
        self.monitor_code = monitor["snmp_mib"]
        self.monitor_val = monitor["desired_mib_value"]
        self.upper_bound = monitor["upper_bound"]

    # status: check based on TL's monitor: true/false
    # IMPORTANT: return value TRUE indicates that the monitor is
    def do_health_check(self, status):
        device_state = self.execute_monitor_code()

        # If the counters are greater than the maximum allowed
        if self.upper_bound and device_state > self.monitor_val:
            return True
        # If the counters are lesser than the minimum allowed
        elif not self.upper_bound and device_state < self.monitor_val:
            return True

        # Otherwise all is well - monitor returns false indicating no need to state change
        return False

    def execute_monitor_code(self):
        # TODO USE SWITCH's APIs to execute the monitor code
        # May be use callback to handle the output based on the need
        # output = device.run(self.monitor_code)
        #self.ovsdb_client.run_command_on_device(self.monitor_code)
        print "monitoring"
        return 7

        errorIndication, errorStatus, errorIndex, varBinds = self.cmdGen.getCmd(
            cmdgen.CommunityData('public'),
            cmdgen.UdpTransportTarget(('127.0.0.1', 161)),
            self.monitor_code
        )
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varbind in varBinds:
                print varbind[0], " = ", varbind[1]
                mibValue = varbind[1]

        return mibValue

