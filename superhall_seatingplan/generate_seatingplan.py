from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import sys
from setup import get_Matrices,plot_setup
from MCR_Dining.superhall_seatingplan.metrics_moves import total_happiness,all_happiness,all_sat_with_guests,all_sat_with_friends,trial_move3
from MCR_Dining.superhall_seatingplan.metrics_moves import happiness,ij_andnearby
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
# folder='/home/ach221/Downloads'
### Get the names from Upay and seating form responses to generate the Matrices required
event_booking_html = f"{folder}/Upay - Event Booking.html"
seating_form_responses = f"{folder}/Superhall Seating Request Form (Responses).xlsx"
swaps_xls = f"{folder}/MTSuperhallSwaps2025-26.xlsx"
A,P,G,seat_positions,guestlist = get_Matrices(event_booking_html,swaps_xls,seating_form_responses) #matrices in csr format
namelist=guestlist.everyone
ntot=A.shape[0]
print(f'total number of seate {ntot}')
'''
Calculate the seating plan using Monte Carlo.
A: adjacency matrix     A[seat#,:]= list of weights on seat#s      Gives score of how good seating is. e.g. A12 = how good is it for 1 to sit with 2
P: preference matrix    P[person#,:]= list of that person's preference on person#s
G: gallery matrix       G[person#,:]= list of person's prefrence on seat#s
s: Seat location        s[person#]= seat#   
p: Person location      p[seat#]= person#   
'''



### Initial conditions
s=np.arange(ntot)
p=np.arange(ntot)
# Random permutation for seating


### Randomize initial confign
# Set a different seed, e.g., 42
s = np.random.permutation(ntot)
p = np.empty_like(s)
p[s] = np.arange(ntot)
h=total_happiness(A,P,G,p,s)

### Setup the plot
show=0
save_to_spreadsheet=0
if show:
    plt.ion()
    sc,cbar,ax,stop_button,text_labels=plot_setup(plt,seat_positions,all_happiness(A,P,G,p,s),p)
    def stop(event):sys.exit()
    stop_button.on_clicked(stop)
        
T0 = 100
T = T0
hlist = []
nt = 1_000_000
all_hlist=[]
all_t=[]
cooling_rate = 0.99995
nhist = 50
tol = 0.1
h_best=0
p_best=p.copy()
h = total_happiness(A, P, G, p, s)


#convert everything to integers NOTE that this means that all weighting MUST be integers
s = s.astype(np.int32)
p = p.astype(np.int32)
s_trial=s.copy()
p_trial=p.copy()

A_indptr = A.indptr.astype(np.int32)
A_indices = A.indices.astype(np.int32)
A_data = A.data.astype(np.int32)

P_indptr  = P.indptr.astype(np.int32)
P_indices = P.indices.astype(np.int32)
P_data    = P.data.astype(np.int32)

G_indptr  = G.indptr.astype(np.int32)
G_indices = G.indices.astype(np.int32)
G_data    = G.data.astype(np.int32)


for it in range(nt):
    # pick two random people to swap
    
    delta_h,s_trial,p_trial = sa_core.trial_move3(ntot, s,p,
                            A_indptr, A_indices, A_data,
                            P_indptr, P_indices, P_data,
                            G_indptr, G_indices, G_data)
    # delta_h,s_trial,p_trial=trial_move3(ntot,s,p,A,P,G)
    # print(delta_h,'it',it,h)
    
    # Metropolis acceptance rule
    if delta_h > 0 or np.random.rand() < np.exp(delta_h / T):
        h += delta_h
        s[:] = s_trial
        p[:] = p_trial

    # # Every 100 steps, monitor progress, and help those who are pissed off
    if it % 1000 == 0:
        score1,total1,pissed1=all_sat_with_guests(s,A,guestlist)
        outstr,npissed2,score2,total2,pissed2=all_sat_with_friends(s,A,P,guestlist)
        #  do moves of making people not mad:
        for pissed_indx in np.unique(np.concatenate([pissed1, pissed2])):
            # delta_h,s_trial,p_trial=trial_move3(ntot,s,p,A,P,G,int(pissed_indx))
            delta_h,s_trial,p_trial = sa_core.trial_move3(ntot, s,p,
                            A_indptr, A_indices, A_data,
                            P_indptr, P_indices, P_data,
                            G_indptr, G_indices, G_data,int(pissed_indx))
            if delta_h > 0 or np.random.rand() < np.exp(delta_h / T):
                h += delta_h
                s[:] = s_trial
                p[:] = p_trial
        score1,total1,pissed1=all_sat_with_guests(s,A,guestlist)
       
        print('SCORE1: {} of {}'.format(score1,total1))
        print(outstr)



        print(f'{it}/{nt}   h={h:.2f}   T={T:.3f}')
        hlist.append(h)

            # Store best configuration if new better one here

        if show:
            ax.set_title(f"Update {it+1}, happiness {h}")
            hall=all_happiness(A,P,G,p,s)
            sc.set_array(hall)  # update scatter color data
            for seat_number, t in enumerate(text_labels):
                t.set_text(p[seat_number])
            sc.set_clim(0, max(hall))       # update color scale range
            cbar.update_normal(sc)    # sync the colorbar with the new limits
            plt.draw()
            plt.pause(0.0001)

    # Check for local minimum (every 1000 steps maybe)
    if len(hlist) >= nhist and it % 1000 == 0:
        recent = np.array(hlist[-nhist:])
        mean = np.mean(recent)
        var = np.var(recent) / (mean**2 + 1e-9)
        if var < tol:
            print(f"Local minimum detected at iteration {it}. Reheating!")
            T *= 10   # reheat
            hlist = []  # reset history

    # Gradual cooling
    T *= cooling_rate

    if h>h_best:# and score1==total1:
        h_best=h
        p_best=p.copy()
        s_best=s.copy()  

    if it%100==0:
        all_hlist.append(int(h))  
        all_t.append(int(it))


## Save the results to the seating plan
p=p_best.copy()
s=s_best.copy()
import openpyxl
print(f'best happiness {h_best}')

# Point to the Excel file in the same folder
base = Path(__file__).parent # Get the path to the current script
filename = base / "Seating-plan-template.xlsx"
wb = openpyxl.load_workbook(filename)
ws = wb.active 
# Write each name into its corresponding cell
for (col, row), person_indx in zip(seat_positions, p_best):
    name=namelist[person_indx]
    # print(row,col)
    ws.cell(row=int(row), column=int(col), value=name)

# Save under a new name to keep the original template safe
wb.save(f"seating_filled.xlsx")
score1,total1,_=all_sat_with_guests(s,A,guestlist)
outstr,npissed,score2,total2,_=all_sat_with_friends(s,A,P,guestlist)
h = total_happiness(A, P, G, p, s)

data = np.array([[score1, total1,score2,total2, npissed, h,args.seed]])

# Save numeric data
np.savetxt("results.txt", data, 
           header="score1 total1 score2 total2 number_pissed_off total_hapiness seed", 
           fmt="%.4f", 
           comments="")
# save happiness graphs
data=np.array([all_t,all_hlist])
np.savetxt("h.txt", data.T, 
           header="nt h", 
           comments="")
# ## plot the h
# plt.plot(all_t,all_hlist)       
# plt.show()
# sys.exit()
if show:
    plt.ioff()  # turn off interactive mode when done
    plt.show()



