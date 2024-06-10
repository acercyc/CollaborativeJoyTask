import numpy as np
from psychopy import visual, core, event
import pygame

target_radius = 0.8

class Target:
    def __init__(self, win, circle_radius=0.8, bar_length=0.1, bar_thickness=0.01, speed=0.02):
        self.circle_radius = circle_radius
        self.bar_length = bar_length
        self.bar_thickness = bar_thickness
        self.speed = speed # Speed of the movement (radians per frame)
        self.bar = visual.Rect(win, width=bar_thickness, height=bar_length, fillColor='black', lineColor='black')
        self.circle = visual.Circle(win, radius=circle_radius, fillColor='white', lineColor='black')
        self.angle = 0  # Initialize angle to 0
    
    def angle2position(self, angle):
        x_pos = self.circle_radius * np.cos(angle)
        y_pos = self.circle_radius * np.sin(angle)
        self.bar.pos = (x_pos, y_pos)
        self.bar.ori = -np.degrees(angle) + 90
        
    def update_position(self):
        self.angle += self.speed  # Update angle based on speed
        self.angle2position(self.angle)    
        
    def reset(self, isRandAngle=False):
        if isRandAngle:
            self.angle = np.random.rand() * 2 * np.pi
        else:
            self.angle = 0
        self.angle2position(self.angle)
        
    def draw(self):
        self.circle.draw()
        self.bar.draw()


class Bullet:
    def __init__(self, win, radius=0.02, color='red', speed=0.1):
        self.bullet = visual.Circle(win, radius=radius, fillColor=color, lineColor=color)
        self.speed = speed
        self.pos = np.array([0.0, 0.0])
        self.direction = None
        
    def update_position(self):
        self.pos += self.speed * self.direction
        self.pos = np.clip(self.pos, -1, 1)
        self.bullet.pos = self.pos

    def draw(self):
        self.bullet.draw()
        
    def reset(self):
        self.pos = np.array([0.0, 0.0])
        self.bullet.pos = self.pos
        self.direction = None
        
    def set_position(self, x, y):
        self.pos = np.array([x, y])
        self.bullet.pos = self.pos
        
        

class Controller:
    def __init__(self, device=0):
        pygame.init()
        self.joystick = pygame.joystick.Joystick(device)  # Initialize the first joystick
        self.joystick.init()
        self.x_left = 0
        self.y_left = 0
        self.x_right = 0
        self.y_right = 0
        self.buttons = [0] * self.joystick.get_numbuttons()
        self.centreRange = 0.0001
        self.shootThreshold = 0.8
        

    def get_state(self, print_state=False):
        # Axis 0: Left Stick Left -> Right
        # Axis 1: Left Stick Up -> Down
        # Axis 2: Right Stick Left -> Right
        # Axis 3: Right Stick Up -> Down
        # Button 0: A Button
        # Button 1: B Button
        # Button 2: X Button
        # Button 3: Y Button
        # Button 4: Left Bumper
        # Button 5: Right Bumper
        # Button 6: Back Button
        # Button 7: Start Button
        # Button 8: Left Stick In
        # Button 9: Right Stick In
        # Button 10: Guide Button 
        pygame.event.pump()

        # Get the current state of the joystick
        self.x_left, self.y_left = self.get_xy('left')
        self.x_right, self.y_right = self.get_xy('right')
        
        
        self.buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
        
        if print_state:
                    print(f"Left Stick: ({self.x_left}, {self.y_left})\tRight Stick: ({self.x_right}, {self.y_right})\tButtons: {self.buttons}")
        return self.x_left, self.y_left, self.x_right, self.y_right, self.buttons
    
    def get_xy(self, side='right'):
        if side == 'left':
            x = self.joystick.get_axis(0)
            y = self.joystick.get_axis(1)
        elif side == 'right':
            x = self.joystick.get_axis(2)
            y = self.joystick.get_axis(3)
            
        # remapping
        y = -y
            
        # if the joystick is not centered in a small range, set it to 0
        if abs(x) < self.centreRange:
            x = 0.0
        if abs(y) < self.centreRange:
            y = 0.0
        
        return x, y
    
    def get_button(self, button):
        return self.joystick.get_button(button)
        
        
    def shootDetection(self, side='right'):
        '''
        If xy exceeds a certain threshold, shoot
        '''
        # Get the xy values
        x, y = self.get_xy(side)
        
        # calculate the magnitude of the vector
        magnitude = np.sqrt(x**2 + y**2)
        direction = np.array([x, y])
        
        # normalise the direction vector to the unit vector
        if magnitude > 0:
            direction = direction / magnitude
        
        if magnitude > self.shootThreshold:
            return True, direction
        else:
            return False, direction        
    
    def close(self):
        pygame.quit()


class Player:
    def __init__(self, win):
        self.target = Target(win, circle_radius=target_radius)
        self.bullet = Bullet(win)
        self.controller = Controller()
        
    def run_shooting(self):
        pass
        
    
    
    
    
    
# Create a window
win = visual.Window([800, 800], color=(0.5, 0.5, 0.5), screen=0)
target = Target(win, circle_radius=target_radius)
bullet = Bullet(win)
controller = Controller()


# Define the parameters for the target movement
# frequency = 0.05  # Frequency of the movement (Hz)
# duration = 20     # Duration of the trial (seconds)
# clock = core.Clock()  # Create a clock to track time


# Initialize the controller

# Run the experiment for the specified duration
while True:
    isShoot = False
    isPlay = True
    bullet.reset()
    target.reset(isRandAngle=True)
    
    
    while True:
        if not isShoot:
            # Get the shoot detection
            isShoot, direction = controller.shootDetection()
        else:
            if bullet.direction is None:
                bullet.direction = direction
                
            # update the states of the bullet and target
            bullet.update_position()
            
            # if the distance is large ane equal to the radius of the circle, 
            # 1. set the position on the circle 
            # 2. stop the bullet update
            # 3. stop target update
            distance = np.linalg.norm(bullet.pos)        
            if distance >= target_radius:
                bullet.set_position(target_radius * bullet.direction[0], target_radius * bullet.direction[1])
                isPlay = False

    
        target.update_position()
    
        # Draw 
        target.draw()
        bullet.draw()
        
        # Flip the window
        win.flip()
        
        if not isPlay:
            break

    # Wait for a button press to start the next trial
    while True:
        if controller.get_button(0) == 1:
            break
        
        core.wait(0.001)
        

# win.close()
