# =============================================================================
# Utility Functions for Use in pyGeo
# =============================================================================

import numpy as np
import sys, os
from mdo_import_helper import mpiPrint, MPI, import_modules

# --------------------------------------------------------------
#                Rotation Functions
# --------------------------------------------------------------

def rotxM(theta):
    '''Return x rotation matrix'''
    theta = theta*np.pi/180
    M = [[1, 0, 0], [0, np.cos(theta), -np.sin(theta)], \
             [0, np.sin(theta), np.cos(theta)]]
    return M

def rotyM(theta):
    ''' Return y rotation matrix'''
    theta = theta*np.pi/180
    M = [[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], \
             [-np.sin(theta), 0, np.cos(theta)]]
    return M

def rotzM(theta):
    ''' Return z rotation matrix'''
    theta = theta*np.pi/180
    M = [[np.cos(theta), -np.sin(theta), 0], \
             [np.sin(theta), np.cos(theta), 0],[0, 0, 1]]
    return M

def rotxV(x, theta):
    ''' Rotate a coordinate in the local x frame'''
    M = [[1, 0, 0], [0, np.cos(theta), -np.sin(theta)], \
             [0, np.sin(theta), np.cos(theta)]]
    return np.dot(M, x)

def rotyV(x, theta):
    '''Rotate a coordinate in the local y frame'''
    M = [[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], \
             [-np.sin(theta), 0, np.cos(theta)]]
    return np.dot(M, x)

def rotzV(x, theta):
    '''Roate a coordinate in the local z frame'''
    M = [[np.cos(theta), -np.sin(theta), 0], \
             [np.sin(theta), np.cos(theta), 0], [0, 0, 1]]
    return np.dot(M, x)

def rotVbyW(V, W, theta):
    ''' Rotate a vector V, about an axis W by angle theta'''

    ux = W[0]
    uy = W[1]
    uz = W[2]
    
    c = np.cos(theta)
    s = np.sin(theta)
    R = np.zeros((3, 3))
    R[0, 0] = ux**2 + (1-ux**2)*c
    R[0, 1] = ux*uy*(1-c) - uz*s
    R[0, 2] = ux*uz*(1-c) + uy*s
    
    R[1, 0] = ux*uy*(1-c) + uz*s
    R[1, 1] = uy**2 + (1-uy**2)*c
    R[1, 2] = uy*uz*(1-c) - ux*s
                    
    R[2, 0] = ux*uz*(1-c) - uy*s
    R[2, 1] = uy*uz*(1-c) + ux*s
    R[2, 2] = uz**2+(1-uz**2)*c

    return np.dot(R, V)

 # --------------------------------------------------------------
 #                I/O Functions
 # --------------------------------------------------------------

def readNValues(handle, N, dtype, binary=False, sep=' '):
    '''Read N values of dtype 'float' or 'int' from file handle'''
    if binary == True:
        sep = ""
    # end if
    if dtype == 'int':
        values = np.fromfile(handle, dtype='int', count=N, sep=sep)
    else:
        values = np.fromfile(handle, dtype='float', count=N, sep=sep)
    return values

def writeValues(handle, values, dtype, binary=False):
    '''Read N values of type 'float' or 'int' from file handle'''
    if binary:
        values.tofile(handle)
    else:
        if dtype == 'float':
            values.tofile(handle, sep=" ", format="%f")
        elif dtype == 'int':
            values.tofile(handle, sep=" ", format="%d")
        # end if
    # end if
    return 

def read_af2(filename, blunt_te=False, blunt_scale=0.1):
    ''' Load the airfoil file of type file_type'''
    f = open(filename, 'r')
    line  = f.readline() # Read (and ignore) the first line
    r = []
    try:
        r.append([float(s) for s in line.split()])
    except:
        r = []
    # end if

    while 1:
        line = f.readline()
        if not line:
            break # end of file
        if line.isspace():
            break # blank line
        r.append([float(s) for s in line.split()])
    # end while
    r = np.array(r)
    x = r[:, 0]
    y = r[:, 1]
    npt = len(x)
    # Check for blunt TE:
    if blunt_te == False:
        if y[0] != y[-1]:
            mpiPrint('Blunt Trailing Edge on airfoil: %s'%(filename))
            mpiPrint('Merging to a point over final %f ...'%(blunt_scale))
            yavg = 0.5*(y[0] + y[-1])
            xavg = 0.5*(x[0] + x[-1])
            y_top = y[0]
            y_bot = y[-1]
            x_top = x[0]
            x_bot = x[-1]
            # Indices on the TOP surface of the wing
            indices = np.where(x[0:npt/2]>=(1-blunt_scale))[0]
            for i in xrange(len(indices)):
                fact = (x[indices[i]]- (x[0]-blunt_scale))/blunt_scale
                y[indices[i]] = y[indices[i]]- fact*(y_top-yavg)
                x[indices[i]] = x[indices[i]]- fact*(x_top-xavg)
            # Indices on the BOTTOM surface of the wing
            indices = np.where(x[npt/2:]>=(1-blunt_scale))[0]
            indices = indices + npt/2
                    
            for i in xrange(len(indices)):
                fact = (x[indices[i]]- (x[-1]-blunt_scale))/blunt_scale
                y[indices[i]] = y[indices[i]]- fact*(y_bot-yavg)
                x[indices[i]] = x[indices[i]]- fact*(x_bot-xavg)
            # end for
        # end if
    # end if
    return x, y

def getCoordinatesFromFile(file_name):
    '''Get a list of coordinates from a file - useful for testing
    Required:
        file_name: filename for file
    Returns:
        coordinates: list of coordinates
    '''

    f = open(file_name, 'r')
    coordinates = []
    for line in f:
        aux = line.split()
        coordinates.append([float(aux[0]), float(aux[1]), float(aux[2])])
    # end for
    f.close()
    coordinates = np.transpose(np.array(coordinates))

    return coordinates
# --------------------------------------------------------------
#            Working with Edges Function
# --------------------------------------------------------------

def e_dist(x1, x2):
    '''Get the eculidean distance between two points'''
    return np.sqrt((x1[0]-x2[0])**2 + (x1[1]-x2[1])**2 + (x1[2]-x2[2])**2)

def e_dist2D(x1, x2):
    '''Get the eculidean distance between two points'''
    return np.sqrt((x1[0]-x2[0])**2 + (x1[1]-x2[1])**2)

def e_dist_b(x1, x2):
    x1b = 0.0
    x2b = 0.0
    db  = 1.0
    x1b = np.zeros(3)
    x2b = np.zeros(3)
    if ((x1[0]-x2[0])**2 + (x1[1]-x2[1])**2 + (x1[2]-x2[2])**2 == 0.0): 
        tempb = 0.0
    else:
        tempb = db/(2.0*np.sqrt(
                (x1[0]-x2[0])**2+(x1[1]-x2[1])**2+(x1[2]-x2[2])**2))
    # end if
    tempb0 = 2*(x1[0]-x2[0])*tempb
    tempb1 = 2*(x1[1]-x2[1])*tempb
    tempb2 = 2*(x1[2]-x2[2])*tempb
    x1b[0] = tempb0
    x2b[0] = -tempb0
    x1b[1] = tempb1
    x2b[1] = -tempb1
    x1b[2] = tempb2
    x2b[2] = -tempb2
    
    return x1b, x2b


# --------------------------------------------------------------
#             Truly Miscellaneous Functions
# --------------------------------------------------------------

def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

