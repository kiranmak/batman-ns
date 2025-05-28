########################
# SHOULD BE RUN AS ROOT
########################
from nest.topology import *
import nest.config as config
from nest.engine.exec import exec_subprocess, exec_subprocess_with_live_output
from nest.engine.ip_link import create_switch, add_int_to_ns , set_int_up
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper

def add_int_to_switch_ns(ns_name, s_name, dev_name):
    exec_subprocess(
        f"ip netns exec {ns_name} ip link set {dev_name} master {s_name}")


def create_batif(ns_name, dev_name):
    exec_subprocess(
        f"ip netns exec {ns_name} ip link add {dev_name} type batadv")

def set_interfaces_up(ns_name, if_list):
    for intf in if_list:
        set_int_up(ns_name, intf)

def clean_ns(ns_names):
    for ns in ns_names:
        exec_subprocess(f"ip netns del {ns}")
        print(f"Deleted node {ns}")
    exec_subprocess(f"ip netns list")


config.set_value("assign_random_names", False)
config.set_value("delete_namespaces_on_termination", False)
b1_ns = "B5"
b2_ns = "B6"
class BatNode:
    def __init__(self, _ns):
        self.node = Node(_ns)
        self.ifs = {}
        self.wt0 = None
        self.wt1 = None
        self.sge0 = None
    def add_hosts(self, hosts):
        self.hosts = hosts

def set_bat_loop_avoidance(ns_name, flag):
    cmd = "batctl bat0 bl"
    set_flag = 1 if flag else 0
    exec_subprocess(f"ip netns exec {ns}  {cmd} {set_flag}")

clean_ns([b1_ns, b2_ns])
B1 = BatNode(b1_ns)
sw = create_switch(b1_ns, "br0")
bt0 = create_batif(b1_ns, "bat0")
add_int_to_switch_ns(b1_ns, "br0", "bat0")
set_bat_loop_avoidance(b1_ns,1)

B2 = BatNode(b2_ns)
sw = create_switch(b2_ns, "br0")
bt0 = create_batif(b2_ns, "bat0")
add_int_to_switch_ns(b2_ns, "br0", "bat0")

(b1_wt1, b2_wt0) = connect(B1.node, B2.node, "wt1", "wt0" )
B1.wt0, B1.wt1 = b2_wt0, b1_wt1

add_int_to_switch_ns(b1_ns, "br0", "wt1")
add_int_to_switch_ns(b2_ns, "br0", "wt0")

h1, h2 = Node("h5"), Node("h6")
#n1 = Network("192.168.1.0/24")  # network between h0 and b0
#n2 = Network("192.168.2.0/24")  # network between h2 and b2
B1.add_hosts([h1])
B2.add_hosts([h2])

(h1_eth0, b1_sge0) = connect(h1, B1.node, "eth0", "sge0" )
(h2_eth0, b2_sge0) = connect(h2, B2.node, "eth0", "sge0" )

# non-mesh interfaces can be aded to br0 but not bat0
# bat0 gets wt0, wt1

add_int_to_switch_ns(b1_ns, "br0", "sge0")
add_int_to_switch_ns(b2_ns, "br0", "sge0")
set_interfaces_up(b1_ns, ["sge0", "wt0", "wt1", "bat0", "br0"])
set_interfaces_up(b2_ns, ["sge0", "wt0", "wt1", "bat0", "br0"])
