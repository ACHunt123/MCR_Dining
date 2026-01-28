from bs4 import BeautifulSoup
import sys
import pandas as pd
import numpy as np


class AttendeeScraper:
    def __init__(self, verbose=0, manual_removal=0):
        self.manual_removal=manual_removal
        self.verbose=verbose
        # initialize the arrays
        self.attendees_guest_map={} #dict of attendes (people who can bring guests) with their guests listed
        self.attendees=[]         # list of attendees (people who can bring guests)
        self.everyone=[]          # everyone (that will be swaped around in the seating plan)
        self.others=[]            # other people (swap guests that are not willing to be mixed)

    def swap_over_guests(self,recipient,donor):
            '''swap the guests of onre person to another (all of them)'''
            self.attendees_guest_map[recipient].extend(self.attendees_guest_map[donor])
            self.attendees_guest_map[donor]=[]

    def remove_people_n_their_guests(self,namelist,removedlist):
        '''remove a set of people from the list (and also their guests)'''
        for name in namelist:
            if name in self.attendees_guest_map:
                if self.verbose: print(f'{name}')
                removedlist.append(name)
                removedlist.extend(self.attendees_guest_map[name])
                if self.verbose and self.attendees_guest_map[name]!=[] : print(f'__{self.attendees_guest_map[name]}')
                del self.attendees_guest_map[name]
            else:
                print(f'warning {name} not found')

    def load_Upay(self,Upay_filepath):
        ''' Scrape the attendees and guests from Upay html
            Each booking_group is in "class_='booking-group'"
            In each one, the attendee has format "font-weight:500" and the guests of each one has "text-indent: 10px".
        '''
        #Open the html with soup
        with open(Upay_filepath, 'r', encoding='utf-8') as f:
            html = f.read()
        self.soup = BeautifulSoup(html, 'html.parser')
        #find each group of attenge and their guests
        booking_groups = self.soup.find_all('div', class_='booking-group')
        for group in booking_groups:
            attendees = group.find_all("p", style=lambda value: value and "font-weight:500" in value)
            guests_of_atendee = group.find_all("p", style=lambda value: value and "text-indent: 10px" in value)
            if len(attendees)>1:
                print('warning: unexpected formatting')
            for attendee in attendees:
                attendee_name = attendee.get_text(strip=True).replace("(Caian ticket - Drinking)", "")
                ## add the attendee to the dict
                self.attendees_guest_map[attendee_name]=[]
            n=1
            for guest in guests_of_atendee:
                ## add the guests to the dictionary
                guest_name = guest.get_text(strip=True).replace("(Caian ticket - Drinking)", "")
                if guest_name != 'Guest':
                    self.attendees_guest_map[attendee_name].append(guest_name)
                else: # If name not given default "to Guest of ..."
                    self.attendees_guest_map[attendee_name].append(f'Guest of {attendee_name} ({n})')
                    # self.attendees_guest_map[attendee_name].append(f'Guest of {attendee_name}')
                    n+=1
        
        self.n_removed=0
        if(self.manual_removal): # manual removal of people from calculation because they are difficult
            from MCR_Dining.xmas_superhall_fixes import remove_extras_from_algo,move_guests_to_correct_hosts
            remove_extras_from_algo(self)
            move_guests_to_correct_hosts(self)

        # self.attendees.extend(list(set(self.attendees_guest_map.keys()))) #list of the people that have booked (not including peoples guests)
        self.attendees.extend(self.attendees_guest_map.keys()) #list of the people that have booked (not including peoples guests)
        ### add to everyone (this is the master list)
        for attendee, guests in self.attendees_guest_map.items():
            self.everyone.append(attendee)
            self.everyone.extend(guests)
        self.everyone=sorted(list(set(self.everyone))) #list(set( )) removes duplicates
        self.Ntot=len(self.everyone)
        return
    
    def load_Swaps(self,swap_filepath):
        ''' Load the swap people THAT WANT TO BE PUT IN SEATING PLAN 
        This is of course not used anymore because of RK's little tantrum'''
        included_colleges=['St Catz','Wolfson','Clare Hall']
        # included_colleges=['St Catz','Wolfson']
        df = pd.read_excel(swap_filepath, engine='openpyxl')
        for index, row in df.iterrows():# go through each row in the spreadsheet
            name = row['Name']
            college = row['College']
            if college in included_colleges:
                if name in self.everyone: #NOTE this is to set duplicates to be guests of eachother (Antonia N on swaps sheet...)
                    self.everyone.append(f'Guest of {name}')
                    self.attendees_guest_map[name]=[f'Guest of {name}']
                else:
                    self.everyone.append(name)
                    self.attendees.append(name)
                    self.attendees_guest_map[name]=[]
            else:
                self.others.append(name)
        return

    def pretty_print(self,print_guests=True):
        ''' print out the attendees and guests'''
        if self.attendees is None: 
            sys.exit('need to get the data first silly')
        for attendee in self.attendees:
            print(attendee)
            for guest in self.attendees_guest_map[attendee]:
                if print_guests: 
                    print(f'__{guest} (guest of {attendee})')

    def find(self,name):
        ''' find the index of the name in the everyone master name-list'''
        index_list=[]
        for indx,person in enumerate(self.everyone):
            if name==person: index_list.append(indx)
        if len(index_list)==0: # noone found
            #sys.exit(f'guest not found in everyone list.\n their name is {name}')
            return np.nan #guest not found
        elif len(index_list)>1:
            sys.exit(f'duplicates found of {name}')
        return index_list[0]


if __name__=='__main__':
    folder='/home/ach221/Desktop'
    event_booking_html = f"{folder}/Upay - Event Booking.html"

        ### Get the names from Upay
    guestlist=AttendeeScraper(event_booking_html)
    guestlist.load_Upay()
    # guestlist.load_Swaps()
    guestlist.pretty_print(print_guests=False)