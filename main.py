import numpy as np
from psychopy import visual, core, event
from psychopy.hardware import keyboard
import pygame

target_radius = 0.4
nPlayers = 2
refresh_rate = 60
isFullScreen = False
isShowPath = True
isShowSelfShot = True
isCountdown = True
countDownColor = ['red', 'Orange', 'LawnGreen']
countDownTime = [2, 3]

ctrlMapping = {
    "left_stick_lr": 0,
    "left_stick_ud": 1,
    "right_stick_lr": 2,
    "right_stick_ud": 3,
    "A": 0,
    "B": 1,
    "X": 2,
    "Y": 3,
    "left_bumper": 4,
    "right_bumper": 5,
    "back": 6,
    "start": 7,
    "left_stick_in": 8,
    "right_stick_in": 9,
    "guide": 10,
}


# ---------------------------------------------------------------------------- #
#                             Experimental objects                             #
# ---------------------------------------------------------------------------- #
class Target:
    def __init__(
        self, win, circle_radius=0.8, bar_length=0.05, bar_thickness=0.005, speed=0.02
    ):
        self.circle_radius = circle_radius
        self.bar_length = bar_length
        self.bar_thickness = bar_thickness
        self.speed = speed  # Speed of the movement (radians per frame)
        self.bar = visual.Rect(
            win,
            width=bar_thickness,
            height=bar_length,
            fillColor="black",
            lineColor="black",
        )
        self.circle = visual.Circle(
            win, radius=circle_radius, fillColor="white", lineColor="black", lineWidth=3
        )
        self.angle = 0  # Angle in radians

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
        self.circle.lineColor = "black"

    def draw(self):
        self.circle.draw()
        self.bar.draw()


class Bullet:
    def __init__(self, win, radius=0.01, fillColor="blue", lineColor='blue', speed=0.05):
        self.bullet = visual.Circle(
            win, radius=radius, fillColor=fillColor, lineColor=lineColor, lineWidth=2
        )
        self.speed = speed
        self.pos = np.array([0.0, 0.0])
        self.direction = None
        
    def get_angle(self):
        return np.arctan2(self.pos[1], self.pos[0])
    
    def set_direction_from_angle(self, angle):
        self.direction = np.array([np.cos(angle), np.sin(angle)])

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


class Rating:
    def __init__(self, win):
        self.win = win
        self.xRange = 0.5
        self.marker = visual.Rect(win, width=0.1, height=0.01, fillColor="black")
        self.line = visual.line(
            win, width=0.005, start=(-self.xRange, 0), end=(self.xRange, 0)
        )
        self.rating = 50

    def draw(self):
        self.marker.pos = (self.rating / 100 * self.xRange, 0)
        self.marker.draw()
        self.line.draw()


class Controller:
    def __init__(self, device=0):
        pygame.init()
        self.joystick = pygame.joystick.Joystick(
            device
        )  # Initialize the first joystick
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
        self.x_left, self.y_left = self.get_xy("left")
        self.x_right, self.y_right = self.get_xy("right")

        self.buttons = [
            self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())
        ]

        if print_state:
            print(
                f"Left Stick: ({self.x_left}, {self.y_left})\tRight Stick: ({self.x_right}, {self.y_right})\tButtons: {self.buttons}"
            )
        return self.x_left, self.y_left, self.x_right, self.y_right, self.buttons

    def get_xy(self, side="right"):
        if side == "left":
            x = self.joystick.get_axis(0)
            y = self.joystick.get_axis(1)
        elif side == "right":
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

    def shootDetection(self, side="right"):
        """
        If xy exceeds a certain threshold, shoot
        """
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


