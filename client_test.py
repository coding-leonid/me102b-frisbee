import socket
import time
import cv2
import sys
import os
import struct
import threading
import RPi.GPIO as GPIO

import settings
import motor_control as mc

# Initialize global variables for scripts that are intended to run
settings.init()

# Start the serial reader thread
serial_thread = threading.Thread(target=mc.serial_reader)
# Set the thread as daemon so it exits when the main thread exits
serial_thread.daemon = True
serial_thread.start()

# Initialize PWM object
GPIO.setmode(GPIO.BOARD)
GPIO.setup(settings.YAW_PWM_PIN, GPIO.OUT, initial=GPIO.HIGH)
pwm = GPIO.PWM(settings.YAW_PWM_PIN, settings.PWM_FREQ)
pwm.start(60) # Start in neutral

def start_client(host: str, port: int):
    # Outer loop trying to establish a connection, catches keyboard interrupts
    try:
        # Create a video capture with correct framerate and 
        cap = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L)
        cap.set(cv2.CAP_PROP_FPS, settings.CAM_FPS)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.IMG_WIDTH)
        while True:
            # Catches connection errors
            try:
                client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                client_socket.connect((host, port))
                # Make a file-like object out of the connection for sending data
                connection = client_socket.makefile('wb')
            except socket.error as e:
                print(f"Error while trying to connect: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)
                continue
            # Inner loop sending and receiving messages, catches send/receive errors
            try:
                while True:
                    # Capture frame
                    ret, frame = cap.read()
                    if not ret:
                        break
                    # Encode frame as jpeg
                    _, buffer = cv2.imencode('.jpg', frame)
                    # Get the size of the encoded frame
                    size = len(buffer)
                    # Send the size of the frame
                    client_socket.sendall(struct.pack('<L', size))
                    # Send the frame data
                    client_socket.sendall(buffer)
                    print(f'Sent image of size {size} bytes')
                    # Receive data from the server
                    data = client_socket.recv(1024)
                    # Process received data
                    if data:
                        center_x = int(data.decode())
                        print(f'Received yaw error: {"INVALID" if center_x == settings.INVALID_VALUE else center_x} pixels')
                        settings.YAW_ERR = int(center_x - settings.IMG_WIDTH / 2)
                        mc.yaw_control(pwm=pwm)
                    time.sleep(1/10)
                
            except Exception as e:
                print(f"Error handling server: {e}")
                pwm.stop()
                GPIO.cleanup()
                client_socket.close()

    # Keyboard interrupt is the exit condition, final cleanup is here
    except KeyboardInterrupt:
        print("Client shutting down...")
        pwm.stop()
        connection.close()
        client_socket.close()
        cap.release()

if __name__ == "__main__":
    # Check that the number of arguments is correct
    if len(sys.argv) != 3:
        print(f"Usage: python3 {os.path.basename(__file__)} <ipv6-host> <port>")
        sys.exit(1)
    
    # Set host and port
    host: str = sys.argv[1]
    port: int = int(sys.argv[2])
    start_client(host, port)
    serial_thread.join()
    GPIO.cleanup()
    print("Exited both threads successfully")
