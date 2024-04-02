import socket
import struct
import cv2
import time

# Connect to the server for sending image data
client_socket_send = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
client_socket_send.connect(('2607:f140:400:11e:7f37:e85f:5e9c:68a5', 8000))

# Connect to the server for receiving data
client_socket_receive = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
client_socket_receive.connect(('2607:f140:400:11e:7f37:e85f:5e9c:68a5', 8001))

# Make a file-like object out of the connection for sending data
connection_send = client_socket_send.makefile('wb')

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
        client_socket_send.sendall(struct.pack('<L', size))
        print(f'Sent byte size: {size}')

        # Send the frame data
        client_socket_send.sendall(buffer)
        time.sleep(1/10)

        # Receive data from the server
        data = client_socket_receive.recv(1024)  # Adjust buffer size as needed
        if data:
            # Process received data
            center_x = int(data.decode())
            print(f'Received center_x: {center_x}')

except Exception as e:
    print(f'Exception caught: {e}')

finally:
    # Send termination message
    client_socket_send.sendall(struct.pack('<L', 0))
    cap.release()
    connection_send.close()
    client_socket_send.close()
    client_socket_receive.close()
    print('Cleanup successful')
