import pygame
from psychopy import visual, core, event
import numpy as np

# from pygame.locals import *

class controller:
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
        self.x_left = self.joystick.get_axis(0)
        self.y_left = self.joystick.get_axis(1)
        self.x_right = self.joystick.get_axis(2)
        self.y_right = self.joystick.get_axis(3)
        
        # if the joystick is not centered in a small range, set it to 0
        if abs(self.x_left) < self.centreRange:
            self.x_left = 0
        if abs(self.y_left) < self.centreRange:
            self.y_left = 0
        if abs(self.x_right) < self.centreRange:
            self.x_right = 0
        if abs(self.y_right) < self.centreRange:
            self.y_right = 0
            
        
        self.buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
        
        if print_state:
                    print(f"Left Stick: ({self.x_left}, {self.y_left})\tRight Stick: ({self.x_right}, {self.y_right})\tButtons: {self.buttons}")
        return self.x_left, self.y_left, self.x_right, self.y_right, self.buttons
    
    def get_xy(self, side='right'):
        if side == 'left':
            return self.joystick.get_axis(0), self.joystick.get_axis(1)
        elif side == 'right':
            return self.joystick.get_axis(2), self.joystick.get_axis(3)
        
    def shootDetection(self, side='right'):
        '''
        If xy exceeds a certain threshold, shoot
        '''
        # Get the xy values
        x, y = self.get_xy(side)
        
        # calculate the magnitude of the vector
        magnitude = np.sqrt(x**2 + y**2)
        direction = np.array([x, y])
        
        if magnitude > self.shootThreshold:
            return True, direction
        else:
            return False, direction        
    
    def close(self):
        pygame.quit()
        
        
if __name__ == "__main__":
    # Test the controller
    controller = controller()
    while True:
        isShoot, direction = controller.shootDetection()
        print(f"Shoot: {isShoot}\tDirection: {direction}")
        
        if 'escape' in event.getKeys():
            break
        
    controller.close()        
    
        