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
            if distance > 100 or distance < 0:
                distance = settings.INVALID_VALUE
                print("Distance measurement: INVALID")
            else:
                print(f"Distance measurement: {distance}")
            
            # Save the distance value
            settings.RANGE = distance

            # Calculate person width (NOTE: evaluates to zero if invalid)
            person_width = settings.PERSON_BOUNDS[1] - settings.PERSON_BOUNDS[0]
            # Check if yaw error is within bounds
            if person_width > 0 and abs(settings.YAW_ERR) < settings.GET_RANGE_PROP * person_width:
                print("Waiting for range measurement...")
                # Gather range measurements and save to list

                # When sufficiently many measurements, send appropriate motor command

                # Wait a little bit before sending the servo command to launch

                # Clear list of measurements

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
        esp32_ser = Serial(settings.ESP32_FILE, baudrate=115200, timeout=1)
        esp32_ser.write("reset\n".encode()) # Reset encoder count before starting! 
        # Communicating with ESP32
        while True:
            # Update encoder count
            try:
                settings.ENCODER_COUNT = int(esp32_ser.readline().decode().strip())
            except ValueError:
                pass
            # Update yaw command
            yaw_control()
            #print(settings.ENCODER_COUNT)
            esp32_ser.write(f"y{settings.YAW_CONTROL}\n".encode())

            if not settings.YAW_IS_RESET and time.perf_counter() - settings.YAW_RESET_TIMER > settings.YAW_TIMEOUT:
                # Holds up the code until finished!
                esp32_ser.write("r\n".encode())
                settings.YAW_IS_RESET = True

            # Check for exit flag
            if settings.SHOULD_EXIT.is_set():
                # Reset yaw position (holds up the code!)
                esp32_ser.write("r\n".encode())
                # Set motor to neutral
                esp32_ser.write(f"y{settings.MOTOR_NEUTRAL}\n".encode())
                break
    
    except Exception as e:
        print(f"Exception thrown in ESP32 thread: {e}")

    finally:
        if "esp32_ser" in locals() and esp32_ser.is_open:
            esp32_ser.close()
        print("ESP32 port closed")
        

def positive_yaw_pwm_map(percentage: float) -> int:
    """Map to actual duty cycle value for positive rotation from a 0-100 range"""
    return int(settings.MOTOR_NEUTRAL - 1.02 * percentage)

def negative_yaw_pwm_map(percentage: float) -> int:
    """Map to actual duty cycle value for negative rotation from a 0-100 range"""
    return int(settings.MOTOR_NEUTRAL + percentage)

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
        #print("Outside yaw limits")
        return

    # Control for positive error
    if settings.YAW_ERR > 0:
        output = min(settings.K_P_YAW * settings.YAW_ERR, 100.)
        settings.YAW_CONTROL = positive_yaw_pwm_map(output)
        #print(f"Commanded: {output}%")
    else: # Control for negative error
        output = min(-settings.K_P_YAW * settings.YAW_ERR, 100.)
        settings.YAW_CONTROL = negative_yaw_pwm_map(output)
        #print(f"Commanded: -{output}%")    


def reset_yaw():
    print("Reset yaw")