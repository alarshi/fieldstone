import numpy as np
import sys as sys
import scipy
import math as math
import time 
import scipy.sparse as sps
from scipy.sparse.linalg.dsolve import linsolve

#------------------------------------------------------------------------------

def NNV(rq,sq):
    NV_0= (1.-rq-sq)
    NV_1= rq
    NV_2= sq
    return NV_0,NV_1,NV_2

def dNNVdr(rq,sq):
    dNVdr_0= -1. 
    dNVdr_1= +1.
    dNVdr_2=  0.
    return dNVdr_0,dNVdr_1,dNVdr_2

def dNNVds(rq,sq):
    dNVds_0= -1. 
    dNVds_1=  0.
    dNVds_2= +1.
    return dNVds_0,dNVds_1,dNVds_2

#------------------------------------------------------------------------------

def sigma_xx_anal(x,y,P,R):
    if experiment==1:
       r1_2=(x-0)**2+(y-R)**2
       r2_2=(x-0)**2+(y+R)**2
       val=-2.*P/np.pi*( (R-y)*x**2/r1_2**2 +(R+y)*x**2/r2_2**2 - 1./(2*R)  )
    else:
       val=0
    return val

def sigma_yy_anal(x,y,P,R):
    if experiment==1:
       r1_2=(x-0)**2+(y-R)**2
       r2_2=(x-0)**2+(y+R)**2
       val=-2.*P/np.pi*( (R-y)**3/r1_2**2 +(R+y)**3/r2_2**2 - 1./(2*R)  )
    else:
       val=0
    return val

def sigma_xy_anal(x,y,P,R):
    if experiment==1:
       r1_2=(x-0)**2+(y-R)**2
       r2_2=(x-0)**2+(y+R)**2
       val=2.*P/np.pi*( (R-y)**2*x/r1_2**2 - (R+y)**2*x/r2_2**2  )
    else:
       val=0
    return val

def sigma_1_anal(x,y,P,R):
    if experiment==1:
       sigxx=sigma_xx_anal(x,y,P,R)
       sigyy=sigma_yy_anal(x,y,P,R)
       sigxy=sigma_xy_anal(x,y,P,R)
       val=0.5*(sigxx+sigyy)+np.sqrt( 0.25*(sigxx-sigyy)**2+sigxy**2 )
    else:
       val=0
    return val

def p_anal(x,y,P,R):
    if experiment==1:
       r1_2=(x-0)**2+(y-R)**2
       r2_2=(x-0)**2+(y+R)**2
       val1=-2.*P/np.pi*( (R-y)*x**2/r1_2**2 +(R+y)*x**2/r2_2**2 - 1./(2*R)  )
       val2=-2.*P/np.pi*( (R-y)**3/r1_2**2 +(R+y)**3/r2_2**2 - 1./(2*R)  )
       val=-0.5*(val1+val2)
    else:
       val=0
    return val

#------------------------------------------------------------------------------

print("-----------------------------")
print("----------fieldstone---------")
print("-----------------------------")

nLayers = 81   # must be odd !
outer_radius=1.

m=3
nqel=3
ndof=2
ndim=2

eps=1e-8

mu=1.                        #
nu=0.25                      # poisson ratio
lambdaa=2.*mu*nu/(1.-2.*nu)  #

rho=0                     # density
gx=0.                     # gravity vector x-component
gy=0.                     # gravity vector y-component

p_bc=1.

visu=1

# experiment=1: disc under vertical compression
# experiment=2: disc under compression left and bottom, no-slip top and right
experiment=2

if experiment==1:
   nsection=6

if experiment==2:
   nsection=8

nel = nsection * nLayers * nLayers                # number of elements
NV  = 1 + int(nsection/2) * nLayers * (nLayers+1) # number of mesh nodes
Nfem=NV*ndof                                       # Total number of degrees of freedom

qcoords_r=[1./6.,1./6.,2./3.] # coordinates & weights 
qcoords_s=[2./3.,1./6.,1./6.] # of quadrature points
qweights =[1./6.,1./6.,1./6.]

#################################################################
# WARNING: the Neumann b.c. are not accurate since at the moment
# they do not use the normal to the element edge!
#################################################################

