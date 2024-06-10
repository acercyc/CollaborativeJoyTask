from psychopy import core, visual, event
import multiprocessing

# Example functions
def function1():
    win = visual.Window([800, 600])
    for frame in range(60):  # Run for 60 frames
        win.flip()
        if event.getKeys(["escape"]):
            break
    win.close()
    print("Function 1 finished")

def function2():
    win = visual.Window([800, 600])
    for frame in range(90):  # Run for 90 frames
        win.flip()
        if event.getKeys(["escape"]):
            break
    win.close()
    print("Function 2 finished")

# Create processes for both functions
process1 = multiprocessing.Process(target=function1)
process2 = multiprocessing.Process(target=function2)

# Start the processes
process1.start()
process2.start()

# Wait for both processes to complete
process1.join()
process2.join()

core.quit()
    