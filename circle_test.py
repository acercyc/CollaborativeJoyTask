from psychopy import visual, core, event
import numpy as np
radius = 0.5  # Adjust the radius value according to the new unit

# Create a window
win = visual.Window(
    size=[800, 800],  # Adjust the size value according to the new unit
    units="height",  # Change units to "height"
    fullscr=False, 
    color=[1, 1, 1],
    screen=1  # Use the second monitor
)

# Create a circle
circle = visual.Circle(
    win=win, 
    radius=radius,  # Increase the radius to make the circle bigger
    edges=128,  
    lineColor=[1, -1, -1],  
    fillColor=None,  
    lineWidth=3  # Adjust the lineWidth value according to the new unit
)

# Create a small ball at the center
center_ball = visual.Circle(
    win=win, 
    radius=0.01,  # Adjust the radius value according to the new unit
    pos=(0, 0),  # Position at the center
    edges=128,  
    lineColor=[-1, -1, -1],  # Set the color of the ball
    fillColor=[-1, -1, -1],  # Set the fill color of the ball
    lineWidth=3  # Adjust the lineWidth value according to the new unit
)

# Create an additional ball that will move along the circle
moving_ball = visual.Circle(
    win=win,
    radius=0.02,  # Adjust the radius value according to the new unit
    edges=128,
    lineColor=[-1, -1, -1],  # Set the color of the ball
    fillColor=[-1, -1, -1],  # Set the fill color of the ball
    lineWidth=3  # Adjust the lineWidth value according to the new unit
)
# Set the speed of the moving ball
speed = 1

# Create a clock to keep track of time
clock = core.Clock()

# Start a loop to animate the moving ball
while True:
    
    # Calculate the new position of the moving ball
    t = clock.getTime() * speed
    x = radius * np.cos(t)
    y = radius * np.sin(t)

    # Update the position of the moving ball
    moving_ball.pos = (x, y)

    # Draw the circle and the balls
    circle.draw()
    center_ball.draw()
    moving_ball.draw()

    # Flip the window to show the drawn circle and balls
    win.flip()

    # Break the loop if a key is pressed
    if len(event.getKeys()) > 0:
        break

    # Clear the event buffer
    event.clearEvents()