class Rating:
    def __init__(self, win, controller, markerSpeed=1):
        self.win = win
        self.controller = controller
        self.markerSpeed = markerSpeed
        self.ratingRange = [0, 100]
        self.ratingTick = [0, 50, 100]
        self.scale = visual.RatingScale(
            win,
            pos=(0, 0.2),
            low=self.ratingRange[0],
            high=self.ratingRange[1],
            precision=100,  # Set precision to 0.01 for finer control
            tickMarks=self.ratingTick,
            markerStart=50,
            marker="triangle",
            showAccept=False,
            scale=None,
            lineColor="black",
            textSize=1,
            textColor="black",
            stretch=2,
            mouseOnly=False,
        )

        self.scale2 = visual.RatingScale(
            win,
            pos=(0, -0.2),
            low=self.ratingRange[0],
            high=self.ratingRange[1],
            precision=100,  # Set precision to 0.01 for finer control
            tickMarks=self.ratingTick,
            markerStart=50,
            marker="triangle",
            showAccept=False,
            scale=None,
            lineColor="black",
            textSize=1,
            textColor="black",
            stretch=2,
            mouseOnly=False,
        )

        # upper text
        self.text = visual.TextStim(
            win, text="Your contribution", pos=(0, 0.3), color="black", height=0.05
        )

        # lower text
        self.text2 = visual.TextStim(
            win,
            text="Partner's contribution",
            pos=(0, -0.3),
            color="black",
            height=0.05,
        )

    def update(self):
        x, _ = self.controller.get_xy()
        rating = self.scale.getRating()
        rating += x * self.markerSpeed
        # check if raing is in the range
        if rating < self.ratingRange[0]:
            rating = self.ratingRange[0]
        elif rating > self.ratingRange[1]:
            rating = self.ratingRange[1]
        self.scale.setMarkerPos(rating)
        return rating

    def update2(self, rating):
        self.scale2.setMarkerPos(rating)

    def set_marker_color(self, color):
        self.scale._setMarkerColor(color)

    def set_marker_color2(self, color):
        self.scale2._setMarkerColor(color)

    def reset(self):
        self.scale.reset()
        self.scale2.reset()

    def draw(self):
        self.scale.draw()
        self.scale2.draw()
        self.text.draw()
        self.text2.draw()


class Feedback:
    def __init__(self, win):
        self.win = win

        # line
        self.xRange = 0.45  # Added parameter for xRange
        self.line = visual.Line(
            self.win, start=(-self.xRange, 0), end=(self.xRange, 0), lineColor="black"
        )
        self.zero_marker = visual.Line(
            self.win, start=(0, -0.01), end=(0, 0.01), lineColor="black"
        )
        self.left_marker = visual.Line(
            self.win,
            start=(-self.xRange, -0.01),
            end=(-self.xRange, 0.01),
            lineColor="black",
        )
        self.right_marker = visual.Line(
            self.win,
            start=(self.xRange, -0.01),
            end=(self.xRange, 0.01),
            lineColor="black",
        )

        # text
        self.textHeight = 0.02  # Renamed from tickTextHeight to textHeight
        self.textPos = -0.05  # Extracted as a parameter for text position
        self.zero_text = visual.TextStim(
            self.win,
            text="0",
            pos=(0, self.textPos),
            color="black",
            height=self.textHeight,
            bold=True,
        )
        self.left_text = visual.TextStim(
            self.win,
            text="-180",
            pos=(-self.xRange, self.textPos),
            color="black",
            height=self.textHeight,
            bold=True,
        )
        self.right_text = visual.TextStim(
            self.win,
            text="180",
            pos=(self.xRange, self.textPos),
            color="black",
            height=self.textHeight,
            bold=True,
        )

        # point
        self.points = [
            visual.Circle(
                self.win,
                radius=0.008,
                fillColor=None,
                lineColor="blue",
                pos=(0, 0),
                lineWidth=4,
            ),
            visual.Circle(
                self.win,
                radius=0.008,
                fillColor=None,
                lineColor="blue",
                pos=(0, 0),
                lineWidth=2,
            ),
        ]
        self.point_average = visual.Circle(
            self.win,
            radius=0.01,
            fillColor=None,
            lineColor="red",
            pos=(0, 0),
            lineWidth=4,
        )

    def draw(self, diffs, jointDiff=None):
        diffs = np.array(diffs) / 360 * self.xRange
        self.line.draw()
        self.zero_marker.draw()
        self.left_marker.draw()
        self.right_marker.draw()
        self.zero_text.draw()
        self.left_text.draw()
        self.right_text.draw()

        # draw all diffs
        for i, diff in enumerate(diffs):
            self.points[i].pos = (diff, 0)
            self.points[i].draw()

        if jointDiff is not None:
            jointDiff = jointDiff / 360 * self.xRange
            self.point_average.pos = (jointDiff, 0)
            self.point_average.draw()


