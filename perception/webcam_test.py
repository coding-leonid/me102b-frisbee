import cv2
import numpy as np
from matplotlib import pyplot as plt
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

# Image size
IMG_SIZE = (640, 480)
# Control proportionality constant
K_P = .5

# Use pretrained nano model
model = YOLO('yolov8n.pt')

# Keep capturing while capture device is open
cap = cv2.VideoCapture(0)
while cap.isOpened():
    # Read and show current frame
    ret, frame = cap.read()
    # Exit if no return value
    if not ret:
        break
    # YOLO person trackning
    results = model.track(frame, persist=False, classes=[0], verbose=False)
    # If we detect people, extract IDs, draw bounding boxes
    if results[0].boxes.id != None:
        # Extract top left and bottom right corner
        boxes = results[0].boxes.xyxy.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        annotator = Annotator(frame, line_width=2, example='test')
        
        # Add bounding boxes, labels and centerpoints
        for box, track_id in zip(boxes, track_ids):
            annotator.box_label(box, label=f'Person {track_id}', color=(0, 255, 0))
            box = box.tolist()
            center_x = int((box[0] + box[2]) / 2)
            center_y = int((box[1] + box[3]) / 2)
            cv2.circle(frame, center=(center_x, center_y), radius=5, color=(0,0,255), thickness=-1)
        
        # No control unless exactly one person in frame
        if len(track_ids) == 1:
            err = center_x - IMG_SIZE[0] / 2
            pwm = np.sign(err) * np.min([K_P * np.abs(err), 100])
            print(pwm)

    cv2.imshow('Person tracker', frame)

    # Quit capturing when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()