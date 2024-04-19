import threading
import time

def init():
    global RANGE, SHOULD_EXIT, IMG_WIDTH, INVALID_VALUE, RANGE_FILE, \
    YAW_ERR, CAM_FPS, K_P_YAW, YAW_PWM_PIN, PWM_FREQ, ESP32_FILE, \
    MOTOR_NEUTRAL, YAW_CONTROL, ENCODER_COUNT, YAW_LIMIT, YAW_TIMEOUT, \
    YAW_RESET_TIMER, YAW_IS_RESET, GET_RANGE_PROP, PERSON_BOUNDS, \
    RANGE_VALS, SUFF_NUM_MEAS, FIRE_REQUEST, FIRE_COMMAND, FIRE_COOLDOWN, \
    FIRE_TIMER, YAW_INT, K_I_YAW, K_D_YAW, PREV_YAW_ERR

    """ ACTUAL SETTINGS """
    # Image width
    IMG_WIDTH = 640
    # FPS of the camera video stream
    CAM_FPS = 10
    # File address of the range sensor serial port
    RANGE_FILE = "/dev/ttyUSB1"
    # File address of the ESP32 controller
    ESP32_FILE = "/dev/ttyUSB0"
    # P-gain for yaw control
    K_P_YAW = .15
    # I-gain for yaw control
    K_I_YAW = 3e-5
    # D-gain for yaw control
    K_D_YAW = .1
    # Previous yaw error value
    PREV_YAW_ERR = 0
    # PWM pin for the yaw motor
    YAW_PWM_PIN = 32
    # PWM frequency (DO NOT TOUCH!!)
    PWM_FREQ = 400
    # Duty cycle value representing neutral motor control
    MOTOR_NEUTRAL = 153
    # Encoder count the yaw motor is limited to in each direction
    YAW_LIMIT = 1000
    # How long [seconds] we accept invalid yaw errors until we reset the yaw
    YAW_TIMEOUT = 5.
    # Condition for considering the range sensor to be pointing at the person
    GET_RANGE_PROP = .45
    # Sufficiently many measurements in order to fire
    SUFF_NUM_MEAS = 5

    """ GLOBAL VARIABLES """
    # Current range reading
    RANGE = 0.
    # Flag for telling the daemons to exit
    SHOULD_EXIT = threading.Event()
    # Current yaw error in pixels
    YAW_ERR = 0
    # Integer value for not performing control / bogus distance measurements
    INVALID_VALUE = 69420 # Also used by the server!
    # Current control input for the yaw
    YAW_CONTROL = MOTOR_NEUTRAL
    # The current encoder count (can encounter some weird values, ususally int)
    ENCODER_COUNT = 0
    # Tracking how long we have been receiving invalid yaw errors (give some time to initialize)
    YAW_RESET_TIMER = time.perf_counter() + YAW_TIMEOUT
    # For flagging that a reset has been done (no need to do multiple resets)
    YAW_IS_RESET = False
    # Bounding box x-values for the person
    PERSON_BOUNDS = [INVALID_VALUE, INVALID_VALUE]
    # List for storing range measurements
    RANGE_VALS = []
    # Flag set by range thread to order ESP32 thread to start firing sequence
    FIRE_REQUEST = False
    # Current PWM firing command
    FIRE_COMMAND = MOTOR_NEUTRAL
    # Cooldown time between firings [s]
    FIRE_COOLDOWN = 10
    # Timer for enforcing firing cooldown time
    FIRE_TIMER = time.perf_counter()
    # Integral of YAW error
    YAW_INT = 0