print ('nLayers  =',nLayers)
print ('NV       =',NV)
print ('nel      =',nel)
print ('Nfem     =',Nfem)
print("-----------------------------")

#################################################################
# grid point setup
#################################################################
start = time.time()

x=np.zeros(NV,dtype=np.float64)          # x coordinates
y=np.zeros(NV,dtype=np.float64)          # y coordinates
outer_node = np.zeros(NV, dtype=np.bool) # on the outer hull yes/no 

# by starting at counter=1, we omit counter=0, which is 
# the center point and it automatically gets x=y=0
 
counter = 1 
for iLayer in range(1,nLayers+1):
    radius = outer_radius * float(iLayer)/float(nLayers)
    nPointsOnCircle = nsection*iLayer
    for iPoint in range (0,nPointsOnCircle):
        # Coordinates are created, starting at twelve o'clock, 
        # going in clockwise direction
        x[counter] = radius * np.sin(2. * np.pi * float(iPoint) / float(nPointsOnCircle))
        y[counter] = radius * np.cos(2. * np.pi * float(iPoint) / float(nPointsOnCircle))
        if iLayer==nLayers:
           outer_node[counter]=True
        counter += 1 
    #enddo
#enddo

np.savetxt('grid.ascii',np.array([x,y]).T,header='# x,y')

print("setup: grid points: %.3f s" % (time.time() - start))

#################################################################
# connectivity
#################################################################
start = time.time()

icon=np.zeros((m,nel),dtype=np.int32)

# first nsection triangles by hand
if nsection==4:
   icon[:,0] = (0,2,1)
   icon[:,1] = (0,3,2)
   icon[:,2] = (0,4,3)
   icon[:,3] = (0,1,4)
   iInner = 1 
   iOuter = 5 
elif nsection==6:
   icon[:,0] = (0,2,1)
   icon[:,1] = (0,3,2)
   icon[:,2] = (0,4,3)
   icon[:,3] = (0,5,4)
   icon[:,4] = (0,6,5)
   icon[:,5] = (0,1,6)
   iInner = 1 
   iOuter = 7 
elif nsection==8:
   icon[:,0] = (0,2,1)
   icon[:,1] = (0,3,2)
   icon[:,2] = (0,4,3)
   icon[:,3] = (0,5,4)
   icon[:,4] = (0,6,5)
   icon[:,5] = (0,7,6)
   icon[:,6] = (0,8,7)
   icon[:,7] = (0,1,8)
   iInner = 1 
   iOuter = 9 
else:
   exit('nsection value not supported')
#end if

storedElems = nsection 

for iLayer in range(2,nLayers+1):  
    nPointsOnCircle = nsection*iLayer   
    #print ('iLayer=',iLayer,'nPointsOnCircle=',nPointsOnCircle,'iInner=',iInner,'iOuter=',iOuter) 
    for iSection in range (1,nsection):     
        #print ('Section',iSection) 
        for iBlock in range(0,iLayer-1):
            icon[:,storedElems] = (iInner, iOuter +1, iOuter )
            #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
            storedElems = storedElems + 1    
            icon[:,storedElems] = (iInner, iInner+1, iOuter + 1) 
            #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
            storedElems = storedElems + 1 
            iInner += 1 
            iOuter += 1 
        #enddo
        icon[:,storedElems] = (iInner, iOuter+1, iOuter )
        #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
        storedElems = storedElems + 1 
        iOuter = iOuter + 1 
    #enddo

    # do the 6th and closing section. This has some extra difficulty where it is 
    # attached to the starting point

    # first do the regular blocks within the section
    #print ('Section',6) 
    for iBlock in range(0,iLayer-2): 
        icon[:,storedElems] = (iInner, iOuter+1, iOuter )
        #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
        storedElems += 1 
        icon[:,storedElems] = (iInner, iInner+1, iOuter + 1) 
        #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
        storedElems += 1 
        iInner += 1
        iOuter += 1
    #enddo

    # do the last block, which shares an inner point with the first section
    icon[:,storedElems] = (iInner, iOuter+1, iOuter )
    #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
    storedElems = storedElems + 1

    icon[:,storedElems] = (iInner, iInner + 1 - nsection*(iLayer-1) , iOuter+1)
    #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
    storedElems += 1 

    # last element, closing the layer.
    icon[:,storedElems] = ( iInner + 1 - nsection*(iLayer-1),iInner+1,iOuter+1 )
    #print ('   elt=',storedElems,'nodes:',icon[:,storedElems])
    storedElems += 1 

    iInner = iInner + 1
    iOuter = iOuter + 2
