import numpy as np
from numpy import linalg as LA
import math
import matplotlib.pyplot as plt
import sys
import time
## The code partially reproduces Figure 3 from paper
# Optimizing adaptive cancer therapy: dynamic programming and evolutionary game theory,
# Proceedings of the Royal Society B: Biological Sciences 287: 20192454 (2020)
# https://doi.org/10.1098/rspb.2019.2454

# Mark Gluzman, Jacob G. Scott, and Alexander Vladimirsky


# Produce optimal control in feedback form and the value function
# for a model of lung cancer proposed by Kaznatcheev et al. [1]

## Helping functions

## Initializaion of the value function u

def u_initiation():
    u = np.ones((n+1,n+1))*hugeVal

    # skip the half of the domain where x1 + x2 > 1
    for ii in range(0,n+1):
        for jj in range(n-ii+1,n+1):
            u[ii][jj] = np.nan
        
     
    # value function = 0 at the recovery zone
    for ii in range(0,n+1):
        for jj in range(0,n-ii+1):
            if  (jj*h < fb):
                u[ii][jj] = 0
    return u

## Instantaneous cost 
def K(_, d):
    y  = d + sigma
    return y

## Direction of movement at state x under control d
def f(x, d):
    
    # transformation into (p, q) coordinates
    p = x[1]
    q = (1-x[0]-x[1])/(1-x[1])

    # direction of movement in (p, q) coordinates
    
    sum_p = 0
    for z in range(0,n_neigh+1):
        sum_p = sum_p + p**z
    
    dq = q*(1-q)*(bv/(n_neigh+1)*sum_p-c)
    dp = p*(1-p)*(ba/(n_neigh+1) - q*(bv-c)-d)
    
    # transformation into (x_G, x_V, x_D) coordinates
    return np.array([-dq*(1-p) - dp*(1-q), dp])


## Find time of movement tau
def tau_func(x, d, i, j):
    
    func = f(x, d)
    
    assert(LA.norm(func)>0)
    
    if (func[0] == 0):
        y = h / abs(func[1])
    elif (func[1] == 0):
        y = h / abs(func[0])
    else:
        if (func[0] * func[1] > 0):
            x1_int = [(i+np.sign(func[0])) * h, j * h]
            x2_int = [i * h, (j+np.sign(func[1])) * h]
        elif (abs(func[1]) > abs(func[0])):
            x1_int = [(i+np.sign(func[0])) * h, (j + np.sign(func[1])) * h]
            x2_int = [i * h, (j+np.sign(func[1])) * h]
        else:
            x1_int = [(i+np.sign(func[0])) * h, j * h]
            x2_int = [(i+np.sign(func[0])) * h, (j + np.sign(func[1])) * h]
        
        k1 = x2_int[0] - x1_int[0]
        k2 = x1_int[1] - x2_int[1]
        kc = - (x1_int[1] * k1 + x1_int[0] * k2)
        y = - (kc + k1*x[1] + k2*x[0]) / (k1*func[1] + k2*func[0])
    
    if (np.isnan(y) or np.isinf(y) or (y <= 0)):
        print('Cannot compute Tau!')
        y = 0
    
    return y

