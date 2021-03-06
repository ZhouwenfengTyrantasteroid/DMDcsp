import numpy as np
import control
import time
import copy
import pickle
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
#plt.rc('text', usetex=True)
#plt.rc('font', size=24)

# Custom libraries
import DMDcsp
import lqg
import data_loader


# Load sparse model
[sys, C, Qe, Re, sens] = pickle.load(open('data/model_sparse.p', 'rb'))
nx = sys.nx
nu = sys.nu
ny = sys.ny
nz = C.shape[0]

nsteps = 8000

# Test data
test_case = "controlled_flow_data"
grid_full = data_loader.grid(test_case, skip_points=1)
test_data = data_loader.flow_data(grid_full, test_case, timestep_skip=1, start=0, end=nsteps)

Y = test_data.wy
U = test_data.u
Z = Y[sens,:]

# LQR weights
Qr = np.diag([0, 0, 0, 0, 1, 1, 0, 0])
Rr = 5.0e+3 * np.eye(nu)

# Initialize lqg controller/estimator
controller = lqg.lqg(sys.A, sys.B, C, Qr, Rr, Qe, Re)
pickle.dump(controller, open('dns_controller/controller.p', 'wb'))

# Compute best estimate of x using the full flow field Y
x_best = np.linalg.pinv(sys.C) @ Y

# Test: estimate x from measurements Z
# Initial values
x_init = np.zeros(nx, dtype=complex)
P_init = np.eye(nx, dtype=complex)
np.save('dns_controller/x_init.npy', x_init)
np.save('dns_controller/P_init.npy', P_init)

# Save DMD modes for full-state estimate
np.save('dns_controller/Phi_hat.npy', sys.C)

x_hat = np.zeros((nx, nsteps), dtype=complex)
P = np.zeros((nx,nx,nsteps), dtype=complex)
x_hat[:,0] = x_init
P[:,:,0] = P_init
u_star = np.zeros((nu,nsteps))

for k in range(nsteps-1):
    u_star[:,k] = controller.lqr(x_hat[:,k])
    x_hat[:,k+1], P[:,:,k+1] = controller.lqe(x_hat[:,k], u_star[:,k],  P[:,:,k], Z[:,k+1])

est_error = np.linalg.norm(x_hat - x_best, ord=2, axis=0) / np.linalg.norm(x_best, ord=2, axis=0)
y_error = np.linalg.norm(sys.C @ x_hat - Y, ord=2, axis=0) / np.linalg.norm(Y, ord=2, axis=0)
P_det = np.linalg.det(np.transpose(P, (2,0,1)))/100.
P_det.shape


Ts = 5

"""
##########################
# Plot mode amplitudes
##########################
fig, axs = plt.subplots(1, figsize=(7,5), facecolor='w', edgecolor='k')
plt.subplots_adjust(hspace=0.6, left=0.18, right=0.95, top=0.95, bottom=0.18)

#mode_i = [0, 1, 2, 3, 4, 5, 6, 7, 8]
mode_i = [0, 1, 2, 3, 4]

for i in mode_i:
    axs.plot(np.real(x_best[i,:nsteps]))

plt.gca().set_prop_cycle(None) # Reset color order

for i in mode_i:
    axs.plot(np.real(x_hat[i,:nsteps]), linestyle='dashed')

axs.set_axisbelow(True)
axs.set_xlabel('Time step k')
axs.set_ylabel('Mode amplitude')
plt.grid(True)
#plt.savefig('/Users/atsol/research/papers/AIAA-MPC-of-LSMS/figures/case_3_inputs.eps')

plt.show()

"""

##########################
# Plot optimal input
##########################
fig, axs = plt.subplots(1, figsize=(12,7), facecolor='w', edgecolor='k')
plt.subplots_adjust(hspace=0.6, left=0.18, right=0.95, top=0.95, bottom=0.18)


axs.plot(u_star[0,:], c = 'k', label='optimal input')
axs.plot(U[0,:nsteps], c = 'r', linestyle='dashed', label='dns input')
axs.plot(Z[0]/10., c = 'b', linestyle='dotted', label='z')
#axs.plot(est_error, c = 'b', linestyle='dashed', label='x-error')
axs.plot(y_error, c = 'b', label='y-error')
#axs.legend()

axs.set_axisbelow(True)
axs.set_xlabel('Time step k')
axs.set_ylabel('Input')
axs.legend(loc='lower right')
plt.grid(True)

plt.show()


"""
##########################
# Plot estimation error
##########################
fig, axs = plt.subplots(1, figsize=(10,5), facecolor='w', edgecolor='k')
plt.subplots_adjust(hspace=0.6, left=0.18, right=0.95, top=0.95, bottom=0.18)

axs.plot(est_error*100, c = 'k')

axs.set_axisbelow(True)
axs.set_xlabel('Time step k')
axs.set_ylabel('Error (%%)')
plt.grid(True)
#plt.savefig('/Users/atsol/research/papers/AIAA-MPC-of-LSMS/figures/case_3_inputs.eps')

plt.show()


"""