def unique(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't np.cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.

    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.

    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u

def unique_index(s, s_hash=None):
    '''
    This function is based on unique

    The idea is to take a list s, and reduce it as per unique.

    However, it additionally calculates a linking index arrary that is
    the same size as the original s, and points to where it ends up in
    the the reduced list

    if s_hash is not specified for sorting, s is used

    '''
    if s_hash != None:
        ind = np.argsort(np.argsort(s_hash))
    else:
        ind = np.argsort(np.argsort(s))
    # end if
    n = len(s)
    t = list(s)
    t.sort()
    
    diff = np.zeros(n, 'bool')

    last = t[0]
    lasti = i = 1
    while i < n:
        if t[i] != last:
            t[lasti] = last = t[i]
            lasti += 1
        else:
            diff[i] = True
        # end if
        i += 1
    # end while
    b = np.where(diff == True)[0]
    for i in xrange(n):
        ind[i] -= b.searchsorted(ind[i], side='right')
    # end for

    return t[:lasti], ind

def pointReduce(points, node_tol=1e-4):
    '''Given a list of N points in ndim space, with possible
    duplicates, return a list of the unique points AND a pointer list
    for the original points to the reduced set'''

    # First 
    points = np.array(points)
    N = len(points)
    dists = []
    for ipt in xrange(N): 
        dists.append(np.sqrt(np.dot(points[ipt], points[ipt])))
    # end for
    temp = np.array(dists)
    temp.sort()
    ind = np.argsort(dists)
    i = 0
    cont = True
    new_points = []
    link = np.zeros(N, 'intc')
    link_counter = 0
   
    while cont:
        cont2 = True
        temp_ind = []
        j = i
        while cont2:
            if abs(dists[ind[i]]-dists[ind[j]])<node_tol:
                temp_ind.append(ind[j])
                j = j + 1
                if j == N: # Overrun check
                    cont2 = False
                # end if
            else:
                cont2 = False
            #end if
        # end while
        sub_points = [] # Copy of the list of sub points with the dists
        for ii in xrange(len(temp_ind)):
            sub_points.append(points[temp_ind[ii]])

        # Brute Force Search them 
        sub_unique_pts, sub_link = pointReduceBruteForce(sub_points, node_tol)
        new_points.extend(sub_unique_pts)

        for ii in xrange(len(temp_ind)):
            link[temp_ind[ii]] = sub_link[ii] + link_counter
        # end if
        link_counter += max(sub_link) + 1

        i = j - 1 + 1
        if i == N:
            cont = False
        # end if
    # end while
    return np.array(new_points), np.array(link)

def pointReduceBruteForce(points,  node_tol=1e-4):
    '''Given a list of N points in ndim space, with possible
    duplicates, return a list of the unique points AND a pointer list
    for the original points to the reduced set

    BRUTE FORCE VERSION

    '''
    N = len(points)
    unique_points = [points[0]]
    link = [0]
    for i in xrange(1, N):
        found_it = False
        for j in xrange(len(unique_points)):
            if e_dist(points[i], unique_points[j]) < node_tol:
                link.append(j)
                found_it = True
                break
            # end if
        # end for
        if not found_it:
            unique_points.append(points[i])
            link.append(j+1)
        # end if
    # end for
    return np.array(unique_points), np.array(link)

def edgeOrientation(e1, e2):
    '''Compare two edge orientations. Basically if the two nodes are
    in the same order return 1 if they are in opposite order, return
    1'''
    
    if [e1[0], e1[1]] == [e2[0], e2[1]]:
        return 1
    elif [e1[1], e1[0]] == [e2[0], e2[1]]:
        return -1
    else:
        mpiPrint('Error with edgeOrientation: Not possible.')
        mpiPrint('Orientation 1 [%d %d]'%(e1[0], e1[1]))
        mpiPrint('Orientation 2 [%d %d]'%(e2[0], e2[1]))
        sys.exit(0)
    # end if

def faceOrientation(f1, f2):
    '''Compare two face orientations f1 and f2 and return the
    transform to get f1 back to f2'''
    
    if [f1[0], f1[1], f1[2], f1[3]] == [f2[0], f2[1], f2[2], f2[3]]:
        return 0
    elif [f1[0], f1[1], f1[2], f1[3]] == [f2[1], f2[0], f2[3], f2[2]]:
        return 1
    elif [f1[0], f1[1], f1[2], f1[3]] == [f2[2], f2[3], f2[0], f2[1]]:
        return 2
    elif [f1[0], f1[1], f1[2], f1[3]] == [f2[3], f2[2], f2[1], f2[0]]:
        return 3
    elif [f1[0], f1[1], f1[2], f1[3]] == [f2[0], f2[2], f2[1], f2[3]]:
        return 4
    elif [f1[0], f1[1], f1[2], f1[3]] == [f2[2], f2[0], f2[3], f2[1]]:
        return 5
    elif [f1[0], f1[1], f1[2], f1[3]] == [f2[1], f2[3], f2[0], f2[2]]:
        return 6
    elif [f1[0], f1[1], f1[2], f1[3]] == [f2[3], f2[1], f2[2], f2[0]]:
        return 7
    else:
        mpiPrint('Error with faceOrientation: Not possible.')
        mpiPrint('Orientation 1 [%d %d %d %d]'%(f1[0], f1[1], f1[2], f1[3]))
        mpiPrint('Orientation 2 [%d %d %d %d]'%(f2[0], f2[1], f2[2], f2[3]))
        sys.exit(0)

def quadOrientation(pt1, pt2):
    '''Given two sets of 4 points in ndim space, pt1 and pt2,
    determine the orientation of pt2 wrt pt1
    This works for both exact quads and "loosely" oriented quads
    .'''
    dist = np.zeros((4, 4))
    for i in xrange(4):
        for j in xrange(4):
            dist[i, j] = e_dist(pt1[i], pt2[j])
        # end for
    # end for

    # Now compute the 8 distances for the 8 possible orientation
    sum_dist = np.zeros(8)
    # corners = [0, 1, 2, 3]
    sum_dist[0] = dist[0, 0] + dist[1, 1] + dist[2, 2] + dist[3, 3] 
    # corners = [1, 0, 3, 2]
    sum_dist[1] = dist[0, 1] + dist[1, 0] + dist[2, 3] + dist[3, 2] 
    # corners = [2, 3, 0, 1]
    sum_dist[2] = dist[0, 2] + dist[1, 3] + dist[2, 0] + dist[3, 1] 
    # corners = [3, 2, 1, 0]
    sum_dist[3] = dist[0, 3] + dist[1, 2] + dist[2, 1] + dist[3, 0] 
    # corners = [0, 2, 1, 3]
    sum_dist[4] = dist[0, 0] + dist[1, 2] + dist[2, 1] + dist[3, 3] 
    # corners = [2, 0, 3, 1]
    sum_dist[5] = dist[0, 2] + dist[1, 0] + dist[2, 3] + dist[3, 1] 
    # corners = [1, 3, 0, 2]
    sum_dist[6] = dist[0, 1] + dist[1, 3] + dist[2, 0] + dist[3, 2] 
    # corners = [3, 1, 2, 0]
    sum_dist[7] = dist[0, 3] + dist[1, 1] + dist[2, 2] + dist[3, 0] 

    index = sum_dist.argmin()

    return index

def orientArray(index, in_array):
    '''Take an input array in_array, and rotate/flip according to the index
    output from quadOrientation'''

    if index == 0:
        out_array = in_array.copy()
    elif index == 1:
        out_array = rotateCCW(in_array)
        out_array = rotateCCW(out_array)
        out_array = reverseRows(out_array)
    elif index == 2:
        out_array = reverseRows(in_array)
    elif index == 3:
        out_array = rotateCCW(in_array) # Verified working
        out_array = rotateCCW(out_array)
    elif index == 4:
        out_array = rotateCW(in_array)
        out_array = reverseRows(out_array)
    elif index == 5:
        out_array = rotateCCW(in_array)
    elif index == 6:
        out_array = rotateCW(in_array)
    elif index == 7:
        out_array = rotateCCW(in_array)
        out_array = reverseRows(out_array)
        
    return out_array

def directionAlongSurface(surface, line):
    '''Determine the dominate (u or v) direction of line along surface'''
    # Now Do two tests: Take N points in u and test N groups
    # against dn and take N points in v and test the N groups
    # again

    N = 3
    sn = np.linspace(0, 1, N)
    dn = np.zeros((N, 3))
    s = np.linspace(0, 1, N)
    for i in xrange(N):
        dn[i, :] = line.getDerivative(sn[i])
    # end for

    u_dot_tot = 0
    for i in xrange(N):
        for n in xrange(N):
            du, dv = surface.getDerivative(s[i], s[n])
            u_dot_tot += np.dot(du, dn[n, :])
        # end for
    # end for

    v_dot_tot = 0
    for j in xrange(N):
        for n in xrange(N):
            du, dv = surface.getDerivative(s[n], s[j])
            v_dot_tot += np.dot(dv, dn[n, :])
        # end for
    # end for

    if abs(u_dot_tot) > abs(v_dot_tot):
        # Its along u now get 
        if u_dot_tot >= 0: 
            return 0 # U same direction
        else:
            return 1 # U opposite direction
    else:
        if v_dot_tot >= 0:
            return 2 # V same direction
        else:
            return 3 # V opposite direction
        # end if
    # end if 

def curveDirection(curve1, curve2):
    '''Determine if the direction of curve 1 is basically in the same
    direction as curve2. Return 1 for same direction, -1 for opposite
    direction'''

    N = 4
    s = np.linspace(0, 1, N)
    tot = 0
    d_forward = 0
    d_backward = 0
    for i in xrange(N):
        tot += np.dot(curve1.getDerivative(s[i]), curve2.getDerivative(s[i]))
        d_forward += e_dist(curve1.getValue(s[i]), curve2.getValue(s[i]))
        d_backward += e_dist(curve1.getValue(s[i]), curve2.getValue(s[N-i-1]))
    # end for

    if tot > 0:
        return tot, d_forward
    else:
        return tot, d_backward

def indexPosition1D(i, N):
    '''This function is a generic function which determines if index
    over a list of length N is an interior point or node 0 or node 1.
    '''
    if i > 0 and i < N-1: # Interior
        return 0, None
    elif i == 0: # Node 0
        return 1, 0
    elif i == N-1: # Node 1
        return 1, 1

def indexPosition2D(i, j, N, M):
    '''This function is a generic function which determines if for a grid
    of data NxM with index i going 0->N-1 and j going 0->M-1, it
    determines if i,j is on the interior, on an edge or on a corner

    The funtion return four values: 
    type: this is 0 for interior, 1 for on an edge and 2 for on a corner
    edge: this is the edge number if type==1
    node: this is the node number if type==2 
    index: this is the value index along the edge of interest -- 
    only defined for edges'''

    if i > 0 and i < N - 1 and j > 0 and j < M-1: # Interior
        return 0, None, None, None
    elif i > 0 and i < N - 1 and j == 0:     # Edge 0
        return 1, 0, None, i
    elif i > 0 and i < N - 1 and j == M - 1: # Edge 1
        return 1, 1, None, i
    elif i == 0 and j > 0 and j < M - 1:     # Edge 2
        return 1, 2, None, j
    elif i == N - 1 and j > 0 and j < M - 1: # Edge 3
        return 1, 3, None, j
    elif i == 0 and j == 0:                  # Node 0
        return 2, None, 0, None
    elif i == N - 1 and j == 0:              # Node 1
        return 2, None, 1, None
    elif i == 0 and j == M -1 :              # Node 2
        return 2, None, 2, None
    elif i == N - 1 and j == M - 1:          # Node 3
        return 2, None, 3, None

def indexPosition3D(i, j, k, N, M, L):
    '''This function is a generic function which determines if for a
    3dgrid of data NxMXL with index i going 0->N-1 and j going 0->M-1
    k going 0->L-1, it determines if i,j,k is on the interior, on a
    face, on an edge or on a corner

    The funtion return theses values: 
    type: this is 0 for interior, 1 for on an face, 
           3 for an edge and 4 for on a corner
    number: this is the face number if type==1,
            this is the edge number if type==2
            this is the node number if type==3 

    index1: this is the value index along 0th dir the face
        of interest OR edge of interest
    index2: this is the value index along 1st dir the face
        of interest
        '''
    
    # Note to interior->Faces->Edges->Nodes to minimize number of if checks

    # Interior:
    if i > 0 and i < N-1 and j > 0 and j < M-1 and k > 0 and k < L-1: 
        return 0, None, None, None

    elif i > 0 and i < N-1 and j > 0 and j < M-1 and k == 0:   # Face 0
        return 1, 0, i, j
    elif i > 0 and i < N-1 and j > 0 and j < M-1 and k == L-1: # Face 1
        return 1, 1, i, j
    elif i == 0 and j > 0 and j < M-1 and k > 0 and k < L-1:   # Face 2
        return 1, 2, j, k
    elif i == N-1 and j > 0 and j < M-1 and k > 0 and k < L-1: # Face 3
        return 1, 3, j, k
    elif i > 0 and i < N-1 and j == 0 and k > 0 and k < L-1:   # Face 4
        return 1, 4, i, k
    elif i > 0 and i < N-1 and j == M-1 and k > 0 and k < L-1: # Face 5
        return 1, 5, i, k

    elif i > 0 and i < N-1 and j == 0 and k == 0:       # Edge 0
        return 2, 0, i, None
    elif i > 0 and i < N-1 and j == M-1 and k == 0:     # Edge 1
        return 2, 1, i, None
    elif i == 0 and j > 0 and j < M-1 and k == 0:       # Edge 2
        return 2, 2, j, None
    elif i == N-1 and j > 0 and j < M-1 and k == 0:     # Edge 3
        return 2, 3, j, None
    elif i > 0 and i < N-1 and j == 0 and k == L-1:     # Edge 4
        return 2, 4, i, None
    elif i > 0 and i < N-1 and j == M-1 and k == L-1:   # Edge 5
        return 2, 5, i, None
    elif i == 0 and j > 0 and j < M-1 and k == L-1:     # Edge 6
        return 2, 6, j, None
    elif i == N-1 and j > 0 and j < M-1 and k == L-1:   # Edge 7
        return 2, 7, j, None
    elif i == 0 and j == 0 and k > 0 and k < L-1:       # Edge 8
        return 2, 8, k, None
    elif i == N-1 and j == 0 and k > 0 and k < L-1:     # Edge 9
        return 2, 9, k, None
    elif i == 0 and j == M-1 and k > 0 and k < L-1:     # Edge 10
        return 2, 10, k, None
    elif i == N-1 and j == M-1 and k > 0 and k < L-1:   # Edge 11
        return 2, 11, k, None

    elif i == 0 and j == 0 and k == 0:                  # Node 0
        return 3, 0, None, None
    elif i == N-1 and j == 0 and k == 0:                # Node 1
        return 3, 1, None, None
    elif i == 0 and j == M-1 and k == 0:                # Node 2
        return 3, 2, None, None
    elif i == N-1 and j == M-1 and k == 0:              # Node 3
        return 3, 3, None, None
    elif i == 0 and j == 0 and k == L-1:                # Node 4
        return 3, 4, None, None
    elif i == N-1 and j == 0 and k == L-1:              # Node 5
        return 3, 5, None, None
    elif i == 0 and j == M-1 and k == L-1:              # Node 6
        return 3, 6, None, None
    elif i == N-1 and j == M-1 and k == L-1:            # Node 7
        return 3, 7, None, None

# --------------------------------------------------------------
#                     Node/Edge Functions
# --------------------------------------------------------------

def edgeFromNodes(n1, n2):
    '''Return the edge coorsponding to nodes n1, n2'''
    if (n1 == 0 and n2 == 1) or (n1 == 1 and n2 == 0):
        return 0
    elif (n1 == 0 and n2 == 2) or (n1 == 2 and n2 == 0):
        return 2
    elif (n1 == 3 and n2 == 1) or (n1 == 1 and n2 == 3):
        return 3
    elif (n1 == 3 and n2 == 2) or (n1 == 2 and n2 == 3):
        return 1

def edgesFromNode(n):
    ''' Return the two edges coorsponding to node n'''
    if n == 0:
        return 0, 2
    if n == 1:
        return 0, 3
    if n == 2:
        return 1, 2
    if n == 3:
        return 1, 3

def edgesFromNodeIndex(n, N, M):
    ''' Return the two edges coorsponding to node n AND return the index
of the node on the edge according to the size (N, M)'''
    if n == 0:
        return 0, 2, 0, 0
    if n == 1:
        return 0, 3, N-1, 0
    if n == 2:
        return 1, 2, 0, M-1
    if n == 3:
        return 1, 3, N-1, M-1

def nodesFromEdge(edge):
    '''Return the nodes on either edge of a standard edge'''
    if edge == 0:
        return 0, 1
    elif edge == 1:
        return 2, 3
    elif edge == 2:
        return 0, 2
    elif edge == 3:
        return 1, 3
    elif edge == 4:
        return 4, 5
    elif edge == 5:
        return 6, 7
    elif edge == 6:
        return 4, 6
    elif edge == 7:
        return 5, 7
    elif edge == 8:
        return 0, 4
    elif edge == 9:
        return 1, 5
    elif edge == 10:
        return 2, 6
    elif edge == 11:
        return 3, 7

# Volume Face/edge functions
def nodesFromFace(face):
    if face == 0:
        return [0, 1, 2, 3]
    elif face == 1:
        return [4, 5, 6, 7]
    elif face == 2:
        return [0, 2, 4, 6]
    elif face == 3:
        return [1, 3, 5, 7]
    elif face == 4:
        return [0, 1, 4, 5]
    elif face == 5:
        return [2, 3, 6, 7]

# --------------------------------------------------------------
#                  Knot Vector Manipulation Functions
# --------------------------------------------------------------
    
def blendKnotVectors(knot_vectors, sym):
    '''Take in a list of knot vectors and average them'''

    nVec = len(knot_vectors)
 
    if sym: # Symmetrize each knot vector first
        for i in xrange(nVec):
            cur_knot_vec = knot_vectors[i].copy()
            if np.mod(len(cur_knot_vec), 2) == 1: #its odd
                mid = (len(cur_knot_vec) -1)/2
                beg1 = cur_knot_vec[0:mid]
                beg2 = (1-cur_knot_vec[mid+1:])[::-1]
                # Average
                beg = 0.5*(beg1+beg2)
                cur_knot_vec[0:mid] = beg
                cur_knot_vec[mid+1:] = (1-beg)[::-1]
                cur_knot_vec[mid] = 0.5
            else: # its even
                mid = len(cur_knot_vec)/2
                beg1 = cur_knot_vec[0:mid]
                beg2 = (1-cur_knot_vec[mid:])[::-1]
                beg = 0.5*(beg1+beg2)
                cur_knot_vec[0:mid] = beg
                cur_knot_vec[mid:] = (1-beg)[::-1]
            # end if
            knot_vectors[i] = cur_knot_vec
        # end for
    # end if

    # Now average them all
   
    new_knot_vec = np.zeros(len(knot_vectors[0]))
    for i in xrange(nVec):
        new_knot_vec += knot_vectors[i]
    # end if

    new_knot_vec /= nVec
    return new_knot_vec

class point_select(object):

    def __init__(self, type, *args, **kwargs):

        '''Initialize a control point selection class. There are several ways
        to initialize this class depending on the 'type' qualifier:

        Inputs:
        
        type: string which inidicates the initialization type:
        
        'x': Define two corners (pt1=,pt2=) on a plane parallel to the
        x=0 plane

        'y': Define two corners (pt1=,pt2=) on a plane parallel to the
        y=0 plane

        'z': Define two corners (pt1=,pt2=) on a plane parallel to the
        z=0 plane

        'quad': Define FOUR corners (pt1=,pt2=,pt3=,pt4=) in a
        COUNTER-CLOCKWISE orientation 

        'list': Define the indices of a list that will be used to
        extract the points

        '''
        
        if type == 'x' or type == 'y' or type == 'z':
            assert 'pt1' in kwargs and 'pt2' in kwargs, 'Error:, two points \
must be specified with initialization type x,y, or z. Points are specified \
with kwargs pt1=[x1,y1,z1],pt2=[x2,y2,z2]'

        elif type == 'quad':
            assert 'pt1' in kwargs and 'pt2' in kwargs and 'pt3' in kwargs \
                and 'pt4' in kwargs, 'Error:, four points \
must be specified with initialization type quad. Points are specified \
with kwargs pt1=[x1,y1,z1],pt2=[x2,y2,z2],pt3=[x3,y3,z3],pt4=[x4,y4,z4]'
            
        # end if
        corners = np.zeros([4, 3])
        if type in ['x', 'y', 'z', 'corners']:
            if type == 'x':
                corners[0] = kwargs['pt1']

                corners[1][1] = kwargs['pt2'][1]
                corners[1][2] = kwargs['pt1'][2]

                corners[2][1] = kwargs['pt1'][1]
                corners[2][2] = kwargs['pt2'][2]

                corners[3] = kwargs['pt2']

                corners[:, 0] = 0.5*(kwargs['pt1'][0] + kwargs['pt2'][0])

            elif type == 'y':
                corners[0] = kwargs['pt1']

                corners[1][0] = kwargs['pt2'][0]
                corners[1][2] = kwargs['pt1'][2]

                corners[2][0] = kwargs['pt1'][0]
                corners[2][2] = kwargs['pt2'][2]

                corners[3] = kwargs['pt2']

                corners[:, 1] = 0.5*(kwargs['pt1'][1] + kwargs['pt2'][1])

            elif type == 'z':
                corners[0] = kwargs['pt1']

                corners[1][0] = kwargs['pt2'][0]
                corners[1][1] = kwargs['pt1'][1]

                corners[2][0] = kwargs['pt1'][0]
                corners[2][1] = kwargs['pt2'][1]

                corners[3] = kwargs['pt2']

                corners[:, 2] = 0.5*(kwargs['pt1'][2] + kwargs['pt2'][2])

            elif type == 'quad':
                corners[0] = kwargs['pt1']
                corners[1] = kwargs['pt2']
                corners[2] = kwargs['pt4'] # Note the switch here from
                                           # CC orientation
                corners[3] = kwargs['pt3']
            # end if

            X = np.reshape(corners, [2, 2, 3])
            exec(import_modules('pySpline'))
            self.box = pySpline.bilinear_surface(X=X)
            self.type = 'box'
        elif type == 'list':
            self.box = None
            self.type = type
            self.indices = np.array(args[0])

        return

    def getPoints(self,  points):

        '''Take in a list of points and return the ones that statify
        the point select class.'''
        pt_list = []
        ind_list = []
        if self.type == 'box':
            for i in xrange(len(points)):
                u0, v0, D, converged = self.box.projectPoint(points[i])
                if u0 > 0 and u0 < 1 and v0 > 0 and v0 < 1: #Its Inside
                    pt_list.append(points[i])
                    ind_list.append(i)
                # end if
            # end for
        elif self.type == 'list':
            for i in xrange(len(self.indices)):
                pt_list.append(points[self.indices[i]])
            # end for
            ind_list = self.indices.copy()
        # end if
        
        return pt_list, ind_list

class topology(object):
    '''
    The base topology class from which the BlockTopology,
    SurfaceTology and CuveTopology classes inherit from
    
    The topology object contains all the info required for the block
    topology (most complex) however, simpiler topologies are handled
    accordingly.

    Class Attributes:
        nVol : The number of volumes in the topology (may be 0)
        nFace: The number of unique faces on the topology (may be 0)
        nEdge: The number of uniuqe edges on the topology 
        nNode: The number of unique nodes on the topology

        nEnt: The number of "entities" in the topology class. This may
        be curves, faces or volumes

        mNodeEnt: The number of NODES per entity. For curves it's 2, for
        surfaces 4 and for volumes 8.

        mEdgeEnt: The number of EDGES per entity. For curves it's 1,
        for surfaces, 4 and for volumes, 12

        mFaceEnt: The number of faces per entity. For curves its's 0,
        for surfaces, 1 and for volumes,6

        mVolEnt: The number of volumes per entity. For curves it's 0,
        for surfaces, 0 and for volumnes, 1

        node_link: The array of size nEnt x mNodesEnt which points
                   to the node for each entity
        edge_link: The array of size nEnt x mEdgeEnt which points
                   to the edge for each edge of entity
        face_link: The array of size nEnt x mFaceEnt which points to 
                   the face of each face on an entity

        edge_dir:  The array of size nEnt x mEdgeEnt which detrmines
                   if the intrinsic direction of this edge is
                   opposite of the direction as recorded in the
                   edge list. edge_dir[entity#][#] = 1 means same direction;
                   -1 is opposite direction.
                  
        face_dir:  The array of size nFace x 6 which determines the 
                   intrinsic direction of this face. It is one of 0->7
                   
        l_index:   The local->global list of arrays for each volue
        g_index:   The global->local list points for the entire topology
        edges:     The list of edge objects defining the topology
        simple    : A flag to determine of this is a "simple" topology 
                   which means there are NO degernate Edges, 
                   NO multiple edges sharing the same nodes and NO 
                   edges which loop back and have the same nodes
                   MUST BE SIMPLE
    '''

    def __init__(self):
        # Not sure what should go here...
        return
    def _calcDGs(self, edges, edge_link, edge_link_sorted, edge_link_ind):

        dg_counter = -1
        for i in xrange(self.nEdge):
            if edges[i][2] == -1: # Not set yet
                dg_counter += 1
                edges[i][2] = dg_counter
                self._addDGEdge(i, edges, edge_link, 
                                edge_link_sorted, edge_link_ind)
            # end if
        # end for
        self.nDG = dg_counter + 1
   
    def _addDGEdge(self, i, edges, edge_link, edge_link_sorted, edge_link_ind):
        left  = edge_link_sorted.searchsorted(i, side='left')
        right = edge_link_sorted.searchsorted(i, side='right')
        res   = edge_link_ind[slice(left, right)]

        for j in xrange(len(res)):
            ient = res[j]/self.mEdgeEnt #Integer Division
            iedge = np.mod(res[j], self.mEdgeEnt)

            pEdges = self._getParallelEdges(iedge)
            oppositeEdges = []
            for iii in xrange(len(pEdges)):
                oppositeEdges.append(
                    edge_link[self.mEdgeEnt*ient + pEdges[iii]])
            
            for ii in xrange(len(pEdges)):
                if edges[oppositeEdges[ii]][2] == -1:
                    edges[oppositeEdges[ii]][2] = edges[i][2]
                    if not edges[oppositeEdges[ii]][0] == \
                            edges[oppositeEdges[ii]][1]:
                        self._addDGEdge(oppositeEdges[ii], edges, 
                                        edge_link, edge_link_sorted, 
                                        edge_link_ind)
                # end if
            # end if
        # end for

    def _getParallelEdges(self, iedge):
        '''Return parallel edges for surfaces and volumes'''

        if self.topo_type == 'surface':
            if iedge == 0: return [1]
            if iedge == 1: return [0]
            if iedge == 2: return [3]
            if iedge == 3: return [2]

        if self.topo_type == 'volume':
            if iedge == 0: 
                return [1, 4, 5]
            if iedge == 1: 
                return [0, 4, 5]
            if iedge == 2: 
                return [3, 6, 7]
            if iedge == 3: 
                return [2, 6, 7]
            if iedge == 4: 
                return [0, 1, 5]
            if iedge == 5: 
                return [0, 1, 4]
            if iedge == 6: 
                return [2, 3, 7]
            if iedge == 7: 
                return [2, 3, 6]
            if iedge == 8: 
                return [9, 10, 11]
            if iedge == 9: 
                return [8, 10, 11]
            if iedge == 10: 
                return [8, 9, 11]
            if iedge == 11: 
                return [8, 9, 10]
        if self.topo_type == 'curve':
            return None

    def printConnectivity(self):
        '''Print the Edge Connectivity to the screen'''

        mpiPrint('-----------------------------------------------\
-------------------------')
        mpiPrint('%4d  %4d  %4d  %4d  %4d '%(
                self.nNode, self.nEdge, self.nFace, self.nVol, self.nDG))
        N_list = self._getDGList()
        mpiPrint('Design Group | Number')
        for i in xrange(self.nDG):
            mpiPrint('%5d        | %5d       '%(i, N_list[i]))
        # end for

        # Always have edges!
        mpiPrint('Edge Number    |   n0  |   n1  |  Cont | Degen | Intsct|\
   DG   |  N     |')
        for i in xrange(len(self.edges)):
            self.edges[i].write_info(i, sys.stdout)
        # end for

        print '%9s Num |'% (self.topo_type), 
        for i in xrange(self.mNodeEnt):
            print ' n%2d|'% (i), 
        for i in xrange(self.mEdgeEnt):
            print ' e%2d|'% (i), 
        print ' ' # Get New line
            
        for i in xrange(self.nEnt):
            print ' %5d        |'% (i), 
            for j in xrange(self.mNodeEnt):
                print '%4d|'%self.node_link[i][j], 
            # end for
            for j in xrange(self.mEdgeEnt):
                print '%4d|'% (self.edge_link[i][j]*self.edge_dir[i][j]), 
            # end for
            print ' '
        # end for
        print('----------------------------------------------------\
--------------------')

        if self.topo_type == 'volume':
            mpiPrint('Vol Number | f0 | f1 | f2 | f3 | f4 | f5 |f0dir|\
f1dir|f2dir|f3dir|f4dir|f5dir|')
            for i in xrange(self.nVol):
                mpiPrint(' %5d     |%4d|%4d|%4d|%4d|%4d|%4d|%5d|%5d|\
%5d|%5d|%5d|%5d|'\
                             %(i, self.face_link[i][0], self.face_link[i][1], 
                               self.face_link[i][2], self.face_link[i][3], 
                               self.face_link[i][3], self.face_link[i][5], 
                               self.face_dir[i][0], self.face_dir[i][1], 
                               self.face_dir[i][2], self.face_dir[i][3], 
                               self.face_dir[i][4], self.face_dir[i][5])) 
            # end for
        # end if
        return

    def writeConnectivity(self, file_name):
        '''Write the full edge connectivity to a file file_name'''
        if MPI:
            MPI.COMM_WORLD.barrier()
            if MPI.COMM_WORLD.rank == 0:
                is_root = True
            else:
                is_root = False
            # end if
        else:
            is_root = True
        # end if

        if is_root:
            f = open(file_name, 'w')
            f.write('%4d  %4d  %4d   %4d  %4d\n'%(
                    self.nNode, self.nEdge, self.nFace, self.nVol, self.nDG))
            f.write('Design Group |  Number\n')
            # Write out the design groups and their number parameter
            N_list = self._getDGList()
            for i in xrange(self.nDG):
                f.write('%5d        | %5d       \n'%(i, N_list[i]))
            # end for

            f.write('Edge Number    |   n0  |   n1  |  Cont | Degen |\
 Intsct|   DG   |  N     |\n')
            for i in xrange(len(self.edges)):
                self.edges[i].write_info(i, f)
            # end for

            f.write('%9s Num |'%(self.topo_type))
            for i in xrange(self.mNodeEnt):
                f.write(' n%2d|'%(i))
            for i in xrange(self.mEdgeEnt):
                f.write(' e%2d|'%(i))
            f.write('\n')

            for i in xrange(self.nEnt):
                f.write(' %5d        |'%(i))
                for j in xrange(self.mNodeEnt):
                    f.write('%4d|'%self.node_link[i][j])
                # end for
                for j in xrange(self.mEdgeEnt):
                    f.write('%4d|'%(self.edge_link[i][j]*self.edge_dir[i][j]))
                # end for
                f.write('\n')
            # end for

            if self.topo_type == 'volume':

                f.write('Vol Number | f0 | f1 | f2 | f3 | f4 | f5 |\
f0dir|f1dir|f2dir|f3dir|f4dir|f5dir|\n')
                for i in xrange(self.nVol):
                    f.write(' %5d     |%4d|%4d|%4d|%4d|%4d|%4d|%5d|\
%5d|%5d|%5d|%5d|%5d|\n'% (i, self.face_link[i][0], self.face_link[i][1], 
                          self.face_link[i][2], self.face_link[i][3], 
                          self.face_link[i][4], self.face_link[i][5], 
                          self.face_dir[i][0], self.face_dir[i][1], 
                          self.face_dir[i][2], self.face_dir[i][3], 
                          self.face_dir[i][4], self.face_dir[i][5])) 

            f.close()
        # end if
        
        return

    def readConnectivity(self, file_name):
        '''Read the full edge connectivity from a file file_name'''
        # We must be able to populate the following:
        #nNode, nEdge, nFace,nVol,node_link,edge_link,
        # face_link,edge_dir,face_dir

        f = open(file_name, 'r')
        aux = f.readline().split()
        self.nNode = int(aux[0])
        self.nEdge = int(aux[1])
        self.nFace = int(aux[2])
        self.nVol  = int(aux[3])
        self.nDG   = int(aux[4])
        self.edges = []
        
        if self.topo_type == 'volume':
            self.nEnt = self.nVol
        elif self.topo_type == 'surface':
            self.nEnt = self.nFace
        elif self.topo_type == 'curve':
            self.nEnt = self.nEdge
        # end if

        f.readline() # This is the header line so ignore

        N_list = np.zeros(self.nDG, 'intc')
        for i in xrange(self.nDG):
            aux = f.readline().split('|')
            N_list[i] = int(aux[1])
        # end for

        f.readline() # Second Header line

        for i in xrange(self.nEdge):
            aux = f.readline().split('|')
            self.edges.append(edge(int(aux[1]), int(aux[2]), int(aux[3]), 
                                   int(aux[4]), int(aux[5]), int(aux[6]), 
                                   int(aux[7])))
        # end for
        f.readline() # This is the third header line so ignore

        self.edge_link = np.zeros((self.nEnt, self.mEdgeEnt), 'intc')
        self.node_link = np.zeros((self.nEnt, self.mNodeEnt), 'intc')
        self.edge_dir  = np.zeros((self.nEnt, self.mEdgeEnt), 'intc')
        
        for i in xrange(self.nEnt):
            aux = f.readline().split('|')
            for j in xrange(self.mNodeEnt):
                self.node_link[i][j] = int(aux[j+1])
            for j in xrange(self.mEdgeEnt):
                self.edge_dir[i][j]  = np.sign(int(aux[j+1+self.mNodeEnt]))
                self.edge_link[i][j] = int(
                    aux[j+1+self.mNodeEnt])*self.edge_dir[i][j]

            # end for
        # end for

        if self.topo_type == 'volume':
            f.readline() # This the fourth header line so ignore

            self.face_link = np.zeros((self.nVol, 6), 'intc')
            self.face_dir  = np.zeros((self.nVol, 6), 'intc')
            for ivol in xrange(self.nVol):
                aux = f.readline().split('|')
                self.face_link[ivol] = [int(aux[i]) for i in xrange(1, 7)]
                self.face_dir[ivol]  = [int(aux[i]) for i in xrange(7, 13)]
            # end for
        # end if
      
        # Set the N_list to the edges
        for iedge in xrange(self.nEdge):
            self.edges[iedge].N = N_list[self.edges[iedge].dg]
            
        return

    def _getDGList(self):
        '''After calcGlobalNumbering is called with the size
        parameters, we can now produce a list of length ndg with the
        each entry coorsponing to the number N associated with that DG'''

        # This can be run in linear time...just loop over each edge
        # and add to dg list
        N_list = np.zeros(self.nDG, 'intc')
        for iedge in xrange(self.nEdge):
            N_list[self.edges[iedge].dg] = self.edges[iedge].N
        # end for
            
        return N_list




class CurveTopology(topology):
    '''
    See topology class for more information
    '''
    def __init__(self, coords=None, file=None):
        '''Initialize the class with data required to compute the topology'''
        topology.__init__(self)
        self.mNodeEnt = 2
        self.mEdgeEnt = 1
        self.mfaceEnt = 0
        self.mVolEnt  = 0
        self.nVol = 0
        self.nFace = 0
        self.topo_type = 'curve'
        self.g_index = None
        self.l_index = None
        self.nGlobal = None
        if file != None:
            self.readConnectivity(file)
            return
        # end if
        
        self.edges = None
        self.simple = True

        # Must have curves
        # Get the end points of each curve

        self.nEdge = len(coords)
        coords = coords.reshape((self.nEdge*2, 3))
        node_list, self.node_link = pointReduce(coords)
        self.node_link = self.node_link.reshape((self.nEdge, 2))
        self.nNode = len(node_list)
        self.edges = []
        self.edge_link = np.zeros((self.nEdge, 1), 'intc')
        for iedge in xrange(self.nEdge):
            self.edge_link[iedge][0] = iedge
        # end for
        self.edge_dir  = np.zeros((self.nEdge, 1), 'intc')

        for iedge in xrange(self.nEdge):
            n1 = self.node_link[iedge][0]
            n2 = self.node_link[iedge][1]
            if n1 < n2:
                self.edges.append(edge(n1, n2, 0, 0, 0, iedge, 2))
                self.edge_dir[iedge][0] = 1
            else:
                self.edges.append(edge(n2, n1, 0, 0, 0, iedge, 2))
                self.edge_dir[iedge][1] = -1
            # end if
        # end for
        self.nDG = self.nEdge
        self.nEnt = self.nEdge
        return

    def calcGlobalNumbering(self, sizes, curve_list=None):
        '''Internal function to calculate the global/local numbering
        for each curve'''
        for i in xrange(len(sizes)):
            self.edges[self.edge_link[i][0]].N = sizes[i]
        # end for
        if curve_list == None:
            curve_list = range(self.nEdge)
        # end if
        
        # ----------------- Start of Edge Computation ---------------------
        counter = 0
        l_index = []

        assert len(sizes) == len(curve_list), 'Error: The list of sizes and \
the list of surfaces must be the same length'

        # Assign unique numbers to the corners -> Corners are indexed
        # sequentially
        node_index = np.arange(self.nNode)
        counter = len(node_index)
        edge_index = [ [] for i in xrange(len(self.edges))]
     
        # Assign unique numbers to the edges

        for ii in xrange(len(curve_list)):
            cur_size = [sizes[ii]]
            icurve = curve_list[ii]
            for iedge in xrange(1):
                edge = self.edge_link[ii][iedge]
                    
                if edge_index[edge] == []:# Not added yet
                    for jj in xrange(cur_size[iedge]-2):
                        edge_index[edge].append(counter)
                        counter += 1
                    # end for
                # end if
            # end for
        # end for

        g_index = [ [] for i in xrange(counter)] # We must add [] for
                                                 # each global node

        for ii in xrange(len(curve_list)):
            icurve = curve_list[ii]
            N = sizes[ii]
            l_index.append(-1*np.ones(N, 'intc'))

            for i in xrange(N):
                type, node = indexPosition1D(i, N)

                if type == 1: # Node
                    cur_node = self.node_link[ii][node]
                    l_index[ii][i] = node_index[cur_node]
                    g_index[node_index[cur_node]].append([icurve, i])
                else:
                    if self.edge_dir[ii][0] == -1:
                        cur_index = edge_index[self.edge_link[ii][0]][N-i-2]
                    else:
                        cur_index = edge_index[self.edge_link[ii][0]][i-1]
                    # end if
                    l_index[ii][i] = cur_index
                    g_index[cur_index].append([icurve, i])
                # end if
            # end for
        # end for
        self.nGlobal = len(g_index)
        self.g_index = g_index
        self.l_index = l_index
        
        return 


class SurfaceTopology(topology):
    '''
    See topology class for more information
    '''
    def __init__(self, coords=None, face_con=None, file=None, node_tol=1e-4,
                 edge_tol=1e-4):
        '''Initialize the class with data required to compute the topology'''
        topology.__init__(self)
        self.mNodeEnt = 4
        self.mEdgeEnt = 4
        self.mfaceEnt = 1
        self.mVolEnt  = 0
        self.nVol = 0
        self.topo_type = 'surface'
        self.g_index = None
        self.l_index = None
        self.nGlobal = None
        if file != None:
            self.readConnectivity(file)
            return
        # end if
        
        self.edges = None
        self.face_index = None
        self.simple = False

        if not face_con == None: 
            face_con = np.array(face_con)
            midpoints = None
            self.nFace = len(face_con)
            self.nEnt = self.nFace
            self.simple = True
            # Check to make sure nodes are sequential
            self.nNode = len(unique(face_con.flatten()))
            if self.nNode != max(face_con.flatten())+1:
                # We don't have sequential nodes
                mpiPrint("Error: Nodes are not sequential")
                sys.exit(1)
            # end if
            
            edges = []
            edge_hash = []
            for iface in xrange(self.nFace):
                #             n1                ,n2               ,dg,n,degen
                edges.append([face_con[iface][0], face_con[iface][1], -1, 0, 0])
                edges.append([face_con[iface][2], face_con[iface][3], -1, 0, 0])
                edges.append([face_con[iface][0], face_con[iface][2], -1, 0, 0])
                edges.append([face_con[iface][1], face_con[iface][3], -1, 0, 0])
            # end for
            edge_dir = np.ones(len(edges), 'intc')
            for iedge in xrange(self.nFace*4):
                if edges[iedge][0] > edges[iedge][1]:
                    temp = edges[iedge][0]
                    edges[iedge][0] = edges[iedge][1]
                    edges[iedge][1] = temp
                    edge_dir[iedge] = -1
                # end if
                edge_hash.append(
                    edges[iedge][0]*4*self.nFace + edges[iedge][1])
            # end for

            edges, edge_link = unique_index(edges, edge_hash)

            self.nEdge = len(edges)
            self.edge_link = np.array(edge_link).reshape((self.nFace, 4))
            self.node_link = np.array(face_con)
            self.edge_dir  = np.array(edge_dir).reshape((self.nFace, 4))

            edge_link_sorted = np.sort(edge_link)
            edge_link_ind    = np.argsort(edge_link)

        elif not coords == None:
            self.nFace = len(coords)
            self.nEnt  = self.nFace
            # We can use the pointReduce algorithim on the nodes
            node_list, node_link = pointReduce(
                coords[:, 0:4, :].reshape((self.nFace*4, 3)), node_tol)
            node_link = node_link.reshape((self.nFace, 4))
          
            # Next Calculate the EDGE connectivity. -- This is Still
            # Brute Force

            edges = []
            midpoints = []
            edge_link = -1*np.ones(self.nFace*4, 'intc')
            edge_dir  = np.zeros((self.nFace, 4), 'intc')

            for iface in xrange(self.nFace):
                for iedge in xrange(4):
                    n1, n2 = nodesFromEdge(iedge)
                    n1 = node_link[iface][n1]
                    n2 = node_link[iface][n2] 
                    midpoint = coords[iface][iedge + 4]
                    if len(edges) == 0:
                        edges.append([n1, n2, -1, 0, 0])
                        midpoints.append(midpoint)
                        edge_link[4*iface + iedge] = 0
                        edge_dir [iface][iedge] = 1
                    else:
                        found_it = False
                        for i in xrange(len(edges)):
                            if [n1, n2] == edges[i][0:2] and n1 != n2:
                                if e_dist(midpoint, midpoints[i]) < edge_tol:
                                    edge_link[4*iface + iedge] = i
                                    edge_dir [iface][iedge] = 1
                                    found_it = True
                                # end if
                            elif [n2, n1] == edges[i][0:2] and n1 != n2:
                                if e_dist(midpoint, midpoints[i]) < edge_tol:
                                    edge_link[4*iface + iedge] = i
                                    edge_dir[iface][iedge] = -1
                                    found_it = True
                                # end if
                            # end if
                        # end for

                        # We went all the way though the list so add
                        # it at end and return index
                        if not found_it:
                            edges.append([n1, n2, -1, 0, 0])
                            midpoints.append(midpoint)
                            edge_link[4*iface + iedge] = i+1
                            edge_dir [iface][iedge] = 1
                    # end if
                # end for
            # end for

            self.nEdge = len(edges)
            self.edge_link = np.array(edge_link).reshape((self.nFace, 4))
            self.node_link = np.array(node_link)
            self.nNode = len(unique(self.node_link.flatten()))
            self.edge_dir = edge_dir

            edge_link_sorted = np.sort(edge_link.flatten())
            edge_link_ind    = np.argsort(edge_link.flatten())

        # end if
            
        # Next Calculate the Design Group Information
        self._calcDGs(edges, edge_link, edge_link_sorted, edge_link_ind)

        # Set the edge ojects
        self.edges = []
        for i in xrange(self.nEdge): # Create the edge objects
            if midpoints: # If they exist
                if edges[i][0] == edges[i][1] and \
                        e_dist(midpoints[i], node_list[edges[i][0]]) < node_tol:
                    self.edges.append(edge(edges[i][0], edges[i][1], 
                                           0, 1, 0, edges[i][2], edges[i][3]))
                else:
                    self.edges.append(edge(edges[i][0], edges[i][1], 
                                           0, 0, 0, edges[i][2], edges[i][3]))
                # end if
            else:
                self.edges.append(edge(edges[i][0], edges[i][1], 
                                       0, 0, 0, edges[i][2], edges[i][3]))
            # end if
        # end for

        return

    def calcGlobalNumberingDummy(self, sizes, surface_list=None):
        '''Internal function to calculate the global/local numbering
        for each surface'''
        for i in xrange(len(sizes)):
            self.edges[self.edge_link[i][0]].N = sizes[i][0]
            self.edges[self.edge_link[i][1]].N = sizes[i][0]
            self.edges[self.edge_link[i][2]].N = sizes[i][1]
            self.edges[self.edge_link[i][3]].N = sizes[i][1]

        if surface_list == None:
            surface_list = range(0, self.nFace)
        # end if
        
        # ----------------- Start of Edge Computation ---------------------
        counter = 0
        g_index = []
        l_index = []

        assert len(sizes) == len(surface_list), 'Error: The list of sizes and \
the list of surfaces must be the same length'

        # Assign unique numbers to the corners -> Corners are indexed
        # sequentially
        node_index = np.arange(self.nNode)
        counter = len(node_index)
        edge_index = [ [] for i in xrange(len(self.edges))]
     
        # Assign unique numbers to the edges

        for ii in xrange(len(surface_list)):
            cur_size = [sizes[ii][0], sizes[ii][0], sizes[ii][1], sizes[ii][1]]
            isurf = surface_list[ii]
            for iedge in xrange(4):
                edge = self.edge_link[ii][iedge]
                    
                if edge_index[edge] == []:# Not added yet
                    if self.edges[edge].degen == 1:
                        # Get the counter value for this "node"
                        index = node_index[self.edges[edge].n1]
                        for jj in xrange(cur_size[iedge]-2):
                            edge_index[edge].append(index)
                        # end for
                    else:
                        for jj in xrange(cur_size[iedge]-2):
                            edge_index[edge].append(counter)
                            counter += 1
                        # end for
                    # end if
                # end if
            # end for
        # end for
     
        g_index = [ [] for i in xrange(counter)] # We must add [] for
                                                 # each global node
        l_index = []

        # Now actually fill everything up

        for ii in xrange(len(surface_list)):
            isurf = surface_list[ii]
            N = sizes[ii][0]
            M = sizes[ii][1]
            l_index.append(-1*np.ones((N, M), 'intc'))
        # end for
        self.l_index = l_index

        return

    def calcGlobalNumbering(self, sizes, surface_list=None):
        '''Internal function to calculate the global/local numbering
        for each surface'''
        for i in xrange(len(sizes)):
            self.edges[self.edge_link[i][0]].N = sizes[i][0]
            self.edges[self.edge_link[i][1]].N = sizes[i][0]
            self.edges[self.edge_link[i][2]].N = sizes[i][1]
            self.edges[self.edge_link[i][3]].N = sizes[i][1]

        if surface_list == None:
            surface_list = range(0, self.nFace)
        # end if
        
        # ----------------- Start of Edge Computation ---------------------
        counter = 0
        g_index = []
        l_index = []

        assert len(sizes) == len(surface_list), 'Error: The list of sizes and \
the list of surfaces must be the same length'

        # Assign unique numbers to the corners -> Corners are indexed
        # sequentially
        node_index = np.arange(self.nNode)
        counter = len(node_index)
        edge_index = [ [] for i in xrange(len(self.edges))]
     
        # Assign unique numbers to the edges

        for ii in xrange(len(surface_list)):
            cur_size = [sizes[ii][0], sizes[ii][0], sizes[ii][1], sizes[ii][1]]
            isurf = surface_list[ii]
            for iedge in xrange(4):
                edge = self.edge_link[ii][iedge]
                    
                if edge_index[edge] == []:# Not added yet
                    if self.edges[edge].degen == 1:
                        # Get the counter value for this "node"
                        index = node_index[self.edges[edge].n1]
                        for jj in xrange(cur_size[iedge]-2):
                            edge_index[edge].append(index)
                        # end for
                    else:
                        for jj in xrange(cur_size[iedge]-2):
                            edge_index[edge].append(counter)
                            counter += 1
                        # end for
                    # end if
                # end if
            # end for
        # end for
     
        g_index = [ [] for i in xrange(counter)] # We must add [] for
                                                 # each global node
        l_index = []

        # Now actually fill everything up

        for ii in xrange(len(surface_list)):
            isurf = surface_list[ii]
            N = sizes[ii][0]
            M = sizes[ii][1]
            l_index.append(-1*np.ones((N, M), 'intc'))

            for i in xrange(N):
                for j in xrange(M):
                    
                    type, edge, node, index = indexPosition2D(i, j, N, M)

                    if type == 0:           # Interior
                        l_index[ii][i, j] = counter
                        g_index.append([[isurf, i, j]])
                        counter += 1
                    elif type == 1:         # Edge
                       
                        if edge in [0, 1]:
                            # Its a reverse dir
                            if self.edge_dir[ii][edge] == -1:
                                cur_index = edge_index[
                                    self.edge_link[ii][edge]][N-i-2]
                            else:  
                                cur_index = edge_index[
                                    self.edge_link[ii][edge]][i-1]
                            # end if
                        else: # edge in [2, 3]
                            # Its a reverse dir
                            if self.edge_dir[ii][edge] == -1: 
                                cur_index = edge_index[
                                    self.edge_link[ii][edge]][M-j-2]
                            else:  
                                cur_index = edge_index[
                                    self.edge_link[ii][edge]][j-1]
                            # end if
                        # end if
                        l_index[ii][i, j] = cur_index
                        g_index[cur_index].append([isurf, i, j])
                            
                    else:                  # Node
                        cur_node = self.node_link[ii][node]
                        l_index[ii][i, j] = node_index[cur_node]
                        g_index[node_index[cur_node]].append([isurf, i, j])
                    # end for
                # end for (j)
            # end for (i)
        # end for (ii)

        # Reorder the indices with a greedy scheme

        new_indices = np.zeros(len(g_index), 'intc')
        new_indices[:] = -1
        new_g_index = [[] for i in xrange(len(g_index))]
        counter = 0

        # Re-order the l_index
        for ii in xrange(len(surface_list)):
            isurf = surface_list[ii]
            N = sizes[ii][0]
            M = sizes[ii][1]
            for i in xrange(N):
                for j in xrange(M):
                    if new_indices[l_index[ii][i, j]] == -1:
                        new_indices[l_index[ii][i, j]] = counter
                        l_index[ii][i, j] = counter 
                        counter += 1
                    else:
                        l_index[ii][i, j] = new_indices[l_index[ii][i, j]]
                    # end if
                # end for
            # end for
        # end for
       
        # Re-order the g_index
        for ii in xrange(len(g_index)):
            isurf = g_index[ii][0][0]
            i     = g_index[ii][0][1]
            j     = g_index[ii][0][2]
            pt = l_index[isurf][i, j]
            new_g_index[pt] = g_index[ii]
            # end for
        # end for
            
        self.nGlobal = len(g_index)
        self.g_index = new_g_index
        self.l_index = l_index
        
        return 

    def getSurfaceFromEdge(self,  edge):
        '''Determine the surfaces and their edge_link index that
        points to edge iedge'''
        # Its not efficient but it works - scales with Nface not constant
        surfaces = []
        for isurf in xrange(self.nFace):
            for iedge in xrange(4):
                if self.edge_link[isurf][iedge] == edge:
                    surfaces.append([isurf, iedge])
                # end if
            # end for
        # end for

        return surfaces

    def makeSizesConsistent(self, sizes, order):
        '''
        Take a given list of [Nu x Nv] for each surface and return
        the sizes list such that all sizes are consistent

        prescedence is given according to the order list: 0 is highest
        prescedence,  1 is next highest ect.
        '''

        # First determine how many "order" loops we have
        nloops = max(order)+1
        edge_number = -1*np.ones(self.nDG, 'intc')
        for iedge in xrange(self.nEdge):
            self.edges[iedge].N = -1
        # end for
    
        for iloop in xrange(nloops):
            for iface in xrange(self.nFace):
                if order[iface] == iloop: # Set this edge
                    for iedge in xrange(4):
                        dg = self.edges[self.edge_link[iface][iedge]].dg
                        if edge_number[dg] == -1:
                            if iedge in [0, 1]:
                                edge_number[dg] = sizes[iface][0]
                            else:
                                edge_number[dg] = sizes[iface][1]
                            # end if
                        # end if
                    # end if
                # end for
            # end for
        # end for

        # Now re-populate the sizes:
        for iface in xrange(self.nFace):
            for i in [0, 1]:
                dg = self.edges[self.edge_link[iface][i*2]].dg
                sizes[iface][i] = edge_number[dg]
            # end for
        # end for

        # And return the number of elements on each actual edge
        nEdge = []
        for iedge in xrange(self.nEdge):
            self.edges[iedge].N = edge_number[self.edges[iedge].dg]
            nEdge.append(edge_number[self.edges[iedge].dg])
        # end if

        return sizes, nEdge

class BlockTopology(topology):
    '''
    See Topology base class for more information
    '''

    def __init__(self, coords=None, node_tol=1e-4, edge_tol=1e-4, file=None):
        '''Initialize the class with data required to compute the topology'''
        
        topology.__init__(self)
        self.mNodeEnt = 8
        self.mEdgeEnt = 12
        self.mFaceEnt = 6
        self.mVolEnt  = 1
        self.topo_type = 'volume'
        self.g_index = None
        self.l_index = None
        self.nGlobal = None
        if file != None:
            self.readConnectivity(file)
            return
        # end if

        coords = np.atleast_2d(coords)
        nVol = len(coords)

        if coords.shape[1] == 8: # Just the corners are given --- Just
                                 # put in np.zeros for the edge and face
                                 # mid points
            temp = np.zeros((nvol, (8 + 12 + 6), 3))
            temp[:, 0:8, :] = coords
            coords = temp.copy()
        # end if

        # ----------------------------------------------------------
        #                     Unique Nodes
        # ----------------------------------------------------------

        # Do the pointReduce Agorithm on the corners
        un, node_link = pointReduce(coords[:, 0:8, :].reshape((nVol*8, 3)))
        node_link = node_link.reshape((nVol, 8))
         
        # ----------------------------------------------------------
        #                     Unique Edges
        # ----------------------------------------------------------
 
        # Now determine the unique edges:
        edge_objs = []
        orig_edges = []
        for ivol in xrange(nVol):
            for iedge in xrange(12):
                # Node number on volume
                n1, n2 = nodesFromEdge(iedge)

                # Actual Global Node Number
                n1 = node_link[ivol][n1]
                n2 = node_link[ivol][n2]

                # Midpoint
                midpoint = coords[ivol][iedge + 8]

                # Sorted Nodes:
                ns = sorted([n1, n2])
        
                # Append the new edge_cmp Object
                edge_objs.append(edge_cmp_object(
                        ns[0], ns[1], n1, n2, midpoint, edge_tol))

                # Keep track of original edge orientation---needed for
                # face direction
                orig_edges.append([n1, n2])
            # end for
        # end for
                    
        # Generate unique set of edges
        unique_edge_objs,  edge_link = unique_index(edge_objs)

        edge_dir = []
        for i in xrange(len(edge_objs)): # This is nVol * 12
            edge_dir.append(edgeOrientation(
                    orig_edges[i], unique_edge_objs[edge_link[i]].nodes))
        # end for

        # ----------------------------------------------------------
        #                     Unique Faces
        # ----------------------------------------------------------

        face_objs = []
        orig_faces = []
        for ivol in xrange(nVol):
            for iface in xrange(6):
                # Node number on volume
                n1, n2, n3, n4 = nodesFromFace(iface)

                # Actual Global Node Number
                n1 = node_link[ivol][n1]
                n2 = node_link[ivol][n2] 
                n3 = node_link[ivol][n3]
                n4 = node_link[ivol][n4] 
                
                # Midpoint --> May be [0, 0, 0] -> This is OK
                midpoint = coords[ivol][iface + 8 + 12]
                
                # Sort the nodes before they go into the faceObject
                ns = sorted([n1, n2, n3, n4])
                face_objs.append(face_cmp_object(ns[0], ns[1], ns[2], ns[3], 
                                                 n1, n2, n3, n4, 
                                                 midpoint, 1e-4))
                # Keep track of original face orientation---needed for
                # face direction
                orig_faces.append([n1, n2, n3, n4])
            # end for
        # end for
                    
        # Generate unique set of faces
        unique_face_objs, face_link = unique_index(face_objs)

        face_dir = []
        for i in xrange(len(face_objs)): # This is nVol * 12
            face_dir.append(faceOrientation(
                    unique_face_objs[face_link[i]].nodes, orig_faces[i]))
            uEdge = face_link[i]
        # end for

        # --------- Set the Requried Data for this class ------------
        self.nNode = len(un)
        self.nEdge = len(unique_edge_objs)
        self.nFace = len(unique_face_objs)
        self.nVol  = len(coords)
        self.nEnt  = self.nVol

        self.node_link = node_link
        self.edge_link = np.array(edge_link).reshape((nVol, 12))
        self.face_link = np.array(face_link).reshape((nVol, 6))

        self.edge_dir  = np.array(edge_dir).reshape((nVol, 12))
        self.face_dir  = np.array(face_dir).reshape((nVol, 6))

        # Next Calculate the Design Group Information
        edge_link_sorted = np.sort(edge_link.flatten())
        edge_link_ind    = np.argsort(edge_link.flatten())

        ue = []
        for i in xrange(len(unique_edge_objs)):
            ue.append([unique_edge_objs[i].nodes[0], 
                       unique_edge_objs[i].nodes[1], -1, 0, 0])
        # end for

        self._calcDGs(ue, edge_link, edge_link_sorted, edge_link_ind)
        
        # Set the edge ojects
        self.edges = []
        for i in xrange(self.nEdge): # Create the edge objects
            self.edges.append(edge(
                    ue[i][0], ue[i][1], 0, 0, 0, ue[i][2], ue[i][3]))
        # end for

        return

    def calcGlobalNumbering(self, sizes=None, volume_list=None, 
                            greedyReorder=False):
        '''Internal function to calculate the global/local numbering
        for each volume'''

        if sizes != None:
            for i in xrange(len(sizes)):
                self.edges[self.edge_link[i][0]].N = sizes[i][0]
                self.edges[self.edge_link[i][1]].N = sizes[i][0]
                self.edges[self.edge_link[i][4]].N = sizes[i][0]
                self.edges[self.edge_link[i][5]].N = sizes[i][0]

                self.edges[self.edge_link[i][2]].N = sizes[i][1]
                self.edges[self.edge_link[i][3]].N = sizes[i][1]
                self.edges[self.edge_link[i][6]].N = sizes[i][1]
                self.edges[self.edge_link[i][7]].N = sizes[i][1]

                self.edges[self.edge_link[i][8]].N  = sizes[i][2]
                self.edges[self.edge_link[i][9]].N  = sizes[i][2]
                self.edges[self.edge_link[i][10]].N = sizes[i][2]
                self.edges[self.edge_link[i][11]].N = sizes[i][2]
            # end for
        else: # N is already set in the edge objects, use them
            sizes = np.zeros((self.nVol, 3), 'intc')
            for ivol in xrange(self.nVol):
                sizes[ivol][0] = self.edges[self.edge_link[ivol][0]].N
                sizes[ivol][1] = self.edges[self.edge_link[ivol][2]].N
                sizes[ivol][2] = self.edges[self.edge_link[ivol][8]].N
            # end for
        # end if

        if volume_list == None:
            volume_list = range(0, self.nVol)
        # end if
        
        # ----------------- Start of Edge Computation ---------------------
        counter = 0
        g_index = []
        l_index = []
    
        assert len(sizes) == len(volume_list), 'Error: The list of sizes and \
the list of volumes must be the same length'

        # Assign unique numbers to the corners -> Corners are indexed
        # sequentially
        node_index = np.arange(self.nNode)
        counter = len(node_index)

        edge_index = [ np.empty((0), 'intc') for i in xrange(self.nEdge)]
        face_index = [ np.empty((0, 0), 'intc') for i in xrange(self.nFace)]
        # Assign unique numbers to the edges

        for ii in xrange(len(volume_list)):
            cur_size_e = [sizes[ii][0], sizes[ii][0], sizes[ii][1], 
                          sizes[ii][1], sizes[ii][0], sizes[ii][0], 
                          sizes[ii][1], sizes[ii][1], sizes[ii][2], 
                          sizes[ii][2], sizes[ii][2], sizes[ii][2]]  

            cur_size_f = [[sizes[ii][0], sizes[ii][1]], 
                          [sizes[ii][0], sizes[ii][1]], 
                          [sizes[ii][1], sizes[ii][2]], 
                          [sizes[ii][1], sizes[ii][2]], 
                          [sizes[ii][0], sizes[ii][2]], 
                          [sizes[ii][0], sizes[ii][2]]]

            ivol = volume_list[ii]
            for iedge in xrange(12):
                edge = self.edge_link[ii][iedge]
                if edge_index[edge].shape == (0, ):# Not added yet
                    edge_index[edge] = np.resize(
                        edge_index[edge], cur_size_e[iedge]-2)
                    if self.edges[edge].degen == 1:
                        # Get the counter value for this "node"
                        index = node_index[self.edges[edge].n1]
                        for jj in xrange(cur_size_e[iedge]-2):
                            edge_index[edge][jj] = index
                        # end for
                    else:
                        for jj in xrange(cur_size_e[iedge]-2):
                            edge_index[edge][jj] = counter
                            counter += 1
                        # end for
                    # end if
                # end if
            # end for
            for iface in xrange(6):
                face = self.face_link[ii][iface]
                if face_index[face].shape == (0, 0):
                    face_index[face] = np.resize(face_index[face], 
                                               [cur_size_f[iface][0]-2, 
                                                cur_size_f[iface][1]-2])
                    for iii in xrange(cur_size_f[iface][0]-2):
                        for jjj in xrange(cur_size_f[iface][1]-2):
                            face_index[face][iii, jjj] = counter
                            counter += 1
                        # end for
                    # end for
                # end if
            # end for
        # end for (volume list)

        g_index = [ [] for i in xrange(counter)] # We must add [] for
                                                 # each global node
        l_index = []

        def addNode(i, j, k, N, M, L):
            type, number, index1, index2 = indexPosition3D(i, j, k, N, M, L)
            
            if type == 1:         # Face 

                if number in [0, 1]:
                    icount = i;imax = N
                    jcount = j;jmax = M
                elif number in [2, 3]:
                    icount = j;imax = M
                    jcount = k;jmax = L
                elif number in [4, 5]:
                    icount = i;imax = N
                    jcount = k;jmax = L
                # end if

                if self.face_dir[ii][number] == 0:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        icount-1, jcount-1]
                elif self.face_dir[ii][number] == 1:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        imax-icount-2, jcount-1]
                elif self.face_dir[ii][number] == 2:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        icount-1, jmax-jcount-2]
                elif self.face_dir[ii][number] == 3:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        imax-icount-2, jmax-jcount-2]
                elif self.face_dir[ii][number] == 4:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        jcount-1, icount-1]
                elif self.face_dir[ii][number] == 5:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        jmax-jcount-2, icount-1]
                elif self.face_dir[ii][number] == 6:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        jcount-1, imax-icount-2]
                elif self.face_dir[ii][number] == 7:
                    cur_index = face_index[
                        self.face_link[ii][number]][
                        jmax-jcount-2, imax-icount-2]
                    
                l_index[ii][i, j, k] = cur_index
                g_index[cur_index].append([ivol, i, j, k])
                            
            elif type == 2:         # Edge
                        
                if number in [0, 1, 4, 5]:
                    if self.edge_dir[ii][number] == -1: # Its a reverse dir
                        cur_index = \
                            edge_index[self.edge_link[ii][number]][N-i-2]
                    else:  
                        cur_index = \
                            edge_index[self.edge_link[ii][number]][i-1]
                    # end if
                elif number in [2, 3, 6, 7]:
                    if self.edge_dir[ii][number] == -1: # Its a reverse dir
                        cur_index = \
                            edge_index[self.edge_link[ii][number]][M-j-2]
                    else:  
                        cur_index = \
                            edge_index[self.edge_link[ii][number]][j-1]
                    # end if
                elif number in [8, 9, 10, 11]:
                    if self.edge_dir[ii][number] == -1: # Its a reverse dir
                        cur_index = \
                            edge_index[self.edge_link[ii][number]][L-k-2]
                    else:  
                        cur_index = \
                            edge_index[self.edge_link[ii][number]][k-1]
                    # end if
                # end if
                l_index[ii][i, j, k] = cur_index
                g_index[cur_index].append([ivol, i, j, k])
                            
            elif type == 3:                  # Node
                cur_node = self.node_link[ii][number]
                l_index[ii][i, j, k] = node_index[cur_node]
                g_index[node_index[cur_node]].append([ivol, i, j, k])
            # end if type
        # end for (volume loop)
        
        # Now actually fill everything up
        for ii in xrange(len(volume_list)):
            ivol = volume_list[ii]
            N = sizes[ii][0]
            M = sizes[ii][1]
            L = sizes[ii][2]
            l_index.append(-1*np.ones((N, M, L), 'intc'))

            # DO the 6 planes
            for k in [0, L-1]:
                for i in xrange(N):
                    for j in xrange(M):
                        addNode(i, j, k, N, M, L)
            for j in [0, M-1]:
                for i in xrange(N):
                    for k in xrange(1, L-1):
                        addNode(i, j, k, N, M, L)

            for i in [0, N-1]:
                for j in xrange(1, M-1):
                    for k in xrange(1, L-1):
                        addNode(i, j, k, N, M, L)
            
        # end for (ii)

        # Add the remainder
        for ii in xrange(len(volume_list)):
            ivol = volume_list[ii]
            N = sizes[ii][0]
            M = sizes[ii][1]
            L = sizes[ii][2]

            NN = sizes[ii][0]-2
            MM = sizes[ii][1]-2
            LL = sizes[ii][2]-2

            to_add = NN*MM*LL
            
            l_index[ii][1:N-1,1:M-1,1:L-1] = \
                np.arange(counter,counter+to_add).reshape((NN,MM,LL))

            counter = counter + to_add
            A = np.zeros((to_add,1,4),'intc')
            A[:,0,0] = ivol
            A[:,0,1:] = np.mgrid[1:N-1,1:M-1,1:L-1].transpose(
                (1,2,3,0)).reshape((to_add,3))
            
            g_index.extend(A)

        # end for

        # Set the following as atributes
        self.nGlobal = len(g_index)
        self.g_index = g_index
        self.l_index = l_index

        if greedyReorder:

            # Reorder the indices with a greedy scheme
            new_indices = np.zeros(len(g_index), 'intc')
            new_indices[:] = -1
            new_g_index = [[] for i in xrange(len(g_index))]
            counter = 0

            # Re-order the l_index
            for ii in xrange(len(volume_list)):
                ivol = volume_list[ii]
                N = sizes[ii][0]
                M = sizes[ii][1]
                L = sizes[ii][2]
                for i in xrange(N):
                    for j in xrange(M):
                        for k in xrange(L):
                            if new_indices[l_index[ii][i, j, k]] == -1:
                                new_indices[l_index[ii][i, j, k]] = counter
                                l_index[ii][i, j, k] = counter 
                                counter += 1
                            else:
                                l_index[ii][i, j, k] = \
                                    new_indices[l_index[ii][i, j, k]]
                            # end if
                        # end for
                    # end for
                # end for
            # end for

            # Re-order the g_index
            for ii in xrange(len(g_index)):
                ivol  = g_index[ii][0][0]
                i     = g_index[ii][0][1]
                j     = g_index[ii][0][2]
                k     = g_index[ii][0][3]
                pt = l_index[ivol][i, j, k]
                new_g_index[pt] = g_index[ii]
                # end for
            # end for
            
            self.g_index = new_g_index
            self.l_index = l_index
        # end if (greedy reorder)

        return 

    def reOrder(self, reOrderList):
        '''This function takes as input a permutation list which is
        used to reorder the entities in the topology object'''
        
        # Class atributates that possible need to be modified
        for i in xrange(8):
            self.node_link[:, i] = self.node_link[:, i].take(reOrderList)
        # end for

        for i in xrange(12):
            self.edge_link[:, i] = self.edge_link[:, i].take(reOrderList)
            self.edge_dir[:, i] = self.edge_dir[:, i].take(reOrderList)

        # end for

        for i in xrange(6):
            self.face_link[:, i] = self.face_link[:, i].take(reOrderList)
            self.face_dir[:, i] = self.face_dir[:, i].take(reOrderList)
        # end for
        
        return

