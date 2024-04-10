import socket
import struct
import time
import cv2
import io
import os
import sys
import numpy as np
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

import settings

# Initialize global variables for scripts that are intended to run
settings.init()

def start_server(host: str, port: int):
    # Create server socket, bind and start listening
    server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(0)
    print(f"Server listening on IPV6 {host} port {port}")
    # Load YOLOv8 nano model
    model = YOLO('yolov8n.pt')
    # Outer loop looking for connections, catches keyboard interrupts
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            connection = client_socket.makefile('rb')
            print(f"Accepted connection from {client_address}")
            # Inner loop sending and receiving messages, catches exceptions during send/receive
            try:
                while True:
                    # Read the length of the image as a 32-bit unsigned int
                    image_len: int = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                    print(f'Received image of size {image_len} bytes')
                    # If the length is zero, quit the loop
                    if not image_len:
                        print('No image received, waiting...')
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
                    # Do inference
                    results = model.track(image, persist=False, classes=[0], verbose=False)
                    # If we detect people, extract IDs, draw bounding boxes
                    if results[0].boxes.id == None:
                        client_socket.send(str(69420).encode("utf-8"))
                    else:
                        # Extract top left and bottom right corner
                        boxes = results[0].boxes.xyxy.cpu()
                        track_ids = results[0].boxes.id.int().cpu().tolist()
                        annotator = Annotator(image, line_width=2, example="test")
                        
                        # Add bounding boxes, labels and centerpoints
                        for box, track_id in zip(boxes, track_ids):
                            annotator.box_label(box, label=f'Person {track_id}', color=(0, 255, 0))
                            box = box.tolist()
                            center_x = int((box[0] + box[2]) / 2)
                            center_y = int((box[1] + box[3]) / 2)
                            cv2.circle(image, center=(center_x, center_y), radius=5, color=(0,0,255), thickness=-1)

                        # No control unless exactly one person in frame
                        if len(track_ids) == 1:
                            client_socket.send(f"{int(box[0])},{int(box[2])}".encode("utf-8"))
                        else:
                            client_socket.send(f"{settings.INVALID_VALUE},{settings.INVALID_VALUE}".encode("utf-8"))

                    cv2.imshow('Person tracker', image)

                    # Quit capturing when 'q' is pressed
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        raise KeyboardInterrupt
                
            except Exception as e:
                print(f"Error handling client: {e}")

            finally:
                print(f"Closing connection from {client_address}")
                client_socket.close()
                cv2.destroyAllWindows()

    # Keyboard interrupt is the exit condition, final cleanup is here
    except KeyboardInterrupt:
        print("Server shutting down...")
        server_socket.close()
        connection.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {os.path.basename(__file__)} <host> <port>")
        sys.exit(1)
    
    host: str = sys.argv[1]
    port: int = int(sys.argv[2])
    start_server(host, port)
