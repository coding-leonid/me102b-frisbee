import socket
import time
import cv2
import sys
import os
import struct

def start_client(host, port):
    # Outer loop trying to establish a connection, catches keyboard interrupts
    try:
        # Create a video capture with correct framerate and 
        cap = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L)
        cap.set(cv2.CAP_PROP_FPS, 10)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
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
                    data = client_socket.recv(1024)  # Adjust buffer size as needed
                    if data:
                        # Process received data
                        center_x = int(data.decode())
                        print(f'Received yaw error: {center_x} pixels')
                    time.sleep(1/10)
                
            except Exception as e:
                print(f"Error handling server: {e}")
                client_socket.close()

    # Keyboard interrupt is the exit condition, final cleanup is here
    except KeyboardInterrupt:
        print("Client shutting down...")
        connection.close()
        client_socket.close()
        cap.release()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {os.path.basename(__file__)} <host> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    start_client(host, port)
