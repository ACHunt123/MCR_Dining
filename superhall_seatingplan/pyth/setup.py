import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from MCR_Dining.getnames import AttendeeScraper
from scipy.sparse import csr_matrix
from MCR_Dining.superhall_seatingplan.pyth.hall_setup import setup_hall
from MCR_Dining.superhall_seatingplan.pyth.metrics_moves import PyMetrics


class SetupMatrices:
    def  __init__(self,guestlist,verbose=0,manual_removal=0):
        # initialize the flags
        self.verbose=verbose                # flag to print out stuff
        self.manual_removal=manual_removal  # manual removal of people because they emailed with issues
        # guestlist
        self.guestlist=guestlist

    def vprint(self, string):
        if self.verbose: print(string)

    def specify_hall_params(self,table_types,table_seats,table_posns,Ntot):
        '''
        Specify the occupies tables, number of seats for each
        and position of each table

        For a full hall:
            table_types=['high','long','long','long','long']
            table_seats=[24,36,40,40,40]
            table_posns=np.array([[3,6],[8,6],[13,6],[18,6],[23,6]]) [cell position of the top left person]

        To add on the gallery, add on 
            table_types+=['square']
            table_seats+=[24]
            table_posns+=np.array([[28,6]]) [cell position of the top left person]
        '''
        # Check that the hall params are valid
        Nsts=np.sum(table_seats)
        if Ntot!=Nsts:
            raise ValueError(f"Number of people ({Ntot}) != Number of seats to allocate ({Nsts})")

        self.table_types=table_types
        self.table_seats=table_seats
        self.table_posns=table_posns
        return

    def read_form_responses(self,seating_form_responses,gallery_seat_indices,A):
  ### Using the seating_form_responses, read off the P and G
        # Below are the questions on the google form, and the weightings we give to each
        name_Q='What is your name ?'
        gallery_Q='I would prefer to be seated in the gallery if it is to be open'
        gallery_weight=5 # weighting for sitting in gallery
        prefs_Qs=['Who would you like to sit next to?  First priority. You will automatically be put with your guests.',
            'Who would you like to sit next to?  Second priority.  You will automatically be put with your guests.',
            'Who would you like to sit next to?  Third priority. You will automatically be put with your guests!!',
            'Who would you not like to sit next to?',]
        prefs_weights=[4,4,3,-20]
        guest_pref=6 # weighting for sitting next to guests
        ###
        self.vprint('\n Preferences from google form:\n')
        df = pd.read_excel(seating_form_responses, engine='openpyxl')
        P=np.zeros_like(A); G=np.zeros_like(A)
        for index, row in df.iterrows():# go through each row in the spreadsheet
            ## do the preferences for seating next to eachother
            name = row[name_Q]
            self.vprint(name)
            name_indx=self.guestlist.find(name)
            if np.isnan(name_indx):
                print(f'name {name} in superhall preference form not found')
                continue
            ## do each person's preference of sitting next to someone (or not...)
            for pl, Question in enumerate(prefs_Qs):
                pref = row[Question]
                verbose_label=['pref. 1','pref. 2','pref. 3','avoids']
                self.vprint(f'__ {verbose_label[pl]}: {pref}')
                if pd.isna(pref): continue # if the preference is not specified in the form continue
                pref_indx=self.guestlist.find(pref) # find the index in the name list
                if np.isnan(pref_indx):
                    print(f'preference of {pref} by {name} not found in guestlist, skipping')
                    continue
                P[name_indx,pref_indx]+=prefs_weights[pl] # assign the preferential weight
            ## do the preferences for sitting in the gallery
            gallery_pref = row[gallery_Q]
            if gallery_pref=='Yes':
                G[name_indx,gallery_seat_indices]=gallery_weight
        
        ### Add preferences for sitting next to your guests
        print(f'total number of people: {len(self.guestlist.everyone)}')
        for attendee in self.guestlist.attendees:
            attendee_indx=self.guestlist.find(attendee)
            if np.isnan(attendee_indx): 
                print(f'attendee {attendee} not found')
                continue
            for guest in self.guestlist.attendees_guest_map[attendee]:
                guest_indx=self.guestlist.find(guest)
                if np.isnan(guest_indx):
                    print(f'guest {guest} not found')
                    continue
                P[guest_indx,attendee_indx]+=guest_pref
                P[attendee_indx,guest_indx]+=guest_pref

        
        if(self.manual_removal):## add in the manual fixes to the preferences
            from MCR_Dining.xmas_superhall_fixes import extra_preferences
            extra_preferences(P,self.guestlist)

        return P, G


    def get_Matrices(self,seating_form_responses):
        '''
        Setup all of the Matrices needed for the Monte Carlo
        A: adjacency matrix [seats->seats]         Gives score of how good seating is. e.g. A12 = how good is it for 1 to sit with 2
        P: preference matrix [people->people]      Gives people's preference of sitting next to eachother. e.g. P23 = how person 2 rated 3
        T: transformation matrix [people->seats]   Stores the position of each person (binary choice)
        G: gallery matrix [people->seats]          Stores preferences of people to be in gallery. Also if needed can add biasing for seats to be at end of table
        '''

        ### Setup the Hall
        A, seat_positions, gallery_seat_indices = setup_hall(self.table_types,self.table_posns,self.table_seats)

        P, G = self.read_form_responses(seating_form_responses,gallery_seat_indices,A)

        # convert to CSR format
        A=csr_matrix(A)
        P=csr_matrix(P)
        G=csr_matrix(G)
        # setup the cython array object
        def csr_to_int32(M): return M.indptr.astype(np.int32),M.indices.astype(np.int32),M.data.astype(np.int32)
        A_indptr, A_indices, A_data = csr_to_int32(A)
        P_indptr, P_indices, P_data = csr_to_int32(P)
        G_indptr, G_indices, G_data = csr_to_int32(G)
        cyth_arrays=[self.guestlist.Ntot,A_indptr, A_indices, A_data,P_indptr, P_indices, P_data, G_indptr, G_indices, G_data]
        
        # build the python metrics object
        pym=PyMetrics(A,P,G,self.guestlist)
        return pym,seat_positions,cyth_arrays

    
    

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
