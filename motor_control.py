import numpy as np
from serial import Serial
import settings


def serial_reader() -> float:
    try:
        # Open serial port
        ser : Serial = Serial('/dev/ttyUSB0', baudrate=9600)
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
            # If bougus value or error, return -1
            if distance > 100 or distance < 0:
                distance = -1
            # Save the distance value
            settings.RANGE = distance
            print(distance)
            # Exit when exit flag is true
            if settings.SHOULD_EXIT.is_set():
                break

    except Exception as e:
        # Handle any exceptions
        print(f"Exception thrown in serial thread: {e}")
    finally:
        # Close the port if something went wrong
        if 'ser' in locals() and ser.is_open:
            ser.close()
        print("Serial port closed")

def des_speed_from_range(range: float) -> float:
    pass


def launch_pwm() -> float:
    pass
