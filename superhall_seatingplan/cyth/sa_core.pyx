# cython: language_level=3, boundscheck=False, wraparound=False
import numpy as np
cimport cython
from libc.stdlib cimport srand,rand

def seed_c_rng(int seed):
    srand(seed)

@cython.cdivision(True)



cpdef int happiness(int person_i,                 
                    int[:] s,
                 int[:] A_indptr,
                 int[:] A_indices,
                 int[:] A_data,
                 int[:] P_indptr,
                 int[:] P_indices,
                 int[:] P_data,
                 int[:] G_indptr,
                 int[:] G_indices,
                 int[:] G_data):
    """    
    1. find the persons seat number
    2. find the person index of the persons preferences
    3. find the places next to the person
    4. go through and compare the  
    """
    cdef int h = 0
    cdef int seat_i = s[person_i] # seat and person index now known
    cdef int n_friends = P_indptr[person_i+1]-P_indptr[person_i]
    cdef int n_adjacents = A_indptr[seat_i+1]-A_indptr[seat_i]
    cdef int n
    cdef int m

    cdef int friend_pref
    cdef int friend_i
    cdef int friend_seat
    cdef int adj_weight
    cdef int adj_seat


    for n in range(n_friends):

        friend_pref = P_data[P_indptr[person_i]+n]
        friend_i = P_indices[P_indptr[person_i]+n]
        friend_seat = s[friend_i]
   
        for m in range(n_adjacents):

            adj_weight = A_data[A_indptr[seat_i]+m]
            adj_seat = A_indices[A_indptr[seat_i]+m]

            if adj_seat == friend_seat:

                h+= adj_weight*friend_pref
    return h


@cython.cdivision(True)
def ij_andnearby(int person_i, int person_j,
                 int[:] s,
                 int[:] p,
                 int[:] A_indptr,
                 int[:] A_indices,
                 int[:] A_data,
                 int[:] P_indptr,
                 int[:] P_indices,
                 int[:] P_data,
                 int[:] G_indptr,
                 int[:] G_indices,
                 int[:] G_data):
    """
    Compute happiness for person_i, person_j and their neighbors.
    Everything is sparse CSR.
    """
    cdef int seat_i = s[person_i]
    cdef int seat_j = s[person_j]

    cdef int idx, person

    # store unique persons (small sets, but use Python set)
    cdef set affected = set()
    affected.add(person_i)
    affected.add(person_j)

    # Neighbors of seat_i
    for idx in range(A_indptr[seat_i], A_indptr[seat_i + 1]):
        affected.add(p[A_indices[idx]])

    # Neighbors of seat_j
    for idx in range(A_indptr[seat_j], A_indptr[seat_j + 1]):
        affected.add(p[A_indices[idx]])

    cdef int total = 0

    for person in affected:
        #add on the happiness
        total += happiness(person,s,
                 A_indptr,A_indices,A_data,
                 P_indptr,P_indices,P_data,
                 G_indptr,G_indices,G_data)

    return total


@cython.cdivision(True)
def swap_seats_inplace(int[:] s, int[:] p,
                       int person_i, int person_j):
    """
    Swap two people in-place
    """
    cdef int seat_i = s[person_i]
    cdef int seat_j = s[person_j]

    s[person_i] = seat_j
    s[person_j] = seat_i

    p[seat_i] = person_j
    p[seat_j] = person_i


cdef void fisher_yates_shuffle(int[:] arr, int n):
    """
    In-place shuffle of a Cython memoryview array using Fisher-Yates.
    arr: int[:] array to shuffle
    n: length of the array
    """
    cdef int i, j, tmp
    for i in range(n - 1, 0, -1):
        j = rand() % (i + 1)
        tmp = arr[i]
        arr[i] = arr[j]
        arr[j] = tmp


@cython.cdivision(True)
def trial_move3(int ntot,
                int[:] s,
                int[:] p,
                int[:] A_indptr,
                int[:] A_indices,
                int[:] A_data,
                int[:] P_indptr,
                int[:] P_indices,
                int[:] P_data,
                int[:] G_indptr,
                int[:] G_indices,
                int[:] G_data,
                int person_i=-1,
                int person_j=-1):
    """
    Random or guided trial move.
    Returns delta_h
    """
    import numpy.random as npr
    cdef int h0
    cdef int h1
    cdef int[:] s_trial = (<object>s).copy()
    cdef int[:] p_trial = (<object>p).copy()
    # for the finding a friend in adjacent seats bit
    cdef int n_friends
    cdef int n_adjacents
    cdef int seat_i
    cdef int n,m,l
    cdef int nearby=0
    cdef int filled=0
    cdef int all_done=0
    cdef int adj_i

    # pick the person_i (if not inputted)
    if person_i < 0:
        person_i = rand() % ntot


    # Pick person_j (if not inputted). Try to pick from friends if possible
    if person_j < 0:
        seat_i = s[person_i]
        # number of mates/adjacent seats
        n_friends = P_indptr[person_i+1]-P_indptr[person_i]
        n_adjacents = A_indptr[seat_i+1]-A_indptr[seat_i]
        # go over all friends in a random order to see who can be switched in
        friend_perm = np.arange(n_friends, dtype=np.int32)
        fisher_yates_shuffle(friend_perm, n_friends)
        for n in friend_perm:
            if all_done: break
            nearby=0
            friend_pref = P_data[P_indptr[person_i]+n]
            friend_i = P_indices[P_indptr[person_i]+n]
            friend_seat = s[friend_i]
            # check if hes nearby
            for m in range(n_adjacents):
                adj_seat = A_indices[A_indptr[seat_i]+m]
                if friend_seat == adj_seat:
                    nearby=1
                    break # no need to finish the loop as we know hes nearby
            # if hes not nearby, switch with a random person who is
            if nearby == 0:
                person_j=friend_i # set this friend as the person_j
                # now we will find a person that is adjacent, but not a friend of person_i
                # if found, we wil swap that person with person_j
                adj_perm = np.arange(n_adjacents, dtype=np.int32)
                fisher_yates_shuffle(adj_perm, n_adjacents)
                # go over all of the adjacent seats at random
                for m in adj_perm:
                    adj_seat = A_indices[A_indptr[seat_i]+m]
                    adj_i = p[adj_seat]
                    # check if the person in that seat is a friend
                    filled=0
                    for l in range(n_friends):
                        friend_i = P_indices[P_indptr[person_i]+l]
                        if friend_i==adj_i:
                            filled=1
                            break
                    if filled == 0:
                        #overrwite the ith person with the adjacent who was not mates with person_i
                        #now switching person_i and person_j guarantees a positive impact
                        person_i=adj_i
                        all_done=1
                        break
    

    # default to a random person if faiulure
    if all_done==0:
        person_j = rand() % ntot
        while person_j == person_i:
            person_j = rand() % ntot


    # Before swap
    h0 = ij_andnearby(person_i, person_j,
                      s, p,
                      A_indptr, A_indices, A_data,
                      P_indptr, P_indices, P_data,
                      G_indptr, G_indices, G_data)

    # Swap
    swap_seats_inplace(s_trial, p_trial, person_i, person_j) #this will change the data in s and p

    # After swap
    h1 = ij_andnearby(person_i, person_j,
                      s_trial, p_trial,
                      A_indptr, A_indices, A_data,
                      P_indptr, P_indices, P_data,
                      G_indptr, G_indices, G_data)

    return h1 - h0, s_trial, p_trial
