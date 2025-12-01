import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from matplotlib.widgets import Button
from MCR_Dining.getnames import AttendeeScraper
from scipy.sparse import csr_matrix
from MCR_Dining.superhall_seatingplan.hall_setup import setup_hall

def get_Matrices(event_booking_html,swaps_xlsprd,seating_form_responses):
    ### Get the names from Upay
    guestlist=AttendeeScraper(event_booking_html,swaps_xlsprd)
    guestlist.load_Upay()
    guestlist.load_Swaps()
    # guestlist.pretty_print()
    # sys.exit()


    '''
    Setup all of the Matrices needed for the Monte Carlo
    A: adjacency matrix [seats->seats]         Gives score of how good seating is. e.g. A12 = how good is it for 1 to sit with 2
    P: preference matrix [people->people]      Gives people's preference of sitting next to eachother. e.g. P23 = how person 2 rated 3
    T: transformation matrix [people->seats]   Stores the position of each person (binary choice)
    G: gallery matrix [people->seats]          Stores preferences of people to be in gallery. Also if needed can add biasing for seats to be at end of table
    '''

    ### Setup the Hall (three long tables and 2 square in the gallery)
    # table_types=['long','long','long','long','square','square']
    # table_seats=[30,30,30,30,12,12]#144-120 =24
    table_types=['long','long','long','long','long']

    table_seats=[24,36,36,36,23] #HT, T1, T2, T3, T4 
    # table_seats=[24,36,36,36,23-15] #HT, T1, T2, T3, T4 
    if np.sum(table_seats)!=len(guestlist.everyone):
        print(f'there are {np.sum(table_seats)} seats, but {len(guestlist.everyone)} people')
        sys.exit()
    # posns=np.array([[3,6],[8,6],[13,6],[18,6],[6,31],[13,31]]) #cell position of the top left person
    posns=np.array([[3,6],[8,6],[13,6],[18,6],[23,6]]) #cell position of the top left person
    A, seat_positions, gallery_seat_indices = setup_hall(table_types,posns,table_seats)

    ### Using the seating_form_responses, read off the P and G
    df = pd.read_excel(seating_form_responses, engine='openpyxl')
    P=np.zeros_like(A); G=np.zeros_like(A)
    for index, row in df.iterrows():# go through each row in the spreadsheet
        ## do the preferences for seating next to eachother
        name = row['What is your name ?']
        Qs=['Who would you like to sit next to?  First priority. You will automatically be put with your guests.',
            'Who would you like to sit next to?  Second priority.  You will automatically be put with your guests.',
            'Who would you like to sit next to?  Third priority. You will automatically be put with your guests!!',]
        name_indx=guestlist.find(name)
        if name_indx==-1:
            print(f'name {name} in superhall preference form not found')
        prefs_weights=[4,4,3] # weighting for the prefs
        for pl, Question in enumerate(Qs):
            pref = row[Question]
            if pd.isna(pref): continue # if the preference is not specified in the form continue
            # print(f'{priority_level} priority is {pref}')
            pref_indx=guestlist.find(pref) # find the index in the name list
            if pref_indx==-1:
                print(f'preference of {pref} not found in guestlist, skipping')
                continue
            P[name_indx,pref_indx]+=prefs_weights[pl] # assign the preferential weight
        ## do the preferences for sitting in the gallery
        gallery_pref = row['I would prefer to be seated in the gallery if it is to be open']
        gallery_weight=5 # weighting for sitting in gallery
        if gallery_pref=='Yes':
            G[name_indx,gallery_seat_indices]=gallery_weight
    
    ### Add preferences for sitting next to your guests
    guest_pref=4
    print(f'total number of people: {len(guestlist.everyone)}')
    for attendee in guestlist.attendees:
        attendee_indx=guestlist.find(attendee)
        if attendee_indx==-1: 
            print(f'attendee {attendee} not found')
            continue
        for guest in guestlist.attendees_guest_map[attendee]:
            guest_indx=guestlist.find(guest)
            if guest_indx==-1:
                print(f'guest {guest} not found')
                continue
            P[guest_indx,attendee_indx]+=guest_pref
            P[attendee_indx,guest_indx]+=guest_pref
     
    return csr_matrix(A),csr_matrix(P),csr_matrix(G),seat_positions,guestlist

def plot_setup(plt,seat_positions,happiness,p,mode='interactive'):
    ### Setup the plot
    if mode=='interactive':plt.ion()
    fig, ax = plt.subplots()
    ax.invert_yaxis() #for excel-like indexing
    sc = ax.scatter([x for x,y in seat_positions],[y for x,y in seat_positions],  c=happiness, cmap='RdYlGn')
    cbar=plt.colorbar(sc,label='n value')
    # Button setup
    button_ax = plt.axes([0.4, 0.05, 0.2, 0.075])  # x, y, width, height
    stop_button = Button(button_ax, 'STOP', color='lightcoral', hovercolor='red')
    text_labels = []
    for seat_number, (x, y) in enumerate(seat_positions):
        t = ax.text(x, y, p[seat_number], fontsize=9, ha='center', va='center', color='black')
        text_labels.append(t)
    return sc,cbar,ax,stop_button,text_labels

    

if __name__=='__main__':
    A,P,T,G,seat_positions = get_Matrices("/mnt/c/Users/Cole/Downloads/Upay - Event Booking.html",
        "/mnt/c/Users/Cole/Downloads/Superhall Seating Request Form (Responses).xlsx")
    ntot=A.shape[0]
    happiness=[int(i) for i in np.arange(0,ntot)]
    print(A.shape)
    print(seat_positions.shape)
    # print
    sc,ax,stop_button=plot_setup(plt,seat_positions,happiness)
    def stop(event):sys.exit()
    stop_button.on_clicked(stop)
    # Loop that updates colors every 5 seconds
    for i in range(1000):  # update 10 times
        ns = np.random.rand(ntot) * 100  # new color values
        sc.set_array(ns)  # update scatter color data
        ax.set_title(f"Update {i+1}")
        plt.draw()
        plt.pause(0.1)  # wait 5 seconds

    plt.ioff()  # turn off interactive mode when done
    plt.show()


# Setup the tables
# names 
# priority [p1,p2,p3]


# Display the first few rows
# print(df.head())
