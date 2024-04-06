import numpy as np
from serial import Serial
import RPi.GPIO as GPIO

import settings


def serial_reader():
    """Thread for taking measurements from the range sensor serial port"""
    try:
        # Open serial port
        ser : Serial = Serial(settings.SERIAL_FILE, baudrate=9600)
        ser.timeout = 1.
        while True:
            # Create a byte array to store received data
            data : bytearray = bytearray(11)
            # Read 11 bytes of data from the serial port
            for i in range(11):
                byte = ser.read()
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
            # Exit when exit flag is true
            if settings.SHOULD_EXIT.is_set():
                break
    # Handle any exceptions
    except Exception as e:
        print(f"Exception thrown in serial thread: {e}")
    
    # Close port on keyboard interrupt
    except KeyboardInterrupt:
        ser.close()
        print('Serial port closed')

    # Close the port if something went wrong
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        print("Serial port closed")


def positive_yaw_pwm_map(percentage: float) -> int:
    """Map to actual duty cycle value for positive rotation from a 0-100 range"""
    return int(60 + 39 * percentage / 100)

def negative_yaw_pwm_map(percentage: float) -> int:
    """Map to actual duty cycle value for negative rotation from a 0-100 range"""
    return int(60 - 2 * percentage / 5)

def yaw_control(pwm: GPIO.PWM):
    # Control for positive error
    if settings.YAW_ERR > 0:
        output = min(settings.K_P_YAW * settings.YAW_ERR, 100.)
        pwm_val = positive_yaw_pwm_map(output)
        print(f"Commanded: {output}%")
    else: # Control for negative error
        output = min(-settings.K_P_YAW * settings.YAW_ERR, 100.)
        pwm_val = negative_yaw_pwm_map(output)
        print(f"Commanded: -{output}%")

    # These values don't work for some reason...
    if pwm_val == 92:
        pwm_val = 91
    elif pwm_val == 41:
        pwm_val = 42

    # Set the duty cycle
    pwm.ChangeDutyCycle(pwm_val)
