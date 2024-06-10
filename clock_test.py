'''
This code is for demostrate clock in psychopy
'''
# import psychopy here
from psychopy import visual, core, event

# create a clock
clock = core.Clock()

# start the clock
clock.reset()

### Use a loop to keep track of time and print the time elapsed
while True:
    # Get the time elapsed
    time_elapsed = clock.getTime()
    
    # Print the time elapsed
    print(time_elapsed)
    
    # Check if the 'q' key is pressed
    if 'q' in event.getKeys():
        break



