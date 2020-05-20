from ovsdb_client import OVSDBConnection
import variables as names
import sys
import argparse


def main(argv):

    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--table_name", type=str, required=False, help="FSM table name to be updated")
    ap.add_argument("-q", "--update_query", type=str, required=True, help="Update query to run on the FSM table")
    args = ap.parse_args()

    ovsdb_client = OVSDBConnection(names.__OVSDB_IP__, names.__OVSDB_PORT__)
    ovsdb_client.update_fsm_table(args.update_query)



if __name__ == "__main__":
    sys.exit(main(sys.argv))