class edge(object):
    '''A class for edge objects'''

    def __init__(self, n1, n2, cont, degen, intersect, dg, N):
        self.n1        = n1        # Integer for node 1
        self.n2        = n2        # Integer for node 2
        self.cont      = cont      # Integer: 0 for c0 continuity, 1
                                   # for c1 continuity
        self.degen     = degen     # Integer: 1 for degenerate, 0 otherwise
        self.intersect = intersect # Integer: 1 for an intersected
                                   # edge, 0 otherwise
        self.dg        = dg        # Design Group index
        self.N         = N         # Number of control points for this edge
        
    def write_info(self, i, handle):
        handle.write('  %5d        | %5d | %5d | %5d | %5d | %5d |\
  %5d |  %5d |\n'\
                     %(i, self.n1, self.n2, self.cont, self.degen, 
                       self.intersect, self.dg, self.N))


class edge_cmp_object(object):
    '''A temporary class for sorting edge objects'''

    def __init__(self, n1, n2, n1o, n2o, mid_pt, tol):
        self.n1 = n1
        self.n2 = n2
        self.nodes = [n1o, n2o]
        self.mid_pt = mid_pt
        self.tol = tol

    def __repr__(self):
        return 'Node1: %d Node2: %d Mid_pt: %f %f %f'% (
            self.n1, self.n2, self.mid_pt[0], self.mid_pt[1], self.mid_pt[2])

    def __cmp__(self, other):
        # This function should return :
        # -1 if self < other
        #  0 if self == other
        #  1 if self > other

        # Basically we want to make three comparisons: n1, n2 and the
        # mid_pt Its (substantially) faster if we break before all 3
        # comparisons are done
        
        n1_cmp = cmp(self.n1, other.n1)
        if n1_cmp: # n1_cmp is non-zero so return with the result
            return n1_cmp

        n2_cmp = cmp(self.n2, other.n2)

        if n2_cmp: # n2_cmp is non-zero so return 
            return n2_cmp

        x_cmp = cmp(self.mid_pt[0], other .mid_pt[0])
        y_cmp = cmp(self.mid_pt[1], other .mid_pt[1])
        z_cmp = cmp(self.mid_pt[2], other .mid_pt[2])
        
        if e_dist(self.mid_pt, other.mid_pt) < self.tol:
            mid_cmp = 0
        else:
            mid_cmp = x_cmp or y_cmp or z_cmp
        # end if

        return mid_cmp

