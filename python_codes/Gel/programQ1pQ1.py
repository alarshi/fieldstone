
import numpy as np
from scipy.linalg import null_space

#------------------------------------------------------------------------------

def NNV(r,s):
    NV_0= 0.25*(1-r)*(1-s) - 0.25*B(r,s)
    NV_1= 0.25*(1+r)*(1-s) - 0.25*B(r,s)
    NV_2= 0.25*(1+r)*(1+s) - 0.25*B(r,s)
    NV_3= 0.25*(1-r)*(1+s) - 0.25*B(r,s)
    NV_4= B(r,s)
    return NV_0,NV_1,NV_2,NV_3,NV_4

def dNNVdr(r,s):
    dNVdr_0=-0.25*(1.-s) -0.25*dBdr(r,s)
    dNVdr_1=+0.25*(1.-s) -0.25*dBdr(r,s)
    dNVdr_2=+0.25*(1.+s) -0.25*dBdr(r,s)
    dNVdr_3=-0.25*(1.+s) -0.25*dBdr(r,s)
    dNVdr_4=dBdr(r,s) 
    return dNVdr_0,dNVdr_1,dNVdr_2,dNVdr_3,dNVdr_4

def dNNVds(r,s):
    dNVds_0=-0.25*(1.-r) -0.25*dBds(r,s)
    dNVds_1=-0.25*(1.+r) -0.25*dBds(r,s)
    dNVds_2=+0.25*(1.+r) -0.25*dBds(r,s)
    dNVds_3=+0.25*(1.-r) -0.25*dBds(r,s)
    dNVds_4=dBds(r,s) 
    return dNVds_0,dNVds_1,dNVds_2,dNVds_3,dNVds_4

def NNP(r,s):
    NP_0= 0.25*(1-r)*(1-s)
    NP_1= 0.25*(1+r)*(1-s)
    NP_2= 0.25*(1+r)*(1+s)
    NP_3= 0.25*(1-r)*(1+s)
    return NP_0,NP_1,NP_2,NP_3 

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def B(r,s):
    if bubble==1:
       return (1-r**2)*(1-s**2)*(1-r)*(1-s)
    elif bubble==2:
       return (1-r**2)*(1-s**2)*(1+beta*(r+s))
    else:
       return (1-r**2)*(1-s**2)

def dBdr(r,s):
    if bubble==1:
       return (1-s**2)*(1-s)*(-1-2*r+3*r**2)
    elif bubble==2:
       return (s**2-1)*(-beta+3*beta*r**2+2*r*(beta*s+1))
    else:
       return (-2*r)*(1-s**2)

def dBds(r,s):
    if bubble==1:
       return (1-r**2)*(1-r)*(-1-2*s+3*s**2) 
    elif bubble==2:
       return (r**2-1)*(-beta+2*s*(beta*r+1)+3*beta*s**2)
    else:
       return (1-r**2)*(-2*s)

#-------------------------------------------------------------

bubble=1
beta=0.25

mV=5
mP=4
nel=1
ndim=2
ndofV=2
ndofP=1

xV = np.empty(5,dtype=np.float64)  # x coordinates
yV = np.empty(5,dtype=np.float64)  # y coordinates

xV[0]=-1 
yV[0]=-1
xV[1]= 1 
yV[1]=-1
xV[2]= 1 
yV[2]=1
xV[3]=-1 
yV[3]=1
xV[4]=0 
yV[4]=0

iconV=np.zeros((mV,nel),dtype=np.int32)
iconP=np.zeros((mP,nel),dtype=np.int32)

iconV[0,0]=0
iconV[1,0]=1
iconV[2,0]=2
iconV[3,0]=3
iconV[4,0]=4

iconP[0:mP,0:nel]=iconV[0:mP,0:nel]

nqperdim=3
qcoords=[-np.sqrt(3./5.),0.,np.sqrt(3./5.)]
qweights=[5./9.,8./9.,5./9.]

NNNV    = np.zeros(mV,dtype=np.float64)           # shape functions V
dNNNVdr  = np.zeros(mV,dtype=np.float64)          # shape functions derivatives
dNNNVds  = np.zeros(mV,dtype=np.float64)          # shape functions derivatives
NNNV    = np.zeros(mV,dtype=np.float64)           # shape functions V
NNNP    = np.zeros(mP,dtype=np.float64)           # shape functions P
dNNNVdx = np.zeros(mV,dtype=np.float64)           # shape functions derivatives
dNNNVdy = np.zeros(mV,dtype=np.float64)           # shape functions derivatives
dNNNVdr = np.zeros(mV,dtype=np.float64)           # shape functions derivatives
dNNNVds = np.zeros(mV,dtype=np.float64)           # shape functions derivatives
b_mat   = np.zeros((3,ndofV*mV),dtype=np.float64) # gradient matrix B 
N_mat   = np.zeros((3,ndofP*mP),dtype=np.float64) # matrix  
G_el=np.zeros((mV*ndofV,mP*ndofP),dtype=np.float64)

iel=0
for iq in range(0,nqperdim):
    for jq in range(0,nqperdim):
        rq=qcoords[iq]
        sq=qcoords[jq]
        weightq=qweights[iq]*qweights[jq]

        NNNV[0:mV]=NNV(rq,sq)
        dNNNVdr[0:mV]=dNNVdr(rq,sq)
        dNNNVds[0:mV]=dNNVds(rq,sq)
        NNNP[0:mP]=NNP(rq,sq)

        # calculate jacobian matrix
        jcb=np.zeros((ndim,ndim),dtype=np.float64)
        for k in range(0,mV):
            jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
            jcb[0,1] += dNNNVdr[k]*yV[iconV[k,iel]]
            jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
            jcb[1,1] += dNNNVds[k]*yV[iconV[k,iel]]
        jcob = np.linalg.det(jcb)
        jcbi = np.linalg.inv(jcb)

        # compute dNdx & dNdy
        xq=0.0
        yq=0.0
        for k in range(0,mV):
            xq+=NNNV[k]*xV[iconV[k,iel]]
            yq+=NNNV[k]*yV[iconV[k,iel]]
            dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
            dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]

        # construct 3x8 b_mat matrix
        for i in range(0,mV):
            b_mat[0:3, 2*i:2*i+2] = [[dNNNVdx[i],0.     ],
                                     [0.        ,dNNNVdy[i]],
                                     [dNNNVdy[i],dNNNVdx[i]]]

        for i in range(0,mP):
            N_mat[0,i]=NNNP[i]
            N_mat[1,i]=NNNP[i]
            N_mat[2,i]=0.

        G_el-=b_mat.T.dot(N_mat)*weightq*jcob

    #end for
#end for


print (G_el*9*5*2)
print (G_el)

G2=G_el[8:10,0:4]
print(G2)
ns = null_space(G2)
print(ns)


