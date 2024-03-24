import socket
import struct
import cv2
import time

client_socket = socket.socket()
client_socket.connect(('10.44.123.70', 8000))

# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    cap = cv2.VideoCapture(0, apiPreference=cv2.CAP_V4L)
    
    # Set desired frame rate (10 fps)
    cap.set(cv2.CAP_PROP_FPS, 10)

    # Set desired resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)

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
        print(f'Sent byte size: {size}')

        # Send the frame data
        client_socket.sendall(buffer)
        time.sleep(1/10)

except Exception as e:
    print(f'Exception caught: {e}')

finally:
    # Send termination message
    client_socket.sendall(struct.pack('<L', 0))
    cap.release()
    connection.close()
    client_socket.close()
    print('Cleanup successful')
