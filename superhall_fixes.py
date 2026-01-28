'''
An example for the corrections one can make to the Guestlist

I put in silly names for GDPR reasons

to activate, in generate_seatingplan.py,
set manual_removal=1

And of course put the correct names into the functions
'''
import numpy as np

def remove_extras_from_algo(self):
    ### remove people and their guests from the set of people to propogate
    if self.verbose: input('removing extra guests accidentally given (thanks Upay)')
    self.removed_swaps=[]
    self.removed_swaps.extend(self.attendees_guest_map['Harry Huckleberry'][1:])
    self.attendees_guest_map['Harry Huckleberry']=[self.attendees_guest_map['Harry Huckleberry'][0]]
    # print(self.attendees_guest_map['Harry Huckleberry'])
    # print(self.removed_swaps)

    ### remove Ben's mates and their guests
    if self.verbose: input('removing Bens mates')
    self.ben_group=[]
    bens_mates = ["Lemon Lime",
            "Tom Tomato",
            "Rose Raspberry",
            "Mike Mango",
            "Alice Apple",
            "Kevin Kiwi",
            "Charlie Cherry",
            "Holly Honeydew", #added from prefs (down from here)
            "Melon Jane"]
    self.remove_people_n_their_guests(bens_mates,self.ben_group)

    ### get the number of removed people
    self.n_removed=len(self.ben_group)+len(self.removed_swaps)


def move_guests_to_correct_hosts(self):
    ### move guests of someone to someone else
    if self.verbose: input('moving guests to Peter')
    self.swap_over_guests("Peter Pineapple","Jack Jackfruit")
    if self.verbose: input('moving guests to Christina')
    self.swap_over_guests("Christina Clementine","Leon Lemon")
    self.swap_over_guests("Christina Clementine","Vanessa Vanilla")


def extra_preferences(P,guestlist):
    ### Add extra preferences to the one shown in the form 
    if guestlist.verbose: input('removing Caroline problems')
    P[guestlist.find('Jenny Juniper'),guestlist.find('Caroline Clementine')]=-10 # Jenny really doesn't like Caroline
    for guest in guestlist.attendees_guest_map['Caroline Clementine']:
        guest_indx=guestlist.find(guest)
        if np.isnan(guest_indx):
            print('not found eep')
        P[guestlist.find('Jenny Juniper'),guest_indx]=-10
    if guestlist.verbose: input('fixing kumquats')
    P[guestlist.find('Kevin Kumquat'),guestlist.find('James Jujube')]=5
    # no need to return P as it is mutable (passed only by reference)