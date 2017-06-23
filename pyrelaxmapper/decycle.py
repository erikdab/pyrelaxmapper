# -*- coding: utf-8 -*-
import networkx as nx


def proc():
    """O.O"""
    in_file = open("synset_hipernyms.txt", "r")
    g = nx.DiGraph()
    for line in in_file:
        l = line.split()
        g.add_node(l[0])
        g.add_node(l[1])
        g.add_edge(l[0], l[1])
    a = nx.strongly_connected_components(g)
    for i in a:
        if i.__len__() > 1:
            print(i)