# EXPLICT FORMULATION
#         if self.n1 < other.n1:
#             return -1
#         elif self.n1 > other.n1:
#             return 1
#         else: # self.n1 and other .n1 are the same
#             if self.n2 < other.n2:
#                 return -1
#             elif self.n2 > other.n2:
#                 return 1
#             else: # n1 and n2 are equal:
                
#                 # Next we will sort by x, y and then z coordiante
                
#                 if e_dist(self.mid_pt, other.mid_pt) < self.tol:
#                     return 0 # Object are the same
#                 else:
                    
#                     if self.mid_pt[0] < other.mid_pt[0]:
#                         return -1
#                     elif self.mid_pt[0] > other.mid_pt[0]:
#                         return 1
#                     else:
#                         if self.mid_pt[1] < other.mid_pt[1]:
#                             return -1
#                         elif self.mid_pt[1] > other.mid_pt[1]:
#                             return 1
#                         else:
#                             if self.mid_pt[2] < other.mid_pt[2]:
#                                 return -1
#                             elif self.mid_pt[2] > other.mid_pt[2]:
#                                 return 1
#                             # end if
#                         # end if
#                     # end if
#                 # end if
#             # end if
#         # end if

class face_cmp_object(object):
    '''A temporary class for sorting edge objects'''

    def __init__(self, n1, n2, n3, n4, n1o, n2o, n3o, n4o, mid_pt, tol):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.nodes = [n1o, n2o, n3o, n4o]
        self.mid_pt = mid_pt
        self.tol = tol

    def __repr__(self):
        return 'Node1: %d Node2: %d Mid_pt: %f %f %f'% (
            self.n1, self.n2, self.mid_pt[0], self.mid_pt[1], self.mid_pt[2])

    def __cmp__(self, other):
        # This function should return :
        # -1 if self < other
        #  0 if self == other
        #  1 if self > other

        # Basically we want to make three comparisons: n1, n2, n3, n4 and the
        # mid_pt Its (substantially) faster if we break before all 
        # comparisons are done
        
        n1_cmp = cmp(self.n1, other.n1)
        if n1_cmp: # n1_cmp is non-zero so return with the result
            return n1_cmp

        n2_cmp = cmp(self.n2, other.n2)

        if n2_cmp: # n2_cmp is non-zero so return 
            return n2_cmp

        n3_cmp = cmp(self.n3, other.n3)
        if n3_cmp: # n3_cmp is non-zero so return
            return n3_cmp

        n4_cmp = cmp(self.n4, other.n4)
        if n4_cmp: # n4_cmp is non-zero so return
            return n4_cmp

        # Finally do mid-pt calc
        x_cmp = cmp(self.mid_pt[0], other .mid_pt[0])
        y_cmp = cmp(self.mid_pt[1], other .mid_pt[1])
        z_cmp = cmp(self.mid_pt[2], other .mid_pt[2])
        
        if e_dist(self.mid_pt, other.mid_pt) < self.tol:
            mid_cmp = 0
        else:
            mid_cmp = x_cmp or y_cmp or z_cmp
        # end if

        return mid_cmp



