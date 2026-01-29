import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys,random,argparse
from MCR_Dining.superhall_seatingplan.pyth.setup import SetupMatrices
from MCR_Dining.getnames import AttendeeScraper
from MCR_Dining.superhall_seatingplan.pyth.utils import fill_spreadsheet, plot_setup
# Import the super fast cython stuff
from MCR_Dining.superhall_seatingplan.cyth import sa_core
"""
============================================================
                 SEATING PLAN ALGORITHM
============================================================
Author: A. C. Hunt

Description:
------------
This module implements a seating plan optimization algorithm
using a combination of Python and Cython for performance. The
algorithm handles guest assignment, special constraints, and
preference scoring to generate reproducible, optimized seating
arrangements. It uses simulated annealing. 
"""

### Inputs
manual_removal=0        # Switch to do the manual removal of guests etc. described in xmas_superhall_fixes
verbose=1               # Switch to make the outputs more verbose
show=0                  # Do an interactive plot showing the movement of seats
save_to_spreadsheet=1   # Save the results to a spreadsheet

### File locations
folder='/home/ach221/Desktop'
event_booking_html = f"{folder}/Upay - Event Booking.html"
seating_form_responses = f"{folder}/Superhall_Seating_Request_Jan31_newest2"
swaps_xls = f"{folder}/MTSuperhallSwaps2025-26.xlsx"
# NOTE the output will automatically be put in the same directory as where the file is being run

### Parameters   
T0 = 150
nt = 1_500_000
cooling_rate = 0.99995
nhist = 50
tol = 0.1

### Set the seed with argparse
parser = argparse.ArgumentParser(description="Run seating / bath simulation with optional seed")
parser.add_argument("--seed", type=int, default=0, help="Random seed")
args = parser.parse_args()
np.random.seed(args.seed)
random.seed(args.seed)
sa_core.seed_c_rng(args.seed)
if verbose: print(f'using seed {args.seed}')

### Get the names from Upay and seating form responses to generate the Matrices required
guestlist=AttendeeScraper(verbose,manual_removal)
guestlist.load_Upay(event_booking_html)
# guestlist.load_Swaps(swaps_xls)
if verbose: print('\n Full Guestlist\n');guestlist.pretty_print(print_guests=True)
print(guestlist.Ntot)
exit()
### Get the Matrices for the propagation
MatMaker = SetupMatrices(guestlist,verbose,manual_removal)
## Specify the tables, their number of seats, and locations
if(0): # the whole hall
    table_types=['high','long','long','long','long']
    table_seats=[24,36,40,40,40]
    table_posns=np.array([[3,6],[8,6],[13,6],[18,6],[23,6]]) #x,-y [coordinate of top left seat]
else:
    table_types=['long','long','long']
    table_seats=[25,26,26]
    table_posns=np.array([[8,6],[13,6],[18,6]])
MatMaker.specify_hall_params(table_types,table_seats,table_posns,guestlist.Ntot)
## Get the matrices and metrics object
pym,seat_positions,cyth_arrays = MatMaker.get_Matrices(seating_form_responses)


### Randomize initial confign
s = np.random.permutation(guestlist.Ntot).astype(np.int32)
p = np.empty_like(s,dtype=np.int32)
p[s] = np.arange(guestlist.Ntot,dtype=np.int32)

### Setup the plot
if show:
    plt.ion()
    sc,cbar,ax,stop_button,text_labels=plot_setup(plt,seat_positions,pym.all_happiness(p,s),p)
    def stop(event):sys.exit()
    stop_button.on_clicked(stop)

### Initialize arrays and counters
h = pym.total_happiness(p, s)
valid_found=0
T = T0  # set current temperature
hlist = []
all_hlist=[]
all_t=[]
h_best=0
p_best=p.copy()
for it in range(nt):
    # monte carlo move
    delta_h,s_trial,p_trial,_ = sa_core.trial_move3(s,p,*cyth_arrays)

    # Metropolis acceptance rule
    if delta_h > 0 or np.random.rand() < np.exp(delta_h / T):
        h += delta_h
        s[:] = s_trial
        p[:] = p_trial

    # help those who are pissed off once the time is late VERY AGGRESSIVE BIAS (+100)
    if it % 1000 == 0:
        # get the annoyed people
        outstr,npissed2,score2,total2,pissed2=pym.all_sat_with_friends(s)
        score1,total1,pissed1=pym.all_sat_with_guests(s)
        all_pissed=np.unique(np.concatenate([pissed1, pissed2]))
        # Output the situation
        print('SCORE1: {} of {}'.format(score1,total1))
        print(outstr)
        print(f'{it}/{nt}   h={h:.2f}   T={T:.3f}')
        # If noones mad, this is a valid solution
        if len(all_pissed) == 0:
            if h>h_best:
                h_best=h
                valid_found=1
                p_best=p.copy()
                s_best=s.copy() 
        #  Do forced moves of making the pissed people not mad:
        for pissed_indx in all_pissed:
            delta_h,s_trial,p_trial,bias = sa_core.trial_move3( s,p,*cyth_arrays, int(pissed_indx))
            if delta_h+bias > 0 or np.random.rand() < np.exp((delta_h+bias) / T):
                h += delta_h
                s[:] = s_trial
                p[:] = p_trial
        hlist.append(h)

        if show:
            ax.set_title(f"Update {it+1}, happiness {h}")
            hall=pym.all_happiness(p,s)
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
 
    # Append the h and the time to a list so we can plot later
    if it%(nt/1000)==0:
        all_hlist.append(int(h))  
        all_t.append(int(it))

# if we didnt find possible solutions, just use the lst one (we could just exit instead though to save memory)
if not valid_found:
    h_best=h
    p_best=p.copy()
    s_best=s.copy() 

## Save the results to the seating plan
p=p_best.copy()
s=s_best.copy()

print(f'best happiness {h_best}')


### Save the statistics for the fit 
loc=Path(__file__).parent # Get the path to the current script
template=f"{loc}/superhall_seatingplan/Seating-plan-template.xlsx"
fill_spreadsheet(template,seat_positions, p_best, guestlist)

score1,total1,_=pym.all_sat_with_guests(s)
outstr,npissed,score2,total2,_=pym.all_sat_with_friends(s)
h = pym.total_happiness(p, s)
data = np.array([[score1, total1,score2,total2, npissed, h,args.seed]])
np.savetxt("results.txt", data, 
           header="# score1 total1 score2 total2 number_pissed_off total_hapiness seed", 
           fmt="%.4f", 
           comments="")

### save happiness graphs
data=np.array([all_t,all_hlist])
# np.savetxt("h.txt", data.T,header="nt h", comments="")
### plot the h
plt.xlabel('t')
plt.ylabel('happiness')
plt.plot(all_t,all_hlist)    
plt.title(f'Simulated annealing of seating-plan seed {args.seed}')   
plt.savefig('h_plot.pdf')
# sys.exit()
if show:
    plt.ioff()  # turn off interactive mode when done
    plt.show()