#enddo

print("setup: connectivity: %.3f s" % (time.time() - start))

#################################################################
# rotate 90 degree mesh to expose flat surface on top and bottom
#################################################################

if (experiment==1):
   temp=np.zeros(NV,dtype=np.float64)   
   temp[:]=x[:]
   x[:]=-y[:]
   y[:]=temp[:]
   np.savetxt('grid_rot.ascii',np.array([x,y]).T,header='# x,y')

#################################################################
# define boundary conditions
# Experiment 1: The boundary conditions for this benchmark are of 
# Neumann nature. # All we need to do is to remove the rotational 
# nullspace. We do so by zeroing the horizontal displacement on 
# the vertical axis and the horizontal displacement on the vertical
# axis since the system is symmetrical with respect to both axis.
# Experiment 2: the no-slip b.c. on the top and right do not allow
# for a null space. 
#################################################################
start = time.time()

bc_fix = np.zeros(Nfem, dtype=np.bool)  # boundary condition, yes/no
bc_val = np.zeros(Nfem, dtype=np.float64)  # boundary condition, value

if experiment==1:
   for i in range(0,NV):
      if abs(x[i])<eps:
         bc_fix[i*ndof]   = True ; bc_val[i*ndof]   = 0.
      if abs(y[i])<eps:
         bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.

if experiment==2:
   for i in range(0,NV):
      if abs(x[i]-outer_radius)<eps:
         bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
         bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.
      if abs(y[i]-outer_radius)<eps:
         bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
         bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.

print("setup: boundary conditions: %.3f s" % (time.time() - start))

#################################################################
# compute area of elements
#################################################################
start = time.time()

area=np.zeros(nel,dtype=np.float64) 
NNNV    = np.zeros(m,dtype=np.float64)           # shape functions V
dNNNVdr  = np.zeros(m,dtype=np.float64)          # shape functions derivatives
dNNNVds  = np.zeros(m,dtype=np.float64)          # shape functions derivatives

for iel in range(0,nel):
    for kq in range (0,nqel):
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]
        NNNV[0:m]=NNV(rq,sq)
        dNNNVdr[0:m]=dNNVdr(rq,sq)
        dNNNVds[0:m]=dNNVds(rq,sq)
        jcb=np.zeros((2,2),dtype=np.float64)
        for k in range(0,m):
            jcb[0,0] += dNNNVdr[k]*x[icon[k,iel]]
            jcb[0,1] += dNNNVdr[k]*y[icon[k,iel]]
            jcb[1,0] += dNNNVds[k]*x[icon[k,iel]]
            jcb[1,1] += dNNNVds[k]*y[icon[k,iel]]
        #end for
        jcob = np.linalg.det(jcb)
        area[iel]+=jcob*weightq
    #end for
#end for

print("     -> area (m,M) %.6e %.6e " %(np.min(area),np.max(area)))
print("     -> total area (meas) %.6f " %(area.sum()))
print("     -> total area (anal) %.6f " %(np.pi*outer_radius**2))

print("compute elements areas: %.3f s" % (time.time() - start))

#################################################################
# build FE matrix
#################################################################
start = time.time()

#a_mat = lil_matrix((Nfem,Nfem),dtype=np.float64)

a_mat = np.zeros((Nfem,Nfem),dtype=np.float64)  # matrix of Ax=b
b_mat = np.zeros((3,ndof*m),dtype=np.float64)   # gradient matrix B 
rhs   = np.zeros(Nfem,dtype=np.float64)         # right hand side of Ax=b
u     = np.zeros(NV,dtype=np.float64)           # x-component displacement 
v     = np.zeros(NV,dtype=np.float64)           # y-component displacement 
NNNV    = np.zeros(m,dtype=np.float64)          # shape functions V
dNNNVdx = np.zeros(m,dtype=np.float64)          # shape functions derivatives
dNNNVdy = np.zeros(m,dtype=np.float64)          # shape functions derivatives
dNNNVdr = np.zeros(m,dtype=np.float64)          # shape functions derivatives
dNNNVds = np.zeros(m,dtype=np.float64)          # shape functions derivatives
c_mat = np.array([[2*mu+lambdaa,lambdaa,0],[lambdaa,2*mu+lambdaa,0],[0,0,mu]],dtype=np.float64) 

