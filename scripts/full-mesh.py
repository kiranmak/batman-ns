#!/usr/bin/env python

# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2022 NITK Surathkal

########################
# SHOULD BE RUN AS ROOT
########################
from nest.topology import *
from nest.engine.exec import exec_subprocess
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper
import nest.config as config

class BatmanNode:
    def __init__(self, name):
        self.name = name
        #exec_subprocess(f"ip netns add {name}")
        self.node = Switch(name)

    def getId(self):
        return self.name

    def add_hosts(self, hosts):
        self.hosts = hosts

    def start(self):
        bh.launch_batman(self.node.id, self.left, self.right)
        bh.create_forwarder(self.node.id, self.left, self.right, self.hosts)

    def stop(self):
        bh.destroy_batman(self.node.id)
        bh.delete_switch(ns_name, "br0")

class MeshRing:
    def __init__(self): # make it general later
        config.set_value("assign_random_names", False)
        config.set_value("delete_namespaces_on_termination", False)
        self.nodes = None
        self.if_pair = None
        self.nonmesh_nodes = None
        self.nonmeshifs = None

    def mesh_topology(self):

        # Create two hosts `h1` and `h2`, and two routers `r1` and `r2`
        B1 = BatmanNode("B1")
        B2 = BatmanNode("B2")
        B3 = BatmanNode("B3")
        B4 = BatmanNode("B4")
        if_down("B1", "B1")

        (b1_wt1, b2_wt0) = connect(B1.node, B2.node, "wt1", "wt0" )
        (b2_wt1, b3_wt0) = connect(B2.node, B3.node, "wt1", "wt0" )
        (b3_wt1, b4_wt0) = connect(B3.node, B4.node, "wt1", "wt0" )
        (b4_wt1, b1_wt0) = connect(B4.node, B1.node, "wt1", "wt0" )

        B1.left, B1.right = b1_wt0, b1_wt1
        B2.left, B2.right = b2_wt0, b2_wt1
        B3.left, B3.right = b3_wt0, b3_wt1
        B4.left, B4.right = b4_wt0, b4_wt1


        h1, h2 = Node("h1"), Node("h2")
        h3, h4 = Node("h3"), Node("h4")
        n1 = Network("192.168.1.0/24")  # network between h0 and b0
        n2 = Network("192.168.2.0/24")  # network between h2 and b2
        B1.add_hosts([h1])
        B2.add_hosts([h2])
        B4.add_hosts([h4])
        B3.add_hosts([h3])

        (h1_eth0, b1_sge0) = connect(h1, B1.node, "eth0", "sge0" )
        (h3_eth0, b3_sge0) = connect(h3, B3.node, "eth0", "sge0" )

        h1_eth0.set_address("192.168.2.3")
        b1_sge0.set_address("192.168.2.4")

        h3_eth0.set_address("192.168.4.3")
        b3_sge0.set_address("192.168.4.4")
        self.nodes = [B1, B2, B3, B4]
        #batctl_if_down("B4", "wt0")

def batctl_if_create(ns_name, ifname):
    exec_subprocess(
      f"ip netns exec {ns_name} ip link add dev {ifname} type veth")

def if_down(ns_name, ifname):
    exec_subprocess(
      f"ip netns exec {ns_name} ip link set down {ifname}")


exec_subprocess(f'ip -all netns delete')
M = MeshRing()
M.mesh_topology()