# --------------------------------------------------------------
#                Array Rotation and Flipping Functions
# --------------------------------------------------------------

def rotateCCW(input):
    '''Rotate the input array 90 degrees CCW'''
    rows = input.shape[0]
    cols = input.shape[1]
    output = np.empty([cols, rows], input.dtype)
 
    for row in xrange(rows):
        for col in xrange(cols):
            output[cols-col-1][row] = input[row][col]
        # end for
    # end for

    return output

def rotateCW(input):
    '''Rotate the input array 90 degrees CW'''
    rows = input.shape[0]
    cols = input.shape[1]
    output = np.empty([cols, rows], input.dtype)
 
    for row in xrange(rows):
        for col in xrange(cols):
            output[col][rows-row-1] = input[row][col]
        # end for
    # end for

    return output

def reverseRows(input):
    '''Flip Rows (horizontally)'''
    rows = input.shape[0]
    cols = input.shape[1]
    output = np.empty([rows, cols], input.dtype)
    for row in xrange(rows):
        output[row] = input[row][::-1].copy()
    # end for

    return output

def reverseCols(input):
    '''Flip Cols (vertically)'''
    rows = input.shape[0]
    cols = input.shape[1]
    output = np.empty([rows, cols], input.dtype)
    for col in xrange(cols):
        output[:, col] = input[:, col][::-1].copy()
    # end for

    return output