for iel in range(0, nel):

    # set 2 arrays to 0 every loop
    K_el = np.zeros((m*ndof,m*ndof),dtype=np.float64)
    f_el = np.zeros(m*ndof)

    for kq in range (0,nqel):
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]
        NNNV[0:m]=NNV(rq,sq)
        dNNNVdr[0:m]=dNNVdr(rq,sq)
        dNNNVds[0:m]=dNNVds(rq,sq)
        jcb=np.zeros((2,2),dtype=np.float64)
        for k in range(0,m):
            jcb[0,0] += dNNNVdr[k]*x[icon[k,iel]]
            jcb[0,1] += dNNNVdr[k]*y[icon[k,iel]]
            jcb[1,0] += dNNNVds[k]*x[icon[k,iel]]
            jcb[1,1] += dNNNVds[k]*y[icon[k,iel]]
        #end for
        jcob = np.linalg.det(jcb)
        jcbi = np.linalg.inv(jcb)

        # compute dNdx & dNdy
        xq=0.0
        yq=0.0
        for k in range(0,m):
            xq+=NNNV[k]*x[icon[k,iel]]
            yq+=NNNV[k]*y[icon[k,iel]]
            dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
            dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]
        #end for

        # construct 3x8 b_mat matrix
        for i in range(0, m):
            b_mat[0:3, 2*i:2*i+2] = [[dNNNVdx[i],0.       ],
                                     [0.        ,dNNNVdy[i]],
                                     [dNNNVdy[i],dNNNVdx[i]]]
        #end for

        # compute elemental K_el matrix
        K_el += b_mat.T.dot(c_mat.dot(b_mat))*weightq*jcob

        # compute elemental rhs vector
        for i in range(0, m):
            f_el[ndof*i  ]+=NNNV[i]*jcob*weightq*gx*rho
            f_el[ndof*i+1]+=NNNV[i]*jcob*weightq*gy*rho
        #end for

    #end for kq

    # impose dirichlet b.c. 
    for k1 in range(0,m):
        for i1 in range(0,ndof):
            ikk=ndof*k1          +i1
            m1 =ndof*icon[k1,iel]+i1
            if bc_fix[m1]:
               K_ref=K_el[ikk,ikk] 
               for jkk in range(0,m*ndof):
                   f_el[jkk]-=K_el[jkk,ikk]*bc_val[m1]
                   K_el[ikk,jkk]=0
                   K_el[jkk,ikk]=0
               K_el[ikk,ikk]=K_ref
               f_el[ikk]=K_ref*bc_val[m1]
            #end if
        #end for 
    #end for

    # impose Neumann b.c.
    inode1=icon[0,iel]
    inode2=icon[1,iel]
    inode3=icon[2,iel]
    if outer_node[inode2] and outer_node[inode3]: # nodes 2&3 on boundary 
       if experiment==1:
          #top boundary
          if y[inode1]>0 and x[inode2]>0 and x[inode3]<0: 
             surf=1#x[inode2]-x[inode3]
             f_el[3]-=surf*p_bc*0.5
             f_el[5]-=surf*p_bc*0.5
          #end if 
          #bottom boundary
          if y[inode1]<0 and x[inode2]<0 and x[inode3]>0: 
             surf=1#x[inode3]-x[inode2]
             f_el[3]+=surf*p_bc*0.5
             f_el[5]+=surf*p_bc*0.5
          #end if 
       if experiment==2:
          # applying Neumann bc on left
          if abs(x[inode3]+outer_radius)<eps:
             surf=1
             f_el[2]+=surf*p_bc*0.5
             f_el[4]+=surf*p_bc*0.5
          #end if 
          if abs(x[inode2]+outer_radius)<eps:
             surf=1
             f_el[2]+=surf*p_bc*0.5
             f_el[4]+=surf*p_bc*0.5
          #end if 
          # applying Neumann bc on bottom
          if abs(y[inode3]+outer_radius)<eps:
             surf=1
             f_el[3]+=surf*p_bc*0.5
             f_el[5]+=surf*p_bc*0.5
          #end if 
          if abs(y[inode2]+outer_radius)<eps:
             surf=1
             f_el[3]+=surf*p_bc*0.5
             f_el[5]+=surf*p_bc*0.5
          #end if 
       #end if 
    #end if 

    # assemble matrix a_mat and right hand side rhs
    for k1 in range(0,m):
        for i1 in range(0,ndof):
            ikk=ndof*k1          +i1
            m1 =ndof*icon[k1,iel]+i1
            for k2 in range(0,m):
                for i2 in range(0,ndof):
                    jkk=ndof*k2          +i2
                    m2 =ndof*icon[k2,iel]+i2
                    a_mat[m1,m2]+=K_el[ikk,jkk]
                #end for
            #end for
            rhs[m1]+=f_el[ikk]
        #end for
    #end for
