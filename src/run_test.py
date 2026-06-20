from pybricks.hubs import EV3Brick
from pybricks.parameters import Port
from pybricks.ev3devices import Motor, UltrasonicSensor
from pybricks.parameters import Port, Stop
from pybricks.tools import wait
from pyhuskylens import *

ev3 = EV3Brick()

hl = HuskyLens(Port.S1)
eyes = UltrasonicSensor(Port.S4)
steering = Motor(Port.A)
drive = Motor(Port.B)

hl.set_alg(ALGORITHM_COLOR_RECOGNITION)

STEER_SPEED = 500
DRIVE_SPEED = 500
DODGE_SPEED = 250
LEFT_ANGLE = 78
RIGHT_ANGLE = -78
ADJUST_LEFT = 120
ADJUST_RIGHT = -90
RESET = 0

AREA_THRESHOLD = 55000

# Boolean flag switch for turning on and off 
ULTRASONIC_ACTIVE = True

"""
1 if clockwise
-1 if counterclockwise
"""
TRACK_DIRECTION = 1

DIR_LEFT = LEFT_ANGLE * TRACK_DIRECTION
DIR_RIGHT = RIGHT_ANGLE * TRACK_DIRECTION

def center_wheels():
    steering.run_target(300, -2, then=Stop.HOLD, wait=True)

def get_dist():
    return (eyes.distance() + eyes.distance() + eyes.distance()) / 3

#For clarity the RED AND GREEN BLOCKS will now be called MARKERS
#block.ID == 2 is GREEN (*TRAIN THE HUSKYLENS*)
#block.ID == 3  is RED (*TRAIN THE HUSKYLENS*)
def marker_detection(blocks):
    ids = [block.ID for block in blocks]

    BA_RED = 0
    BA_GREEN = 0
    RED_CENTER = 0
    GREEN_CENTER = 0
    MARKER_TACKLED = None
    TARGET_AREA = 0


    totoong_bricks = []

    for block in blocks:
        if block.ID in [2,3]:
            aspect_ratio = block.width / block.height
            print("ID:", block.ID, "Ratio:", aspect_ratio)
            if aspect_ratio >= 2.0: # Lower the number to be more strict on the lines if needed
                print("flat line detected!")
            else:
                totoong_bricks.append(block)
    
    totoong_ids = [block.ID for b in totoong_bricks]

    if 2 in totoong_ids and 3 in totooing_ids:
        print("More than 1 Marker seen")

        for block in totoong_ids:
            if block.ID == 3:
                BA_RED = block.width * block.height
                RED_CENTER = block.x
                MARKER_TACKLED = "RED"



            elif block.ID == 2:
                BA_GREEN = block.width * block.height
                GREEN_CENTER = block.x
                MARKER_TACKLED = "GREEN"

        if BA_RED > BA_GREEN:
            TARGET_AREA = BA_RED

        elif BA_GREEN > BA_RED:
            TARGET_AREA = BA_GREEN

    elif 3 in totoong_ids and not 2 in totoong_ids:
        MARKER_TACKLED = "AutoRED"
        for block in blocks:
            if block.ID == 3: TARGET_AREA = block.width * block.height

    elif 2 in totoong_ids and not 3 in totoong_ids:
        MARKER_TACKLED = "AutoGREEN"
        for block in blocks:
            if block.ID == 2: TARGET_AREA = block.width * block.height

    return MARKER_TACKLED, TARGET_AREA

#PREMADE SET RUN PATHS needs to be tweaked
def turn_marker(MARKER_TACKLED):

    if MARKER_TACKLED == "AutoRED":
        steering.run_target(STEER_SPEED, DIR_LEFT, then=Stop.HOLD, wait=False)
        wait(500)
        center_wheels()
        steering.run_target(STEER_SPEED, DIR_RIGHT, then=Stop.HOLD, wait=False)
        wait(1950)
        center_wheels()
        drive.run(0)
        wait(150) # Moves for 150ms while turned left

    elif MARKER_TACKLED == "AutoGREEN":
        steering.run_target(STEER_SPEED, DIR_RIGHT, then=Stop.HOLD, wait=False)
        wait(500)
        center_wheels()
        steering.run_target(STEER_SPEED, DIR_LEFT, then=Stop.HOLD, wait=False)
        wait(1950)
        center_wheels()
        drive.run(0)
        wait(150) # Moves for 150ms while turned left
        print(MARKER_TACKLED)

center_wheels()


#Main Execution Loop
# --- Main Execution Loop (Color Recognition Mode) ---
while True:
    blocks = hl.get_blocks()
    # 1. Gather all block IDs present in the current camera frame
    ids = [block.ID for block in blocks]
    
    
    """
    this has a bug with the huskylens ai camera because its literally
    detecting the green as 
    """
    
    if ULTRASONIC_ACTIVE == True:
        DISTANCE = get_dist()
    else:
        DISTANCE = 9999

    white_block = None
    for block in blocks:
        if block.ID == 1:
            white_block = block
            break

    DYNAMIC_DODGE_ANGLE = LEFT_ANGLE * TRACK_DIRECTION

    # --- PRIORITY 1: SINGLE RED BRICK DETECTED ---
    if 3 in ids:
        marker_to_hit, AREA_BLOCK = marker_detection(blocks)
        print("Marker triggered:", marker_to_hit, "Area:", AREA_BLOCK)
        
        if marker_to_hit == "AutoRED" and AREA_BLOCK >= 4000:
            turn_marker("AutoRED") # Runs your smooth blind-spot time dodge
            
            # CLEARANCE DELAY: Drive straight briefly to finish passing the brick side
            center_wheels()
            drive.run(DRIVE_SPEED)
            wait(500) 
        else:
            # Marker seen far away, let fallback line-keeping handle driving
            pass 

    # --- PRIORITY 2: DEFAULT WHITE LINE KEEPING ---
    # This handles 90% of your run when no brick obstacles are in the way
    elif white_block is not None:
        AREA_W = white_block.width * white_block.height
        print("Tracking White Line. Area:", AREA_W)

        if 74000 <= AREA_W <= 77000:
            center_wheels()
            drive.run(DRIVE_SPEED)
        else:
            DYNAMIC_LEFT_ANGLE = 1200
            DYNAMIC_DODGE_ANGLE_SHARP = DYNAMIC_LEFT_ANGLE * TRACK_DIRECTION
            # If the white area stretches or shifts, make the tracking correction
            steering.run_target(STEER_SPEED, DYNAMIC_DODGE_ANGLE_SHARP, then=Stop.HOLD, wait=False)
            wait(1000)
            center_wheels()
            drive.run(DRIVE_SPEED)
    # --- PRIORITY 4: CATCH-ALL FALLBACK ---
    else:
        print("Lost all tracking data! Coasting straight...")
        center_wheels()
        drive.run(DRIVE_SPEED)

    # Small loop refresh rate pause
    wait(50)

    # --- PRIORITY 3: ULTRASONIC FAILSAFE ---
    # Only checks if it loses the line or if a wall/brick sneaks inside its blindspot
    """ 
    elif DISTANCE < 500:
        print("Ultrasonic Failsafe Triggered! Distance:", DISTANCE)
        ULTRASONIC_ACTIVE = True
        DYNAMIC_DODGE_ANGLE = LEFT_ANGLE * TRACK_DIRECTION

        steering.run_target(STEER_SPEED, DYNAMIC_DODGE_ANGLE, then=Stop.HOLD, wait=False)
        drive.run(DRIVE_SPEED)
        wait(200)
        center_wheels()
    """

    