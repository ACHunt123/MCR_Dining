import numpy as np
import sys

''' All of the functions to measure happiness etc'''
class PyMetrics():
    def __init__(self,A,P,G,guestlist):
        self.A=A
        self.P=P
        self.G=G
        self.guestlist=guestlist
        
    def happiness(self,person_indx,s):
        """    
        1. find the persons seat number
        2. find the person index of the persons preferences
        3. find the places next to the person
        4. go through and compare the  
        """
        h = 0.0
        seat_number = s[person_indx]

        friends = self.P.getrow(person_indx)      # preferences for other people
        adjacents = self.A.getrow(seat_number)    # adjacency for this person's seat

        # Iterate through friends and adjacent seats
        for friend_pref, friend_seat in zip(friends.data, s[friends.indices]):
            for adj_weight, adj_seat in zip(adjacents.data, adjacents.indices):
                if friend_seat == adj_seat:
                    h += friend_pref * adj_weight
        # Add the Gallery contribution
        h += self.G[person_indx,seat_number]
        return h

    def all_happiness(self,p,s):
        return np.array([self.happiness(p_indx,s) for p_indx in p])

    def total_happiness(self,p,s):
        return np.sum(self.all_happiness(p,s))


    def sat_with_friends(self,s,attendee):
        ''' Check that the selected person is sat with all of their friends (high priorities)'''
        person_i=self.guestlist.find(attendee)
        person_seat = s[person_i]
        adjacents = self.A.getrow(person_seat)    # adjacency for this person's seat
        count=0;total=0; pissed=[]
        friends = self.P.getrow(person_i)      # preferences for other people (value is how much, index is the friend index)
        for friend_pref, friend_seat in zip(friends.data, s[friends.indices]):
            if friend_pref<0: continue #skip those who dont wanna be with eachother 
            total+=1
            for adj_seat in adjacents.indices:
                if friend_seat == adj_seat:
                    count+=1
                    break
        if (count==0) and (len(friends.indices)!=0):  
            pissed=[person_i]
        return count, total, pissed


    def sat_with_guests(self,s,attendee):
        ''' Check that the selected person is sat with all of their guests'''
        person_i=self.guestlist.find(attendee)
        seat_number = s[person_i]
        name=self.guestlist.everyone[person_i]

        adjacents = self.A.getrow(seat_number)    # adjacency for this person's seat
        count=0;total=0; pissed=[]
        nguests=len(self.guestlist.attendees_guest_map[name])
        if nguests>3:
            threshold=2 #all of the adjacent seats (including diagonals)
        else:
            threshold=4 #only the opposite and next to seats

        for guest in self.guestlist.attendees_guest_map[name]:
            total+=1
            guest_indx=self.guestlist.find(guest)
            guest_location=s[guest_indx]
            for adj_indx in adjacents.indices[adjacents.data>=threshold]: #make sure they are either next to eachother or diagonal
                if guest_location == adj_indx:
                    count+=1
                    break
        if count!=total:
            pissed=[person_i]
        return count, total, pissed

    def all_sat_with_guests(self,s):
        score=0;total=0; pissed=[]
        for attendee in self.guestlist.attendees: 
            si, ti, pi = self.sat_with_guests(s,attendee)
            score+=si ; total+= ti; pissed.extend(pi)
        return score,total, pissed

    def all_sat_with_friends(self,s):
        score=0;total=0;pissed=[]
        for attendee in self.guestlist.attendees: 
            si, ti, pi = self.sat_with_friends(s,attendee)
            score+=si ; total+= ti; pissed.extend(pi)
        outstr=f'SCORE2: {score} of {total}. People pissed:\n'
        for pi in pissed:
            outstr+= f'___ {self.guestlist.everyone[pi]}\n'
        return outstr,len(pissed),score,total,pissed

