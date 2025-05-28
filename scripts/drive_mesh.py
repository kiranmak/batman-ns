########################
# SHOULD BE RUN AS ROOT
########################
from nest.topology import *
import nest.config as config
from nest.engine.exec import exec_subprocess, exec_subprocess_with_live_output
from nest.engine.ip_link import (create_switch,
                                 add_int_to_ns,
                                 set_int_up,
                                 setup_veth)

from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper

def nest_config_init():
    config.set_value("assign_random_names", False)
    config.set_value("delete_namespaces_on_termination", False)

class BatNode:
    def __init__(self, _ns):
        self.node = Node(_ns)
        self.ns = _ns
        self.ifs = {}
        self.wt0 = None
        self.wt1 = None
        self.sge0 = None
        self.hosts = []

    def add_sgw_ifs(self, sgeifs):

        for idx in range(len(sgeifs)):
            hname = self.ns + "_h" + '{:#02d}'.format(idx)
            exec_subprocess( f"ip netns add {hname}")
            setup_veth(hname, self.ns, "eth0", sgeifs[idx])
            self.hosts.append(hname)

        self.add_to_bridge(sgeifs)

    def connect_ifs(self, other, myif, otherif):
        (b1_wt1, b2_wt0) = connect(self.node, other.node, myif, otherif)

    def set_mac_addresses(self, idx):
        ifs = {"wt0": "a4:f9:10:00:ba:",
               "wt1": "a4:f9:10:00:bb:",
               "sge0":"a4:f9:10:00:bc:",
               "sge1":"a4:f9:10:00:bd:" ,
               "bat0":"a4:f9:10:00:be:" }
        for if_name, prefix in ifs.items():
            cmd = f" ifconfig {if_name} hw ether "
            mac = prefix + '{:#02d}'.format(idx)
            exec_subprocess( f"ip netns exec {self.ns} {cmd} {mac}")

        for hidx, h in enumerate(self.hosts):
            cmd = f" ifconfig eth0 hw ether "
            prefix = 'a4:f9:10:00:{:#02d}:'.format(idx)
            mac = prefix + '{:#02d}'.format(hidx)
            print( f"ip netns exec {h} {cmd} {mac}")
            exec_subprocess( f"ip netns exec {h} {cmd} {mac}")

    def add_batctl(self, iflist):
        for ifname in iflist:
            add_int_to_switch_ns(self.ns, "bat0", ifname)

    def add_to_bridge(self, iflist):
        for ifname in iflist:
            add_int_to_switch_ns(self.ns, "br0", ifname)

def add_int_to_switch_ns(ns_name, s_name, dev_name):
    cmd = f" ip link set {dev_name} master {s_name}"
    exec_subprocess( f"ip netns exec {ns_name} {cmd}")

def create_host_if(ns_name, hname):
    name = ns_name + "_" + hname
    exec_subprocess( f"ip netns add {name}")

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

def set_bat_loop_avoidance(ns, flag):
    cmd = "batctl bat0 bl"
    set_flag = 1 if flag else 0
    exec_subprocess(f"ip netns exec {ns}  {cmd} {set_flag}")



if __name__ == "__main__":
    nest_config_init()
    ns_db = ["B1", "B2", "B3", "B4", "B5", "B6"]
    batnode = {}
    clean_ns(ns_db)

    for node in ns_db:
        batnode[node] = BatNode(node)
        sw = create_switch(node, "br0")
        bt0 = create_batif(node, "bat0")
        add_int_to_switch_ns(node, "br0", "bat0")
        set_bat_loop_avoidance(node, 1)


    batnode["B1"].connect_ifs(batnode["B2"], "wt1", "wt0")
    batnode["B2"].connect_ifs(batnode["B3"], "wt1", "wt0")
    batnode["B3"].connect_ifs(batnode["B4"], "wt1", "wt0")
    batnode["B4"].connect_ifs(batnode["B5"], "wt1", "wt0")
    batnode["B5"].connect_ifs(batnode["B6"], "wt1", "wt0")
    # close the loop
    batnode["B6"].connect_ifs(batnode["B1"], "wt1", "wt0")

    for node in ns_db:
        batnode[node].add_batctl(["wt0", "wt1"])


    index = 0
    for node in ns_db:
        index += 1
        batnode[node].add_sgw_ifs(["sge0", "sge1"])

    index = 0
    for node in ns_db:
        index += 1
        batnode[node].set_mac_addresses(index)

    for node in ns_db:
        set_interfaces_up(node, ["sge0", "wt0", "wt1", "bat0", "br0"])

