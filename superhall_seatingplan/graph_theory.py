from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import sys
from setup import get_Matrices,plot_setup
from MCR_Dining.superhall_seatingplan.cyth import sa_core

import argparse
import numpy as np
# Add argparse
parser = argparse.ArgumentParser(description="Run seating / bath simulation with optional seed")
parser.add_argument("--seed", type=int, default=0, help="Random seed")
args = parser.parse_args()

# Set the seed
np.random.seed(args.seed)
import random
random.seed(args.seed)
sa_core.seed_c_rng(args.seed)
print(f'using seed {args.seed}')


folder='/mnt/c/Users/Cole/Downloads'
folder='/home/colehunt/software/MCR-dining/data'
folder='/home/ach221/Desktop'
folder='/home/ach221/Downloads'
### Get the names from Upay and seating form responses to generate the Matrices required
event_booking_html = f"{folder}/Upay - Event Booking.html"
seating_form_responses = f"{folder}/Superhall Seating Request Form (Responses).xlsx"
swaps_xls = f"{folder}/MTSuperhallSwaps2025-26.xlsx"
A,P,G,seat_positions,guestlist = get_Matrices(event_booking_html,swaps_xls,seating_form_responses) #matrices in csr format
namelist=guestlist.everyone
ntot=A.shape[0]
print(f'total number of seate {ntot}')

import igraph as ig
import leidenalg as la

g = ig.Graph.TupleList(
    edges=[(i, j, P[i,j]) for i in range(ntot) for j in range(ntot) if P[i,j]>3],
    weights=True,
    directed=True
)
# tol=0
# g = ig.Graph.TupleList(
#     edges=[(i, j, P[i,j]) for i in range(ntot) for j in range(ntot) if P[i,j]/P[i,:].sum()>0],
#     weights=True,
#     directed=True
# )
# strong_comps = g.components(mode='STRONG')
# for i, comp in enumerate(strong_comps):
#     print(f"Strong Component {i} (size {len(comp)}): {comp}")
weak_comps = g.components(mode='WEAK')
for i, comp in enumerate(weak_comps):
    print(f"Weak Component {i} (size {len(comp)}): {comp}")




sys.exit()
# choose your resolution parameter (gamma) 
gamma = 0   # this is the minimum (gives the graph with only disconnections)
# gamma = 1.0 is default
# gamma > 1 → more, smaller communities

partition = la.find_partition(
    g,
    la.RBConfigurationVertexPartition,
    weights='weight',
    resolution_parameter=gamma
)

# print results
for i, community in enumerate(partition):
    print(f"Component {i} (size {len(community)}): {community}")
    for person_i in community:
        name = namelist[person_i]
        name=guestlist.everyone[person_i]
        guests = guestlist.attendees_guest_map[name]

        present = 0
        for guest_name in guests:
            if guestlist.find(guest_name) not in community:
                print(guest_name,'not in')






# Get the connected components
components = g.components()  

# Print results
for i, comp in enumerate(components):
    print(f"Component {i} (size {len(comp)}): {comp}")



import networkx as nx
G = nx.Graph()
for i in range(ntot):
    for j in range(ntot):
        w = P[i,j]
        if w > 0:
            G.add_edge(i, j, weight=w)

components = list(nx.connected_components(G))
for comp in components:
    print(list(comp))