## Return value funcion at state xtilde
# u interped at (x + tau * f(x,b))
def u_interped(u, xtilde, i, j):
    
    dist = h*math.sqrt(2)
    
    # there are 6 possible combinations of 2 neighboring meshpoints.
    
    ###### 3 #############
    #####--------#########   *---->|
    ###4 -        - 1 ####   ^     |
    #####-          -#####   |     \/
    #### 2 -        - 6 ##   |<----*
    #########--------#####
    ############# 5 ######
    
    #*----> is the direction where * is point that we include
    
    # value function at state xtilde is approximated by interpolation
    # using the neighboring meshpoint values.
      
        #1
    if (xtilde[0] >= i*h) and (xtilde[1] > j*h):
        x1_int = np.array([i*h, (j+1)*h])
        gamma = LA.norm(xtilde-x1_int) / dist
        y = u[i][j+1]*(1-gamma) + u[i+1][j]*gamma
        #2
    elif (xtilde[0] <= i*h) and (xtilde[1] < j*h) and (i!=0):
        x1_int = np.array([i*h, (j-1)*h])
        gamma = LA.norm(xtilde-x1_int) / dist
        y = u[i][j-1]*(1-gamma) + u[i-1][j]*gamma    
        #3
    elif (xtilde[0] != i*h) and (abs(xtilde[1] - (j+1)*h) < tinyVal):
        x1_int = np.array([(i-1)*h, (j+1)*h])
        gamma = LA.norm(xtilde-x1_int) / h
        y = u[i-1][j+1]*(1-gamma) + u[i][j+1]*gamma
        #4
    elif (abs(xtilde[0] - (i-1)*h) < tinyVal) and (xtilde[1] != (j+1)*h):
        x1_int = np.array([(i-1)*h, j*h])
        gamma = LA.norm(xtilde-x1_int) / h
        y = u[i-1][j]*(1-gamma) + u[i-1][j+1]*gamma  
        #5
    elif (xtilde[0] != i*h) and (abs(xtilde[1] - (j-1)*h) < tinyVal):
        x1_int = np.array([(i+1)*h, (j-1)*h])
        gamma = LA.norm(xtilde-x1_int) / h
        y = u[i+1][j-1]*(1-gamma) + u[i][j-1]*gamma
        #6
    elif (abs(xtilde[0] - (i+1)*h) < tinyVal) and (xtilde[1] != (j-1)*h):
        x1_int = np.array([(i+1)*h, j*h])
        gamma = LA.norm(xtilde-x1_int) / h
        y = u[i+1][j]*(1-gamma) + u[i+1][j-1]*gamma
    elif (i==0) and (xtilde[1] < j*h):
        y = u[i][j-1]
    elif (i==0) and (xtilde[1] > j*h):
        y = u[i][j+1]
    else:
        print('We are not in any quadrant at all!')
        y = 0
    
    return y

## Visualization of the optimal control and value function

def show_plots():
    
    [X,Y] = np.meshgrid(np.arange(0.0,1.0 + h,h), np.arange(0.0,1.0 + h,h))
    [X,Y] = transf(X.conj().transpose(),Y.conj().transpose()) # transformation into a regular triangular mesh
    uu = u
    for ii in range(0,n+1):
        for jj in range(0,n+1):
            if ((jj*h < fb)  or (jj*h > 1- fb)):
                uu[ii][jj] = np.nan
            if (uu[ii][jj]>10):
                uu[ii][jj]=10
             
    fig = plt.figure(figsize=(6,6))
    #mymap = [parula(2)  0, 1, 0]
    #colormap(mymap)
    plt.pcolor(X, Y, d_matr)# plot optimal control
    #hold on(draw 2 figures on the same graph)
    #contour(X, Y, uu, 'r')# plot value function
    plt.contour(X,Y,uu,colors=['red'])
    plt.axis([0,1,0,1]) #axis([0 1 0 1])
    plt.show(fig)
    #shading flat



## Transformation to simplex x1 + x2 + x3 = 1

def transf(X,Y):

    T= np.array([[1, 1/2], 
                 [0, math.sqrt(3)/2]]) # linear transformation into a regular triangular mesh
    X_tr=X 
    Y_tr=Y
    for i1 in range(1, len(X[:,0]) + 1):
        for i2 in range(1, len(X[:,0]) + 1):
            var = np.matmul(T,np.array([X[i1-1][i2-1], Y[i1-1][i2-1]]).conj().transpose()).conj().transpose()
            X_tr[i1-1][i2-1]=var[0]
            Y_tr[i1-1][i2-1]=var[1]
        
    return [X_tr,Y_tr]


## Display time
def displayTime(seconds):
    minute, second = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    return hour, minute, second
    
## Model parameters
d_max = 3 # MTD
sigma = 0.01 # time penalty
ba = 2.5 # the benefit per unit of acidification
bv = 2 # the benefit from the oxygen per unit of vascularization
c = 1 # the cost of production VEGF
n_neigh = 4 #the number of cells in the interaction group.
fb = 10**(-1.5) # failure barrier, recovery barrier

