# cython: language_level=3, boundscheck=False, wraparound=False
import numpy as np
cimport cython

@cython.cdivision(True)



cdef int happiness(int person_i,                 
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
                int person_i=-1):
    """
    Random or guided trial move.
    Returns delta_h
    """
    cdef int person_j
    cdef int h0, h1
    import numpy.random as npr

    if person_i < 0:
        person_i = npr.randint(0, ntot)

    # Pick person_j != person_i
    person_j = npr.randint(0, ntot)
    while person_j == person_i:
        person_j = npr.randint(0, ntot)


    # Before swap
    h0 = ij_andnearby(person_i, person_j,
                      s, p,
                      A_indptr, A_indices, A_data,
                      P_indptr, P_indices, P_data,
                      G_indptr, G_indices, G_data)

    # Swap
    swap_seats_inplace(s, p, person_i, person_j) #this will change the data in s and p
    # has been checked to change s

    # After swap
    h1 = ij_andnearby(person_i, person_j,
                      s, p,
                      A_indptr, A_indices, A_data,
                      P_indptr, P_indices, P_data,
                      G_indptr, G_indices, G_data)


    return h1 - h0
