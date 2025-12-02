import numpy as np
import sys

''' All of the functions to measure happiness etc'''

def happiness(person_indx,A,P,G,s):
    """    
    1. find the persons seat number
    2. find the person index of the persons preferences
    3. find the places next to the person
    4. go through and compare the  
    """
    h = 0.0
    seat_number = s[person_indx]

    friends = P.getrow(person_indx)      # preferences for other people
    adjacents = A.getrow(seat_number)    # adjacency for this person's seat

    # Iterate through friends and adjacent seats
    for friend_pref, friend_seat in zip(friends.data, s[friends.indices]):
        for adj_weight, adj_seat in zip(adjacents.data, adjacents.indices):
            if friend_seat == adj_seat:
                h += friend_pref * adj_weight
    # Add the Gallery contribution
    h += G[person_indx,seat_number]

    return h

def ij_andnearby(person_i,person_j,A,P,G,s,p):
    """Happiness of person_i, person_j, and all their adjacent neighbors (no double counting)."""
    seat_i, seat_j = s[person_i], s[person_j]
    adj_i, adj_j = A.getrow(seat_i), A.getrow(seat_j)
    # Map seats to people sitting there, np.unique removes double counting
    affected_people = np.unique(np.concatenate([[person_i, person_j], p[adj_i.indices],p[adj_j.indices]]))
    # Sum happiness for all affected people
    total = sum(happiness(person, A, P, G, s) for person in affected_people)
    return total

def trial_move(ntot,s,p,A,P,G,h):
    i, j = np.random.choice(ntot, size=2, replace=False)
    s_trial, p_trial = swap_seats(i, j, s.copy(), p.copy())
    h_trial = total_happiness(A, P, G, p_trial, s_trial)
    return h_trial - h,h_trial,s_trial,p_trial

def trial_move2(ntot,s,p,A,P,G):
    ''' Picks two random people and swaps'''
    i, j = np.random.choice(ntot, size=2, replace=False)
    h0 =ij_andnearby(i,j,A,P,G,s,p)
    s_trial, p_trial = swap_seats(i, j, s.copy(), p.copy())
    h1 =ij_andnearby(i,j,A,P,G,s_trial,p_trial) 

    return h1-h0,s_trial,p_trial

def trial_move3(ntot,s,p,A,P,G,person_i=None):
    ''' Gets a random (or specified) person. 
        Sees if they have any preferences not sat with them
        If so, swaps that friend with a random adjacent seat of theirs
        If not, revery to trial move2
    '''
    if person_i is None: person_i = np.random.randint(ntot)
    seat_i = s[person_i]

    friends = P.getrow(person_i)      # preferences for other people
    adjacents = A.getrow(seat_i)    # adjacency for this person's seat

   # Vectorized: get friend seats and adjacent seats
    friend_seats = s[friends.indices]
    adjacent_seats = adjacents.indices

    # Use NumPy set operations (implemented in C — very fast)
    friends_not_nearby = friends.indices[~np.isin(friend_seats, adjacent_seats)]
    adjacent_seats_not_used = adjacent_seats[~np.isin(adjacent_seats, friend_seats)]

    if len(friends_not_nearby)>0:
        i = np.random.choice(friends_not_nearby)
        if len(adjacent_seats_not_used)>0:
            seat_j = np.random.choice(adjacent_seats_not_used)
        else:
            seat_j = np.random.choice(adjacent_seats)
        j=p[seat_j]
    else:
        i, j = np.random.choice(ntot, size=2, replace=False)

    h0 =ij_andnearby(i,j,A,P,G,s,p)
    s_trial, p_trial = swap_seats(i, j, s.copy(), p.copy())
    h1 =ij_andnearby(i,j,A,P,G,s_trial,p_trial) 

    return h1-h0,s_trial,p_trial


def all_happiness(A,P,G,p,s):
    return np.array([happiness(p_indx,A,P,G,s) for p_indx in p])

def total_happiness(A,P,G,p,s):
    return np.sum(all_happiness(A,P,G,p,s))

def swap_seats(person_i,person_j,s,p):
    ''' Swap person index i and person index j in both the maps'''
    # Update the seat of person_i and person_j
    s[person_i],s[person_j]=s[person_j],s[person_i]
    # Update the invesr map accordingly
    p[s[person_i]],p[s[person_j]]=person_i,person_j
    return s,p

def sat_with_friends(s,A,P,attendee,guestlist):
    ''' Check that the selected person is sat with all of their friends (high priorities)'''
    person_i=guestlist.find(attendee)
    person_seat = s[person_i]
    adjacents = A.getrow(person_seat)    # adjacency for this person's seat

    count=0
    total=0
    friends = P.getrow(person_i)      # preferences for other people (value is how much, index is the friend index)
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


def sat_with_guests(s,A,attendee,guestlist):
    ''' Check that the selected person is sat with all of their guests'''
    person_i=guestlist.find(attendee)
    seat_number = s[person_i]
    name=guestlist.everyone[person_i]

    adjacents = A.getrow(seat_number)    # adjacency for this person's seat
    count=0
    total=0
    pissed=[]
    nguests=len(guestlist.attendees_guest_map[name])
    if nguests>3:
        threshold=2 #all of the adjacent seats (including diagonals)
    else:
        threshold=4 #only the opposite and next to seats

    for guest in guestlist.attendees_guest_map[name]:
        total+=1
        guest_indx=guestlist.find(guest)
        guest_location=s[guest_indx]
        for adj_indx in adjacents.indices[adjacents.data>=threshold]: #make sure they are either next to eachother or diagonal
            if guest_location == adj_indx:
                count+=1
                break
    if count!=total:
        pissed=[person_i]
    return count, total, pissed

def all_sat_with_guests(s,A,guestlist):
    score=0;total=0; pissed=[]
    for attendee in guestlist.attendees: 
        si, ti, pi = sat_with_guests(s,A,attendee,guestlist)
        score+=si ; total+= ti; pissed.extend(pi)
    return score,total, pissed

def all_sat_with_friends(s,A,P,guestlist):
    score=0;total=0;pissed=[]
    for attendee in guestlist.attendees: 
        si, ti, pi = sat_with_friends(s,A,P,attendee,guestlist)
        score+=si ; total+= ti; pissed.extend(pi)
    outstr=f'SCORE2: {score} of {total}. People pissed:\n'
    for pi in pissed:
        outstr+= f'___ {guestlist.everyone[pi]}\n'
    return outstr,len(pissed),score,total,pissed

