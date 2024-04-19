import numpy as np
import time
from serial import Serial

import settings


def range_sensor_thread():
    """Thread for taking measurements from the range sensor serial port"""
    try:
        # Open serial port
        range_ser = Serial(settings.RANGE_FILE, baudrate=9600)
        range_ser.timeout = 1.
        while True:
            # Create a byte array to store received data
            data = bytearray(11)
            # Read 11 bytes of data from the serial port
            for i in range(11):
                byte = range_ser.read()
                if len(byte) == 0:
                    break
                data[i] = ord(byte)
            # Calculate distance based on received data
            distance : float = (data[3] - 0x30) * 100 + (data[4] - 0x30) * 10 + (data[5] - 0x30) * 1 + \
                    (data[7] - 0x30) * 0.1 + (data[8] - 0x30) * 0.01 + (data[9] - 0x30) * 0.001
            # Check for bogus value
            if distance > 100 or distance < 0 or np.isnan(distance):
                distance = settings.INVALID_VALUE
                #print("Distance measurement: INVALID")
            else:
                #print(f"Distance measurement: {distance}")
                pass
            
            # Save the distance value
            settings.RANGE = distance

            # Calculate person width (NOTE: evaluates to zero if invalid)
            #person_width = settings.PERSON_BOUNDS[1] - settings.PERSON_BOUNDS[0]
            #print(settings.YAW_ERR)
            # Check if yaw error is within bounds
            if not settings.FIRE_REQUEST \
               and time.perf_counter() > settings.FIRE_TIMER + settings.FIRE_COOLDOWN \
               and abs(settings.YAW_ERR) < 10 \
               and settings.RANGE != settings.INVALID_VALUE:
                #and person_width > 0 \
                #and abs(settings.YAW_ERR) < settings.GET_RANGE_PROP * person_width:
                # Gather range measurements and save to list
                settings.RANGE_VALS.append(settings.RANGE)
                print(f"Gathered range measurement {settings.RANGE}")
                # When sufficiently many measurements, initiate firing sequence
                if len(settings.RANGE_VALS) >= settings.SUFF_NUM_MEAS:
                    print("Firing request")
                    # Compute the PWM value here!
                    settings.FIRE_COMMAND = 70
                    settings.FIRE_REQUEST = True
            # If a single frame does not fulfill conditions, reset
            else:
                settings.RANGE_VALS.clear()

            # Exit when exit flag is true
            if settings.SHOULD_EXIT.is_set():
                break
    # Handle any exceptions
    except Exception as e:
        print(f"Exception thrown in range thread: {e}")

    # Close the port if something went wrong
    finally:
        if "range_ser" in locals() and range_ser.is_open:
            range_ser.close()
        print("Range port closed")


def esp32_thread():
    try:
        # Connect to ESP32 via serial port
        esp32_ser = Serial(settings.ESP32_FILE, baudrate=115200, timeout=0.1)
        esp32_ser.write("r\n".encode())
        request_sent = False
        # Communicating with ESP32
        while True:
            # Check for exit flag
            if settings.SHOULD_EXIT.is_set():
                # Reset yaw position
                esp32_ser.write("r\n".encode())
                # Set motor to neutral
                esp32_ser.write(f"y{settings.MOTOR_NEUTRAL}\n".encode())
                break
            
            # Read from the ESP32
            data = esp32_ser.readline().decode().strip()
            # Reset firing flags when firing sequence is finished

            if data == "f":
                print("Firing finished")
                settings.FIRE_REQUEST = False
                request_sent = False
                settings.FIRE_TIMER = time.perf_counter()
            
            # Incase fire request, perform firing sequence, skip rest of the loop
            if request_sent:
                continue
            if settings.FIRE_REQUEST and not request_sent:
                #print(f"Sent request with average distance {np.mean(settings.RANGE_VALS)}")
                #esp32_ser.write(f"f{settings.FIRE_COMMAND}".encode())
                request_sent = True
                continue
            
            # Update encoder count
            try:
                settings.ENCODER_COUNT = int(data)
            except ValueError:
                pass
            # Update yaw command
            yaw_control()
            #print(settings.ENCODER_COUNT)
            #print(f"Sent yaw command {settings.YAW_CONTROL}")
            esp32_ser.write(f"y{settings.YAW_CONTROL}\n".encode())

            
    
    except Exception as e:
       print(f"Exception thrown in ESP32 thread: {e}")

    finally:
        if "esp32_ser" in locals() and esp32_ser.is_open:
            esp32_ser.close()
            esp32_ser.write("f153".encode())
        print("ESP32 port closed")
        

def positive_yaw_pwm_map(percentage: float) -> int:
    """Map to actual duty cycle value for positive rotation from a 0-100 range"""
    return int(150 - 0.12 * percentage) if percentage > 3 else settings.MOTOR_NEUTRAL

def negative_yaw_pwm_map(percentage: float) -> int:
    """Map to actual duty cycle value for negative rotation from a 0-100 range"""
    return int(160 + 0.12 * percentage) if percentage > 3 else settings.MOTOR_NEUTRAL

def yaw_control():
    # If invalid value, no control
    if settings.YAW_ERR == settings.INVALID_VALUE:
        settings.YAW_CONTROL = settings.MOTOR_NEUTRAL
        return
    
    # If we are outside allowed limits, only control in the right direction
    # Checking abs. value and that error and encoder count and
    # that it wants to control in the opposite direction
    if abs(settings.ENCODER_COUNT) >= settings.YAW_LIMIT and settings.ENCODER_COUNT * settings.YAW_ERR < 0:
        settings.YAW_CONTROL = settings.MOTOR_NEUTRAL
        print("Outside yaw limits")
        return

    if abs(settings.K_I_YAW * (settings.YAW_INT + settings.YAW_ERR)) < 100:
        settings.YAW_INT += settings.YAW_ERR
    
    # In case error changes sign, remove all integral windup
    if settings.YAW_INT * settings.YAW_ERR < 0:
        settings.YAW_INT = 0
    output = settings.K_P_YAW * settings.YAW_ERR \
        + settings.K_I_YAW * settings.YAW_INT \
        + settings.K_D_YAW * (settings.YAW_ERR - settings.PREV_YAW_ERR)
    settings.PREV_YAW_ERR = settings.YAW_ERR

    # Control in positive direction
    if output > 0:
        output = min(output, 100)
        settings.YAW_CONTROL = positive_yaw_pwm_map(output)
        #print(f"Commanded: {output}%")
    else: # Control in negative direction
        output = min(-output, 100.)
        settings.YAW_CONTROL = negative_yaw_pwm_map(output)
        #print(f"Commanded: -{output}%")


def firing_seq():
    """
    Based on a list of range measurements, spool up
    the motor and command the servo to fire the frisbee
    """

    # Calculate average distance
    dist = np.mean(settings.RANGE_VALS)
    
    # Command motor to fire proportionally to the distance

    # Wait a little bit

    # Command the servo to fire

    # Clear the measurement list
    settings.RANGE_VALS.clear()