#end for

print("     -> rhs (m,M) %.4f %.4f " %(np.min(rhs),np.max(rhs)))

print("build FE matrix: %.3f s" % (time.time() - start))

#################################################################
# solve system
#################################################################
start = time.time()

sol = sps.linalg.spsolve(sps.csr_matrix(a_mat),rhs)

print("solve time: %.3f s" % (time.time() - start))

#####################################################################
# put solution into separate x,y velocity arrays
#####################################################################
start = time.time()

u,v=np.reshape(sol,(NV,2)).T

print("     -> u (m,M) %.4f %.4f " %(np.min(u),np.max(u)))
print("     -> v (m,M) %.4f %.4f " %(np.min(v),np.max(v)))

np.savetxt('displacement.ascii',np.array([x,y,u,v]).T,header='# x,y,u,v')

#####################################################################
# retrieve pressure and compute elemental strain
#####################################################################
start = time.time()

#u[:]=x[:]**2
#v[:]=y[:]**2

xc  = np.zeros(nel,dtype=np.float64)  
yc  = np.zeros(nel,dtype=np.float64)  
exx = np.zeros(nel,dtype=np.float64)  
eyy = np.zeros(nel,dtype=np.float64)  
exy = np.zeros(nel,dtype=np.float64)  
e   = np.zeros(nel,dtype=np.float64)  
p   = np.zeros(nel,dtype=np.float64)   
divv= np.zeros(nel,dtype=np.float64)  

for iel in range(0,nel):
    rq = 1./3.
    sq = 1./3.
    NNNV[0:m]=NNV(rq,sq)
    dNNNVdr[0:m]=dNNVdr(rq,sq)
    dNNNVds[0:m]=dNNVds(rq,sq)
    jcb=np.zeros((2,2),dtype=np.float64)
    for k in range(0,m):
        jcb[0,0]+=dNNNVdr[k]*x[icon[k,iel]]
        jcb[0,1]+=dNNNVdr[k]*y[icon[k,iel]]
        jcb[1,0]+=dNNNVds[k]*x[icon[k,iel]]
        jcb[1,1]+=dNNNVds[k]*y[icon[k,iel]]
    jcob=np.linalg.det(jcb)
    jcbi=np.linalg.inv(jcb)
    for k in range(0,m):
        dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
        dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]
    for k in range(0,m):
        xc[iel] += NNNV[k]*x[icon[k,iel]]
        yc[iel] += NNNV[k]*y[icon[k,iel]]
        exx[iel] += dNNNVdx[k]*u[icon[k,iel]]
        eyy[iel] += dNNNVdy[k]*v[icon[k,iel]]
        exy[iel] += 0.5*dNNNVdy[k]*u[icon[k,iel]]+ 0.5*dNNNVdx[k]*v[icon[k,iel]]
    divv[iel]=exx[iel]+eyy[iel]
    e[iel]=np.sqrt(0.5*(exx[iel]*exx[iel]+eyy[iel]*eyy[iel])+exy[iel]*exy[iel])
    p[iel]=-(lambdaa+mu)*(exx[iel]+eyy[iel])

