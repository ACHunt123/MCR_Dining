import numpy as np
import sys
from scipy.linalg import block_diag

def setup_hall(table_types,posns,table_seats):
    '''
    Setup a model of the Hall+Gallery, provided the table_types, positions and number of seats
    There are two types of tables, some long, and some square (in gallery)
    We assume that separate tables have no adjacent seats. This makes the problem block-diagonal (YAY)
    We number the tables from top left (north is high-table) anticlockwise, starting from left most table. First hall, then gallery
    '''
    def A_blk(table_type,nsts,posn=np.array([0,0])):
        seat_positions=np.zeros((nsts,2))
        A_block=np.zeros((nsts,nsts))
        if table_type in ['long','high']:
            ''' Assigns the adjacency matrix for a long table. Works for odd number of people too (as the indexing is bi-directional)
            4   3
            | /       |  
            X - 5   table
            | \       V  
            4   3
            If high table, we add an extra seat at the head and foot of the table
            '''
            ### weights
            w_opposite=5
            w_adjacent=4
            w_diagonal=3
            if table_type=='high': extra_len=1
            if table_type=='long': extra_len=0
            l_indices=np.arange(extra_len,nsts//2)
            r_indices=np.arange(nsts//2,nsts-extra_len)
            # do the head of the table (if high table)
            if table_type=='high':
                seat_positions[0,:] = posn + np.array([1,0])
                A_block[0,r_indices[0]]=A_block[r_indices[0],0]=w_opposite
                A_block[0,l_indices[0]]=A_block[l_indices[0],0]=w_opposite
            for i, (l_indx,r_indx) in enumerate(zip(l_indices,r_indices)):
                i+=extra_len
                ### assign the seat positions
                seat_positions[l_indx,:] = posn + i*np.array([0,1])
                seat_positions[r_indx,:] = posn + np.array([2,0])+ i*np.array([0,1])
                # across from eachother
                A_block[l_indx,r_indx]=A_block[r_indx,l_indx]=w_opposite 
                # next to eachother and diagonals
                if l_indx+1 in l_indices:
                    A_block[l_indx,l_indx+1]=A_block[l_indx+1,l_indx]=w_adjacent
                    A_block[r_indx,l_indx+1]=A_block[l_indx+1,r_indx]=w_diagonal 
                if r_indx+1 in r_indices:
                    A_block[r_indx,r_indx+1]=A_block[r_indx+1,r_indx]=w_adjacent
                    A_block[l_indx,r_indx+1]=A_block[r_indx+1,l_indx]=w_diagonal
                if l_indx-1 in l_indices:
                    A_block[l_indx,l_indx-1]=A_block[l_indx-1,l_indx]=w_adjacent
                    A_block[r_indx,l_indx-1]=A_block[l_indx-1,r_indx]=w_diagonal
                if r_indx-1 in r_indices:
                    A_block[r_indx,r_indx-1]=A_block[r_indx-1,r_indx]=w_adjacent
                    A_block[l_indx,r_indx-1]=A_block[r_indx-1,l_indx]=w_diagonal
            ### add on the last position if the number of seats is odd (deosnt work for high table)
            if len(r_indices)!=len(l_indices):
                if table_type=='high': sys.exit('high table must have an even number of people')
                seat_positions[r_indices[-1],:] = posn + np.array([2,0])+ (i+1)*np.array([0,1])
            # do the end of the table (if high)
            if table_type=='high':
                seat_positions[-1,:] = posn + np.array([1,0])+ (i+1)*np.array([0,1])
                A_block[-1,r_indices[-1]]=A_block[r_indices[-1],-1]=w_opposite
                A_block[-1,l_indices[-1]]=A_block[l_indices[-1],-1]=w_opposite
            return A_block,seat_positions
        elif table_type=='square':
            ''' Assigns the adjacency matrix for a long table. Currently assumes 4n people'''
            assert (nsts)%4==0,'number of seats on table must be 4n'
            n1side=(nsts)/4
            directions=np.array([[0,1],[1,0],[0,-1],[-1,0]])

            indices=np.arange(0,nsts)
            seat_position=posn.copy()
            for indx in indices:
                if indx%n1side==0:                
                    seat_position+=directions[int(indx//n1side),:]

                ### seat position
                seat_positions[indx,:] = seat_position
                seat_position+=directions[int(indx//n1side),:]
                ### weights
                w_adjacent1=5
                w_adjacent2=1

                # directly next to eachother 
                A_block[indx,(indx+1)%nsts]=A_block[(indx+1)%nsts,indx]=w_adjacent1
                # two away
                A_block[indx,(indx+2)%nsts]=A_block[(indx+2)%nsts,indx]=w_adjacent2
        return A_block, seat_positions
    ### Put the seat positions and Adjacency matrices together    
    A=None
    seat_positions=None
    gallery_seat_indices=None
    i0=0
    for table_type,posn,seats in zip(table_types,posns,table_seats):
        A_i,seat_positions_i=A_blk(table_type,seats,posn=posn)
        seat_positions=np.concatenate([seat_positions,seat_positions_i]) if seat_positions is not None else seat_positions_i
        if table_type=='square': # get the indices of the gallery seats
            gallery_seat_indices=np.concatenate([gallery_seat_indices,np.arange(i0,i0+seats)]) if gallery_seat_indices is not None else np.arange(i0,i0+seats)
        else:
            gallery_seat_indices=np.concatenate([gallery_seat_indices,np.arange(i0,i0+seats)*0]) if gallery_seat_indices is not None else np.arange(i0,i0+seats)*0
        i0+=seats
        A=block_diag(A,A_i) if A is not None else A_i
    gallery_seat_indices = gallery_seat_indices.astype(int)
    return A,seat_positions,gallery_seat_indices