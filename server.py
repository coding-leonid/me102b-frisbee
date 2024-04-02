import io
import socket
import struct
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
server_socket.bind(('::1', 8000))  # Use the IPv6 loopback address
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb')

model = YOLO('yolov8n.pt')

# Create a socket for sending data back to the client
client_send_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
client_send_socket.connect(('::1', 8001))  # Use the IPv6 loopback address and the port of the client
try:
    img = None
    while True:
        # Read the length of the image as a 32-bit unsigned int
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        #print(f'Read size: {image_len}')
        # If the length is zero, quit the loop
        if not image_len:
            print('No image received, waiting')
            time.sleep(5)
            continue
        # Construct a stream to hold the image data and read the image
        # data from the connection
        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))
        # Rewind the stream and decode the image data
        image_stream.seek(0)
        data = np.frombuffer(image_stream.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)  # 1 means load color image

        results = model.track(image, persist=False, classes=[0], verbose=False)
        # If we detect people, extract IDs, draw bounding boxes
        if results[0].boxes.id != None:
            # Extract top left and bottom right corner
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            annotator = Annotator(image, line_width=2, example='test')
            
            # Add bounding boxes, labels and centerpoints
            for box, track_id in zip(boxes, track_ids):
                annotator.box_label(box, label=f'Person {track_id}', color=(0, 255, 0))
                box = box.tolist()
                center_x = int((box[0] + box[2]) / 2)
                center_y = int((box[1] + box[3]) / 2)
                cv2.circle(image, center=(center_x, center_y), radius=5, color=(0,0,255), thickness=-1)
            
            # No control unless exactly one person in frame
            if len(track_ids) == 1:
                client_send_socket.sendall(str(center_x).encode())

        cv2.imshow('Person tracker', image)

        # Quit capturing when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f'Exception caught: {e}')

finally:
    connection.close()
    server_socket.close()
    print('Cleanup successful')