class ButtonIndicator:
    def __init__(self, win):
        self.win = win
        self.size = 0.05
        # a small square to indicate the button press
        self.indicators = [
            visual.Rect(
                win,
                width=self.size,
                height=self.size,
                fillColor=None,
                lineColor="black",
                lineWidth=2,
                pos=(-0.45, -0.45),
            ),
            visual.Rect(
                win,
                width=self.size,
                height=self.size,
                fillColor=None,
                lineColor="black",
                lineWidth=2,
                pos=(0.45, -0.45),
            ),
        ]

    def draw(self, isPress1, isPress2):
        if isPress1:
            self.indicators[0].fillColor = "green"
        else:
            self.indicators[0].fillColor = None

        if isPress2:
            self.indicators[1].fillColor = "green"
        else:
            self.indicators[1].fillColor = None

        for indicator in self.indicators:
            indicator.draw()


class Player:
    def __init__(self, win, controllerID=0):
        # External instances
        self.win = win

        # Internal instances
        self.target = Target(win, circle_radius=target_radius)
        self.bullet = Bullet(win, lineColor=None)
        self.bullet_joint = Bullet(win, fillColor=None, lineColor="red")
        self.controller = Controller(device=controllerID)
        self.instruction = visual.TextStim(
            win, text="Instruction is empty", color="black", height=0.05
        )
        self.rating = Rating(win, self.controller)
        self.feedback = Feedback(win)
        self.buttonIndicator = ButtonIndicator(win)


class Coordinator:
    def __init__(self, players):
        self.players = players

    def waitButtonPress(self, button=0, clearBuffer=False):
        isPress = np.array([False, False])
        while np.any(isPress == False):
            for i in range(nPlayers):
                if isPress[i] == False:
                    isPress[i] = self.players[i].controller.get_button(button) == 1

            self.players[0].buttonIndicator.draw(isPress[0], isPress[1])
            self.players[0].win.flip(clearBuffer=clearBuffer)

            self.players[1].buttonIndicator.draw(isPress[1], isPress[0])
            self.players[1].win.flip(clearBuffer=clearBuffer)


# ---------------------------------------------------------------------------- #
#                                   decerator                                  #
# ---------------------------------------------------------------------------- #
# make a decorator that can run the function for 2 players
def apply_multiplayer(func):
    def wrapper(players, *args, **kwargs):
        # check if list
        if not isinstance(players, list):
            players = [players]

        # run the function for each player
        ouputs = [None, None]
        for player in players:
            ouputs[i] = func(player, *args, **kwargs)

        return ouputs

    return wrapper


