import socket
import time
import cv2
import sys
import os
import struct
import threading
import numpy as np

import settings
import motor_control as mc

# Initialize global variables for scripts that are intended to run
settings.init()

# Start the range sensor thread
range_thread = threading.Thread(target=mc.range_sensor_thread)
esp32_thread = threading.Thread(target=mc.esp32_thread)
# Set the threads as daemons so they exit when the main thread exits
range_thread.daemon = True
esp32_thread.daemon = True
range_thread.start()
esp32_thread.start()


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
                # When connection is lost, make sure to invalidate all values
                settings.RANGE = settings.INVALID_VALUE
                settings.PERSON_BOUNDS = [settings.INVALID_VALUE, settings.INVALID_VALUE]
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
                    #print(f'Sent image of size {size} bytes')
                    # Receive data from the server
                    data = client_socket.recv(1024)
                    # Process received data
                    if data:
                        settings.PERSON_BOUNDS = [int(x) for x in data.decode().split(",")]
                        center_x = np.mean(settings.PERSON_BOUNDS)
                        # Only do control if received value is valid
                        if settings.PERSON_BOUNDS[0] == settings.INVALID_VALUE:
                            print(f"Received yaw error: INVALID")
                            settings.YAW_ERR = settings.INVALID_VALUE
                        else:
                            print(f"Received L = {settings.PERSON_BOUNDS[0]}, R = {settings.PERSON_BOUNDS[1]}, C = {center_x}")
                            # Error is defined as the distance from the center of the image
                            settings.YAW_ERR = int(center_x - settings.IMG_WIDTH / 2)
                            # We have exited/are not in a stream of invalid values
                            settings.YAW_RESET_TIMER = time.perf_counter()
                            settings.YAW_IS_RESET = False
                            #print(settings.ENCODER_COUNT)
                    time.sleep(1/10)
                
            except Exception as e:
                print(f"Error handling server: {e}")
                client_socket.close()

    # Keyboard interrupt is the exit condition, final cleanup is here
    except KeyboardInterrupt:
        print("Client shutting down...")
        settings.SHOULD_EXIT.set()
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
    range_thread.join()
    esp32_thread.join()
    print("Exited all threads successfully")