def getBiLinearMap(edge0, edge1, edge2, edge3):
    '''Get the UV coordinates on a square defined from spacing on the edges'''

    assert len(edge0)==len(edge1), 'Error, getBiLinearMap:\
 The len of edge0 and edge1 are not the same'
    assert len(edge2)==len(edge3), 'Error, getBiLinearMap:\
 The len of edge2 and edge3 are no the same'

    N = len(edge0)
    M = len(edge2)

    UV = np.zeros((N, M, 2))

    UV[:, 0, 0] = edge0
    UV[:, 0, 1] = 0.0

    UV[:, -1, 0] = edge1
    UV[:, -1, 1] = 1.0

    UV[0, :, 0] = 0.0
    UV[0, :, 1] = edge2

    UV[-1, :, 0] = 1.0
    UV[-1, :, 1] = edge3
   
    for i in xrange(1, N-1):
        x1 = edge0[i]
        y1 = 0.0

        x2 = edge1[i]
        y2 = 1.0

        for j in xrange(1, M-1):
            x3 = 0
            y3 = edge2[j]

            x4 = 1.0
            y4 = edge3[j]

            UV[i, j] = calc_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
            
        # end for
    # end for
  
    return UV

def calc_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    # Calc the intersection between two line segments defined by
    # (x1,y1) to (x2,y2) and (x3,y3) to (x4,y4)

    denom = (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)
    ua = ((x4-x3)*(y1-y3)-(y4-y3)*(x1-x3))/denom
    xi = x1 + ua*(x2-x1)
    yi = y1 + ua*(y2-y1)

    return xi, yi