def apply_multiplayer_wait(func):
    """
    The applied function need to return isRunning
    """

    def wrapper(players, *args, **kwargs):
        if not isinstance(players, list):
            players = [players]

        isRunning = [True] * len(players)
        outputs = [None] * len(players)
        while np.any(isRunning):
            for i in range(nPlayers):
                if isRunning[i]:
                    isRunning[i], outputs[i] = func(players[i], *args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------- #
#                                     math                                     #
# ---------------------------------------------------------------------------- #
def angleDiff(origin, x):
    """
    Compute the angle difference between angle A and angle B
    considering circular coordinates and keeping the difference within 180 degrees.

    :param A: Angle A in degrees
    :param B: Angle B in degrees
    :return: Angle difference in degrees
    """
    # Normalize both angles to the range [0, 360)
    origin = origin % 360
    x = x % 360

    # Compute the raw difference
    diff = x - origin

    # Adjust the difference to be within [-180, 180)
    if diff >= 180:
        diff -= 360
    elif diff < -180:
        diff += 360

    return diff


def calWeightedAverage(angles, weights):
    """
    Calculate the weighted average of a list of angles
    """
    angles = np.array(angles)
    weights = np.array(weights)

    # normalise the weights
    weights = np.array(weights) / np.sum(weights)

    # compute the weighted average
    return np.dot(weights, angles)


# ---------------------------------------------------------------------------- #
#                                    design                                    #
# ---------------------------------------------------------------------------- #
def checkQuit(key="escape"):
    keys = kb.getKeys()
    if key in keys:
        core.quit()


def run_shooting(speed, isShowPath=False, isCountdown=False):
    isShoots = [False, False]
    isPlay = [True, True]
    isCountdown = [isCountdown, isCountdown]
    directions = [None, None]
    distances = [None, None]
    target_angle = [None, None]
    bullet_angle = [None, None]
    for i in range(nPlayers):
        players[i].bullet.reset()
        players[i].bullet_joint.reset()
        players[i].target.reset(isRandAngle=True)
        players[i].target.speed = speed[i]

    t0 = core.getTime()
    while np.any(isPlay):
        checkQuit()
        for i in range(nPlayers):

            if isPlay[i]:
                if isCountdown[i]:
                    t = core.getTime()
                    if t - t0 < countDownTime[0]:
                        players[i].target.circle.lineColor = countDownColor[0]
                    elif t - t0 < countDownTime[1]:
                        players[i].target.circle.lineColor = countDownColor[1]
                    else:
                        players[i].target.circle.lineColor = countDownColor[2]
                        isCountdown[i] = False
                else:

                    if not isShoots[i]:
                        # Get the shoot detection
                        isShoots[i], directions[i] = players[i].controller.shootDetection()
                    else:
                        if players[i].bullet.direction is None:
                            players[i].bullet.direction = directions[i]

                        # update the states of the bullet and target
                        players[i].bullet.update_position()

                        # if the distance is large ane equal to the radius of the circle,
                        # 1. set the position on the circle
                        # 2. stop the bullet update
                        # 3. stop target update
                        distances[i] = np.linalg.norm(players[i].bullet.pos)
                        if distances[i] >= target_radius:
                            players[i].bullet.set_position(
                                target_radius * players[i].bullet.direction[0],
                                target_radius * players[i].bullet.direction[1],
                            )
                            isPlay[i] = False
                            target_angle[i] = players[i].target.angle
                            bullet_angle[i] = np.arctan2(
                                players[i].bullet.pos[1], players[i].bullet.pos[0]
                            )

                players[i].target.update_position()

                # Draw
                players[i].target.draw()
                if isShowPath:
                    players[i].bullet.draw()
                players[i].bullet_joint.draw()
                players[i].win.flip()

    # convert the angle to degree
    target_angle = np.degrees(target_angle)
    bullet_angle = np.degrees(bullet_angle)

    return target_angle, bullet_angle


def run_raiting():
    for i in range(nPlayers):
        players[i].rating.reset()
    isPlay = [True, True]
    rating = [50, 50]
    while np.any(isPlay):
        checkQuit()

        for i in range(nPlayers):
            if isPlay[i]:
                if players[i].controller.get_button(0) == 1:
                    isPlay[i] = False
                    players[i].rating.set_marker_color("green")
                    if i == 0:
                        players[1].rating.set_marker_color2("green")
                    elif i == 1:
                        players[0].rating.set_marker_color2("green")

                rating[i] = players[i].rating.update()
                if i == 0:
                    players[1].rating.update2(rating[0])
                elif i == 1:
                    players[0].rating.update2(rating[1])

        for i in range(nPlayers):
            players[i].rating.draw()
            players[i].win.flip()
    return rating


def run_cleanScreen():
    for i in range(nPlayers):
        players[i].win.flip()


def run_startExp(button=0):
    isPress = np.array([False, False])
    while np.any(isPress == False):
        checkQuit()
        for i in range(nPlayers):
            players[i].instruction.text = (
                "Welcome to the experiment\nPlease press A to continue"
            )
            players[i].instruction.draw()
            if isPress[i] == False:
                isPress[i] = players[i].controller.get_button(button) == 1

        players[0].buttonIndicator.draw(isPress[0], isPress[1])
        players[0].win.flip()

        players[1].buttonIndicator.draw(isPress[1], isPress[0])
        players[1].win.flip()


def run_instruction(instruction):
    for i in range(nPlayers):
        players[i].instruction.text = instruction
        players[i].instruction.draw()
        players[i].win.flip()


def run_instruction_waitPress(instruction, button=0):
    isPress = np.array([False, False])
    while np.any(isPress == False):
        checkQuit()
        for i in range(nPlayers):
            players[i].instruction.text = instruction
            players[i].instruction.draw()
            if isPress[i] == False:
                isPress[i] = players[i].controller.get_button(button) == 1

        players[0].buttonIndicator.draw(isPress[0], isPress[1])
        players[0].win.flip()

        players[1].buttonIndicator.draw(isPress[1], isPress[0])
        players[1].win.flip()


def run_feedback(diffs, jointDiff=None, button=0):
    isPress = np.array([False, False])
    while np.any(isPress == False):
        checkQuit()
        for i in range(nPlayers):
            if isPress[i] == False:
                isPress[i] = players[i].controller.get_button(button) == 1

        players[0].feedback.draw(diffs, jointDiff=jointDiff)
        players[0].buttonIndicator.draw(isPress[0], isPress[1])
        players[0].win.flip()

        players[1].feedback.draw(np.flip(diffs), jointDiff=jointDiff)
        players[1].buttonIndicator.draw(isPress[1], isPress[0])
        players[1].win.flip()


def run_feedback_jointShoot(jointDiff=None, isShowSelfShot=False, button=0):
    isPlay = [True, True]
    isPress = np.array([False, False])
    distances = [None, None]
    for i in range(nPlayers):
        players[i].bullet_joint.reset()
        angle = players[i].target.angle
        angle += np.radians(jointDiff)
        players[i].bullet_joint.set_direction_from_angle(angle)                
    
    while np.any(isPlay):
        checkQuit()
        for i in range(nPlayers):
            players[i].bullet_joint.update_position()
            distances[i] = np.linalg.norm(players[i].bullet_joint.pos)
            if distances[i] >= target_radius:
                players[i].bullet_joint.set_position(
                    target_radius * players[i].bullet_joint.direction[0],
                    target_radius * players[i].bullet_joint.direction[1],
                )
                isPlay[i] = False       
            players[i].target.draw()
            players[i].bullet_joint.draw()
            players[i].win.flip()
            


# ---------------------------------------------------------------------------- #
#                               start experiment                               #
# ---------------------------------------------------------------------------- #
if __name__ == "__main__":

    # ------------------------------ initialisation ------------------------------ #
    kb = keyboard.Keyboard()

    # windows
    wins = [
        visual.Window(
            [800, 800],
            color=(0.5, 0.5, 0.5),
            units="height",
            screen=0,
            fullscr=isFullScreen,
            waitBlanking=False,
        ),
        visual.Window(
            [800, 800],
            color=(0.5, 0.5, 0.5),
            units="height",
            screen=1,
            fullscr=isFullScreen,
            waitBlanking=True,
        ),
    ]

    # players
    players = [Player(wins[0], controllerID=0), Player(wins[1], controllerID=1)]

    # parameters
    iTrial = 1
    nTrial = 100

    # ---------------------------------------------------------------------------- #
    #                             start the experiment                             #
    # ---------------------------------------------------------------------------- #
    # start message
    # instruction = "Welcome to the experiment\nPlease press A to continue"
    # run_instruction_waitPress(instruction)
    # core.wait(2)

    while iTrial <= nTrial:
        # trial start instruction
        # instruction = f"Trial {iTrial}"
        # run_instruction(instruction)
        # core.wait(1)

        # contribution
        # weights = run_raiting()
        # core.wait(1)
        # run_cleanScreen()
        
        weights = np.array([50, 50])
        target_angle = np.array([0, 0])
        bullet_angle = np.array([30, -60])
        # shooting
        # run_instruction("Prepare to shoot")
        # core.wait(1)
        
        speed = [0.02, 0.02]
        target_angle, bullet_angle = run_shooting(speed, isShowPath=isShowPath, isCountdown=isCountdown)
        core.wait(1)

        # compute the difference
        diffs = [
            angleDiff(target_angle[0], bullet_angle[0]),
            angleDiff(target_angle[1], bullet_angle[1]),
        ]
        jointDiff = calWeightedAverage(diffs, weights) # angle in degrees

        # feedback
        # run_feedback(diffs, jointDiff=jointDiff)
        run_feedback_jointShoot(jointDiff=jointDiff, isShowSelfShot=isShowSelfShot)
        core.wait(3)
        run_cleanScreen()

        # trial end
        iTrial += 1

    # end message
    run_instruction("The experiment is finished")
    core.wait(3)

    wins[0].close()
    wins[1].close()
    core.quit()