print("     -> p (m,M) %.4f %.4f " %(np.min(p),np.max(p)))
print("     -> exx (m,M) %.6e %.6e " %(np.min(exx),np.max(exx)))
print("     -> eyy (m,M) %.6e %.6e " %(np.min(eyy),np.max(eyy)))
print("     -> exy (m,M) %.6e %.6e " %(np.min(exy),np.max(exy)))

np.savetxt('pressure.ascii',np.array([xc,yc,p]).T,header='# xc,yc,p')
np.savetxt('strain.ascii',np.array([xc,yc,exx,eyy,exy]).T,header='# xc,yc,exx,eyy,exy')

print("compute press & sr: %.3f s" % (time.time() - start))

#################################################################
# compute elemental stress 
#################################################################

sigma_xx = np.zeros(nel,dtype=np.float64)  
sigma_yy = np.zeros(nel,dtype=np.float64)  
sigma_xy = np.zeros(nel,dtype=np.float64)  
sigma_angle = np.zeros(nel,dtype=np.float64)  
sigma_1 = np.zeros(nel,dtype=np.float64)  

sigma_xx[:]=lambdaa*divv[:]+2*mu*exx[:]
sigma_yy[:]=lambdaa*divv[:]+2*mu*eyy[:]
sigma_xy[:]=               +2*mu*exy[:]

sigma_angle[:]=np.arctan(2.*sigma_xy[:]/(sigma_xx[:]-sigma_yy[:]))/2. /np.pi*180

sigma_1=0.5*(sigma_xx[:]+sigma_yy[:])+np.sqrt( 0.25*(sigma_xx[:]-sigma_yy[:])**2+sigma_xy[:]**2 )

#################################################################
# project pressure, strain and stress onto nodes
#################################################################
start = time.time()

q = np.zeros(NV,dtype=np.float64)  
exx_nodal = np.zeros(NV,dtype=np.float64)  
eyy_nodal = np.zeros(NV,dtype=np.float64)  
exy_nodal = np.zeros(NV,dtype=np.float64)  
sigma_xx_nodal = np.zeros(NV,dtype=np.float64)  
sigma_yy_nodal = np.zeros(NV,dtype=np.float64)  
sigma_xy_nodal = np.zeros(NV,dtype=np.float64)  
sigma_angle_nodal = np.zeros(NV,dtype=np.float64)  
sigma_1_nodal = np.zeros(NV,dtype=np.float64)  
sigma_2_nodal = np.zeros(NV,dtype=np.float64)  
counter = np.zeros(NV,dtype=np.float64)  

for iel in range(0,nel):
    inode1=icon[0,iel]
    inode2=icon[1,iel]
    inode3=icon[2,iel]
    q[inode1]+=p[iel] 
    q[inode2]+=p[iel] 
    q[inode3]+=p[iel] 
    exx_nodal[inode1]+=exx[iel]
    exx_nodal[inode2]+=exx[iel]
    exx_nodal[inode3]+=exx[iel]
    eyy_nodal[inode1]+=eyy[iel]
    eyy_nodal[inode2]+=eyy[iel]
    eyy_nodal[inode3]+=eyy[iel]
    exy_nodal[inode1]+=exy[iel]
    exy_nodal[inode2]+=exy[iel]
    exy_nodal[inode3]+=exy[iel]
    sigma_xx_nodal[inode1]+=sigma_xx[iel]
    sigma_xx_nodal[inode2]+=sigma_xx[iel]
    sigma_xx_nodal[inode3]+=sigma_xx[iel]
    sigma_yy_nodal[inode1]+=sigma_yy[iel]
    sigma_yy_nodal[inode2]+=sigma_yy[iel]
    sigma_yy_nodal[inode3]+=sigma_yy[iel]
    sigma_xy_nodal[inode1]+=sigma_xy[iel]
    sigma_xy_nodal[inode2]+=sigma_xy[iel]
    sigma_xy_nodal[inode3]+=sigma_xy[iel]
    counter[inode1]+=1
    counter[inode2]+=1
    counter[inode3]+=1

q[:]/=counter[:]
exx_nodal[:]/=counter[:]
eyy_nodal[:]/=counter[:]
exy_nodal[:]/=counter[:]
sigma_xx_nodal[:]/=counter[:]
sigma_yy_nodal[:]/=counter[:]
sigma_xy_nodal[:]/=counter[:]

