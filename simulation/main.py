import numpy as np
import matplotlib.pyplot as plt



class FrisbeeSimulator():
    def __init__(self):
        """ PARAMETERS """
        # The acceleration of gravity (m/s^2).
        self.g = -9.82
        # The mass of a standard frisbee in kilograms.
        self.mass = .175
        # The density of air in kg/m^3.
        self.rho = 1.23
        # The area of a standard frisbee.
        self.area = .0568
        # The lift coefficient at alpha = 0.
        self.cl0 = .1
        # The lift coefficient dependent on alpha.
        self.cla = 1.4
        # The drag coefficent at alpha = 0.
        self.cd0 = .08
        # The drag coefficient dependent on alpha.
        self.cda = 2.72
        self.alpha0 = -4. * np.pi / 180
        # Time step size
        self.dt = .001
        # Initial position (static)
        self.x0 = 0.
        self.y0 = 1.

    def simulate(self, initial_speed, initial_angle, full_path=True):
        x = self.x0
        y = self.y0
        # Compute initial velocities
        vx = initial_speed * np.cos(initial_angle)
        vy = initial_speed * np.sin(initial_angle)
        # Compute lift and drag
        Cl = self.cl0 + self.cla * initial_angle
        Cd = self.cd0 + self.cda * (initial_angle - self.alpha0) ** 2
        x_vals, y_vals = [], []
        while y >= 0.:
            # Compute acceleration
            ax = -(self.rho * (vx ** 2) * self.area * Cd) / (2 * self.mass) * self.dt
            ay = (self.g + (self.rho * (vx ** 2) * self.area * Cl) / (2 * self.mass)) * self.dt
            # Compute velocity and position
            vx += ax
            vy += ay
            x += vx * self.dt
            y += vy * self.dt
            x_vals.append(x)
            y_vals.append(y)
        
        if full_path:
            return x_vals, y_vals
        else:
            return x
            




if __name__ == "__main__":
    # Create simulation object
    sim = FrisbeeSimulator()
    
    # Ranges of angles and speeds
    speed_vals = np.linspace(1., 25., num=50)
    angle_vals = np.linspace(0., 1., num=50)


    """
    # Fix speed, vary angle
    intial_speed = 10.
    dists = [sim.simulate(intial_speed, angle, full_path=False) for angle in angle_vals]

    # Angle plot
    plt.plot(angle_vals, dists)
    plt.show()

    # Fix angle, vary speed
    initial_angle = .2
    dists = [sim.simulate(speed, initial_angle, full_path=False) for speed in speed_vals]

    # Speed plot 
    plt.plot(speed_vals, dists)
    plt.show()
    """

    