def checkInput(input, input_name, data_type, data_rank, data_shape=None):
    '''This is a generic function to check the data type and sizes of
    inputs in functions where the user must supply proper
    values. Since Python does not do type checking on Inputs, this is
    required

    input: The input argument

    input_name: A stringo with the arguments name to be used in an 
                output error message

    data_type: The requested numpy data type. Up-casting will be done
               automatically, warnings will be issued if downcasting or 
               doing a float to int conversion etc. A value of None 
               indicates the data_type is not be checked.

    rank     : The desired rank of the array. It is 0 for scalars, 1 for 
               vectors, 2 for matrices etc. 

    data_shape: The required shape of the data. A value of 0 indicates
                a scalar. 1D arrays are specified with a value =>
                1. Higher dimensional arrays sizes are specified with
                a list such as [dim0,dim1,...,dimN]. A value of None
                indicates the data shape is not to be checked
          
    Output : Returns the input value iff it conforms to the specified 
             data_type and data_shape. Execption is raised otherwise. 
             
''' 

    # Checking the depth is the first and easiest thing to do.
    rank = checkRank(input)
    if not(rank == data_rank):
        if data_rank == 0:
            mpiPrint('Error: \'%s\' must be a scalar, rank=0.\
 Input of rank %d was given.'%(input_name, rank))
            sys.exit(0)
        elif data_rank == 1:
            mpiPrint('Error: \'%s\' must be a vector, rank=1.\
 Input of rank %d was given.'%(input_name, rank))
            sys.exit(0)
        elif data_rank == 2:
            mpiPrint('Error: \'%s\' must be a matrix,  rank=2.\
 Input of rank %d was given.'%(input_name, rank))
            sys.exit(0)
        else:
            mpiPrint('Error: \'%s\' must be of rank %d.\
 Input of rank %d was given.'%(input_name, data_rank, rank))
            sys.exit(0)
        # end if
    # end if

    # Now we know the rank is what we expect it to be

    if rank == 0: #Scalar Case
        if data_type == None: # No need to check type and data_shape
                              # is irrelevant
            return input
        # end if

        input_type = type(input)

        if data_type == complex: # We can upcast-ANYthing to complex
            input = complex(input)
        elif data_type == float:
            if isinstance(input, complex):
                mpiPrint('Error: \'%s\' must be a given a \'float\' value,\
 not a \'%s\' value'%(input_name, input_type.__name__))
                sys.exit(0)
            else:
                input = float(input)
            # end if
        elif data_type == int:
            if isinstance(input, (complex, float)):
                mpiPrint('Error: \'%s\' must be a given a \'int\' value,\
 not a \'%s\' value'%(input_name, input_type.__name__))
                sys.exit(0)
            else:
                input = int(input)
            # end if
        elif data_type == bool:
            if isinstance(input, (complex, float, int)):
                mpiPrint('Error: \'%s\' must be a given a \'bool\' value,\
 not a \'%s\' value'%(input_name, input_type.__name__))
                sys.exit(0)
            else:
                input = bool(input)
            # end if
        # end if

        return input
    else: # We have array-like objects
        try:
            input = np.array(input)
        except:
            mpiPrint('Error: Rank>1 object must be cast-able to\
 numpy array for checkInput to work')
        # end try

        if not(data_type == None): # Now check the data type
            if rank == 1: 
                test_val = input[0]
            if rank == 2: 
                test_val = input[0][0]
            if rank == 3: 
                test_val = input[0][0][0]
            if rank == 4: 
                test_val = input[0][0][0][0]
            if rank == 5: 
                test_val = input[0][0][0][0][0]

            input_type = type(test_val)

            if data_type == complex: # We can upcast-ANYthing to complex
                input = input.astype('D')
            elif data_type == float:
                if isinstance(test_val, complex):
                    mpiPrint('Error: \'%s\' must be of type \'float\',\
 not type \'%s\'.'%(input_name, input_type.__name__))
                    sys.exit(0)
                else:
                    input = input.astype('d')
                # end if
            elif data_type == int:
                if isinstance(test_val, (complex, float)):
                    mpiPrint('Error: \'%s\' must be of type \'int\',\
 not type \'%s\'.'%(input_name, input_type.__name__))
                    sys.exit(0)
                else:
                    input = input.astype('intc')
                # end if
            elif data_type == bool:
                if isinstance(test_val, (complex, float, int)):
                    mpiPrint('Error: \'%s\' must be of type \'bool\',\
 not type \'%s\'.'%(input_name, input_type.__name__))
                    sys.exit(0)
                else:
                    input = input.astype('bool')
                # end if
            # end if
        # end if

        if not(data_shape) == None:
            # Check the size of each rank
            if isinstance(data_shape, int): # Make sure data_shape is iterable
                data_shape = np.array([data_shape])
            # end if

            array_shape = input.shape
            for irank in xrange(rank):
                if not(array_shape[irank] == data_shape[irank]):
                    mpiPrint('Error: \'%s\' must have a length of %d\
 in rank %d, not %d.'% (input_name, data_shape[irank], irank, 
                        array_shape[irank]))
                    sys.exit(0)
                # end if
            # end for
        # end if

        return input # If we made it to the end, just return input
    # end if

def fill_knots(t, k, level):
    t = t[k-1:-k+1] # Strip out the np.zeros
    new_t = np.zeros(len(t) + (len(t)-1)*level)
    start = 0 
    for i in xrange(len(t)-1):
        new_t[start:start+level+2] = np.linspace(t[i], t[i+1], level+2)
        start += level + 1
    # end for
    return new_t

def projectNode(pt, up_vec, p0, v1, v2):
    '''
    Project a point pt onto a triagnulated surface and return two
    intersections.

    pt: The initial point
    up_vec: The vector pointing in the search direction
    p0: A numpy array of triangle origins
    v1: A numpy array of the first triangle vectors
    v2: A numpy array of the second triangle vectors
    '''

    # Get the bounds of the geo object so we know what to scale by
    import pySpline
    fail = 0
    if p0.shape[0] == 0:
        fail = 2
        return None, None, fail

    sol, n_sol = pySpline.pyspline.line_plane(pt, up_vec, p0.T, v1.T, v2.T)
    sol = sol.T

    if n_sol == 0:
        fail = 2
        return None, None, fail
    elif n_sol == 1:
        fail = 1
        return sol[0, 3:6],  None,  fail
    elif n_sol == 2:
        fail = 0
        # Determine the 'top' and 'bottom' solution
        first  = sol[0, 3:6]
        second = sol[1, 3:6]

        if np.dot(first - pt, up_vec) >= np.dot(second - pt, up_vec):
            return first, second, fail
        else:
            return second, first, fail
    else:
        # This just returns the two points with the minimum absolute 
        # distance to the points that have been found.
        fail = -1

        pmin = abs(np.dot(sol[:n_sol, 3:6] - pt, up_vec))
        min_index = np.argsort(pmin)
        
        return sol[min_index[0], 3:6], sol[min_index[1], 3:6], fail

def projectNodePosOnly(pt, up_vec, p0, v1, v2):
    '''
    Project a point pt onto a triagnulated surface and the solution
    that is the closest in the positive direction (as defined by
    up_vec).

    pt: The initial point
    up_vec: The vector pointing in the search direction
    p0: A numpy array of triangle origins
    v1: A numpy array of the first triangle vectors
    v2: A numpy array of the second triangle vectors
    '''

    # Get the bounds of the geo object so we know what to scale by
    import pySpline
    fail = 0
    if p0.shape[0] == 0:
        fail = 1
        return None, fail

    sol, n_sol = pySpline.pyspline.line_plane(pt, up_vec, p0.T, v1.T, v2.T)
    sol = sol.T

    if n_sol == 0:
        fail = 1
        return None, fail
    elif n_sol >= 1:
        # Find the least positve solution
        min_index = -1
        d = 0.0
        for k in xrange(n_sol):
            dn = np.dot(sol[k, 3:6] - pt, up_vec)
            if dn >= 0.0 and (min_index == -1 or dn < d):
                min_index = k
                d = dn
        
        if min_index >= 0:
            return sol[min_index, 3:6], fail

    fail = 1
    return None, fail


def tfi_2d(e0, e1, e2, e3):
    # Input
    # e0: Nodes along edge 0. Size Nu x 3
    # e1: Nodes along edge 1. Size Nu x 3
    # e0: Nodes along edge 2. Size Nv x 3
    # e1: Nodes along edge 3. Size Nv x 3
    import pySpline
    try:
        X = pySpline.pyspline.tfi2d(e0.T, e1.T, e2.T, e3.T).T
    except:
     
        Nu = len(e0)
        Nv = len(e2)
        assert Nu == len(e1), 'Number of nodes on edge0 and edge1\
 are not the same, %d %d'%(len(e0), len(e1))
        assert Nv == len(e3), 'Number of nodes on edge2 and edge3\
 are not the same, %d %d'%(len(e2), len(e3))

        U = np.linspace(0, 1, Nu)
        V = np.linspace(0, 1, Nv)

        X = np.zeros((Nu, Nv, 3))

        for i in xrange(Nu):
            for j in xrange(Nv):
                X[i, j] = (1-V[j])*e0[i] + V[j]*e1[i] +\
                    (1-U[i])*e2[j] + U[i]*e3[j] - \
                    (U[i]*V[j]*e1[-1] + U[i]*(1-V[j])*e0[-1] +\
                         V[j]*(1-U[i])*e1[0] + (1-U[i])*(1-V[j])*e0[0])
            # end for
        # end for
    # end try

    return X

def linear_edge(pt1, pt2, N):
    # Return N points along line from pt1 to pt2
    pts = np.zeros((N, 3))

    for i in xrange(N):
        pts[i] = float(i)/(N-1)*(pt2-pt1) + pt1
    return pts

def checkRank(input):
    if not(hasattr(input, '__iter__')):
        return 0
    else:
        return 1 + checkRank(input[0])

def split_quad(e0, e1, e2, e3, alpha, beta, N_O):
    # This function takes the coordinates of a quad patch, and
    # creates an O-grid inside the quad making 4 quads and leaving
    # a hole in the center whose size is determined by alpha and
    # beta

    # Input                        Output 
    #       2             3        2      e1     3 
    #       +-------------+        +-------------+
    #       |             |        |\           /|
    #       |             |        | \c2  P1 c3/ |
    #       |             |        |  \       /  |
    #       |             |        |   \6   7/   |
    #       |             |        |    \***/    |
    #       |             |     e2 | P2 *   * P3 | e3
    #       |             |        |    /***\    |
    #       |             |        |   / 4  5\   |
    #       |             |        |  /       \  |
    #       |             |        | /c0 P0  c1\ |
    #       |             |        |/           \|
    #       +-------------+        +-------------+
    #       0             1        0     e0      1

    # Input:
    # e0: points along edge0
    # e1: points along edge1
    # e2: points along edge2
    # e3: points along edge3
    # alpha: Fraction of hole covered by u-direction
    # beta : Fraction of hole covered by v-direction

    # Makeing the assumption each edge is fairly straight
    Nu = len(e0)
    Nv = len(e2)

    # Corners of patch
    pts = np.zeros((4, 3))
    pts[0] = e0[0]
    pts[1] = e0[-1]
    pts[2] = e1[0]
    pts[3] = e1[-1]

    # First generate edge lengths
    l = np.zeros(4)
    l[0] = e_dist(pts[0], pts[1])
    l[1] = e_dist(pts[2], pts[3])
    l[2] = e_dist(pts[0], pts[2])
    l[3] = e_dist(pts[1], pts[3])

    # Vector along edges 0->3
    vec = np.zeros((4, 3))
    vec[0] = pts[1]-pts[0]
    vec[1] = pts[3]-pts[2]
    vec[2] = pts[2]-pts[0]
    vec[3] = pts[3]-pts[1]

    U = 0.5*(vec[0]+vec[1])
    V = 0.5*(vec[2]+vec[3])
    u = U/np.linalg.norm(U)
    v = V/np.linalg.norm(V)

    mid  = np.average(pts, axis=0)

    u_bar = 0.5*(l[0]+l[1])*alpha
    v_bar = 0.5*(l[2]+l[3])*beta

    aspect = u_bar/v_bar
   
    if aspect < 1: # its higher than wide, logically roate the element
        v, u = u, -v
        v_bar, u_bar = u_bar, v_bar
        alpha, beta = beta, alpha
        Nv, Nu = Nu, Nv

        E0 = e2[::-1, :].copy()
        E1 = e3[::-1, :].copy()
        E2 = e1.copy()
        E3 = e0.copy()

        #Also need to permute points
        PTS = np.zeros((4, 3))
        PTS[0] = pts[2].copy()
        PTS[1] = pts[0].copy()
        PTS[2] = pts[3].copy()
        PTS[3] = pts[1].copy()
    else:
        E0 = e0.copy()
        E1 = e1.copy()
        E2 = e2.copy()
        E3 = e3.copy()
        PTS = pts.copy()
    # end if

    rect_corners = np.zeros((4, 3))

    # These are the output pactch object
    P0 = np.zeros((Nu, 4, 3), 'd') 
    P1 = np.zeros((Nu, 4, 3), 'd') 
    P2 = np.zeros((Nv, 4, 3), 'd') 
    P3 = np.zeros((Nv, 4, 3), 'd') 

    rad = v_bar*beta
    rect_len = u_bar-2*rad
    if rect_len < 0:
        rect_len = 0
    # end if
    # Determine 4 corners of rectangular part

    rect_corners[0] = mid-u*(rect_len/2)-np.sin(np.pi/4)*\
        rad*v-np.cos(np.pi/4)*rad*u
    rect_corners[1] = mid+u*(rect_len/2)-np.sin(np.pi/4)*\
        rad*v+np.cos(np.pi/4)*rad*u
    rect_corners[2] = mid-u*(rect_len/2)+np.sin(np.pi/4)*\
        rad*v-np.cos(np.pi/4)*rad*u
    rect_corners[3] = mid+u*(rect_len/2)+np.sin(np.pi/4)*\
        rad*v+np.cos(np.pi/4)*rad*u

    arc_len = np.pi*rad/2 + rect_len # Two quarter circles straight line
    eighth_arc = 0.25*np.pi*rad
    # We have to distribute Nu-2 nodes over this arc-length
    spacing = arc_len/(Nu-1)

    bot_edge = np.zeros((Nu, 3), 'd')
    top_edge = np.zeros((Nu, 3), 'd')
    bot_edge[0] = rect_corners[0]
    bot_edge[-1] = rect_corners[1]
    top_edge[0] = rect_corners[2]
    top_edge[-1] = rect_corners[3]
    for i in xrange(Nu-2):
        dist_along_arc = (i+1)*spacing
        if dist_along_arc < eighth_arc:
            theta = dist_along_arc/rad # Angle in radians
            bot_edge[i+1] = mid-u*(rect_len/2) - \
                np.sin(theta+np.pi/4)*rad*v - np.cos(theta+np.pi/4)*rad*u
            top_edge[i+1] = mid-u*(rect_len/2) + \
                np.sin(theta+np.pi/4)*rad*v - np.cos(theta+np.pi/4)*rad*u
        elif dist_along_arc > rect_len+eighth_arc:
            theta = (dist_along_arc-rect_len-eighth_arc)/rad
            bot_edge[i+1] = mid+u*(rect_len/2) + \
                np.sin(theta)*rad*u - np.cos(theta)*rad*v
            top_edge[i+1] = mid+u*(rect_len/2) + \
                np.sin(theta)*rad*u + np.cos(theta)*rad*v
        else:
            top_edge[i+1] = mid -u*rect_len/2 + rad*v + \
                (dist_along_arc-eighth_arc)*u 
            bot_edge[i+1] = mid -u*rect_len/2 - rad*v + \
                (dist_along_arc-eighth_arc)*u 

    # end for

    left_edge = np.zeros((Nv, 3), 'd')
    right_edge = np.zeros((Nv, 3), 'd')
    theta = np.linspace(-np.pi/4, np.pi/4, Nv)

    for i in xrange(Nv):
        left_edge[i]  = mid-u*(rect_len/2) + \
            np.sin(theta[i])*rad*v - np.cos(theta[i])*rad*u
        right_edge[i] = mid+u*(rect_len/2) + \
            np.sin(theta[i])*rad*v + np.cos(theta[i])*rad*u
    # end if

    # Do the corner edges
    c0 = linear_edge(PTS[0], rect_corners[0], N_O)
    c1 = linear_edge(PTS[1], rect_corners[1], N_O)
    c2 = linear_edge(PTS[2], rect_corners[2], N_O)
    c3 = linear_edge(PTS[3], rect_corners[3], N_O)

    # Now we can finally do the pactches

    P0 = tfi_2d(E0, bot_edge, c0, c1)
    P1 = tfi_2d(E1, top_edge, c2, c3)
    P2 = tfi_2d(E2, left_edge, c0, c2)
    P3 = tfi_2d(E3, right_edge, c1, c3)

    if aspect < 1:
        return P3, P2, P0[::-1, :, :], P1[::-1, :, :]
    else:
        return P0, P1, P2, P3
    # end if
  