sigma_angle_nodal[:]=np.arctan(2.*sigma_xy_nodal[:]/(sigma_xx_nodal[:]-sigma_yy_nodal[:]))/2. /np.pi*180

sigma_1_nodal=0.5*(sigma_xx_nodal[:]+sigma_yy_nodal[:]) \
           +np.sqrt( 0.25*(sigma_xx_nodal[:]-sigma_yy_nodal[:])**2+sigma_xy_nodal[:]**2 )
sigma_2_nodal=0.5*(sigma_xx_nodal[:]+sigma_yy_nodal[:]) \
           -np.sqrt( 0.25*(sigma_xx_nodal[:]-sigma_yy_nodal[:])**2+sigma_xy_nodal[:]**2 )

print("     -> q (m,M) %.4f %.4f " %(np.min(q),np.max(q)))
print("     -> exx (m,M) %.6e %.6e " %(np.min(exx_nodal),np.max(exx_nodal)))
print("     -> eyy (m,M) %.6e %.6e " %(np.min(eyy_nodal),np.max(eyy_nodal)))
print("     -> exy (m,M) %.6e %.6e " %(np.min(exy_nodal),np.max(exy_nodal)))

np.savetxt('q.ascii',np.array([x,y,q]).T,header='# x,y,q')
np.savetxt('strain_nodal.ascii',np.array([x,y,exx_nodal,eyy_nodal,exy_nodal]).T)

print("compute nodal quantities: %.3f s" % (time.time() - start))

#####################################################################
# compute root mean square displacement vrms 
#####################################################################
start = time.time()

vrms=0.
avrg_u=0.
avrg_v=0.

for iel in range (0,nel):
    for kq in range (0,nqel):
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]
        NNNV[0:m]=NNV(rq,sq)
        dNNNVdr[0:m]=dNNVdr(rq,sq)
        dNNNVds[0:m]=dNNVds(rq,sq)
        jcb=np.zeros((2,2),dtype=np.float64)
        for k in range(0,m):
            jcb[0,0] += dNNNVdr[k]*x[icon[k,iel]]
            jcb[0,1] += dNNNVdr[k]*y[icon[k,iel]]
            jcb[1,0] += dNNNVds[k]*x[icon[k,iel]]
            jcb[1,1] += dNNNVds[k]*y[icon[k,iel]]
        jcob = np.linalg.det(jcb)
        uq=0.
        vq=0.
        for k in range(0,m):
            uq+=NNNV[k]*u[icon[k,iel]]
            vq+=NNNV[k]*v[icon[k,iel]]
        vrms+=(uq**2+vq**2)*weightq*jcob
        avrg_u+=uq*weightq*jcob
        avrg_v+=vq*weightq*jcob
    # end for kq
# end for iel

avrg_u/=np.sum(area)
avrg_v/=np.sum(area)

print("     -> vrms   = %.6e m/s" %(vrms))
print("     -> avrg u = %.6e m/s" %(avrg_u))
print("     -> avrg v = %.6e m/s" %(avrg_v))

print("compute vrms: %.3fs" % (time.time() - start))

#################################################################
# write out quantities on axis for (gnu)plotting 
#################################################################

xaxis_file=open('xaxis.ascii',"w")
for i in range(0,NV):
    if abs(y[i])<eps: 
       xaxis_file.write("%8e %8e %8e %8e %8e %8e %8e %8e %8e %8e\n" %(
                         x[i],u[i],v[i],q[i],
                         exx_nodal[i],
                         eyy_nodal[i],
                         exy_nodal[i],
                         sigma_xx_nodal[i],
                         sigma_yy_nodal[i],
                         sigma_xy_nodal[i]))

yaxis_file=open('yaxis.ascii',"w")
for i in range(0,NV):
    if abs(x[i])<eps: 
       yaxis_file.write("%8e %8e %8e %8e %8e %8e %8e %8e %8e %8e\n" %(
                         y[i],u[i],v[i],q[i],
                         exx_nodal[i],
                         eyy_nodal[i],
                         exy_nodal[i],
                         sigma_xx_nodal[i],
                         sigma_yy_nodal[i],
                         sigma_xy_nodal[i]))

#################################################################