## Discretization parameters
n = 9000 # number of meshpoints along one side
h = 1 / n
# the algorithm terminates when the difference between value functions
# in sequential iterations falls below 'iter_tol'
iter_tol = 10**(-4)

hugeVal = 100000 # a large number ~ infinity
tinyVal = 10**(-10) # a small number ~ 0

## Initiallization
d_matr = np.zeros((n+1,n+1)) # control
u = u_initiation() # value function



## Main part
change = hugeVal # current difference between value functions in sequential iterations
k = 0 # iteration number
while (change > iter_tol):
    change = 0

    # alternating meshpoint orderings (“Fast Sweeping”)
    if (k%4 == 0):
        irange = range(0,n+1)
        jrange = range(0,n+1)
    elif (k%4 == 1):
        irange = range(0,n+1)
        jrange = range(n,0,-1)
    elif (k%4 == 2):
        irange = range(n,0,-1)
        jrange = range(n,0,-1)
    elif (k%4 == 3):
        irange = range(n,0,-1)
        jrange = range(0,n+1)
    else:
        print('weird k')
    
    start = time.time()
    
    for i in irange:
        for j in jrange:
            elapsedTime = time.time() - start;
            estimatedRemaining = int(elapsedTime * (n*n)/(i*n + j+1) - elapsedTime)
            displayElapsed = displayTime(elapsedTime)
            displayEstimated = displayTime(estimatedRemaining)
            sys.stdout.write("\r[%d/%d], [%d/%d], Elapsed: %ih %im %is ETA: %ih %im %is " 
                         % (i, len(irange)-1, j, len(jrange)-1, displayElapsed[0], displayElapsed[1], displayElapsed[2],
                            displayEstimated[0], displayEstimated[1], displayEstimated[2]))
            sys.stdout.flush()
            if (i+j > n): # skip the half of the domain if x1+x2 > 1
                d_matr[i][j] = np.nan
                continue
            
            x1 = i*h
            x2 = j*h
            x = np.array([x1, x2])
            if (x2 > fb) and (x2 < 1-fb): # skip fixed recovery and failure zones
                
                u_new = hugeVal
                for d in [0, d_max]:
                    if (LA.norm(f(x, d))==0):
                        continue
                
                    tau = tau_func(x, d, i, j)
                    xtilde = x + tau * f(x, d) # new state
                    # value of u under control d
                    u_possible = tau * K(x, d) + u_interped(u, xtilde, i , j)
                    
                    if (u_possible < u_new):
                        u_new = u_possible
                        d_new = d
                    
                
                
                #update the value function u at state x
                if (u_new < u[i][j]):
                    this_change = u[i][j] - u_new
                    u[i][j] = u_new
                    d_matr[i][j] = d_new
                    if (this_change > change):
                        change = this_change
    k = k + 1
    # print the current difference between value functions in sequential iterations
    print(change)


    

## Visualization of the optimal control and value function
[X,Y] = np.meshgrid(np.arange(0.0,1.0 + h,h), np.arange(0.0,1.0 + h,h))
[X,Y] = transf(X.conj().transpose(),Y.conj().transpose()) # transformation into a regular triangular mesh
uu = u
for ii in range(0,n+1):
    for jj in range(0,n+1):
        if ((jj*h < fb)  or (jj*h > 1- fb)):
            uu[ii][jj] = np.nan
        if (uu[ii][jj]>10):
            uu[ii][jj]=10
         
fig = plt.figure(figsize=(6,6))
#mymap = [parula(2)  0, 1, 0]
#colormap(mymap)
plt.pcolor(X, Y, d_matr)# plot optimal control
#hold on(draw 2 figures on the same graph)
#contour(X, Y, uu, 'r')# plot value function
plt.contour(X,Y,uu,colors=['red'])
plt.axis([0,1,0,1]) #axis([0 1 0 1])
plt.show(fig)
#shading flat



## References
# [1] Kaznatcheev A, Vander Velde R, Scott JG, Basanta D.
# 2017 Cancer treatment scheduling and dynamic
# heterogeneity in social dilemmas of tumour acidity
# and vasculature. Br. J. Cancer 116, 785–792.




