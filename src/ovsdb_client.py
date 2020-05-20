import collections
import json
import logging
import os
import socket
import threading
import yaml
import variables as names
from jsonrpclib import Server
import ssl

logging.basicConfig(level=logging.DEBUG)

"""
a simple client to talk to ovsdb over json rpc
"""

delete_json = \
[
    "FSM",
    {
        "op":"delete",
        "table":"",
        "where": []
    }
]

insert_json = \
[
        "FSM",
        {
            "op":"insert",
            "table":"",
            "row":{}
        }
]

select_json = \
[
        "FSM",
        {
            "op":"select",
            "table":"",
            "where":[]
        }
]

"""
Value inside where clause:
[
    "",
    "==",
    [
        "",
        ""
    ]
]
"""


def default_echo_handler(message, ovsconn):
    logging.debug("responding to echo")
    ovsconn.send({"result": message.get("params", None), "error": None, "id": message['id']})

def default_message_handler(message, ovsconn):
    logging.debug("default handler called for method %s", message['method'])
    ovsconn.responses.append(message)

class OVSDBConnection(threading.Thread):
    """Connects to an ovsdb server that has manager set using
        ovs-vsctl set-manager ptcp:5000
        clients can make calls and register a callback for results, callbacks
         are linked based on the message ids.
        clients can also register methods which they are interested in by
        providing a callback.
    """

    def __init__(self, IP, PORT, **handlers):
        super(OVSDBConnection, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((IP, PORT))
        self.responses = []
        self.callbacks = {}
        self.callback_id = 0
        self.read_on = True
        self.handlers = handlers or {"echo": default_echo_handler}
        #self.daemon = True TODO Run thread in BG.
        self.start()

    def send(self, message, callback=None):
        if callback:
            self.callback_id += 1
            message['id'] = self.callback_id
            self.callbacks[self.callback_id] = callback
        self.socket.send(json.dumps(message))

    def response(self, id):
        return [x for x in self.responses if x['id'] == id]

    def set_handler(self, method_name, handler):
        self.handlers[method_name] = handler

    def _on_remote_message(self, message):
        try:
            json_m = json.loads(message,
                                object_pairs_hook=collections.OrderedDict)
            #check first to see if the message is for a method and we have a
            # handler for it
            handler_method = json_m.get('method', None)
            # handler method is returned as "echo" for default case.
            if handler_method:
                self.handlers.get(handler_method, default_message_handler)(
                    json_m, self)
            elif json_m.get("result", None) and json_m['id'] in self.callbacks:
                id = json_m['id']
                #check if this is a result of an earlier call we made and that
                # we have a callback registered
                if not self.callbacks[id](json_m):
                    # if callback is to be persisted, callback should return
                    # something
                    self.callbacks.pop(id)
            else:
                #add it for sync clients
                default_message_handler(message, self)
        except Exception as e:
            logging.exception("exception [%s] while handling message [%s]", e.message, message)
        #self.read_on = False

    def __echo_response(message, self):
        self.send({"result": message.get("params", None),
                   "error": None, "id": message['id']})

    def run(self):

        chunks = []
        lc = rc = 0
        while self.read_on:
            response = self.socket.recv(4096)
            if response:
                response = response.decode('utf8')
                message_mark = 0
                for i, c in enumerate(response):
                    #todo fix the curlies in quotes
                    if c == '{':
                        lc += 1
                    elif c == '}':
                        rc += 1

                    if rc > lc:
                        raise Exception("json string not valid")

                    elif lc == rc and lc is not 0:
                        chunks.append(response[message_mark:i + 1])
                        message = "".join(chunks)
                        self._on_remote_message(message)
                        lc = rc = 0
                        message_mark = i + 1
                        chunks = []

                chunks.append(response[message_mark:])

    def stop(self, force=False):
        self.read_on = False
        if force:
            self.socket.close()

    def fsm_table_prune(self, fsm_table_name):
        delete_json[1]["table"] = fsm_table_name
        delete_query = {"method": "transact", "params": delete_json}
        #print (json.dumps(delete_query, indent=4))
        self.send(delete_query, self.res)

    def fsm_table_setup(self, fsm_table_name):
        path = ''.join([os.getcwd(), "/../config/", fsm_table_name, ".yaml"])
        file_path = os.path.abspath(path)
        with open(file_path, 'r') as stream:
            rows =  yaml.safe_load(stream)
            for row in rows:
                insert_json[1]["table"] = fsm_table_name
                insert_json[1]["row"] = row
                insert_query = {"method": "transact", "params": insert_json}
                #print json.dumps(insert_query, indent=4)
                self.send(insert_query, self.res)

    def get_fsm_table(self, **kwargs):
        transact_query = {"method": "transact", "params": select_json}
        select_json[1]["table"] = kwargs["table_name"]
        select_json[1]["where"] = kwargs["where"]
        self.send(transact_query, kwargs["callback"])

    def init_fsm_tables(self):
        for table in names.__FSM_TABLE_LIST__:
            self.fsm_table_prune(table)
            self.fsm_table_setup(table)

    def update_fsm_table(self, update_json):
        update_query = {"method": "transact", "params": json.loads(update_json)}
        self.send(update_query, self.update_callback)

    def update_callback(self, message):
        logging.debug("Updated the table and now exiting")
        self.read_on = False

    def run_command_on_device(self, command):
        # TODO This is a temporary workaround for certificate_verify_failed error for HTTPS
        if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
            ssl._create_default_https_context = ssl._create_unverified_context

        # switch = Server("https://admin:admin@10.0.0.254:443/command-api")
        server = "https://" + names.__USERNAME__ + ":" + names.__PASSWORD__ \
                 + "@" + names.__SWITCH_IP_PORT__ + "/command-api"
        switch = Server(server)
        # response = switch.runCmds(1, ["show hostname"])
        response = switch.runCmds(1, command)
        logging.debug("Response: " + response)

    def res(self, message):
        #print "ovsdb-server response ", json.dumps(message, indent=4)
        return False