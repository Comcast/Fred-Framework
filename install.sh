
##############  SETUP PACKAGES  ###############
cd packages/
tar -xzvf pycryptodomex-3.7.0.tar.gz 
tar -xzvf pyasn1-0.4.4.tar.gz 
tar -xzvf pysnmp-4.4.6.tar.gz 

cd pyasn1-0.4.4
python setup.py install
cd ../pycryptodomex-3.7.0
python setup.py install
cd ../pysnmp-4.4.6
python setup.py install
cd ../
rm -rf pyasn1-0.4.4
rm -rf pycryptodomex-3.7.0
rm -rf pysnmp-4.4.6
cd ../

##############  SETUP OVSDB-SERVER  ###############
cd ovsdb_db/
rm ./fsm.db
ovsdb-tool create ./fsm.db ./fsm.ovsschema
mkdir /var/run/openvswitch
touch /var/run/openvswitch/ovsdb-server.pid
mkdir /var/log/openvswitch
touch /var/log/openvswitch/ovsdb-server.log
ovs-appctl -t ovsdb-server exit
ovsdb-server --pidfile --detach --log-file --remote punix:/var/run/openvswitch/db.sock ./fsm.db
ovs-appctl -t ovsdb-server ovsdb-server/add-remote ptcp:6640
ovsdb-client dump  tcp:127.0.0.1:6640