if visu==1:
    vtufile=open('solution.vtu',"w")
    vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
    vtufile.write("<UnstructuredGrid> \n")
    vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(NV,nel))
    #####
    vtufile.write("<Points> \n")
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" %(x[i],y[i],0.))
    vtufile.write("</DataArray>\n")
    vtufile.write("</Points> \n")

    vtufile.write("<CellData Scalars='scalars'>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='area' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (area[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='exx' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (exx[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='eyy' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (eyy[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='exy' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (exy[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='strain' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (e[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='p' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (p[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_xx' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (sigma_xx[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_yy' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (sigma_yy[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_xy' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (sigma_xy[iel]))
    vtufile.write("</DataArray>\n")

    vtufile.write("<DataArray type='Float32' Name='sigma_angle' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (sigma_angle[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_1' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (sigma_1[iel]))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='p (th)' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (p_anal(xc[iel],yc[iel],p_bc,outer_radius)))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='div(v)' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" %divv[iel]) 
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("</CellData>\n")

    vtufile.write("<PointData Scalars='scalars'>\n")
    #--
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='displacement' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" %(u[i],v[i],0.))
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='q' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" %q[i])
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='exx' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" %exx_nodal[i])
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='eyy' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" %eyy_nodal[i])
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='exy' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" %exy_nodal[i])
    vtufile.write("</DataArray>\n")

    vtufile.write("<DataArray type='Float32' Name='sigma_xx' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_xx_nodal[i])
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_yy' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_yy_nodal[i])
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_xy' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_xy_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='sigma_angle' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_angle_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='sigma_1' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_1_nodal[i])
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_2' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_2_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='sigma princ. 1' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" % (sigma_1_nodal[i]*np.cos(sigma_angle_nodal[i]),
                                             sigma_1_nodal[i]*np.sin(sigma_angle_nodal[i]), 0.)   )
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='sigma princ. 2' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" % (sigma_2_nodal[i]*np.cos(sigma_angle_nodal[i]+np.pi/2),
                                             sigma_2_nodal[i]*np.sin(sigma_angle_nodal[i]+np.pi/2), 0.)   )
    vtufile.write("</DataArray>\n")

    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='sigma princ. 1 dir' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" % (np.cos(sigma_angle_nodal[i]),
                                             np.sin(sigma_angle_nodal[i]), 0.)   )
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='sigma princ. 2 dir' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" % (np.cos(sigma_angle_nodal[i]+np.pi/2),
                                             np.sin(sigma_angle_nodal[i]+np.pi/2), 0.)   )
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='sigma_xx (th)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_xx_anal(x[i],y[i],p_bc,outer_radius) )
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_yy (th)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_yy_anal(x[i],y[i],p_bc,outer_radius) )
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_xy (th)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_xy_anal(x[i],y[i],p_bc,outer_radius) )
    vtufile.write("</DataArray>\n")
    vtufile.write("<DataArray type='Float32' Name='sigma_1 (th)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % sigma_1_anal(x[i],y[i],p_bc,outer_radius) )
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='outer_node' Format='ascii'> \n")
    for i in range(0,NV):
        if outer_node[i]:
           vtufile.write("%10e \n" % 1)
        else:
           vtufile.write("%10e \n" % 0)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='bc_fix (u)' Format='ascii'> \n")
    for i in range(0,NV):
        if bc_fix[i*ndof]:
           vtufile.write("%10e \n" % 1)
        else:
           vtufile.write("%10e \n" % 0)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='bc_fix (v)' Format='ascii'> \n")
    for i in range(0,NV):
        if bc_fix[i*ndof+1]:
           vtufile.write("%10e \n" % 1)
        else:
           vtufile.write("%10e \n" % 0)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("</PointData>\n")
    #####
    vtufile.write("<Cells>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%d %d %d \n" %(icon[0,iel],icon[1,iel],icon[2,iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%d \n" %((iel+1)*3))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
    for iel in range (0,nel):
        vtufile.write("%d \n" %5)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("</Cells>\n")
    #####
    vtufile.write("</Piece>\n")
    vtufile.write("</UnstructuredGrid>\n")
    vtufile.write("</VTKFile>\n")
    vtufile.close()

print("-----------------------------")
print("------------the end----------")
print("-----------------------------")