class geoDVGlobal(object):
     
    def __init__(self, dv_name, value, lower, upper, function, useit=True):
        
        '''Create a geometric design variable (or design variable group)
        See addGeoDVGloabl in pyGeo for more information
        '''

        self.name = dv_name
        self.value = np.atleast_1d(np.array(value)).astype('D')
        self.nVal = len(self.value)

        low = np.atleast_1d(np.array(lower))
        if len(low) == self.nVal:
            self.lower = low
        else:
            self.lower = np.ones(self.nVal)*lower
        # end if

        high = np.atleast_1d(np.array(upper))
        if len(high) == self.nVal:
            self.upper = high
        else:
            self.upper = np.ones(self.nVal)*upper
        # end if

        self.range    = self.upper-self.lower
        self.function = function
        self.useit    = useit

        return

    def __call__(self, ref_axis):

        '''When the object is called, actually apply the function'''
        # Run the user-supplied function
        return self.function(self.value, ref_axis)


class geoDVLocal(object):
     
    def __init__(self, dv_name, lower, upper, axis, coef_list, useit=True):
        
        '''Create a set of gemoetric design variables whcih change the shape
        of a surface surface_id. Local design variables change the surface
        in all three axis.
        See addGeoDVLOcal for more information
        '''
        N = len(axis)

        self.nVal = len(coef_list)*N
        self.value = np.zeros(self.nVal, 'D')
        self.name = dv_name
        self.lower = lower*np.ones(self.nVal)
        self.upper = upper*np.ones(self.nVal)
        self.range    = self.upper-self.lower
       
        self.coef_list = np.zeros((self.nVal, 2), 'intc')
        
        j = 0

        for i in xrange(len(coef_list)):
            if 'x' in axis.lower():
                self.coef_list[j] = [coef_list[i], 0]
                j += 1
            elif 'y' in axis.lower():
                self.coef_list[j] = [coef_list[i], 1]
                j += 1
            elif 'z' in axis.lower():
                self.coef_list[j] = [coef_list[i], 2]
                j += 1
            # end if
        # end for
        
        return

    def __call__(self, coef):

        '''When the object is called, apply the design variable values to 
        coefficients'''
        
        for i in xrange(self.nVal):
            coef[self.coef_list[i, 0], self.coef_list[i, 1]] += self.value[i]
        # end for
      
        return coef

    
def createTriPanMesh(geo, tripan_file, wake_file,
                     specs_file=None, default_size=0.1):
    '''
    Create a TriPan mesh from a pyGeo object.

    geo:          The pyGeo object
    tripan_file:  The name of the TriPan File
    wake_file:    The name of the wake file
    specs_file:   The specification of panels/edge and edge types
    default_size: If no specs_file is given, attempt to make edges with
    default_size-length panels
    
    This cannot be run in parallel!
    '''
    
    # Use the topology of the entire geo object
    topo = geo.topo

    n_edge = topo.nEdge
    n_face = topo.nFace
    
    # Face orientation
    face_orientation = [1]*n_face
    # edge_number == number of panels along a given edge
    edge_number = -1*np.ones(n_edge, 'intc')
    # edge_type == what type of parametrization to use along an edge
    edge_type   = ['linear']*n_edge
    wake_edges = []
    wake_dir   = []

    if specs_file:
        f = open(specs_file, 'r')
        line = f.readline().split()
        if int(line[0]) != n_face:
            mpiPrint('Number of faces do not match in specs file')
        if int(line[1]) != n_edge:
            mpiPrint('Number of edges do not match in specs file')
        # Discard a line
        f.readline()
        # Read in the face info
        for iface in xrange(n_face):
            aux = f.readline().split()
            face_orientation[iface] = int(aux[1])
        f.readline()
        # Read in the edge info
        for iedge in xrange(n_edge):
            aux = f.readline().split()
            edge_number[iedge] = int(aux[1])
            edge_type[iedge] = aux[2]
            if int(aux[5]) > 0:
                wake_edges.append(iedge)
                wake_dir.append(1)
            elif int(aux[5]) < 0:
                wake_edges.append(iedge)
                wake_dir.append(-1)
            # end if
        # end for
        f.close()
    else:
        default_size = float(default_size)
        # First Get the default number on each edge
    
        for iface in xrange(n_face):
            for iedge in xrange(4):
                # First check if we even have to do it
                if edge_number[topo.edge_link[iface][iedge]] == -1:
                    # Get the physical length of the edge
                    edge_length = \
                        geo.surfs[iface].edge_curves[iedge].getLength()

                    # Using default_size calculate the number of panels 
                    # along this edge
                    edge_number[topo.edge_link[iface][iedge]] = \
                        int(np.floor(edge_length/default_size))+2
                # end if
            # end for
        # end for
    # end if
    
    # Create the sizes Geo for the make consistent function
    sizes = []
    order = [0]*n_face
    for iface in xrange(n_face):
        sizes.append([edge_number[topo.edge_link[iface][0]], 
                      edge_number[topo.edge_link[iface][2]]])
    # end for
    sizes, edge_number = topo.makeSizesConsistent(sizes, order)

    # Now we need to get the edge parameter spacing for each edge
    topo.calcGlobalNumbering(sizes) # This gets g_index,l_index and counter

    # Now calculate the intrinsic spacing for each edge:
    edge_para = []
    for iedge in xrange(n_edge):
        if edge_type[iedge] == 'linear':
            spacing = np.linspace(0.0, 1.0, edge_number[iedge])
            edge_para.append(spacing)
        elif edge_type[iedge] == 'cos':
            spacing = 0.5*(1.0 - np.cos(np.linspace(
                        0, np.pi, edge_number[iedge])))
            edge_para.append(spacing)
        elif edge_type[iedge] == 'hyperbolic':
            x = np.linspace(0.0, 1.0, edge_number[iedge])
            beta = 1.8
            spacing = x - beta*x*(x - 1.0)*(x - 0.5)
            edge_para.append(spacing)
        else:
            mpiPrint('Warning: Edge type %s not understood. \
Using a linear type'%(edge_type[iedge]))
            edge_para.append(0, 1, edge_number[iedge])
        # end if
    # end for

    # Get the number of panels
    n_panels = 0
    n_nodes = len(topo.g_index)
    for iface in xrange(n_face):
        n_panels += (sizes[iface][0]-1)*(sizes[iface][1]-1)        
    # end for

    # Open the outputfile
    fp = open(tripan_file, 'w')

    # Write he number of points and panels
    fp.write('%5d %5d\n'%(n_nodes, n_panels))
   
    # Output the Points First
    UV = []
    for iface in xrange(n_face):
        uv = getBiLinearMap(edge_para[topo.edge_link[iface][0]],
                            edge_para[topo.edge_link[iface][1]],
                            edge_para[topo.edge_link[iface][2]],
                            edge_para[topo.edge_link[iface][3]])
        UV.append(uv)

    # end for
    
    for ipt in xrange(len(topo.g_index)):
        iface = topo.g_index[ipt][0][0]
        i     = topo.g_index[ipt][0][1]
        j     = topo.g_index[ipt][0][2]
        pt = geo.surfs[iface].getValue(UV[iface][i, j][0],  UV[iface][i, j][1])
        fp.write( '%12.10e %12.10e %12.10e \n'%(pt[0], pt[1], pt[2]))
    # end for

    # Output the connectivity Next
    for iface in xrange(n_face):
        if face_orientation[iface] >= 0:
            for i in xrange(sizes[iface][0]-1):
                for j in xrange(sizes[iface][1]-1):
                    fp.write('%d %d %d %d \n'%(topo.l_index[iface][i, j], 
                                               topo.l_index[iface][i+1, j], 
                                               topo.l_index[iface][i+1, j+1], 
                                               topo.l_index[iface][i, j+1]))
        else:
            for i in xrange(sizes[iface][0]-1):
                for j in xrange(sizes[iface][1]-1):
                    fp.write('%d %d %d %d \n'%(topo.l_index[iface][i, j], 
                                               topo.l_index[iface][i, j+1], 
                                               topo.l_index[iface][i+1, j+1], 
                                               topo.l_index[iface][i+1, j]))

            # end for
        # end for
    # end for
    fp.write('\n')
    fp.close()

    # Output the wake file
    fp = open(wake_file,  'w')
    fp.write('%d\n'%(len(wake_edges)))
    print 'wake_edges:', wake_edges

    for k in xrange(len(wake_edges)):
        # Get a surface/edge for this edge
        surfaces = topo.getSurfaceFromEdge(wake_edges[k])
        iface = surfaces[0][0]
        iedge = surfaces[0][1]
        if iedge == 0:
            indices = topo.l_index[iface][:, 0]
        elif iedge == 1:
            indices = topo.l_index[iface][:, -1]
        elif iedge == 2:
            indices = topo.l_index[iface][0, :]
        elif iedge == 3:
            indices = topo.l_index[iface][-1, :]
        # end if
        
        fp.write('%d\n'%(len(indices)))

        if wake_dir[k] > 0:
            for i in xrange(len(indices)):
                # A constant in TriPan to indicate projected wake
                te_node_type = 3 
                fp.write('%d %d\n'%(indices[i],  te_node_type))
        else:
            for i in xrange(len(indices)):
                te_node_type = 3 
                fp.write('%d %d\n'%(indices[len(indices)-1-i], te_node_type))
        # end for
    # end for

    fp.close()

    # Write out the default specFile
    if specs_file == None:
        (dirName, fileName) = os.path.split(tripan_file)
        (fileBaseName, fileExtension) = os.path.splitext(fileName)
        if dirName != '':
            new_specs_file = dirName+'/'+fileBaseName+'.specs'
        else:
            new_specs_file = fileBaseName+'.specs'
        # end if
        specs_file = new_specs_file

    if not os.path.isfile(specs_file):
        f = open(specs_file, 'w')
        f.write('%d %d Number of faces and number of edges\n'%(n_face, n_edge))
        f.write('Face number   Normal (1 for regular, -1 for\
 reversed orientation\n')
        for iface in xrange(n_face):
            f.write('%d %d\n'%(iface, face_orientation[iface]))
        f.write('Edge Number #Node Type     Start Space   End Space\
   WakeEdge\n') 
        for iedge in xrange(n_edge):
            if iedge in wake_edges:
                f.write( '  %4d    %5d %10s %10.4f %10.4f  %1d \n'%(\
                        iedge, edge_number[iedge], edge_type[iedge],
                        .1, .1, 1))
            else:
                f.write( '  %4d    %5d %10s %10.4f %10.4f  %1d \n'%(\
                        iedge, edge_number[iedge], edge_type[iedge],
                        .1, .1, 0))
            # end if
        f.close()

    return
 
