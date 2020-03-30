import numpy as np
import matplotlib.pyplot as plt
plt.rc('text', usetex=True)
plt.rc('font', size=24)
from matplotlib import animation
from matplotlib import patches
import time
from scipy import signal

# Class defining the snapshot grid
class grid(object):
    def __init__(self, case_name, skip_points=1):
        print('\nReading shapshot grid:')

        # Grid data - Load full grid
        grid_full = np.load('data/' + case_name + '-grid.npy')
        npx_full = np.unique(grid_full[:,0]).shape[0]
        npz_full = np.unique(grid_full[:,2]).shape[0]
        npoints_full = npx_full*npz_full

        # Indices of grid points to be used
        self.skip_points = skip_points
        x_idx = np.arange(0,npx_full,skip_points)
        z_idx = np.arange(0,npz_full,skip_points)
        self.idx = np.ravel_multi_index((x_idx[:,np.newaxis], z_idx), (npx_full, npz_full)).flatten()

        # Keep only fine grid points (specified by self.idx)
        self.grid = grid_full[self.idx,:]
        self.x = self.grid[:,0]
        self.z = self.grid[:,2]
        self.npx = np.unique(self.x).shape[0]
        self.npz = np.unique(self.z).shape[0]
        self.npoints = self.npx*self.npz

        # Grid limits
        self.xmin = np.min(self.x)
        self.xmax = np.max(self.x)
        self.zmin = np.min(self.z)
        self.zmax = np.max(self.z)

        # Print info
        print('    Grid size:   ', self.npx, 'x', self.npz, ' = ', self.npoints)
        print('               of', npx_full, 'x', npz_full, ' = ', npoints_full)

    def X(self):
        return self.x.reshape((self.npx, self.npz))

    def Z(self):
        return self.z.reshape((self.npx, self.npz))

    def unravel(self, m):
        return np.unravel_index(m, (self.npx, self.npz))

    def ravel(self, m):
        return np.ravel_multi_index(m, (self.npx, self.npz))

    def export_to_tecplot(self, fname):
        F = open(fname, 'w')
        F.write('filetype = grid, variables = "x", "y", "z"\n')
        F.write('zone f=point t="Control Grid",' + 'i=' + str(self.npx) + ' j=' + str(1) + ' k=' + str(self.npy) + '\n')

        for i in range(self.npoints):
            F.write(str(self.grid[i,0]) + ' ' + str(0.0) + ' ' + str(self.grid[i,1]) + '\n')
        
        F.close()




class flow_data(object):

    def __init__(self, grid, case_name, timestep_skip=1, start=0, end=None):

        print('\nReading shapshots for case', case_name, '\b:')

        self.grid = grid
        self.idx = grid.idx
        self.npoints = grid.npoints
        self.nvariables = 1
        self.ny = self.npoints*self.nvariables

        self.npx = grid.npx
        self.npz = grid.npz

        # Input data
        u = np.load('data/' + case_name + '-input.npy')
        self.ptotal = u.shape[1] # Number of snapshots
        self.u = u[:,start:end:timestep_skip]
        self.nu = u.shape[0] # Number of inputs

        if end is None:
            end = self.ptotal

        # Flow data
        self.timestep_skip = timestep_skip
        self.p = (end - start)//timestep_skip # Number of snapshots available
        self.wy = np.load('data/' + case_name + '-wy.npy')[self.idx,start:end:timestep_skip]

        # Time series
        self.t = np.expand_dims(np.array(range(self.p)), axis=0)

        # First snapshot
        self.wy_0 = self.wy[:,0]

        # Print info
        print('    Number of snapshots: %d of %d available' % (self.p, self.ptotal))
        print('    Number of variables: ', self.nvariables)
        print('    Number of outputs: ', self.ny)
        print('    First snapshot: ', start)
        print('    Last snapshot:  ', end)
        print('    Skipping every %d time steps' % timestep_skip)
        

    def ravel(self, m):
        return np.ravel_multi_index(m, (self.npx, self.npz))


    def plot(self):
        nlevels = 41
        wymin = -10
        wymax = 10

        X = self.grid.X()
        Z = self.grid.Z()
        xmax = np.max(X)
        
        def WY(k):
            return self.wy[:,k].reshape((self.npx, self.npz))

        fig, axs = plt.subplots(1, figsize=(10,5), facecolor='w', edgecolor='k')
        cont = axs.contourf(X, Z, WY(0), nlevels, cmap='coolwarm', vmin=wymin, vmax=wymax)
       #plt.clim(wymin, wymax)
        cbar = fig.colorbar(cont, ax=axs, orientation='vertical')
       #cbar.ax.set_autoscale_on(True)
        cbar.set_ticks(np.linspace(wymin, wymax, num=6, endpoint=True))

        # Flat plate patch
        delx = 5.0/768.0
        delz = 2.0/384.0
        xc = 249*delx
        zc = 192*delz
        alpha = 20.0*np.pi/180.0
        DL = 80*delx
        DT = 6*delz
        flat_plate = patches.Rectangle((xc - DL*np.cos(alpha)/2. - DT*np.sin(alpha)/2.,
                                        zc + DL*np.sin(alpha)/2. - DT*np.cos(alpha)/2.),
                                        DL,
                                        DT,
                                        angle=-(alpha*180.0/np.pi),
                                        linewidth=1, edgecolor='black', facecolor='black')
        axs.add_patch(flat_plate)
        axs.set_xlim([1,xmax])
       #cbar.ax.locator_params(nbins=6)

        def animate(k):
            axs.clear()
            cont = axs.contourf(X, Z, WY(k), nlevels, cmap='coolwarm', vmin=wymin, vmax=wymax)
            axs.set_xlabel('$x$')
            axs.set_ylabel('$z$')
            axs.set_aspect('equal', 'box')
            axs.add_patch(flat_plate)
            axs.set_xlim([1,xmax])
            
            return cont

        anim = animation.FuncAnimation(fig, animate, frames = range(0,self.p,4), interval=100)

        return anim

