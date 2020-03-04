import threading
from edgetpu.detection.engine import DetectionEngine
from PIL import Image
from timeit import time
import cv2
from tools.CentroidTracker import CentroidTracker
from tools.RethinkDb import DataManager
from collections import deque
from threading import Thread


class VideoCamera(object):
    """
    Video camera class:
    this class all the video processing, the received frames are sent to the web interface.
    """

    def __init__(self, threshold=0.65, inverted=False, bbox=False, crossing=False, accuracy=False, video_status=False,
                 back_color=0, fore_color=(255, 255, 255), bbox_color=(0, 0, 255), crossing_color=(255, 255, 0)):
        # Open a camera
        self.cap = cv2.VideoCapture(1)

        # DataController
        self.manager = DataManager(host="10.10.20.53", database="person-counter")
        self.table = "The_Core"

        # colors
        self.video_back_color = back_color
        self.video_foreground_color = fore_color
        self.bbox_color = bbox_color
        self.crossing_color = crossing_color

        # flags
        self.flag_inverted = inverted
        self.threshold = threshold
        self.bbox = bbox
        self.accuracy = accuracy
        self.video_status = video_status
        self.crossing = crossing

        #
        self.persons_in = 0
        self.line_trail = dict()
        self.engine = DetectionEngine('model_tflite/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite')
        self.ct = CentroidTracker()

        # Initialize video recording environment
        self.is_record = False
        self.out = None

        self.frame = None
        Thread(target=lambda: self.run_loop()).start()

    def __del__(self):
        self.cap.release()

    def run_loop(self):
        while True:
            ret, frame = self.cap.read()
            if ret:
                t1 = time.time()
                img = Image.fromarray(frame)
                width, height = img.size
                line1 = int(height / 2 - 50)

                # Run inference.
                detections = self.engine.detect_with_image(img, threshold=self.threshold, keep_aspect_ratio=True,
                                                           relative_coord=False, top_k=10,
                                                           resample=Image.NEAREST)  # BICUBIC
                boxs = []

                # Display result.
                for obj in detections:
                    if obj.label_id == 0:
                        box = obj.bounding_box.flatten().tolist()
                        if self.bbox:
                            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])),
                                          self.bbox_color, 5)
                            # if self.accuracy:
                            cv2.putText(frame, str(round(obj.score, 2)), (int(box[0]) + 10, int(box[1] - 10)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, self.bbox_color, 2)
                        boxs.append(box)

                objects = self.ct.update(boxs)

                for (objectID, centroid) in objects.items():
                    if objectID not in self.line_trail.keys():
                        self.line_trail[objectID] = deque(maxlen=2)
                    if self.bbox:
                        cv2.putText(frame, str(objectID), (centroid[0] - 10, centroid[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    self.bbox_color, 4)
                        cv2.circle(frame, (centroid[0], centroid[1]), 4, self.bbox_color, -1)
                    center = (centroid[1], centroid[2])
                    self.line_trail[objectID].appendleft(center)
                    try:
                        diff = abs(self.line_trail[objectID][0][0] - self.line_trail[objectID][1][0])
                        if diff < 60:
                            if self.line_trail[objectID][0][1] < int(line1) and self.line_trail[objectID][1][1] > int(
                                    line1):
                                if self.flag_inverted:
                                    self.persons_in += 1
                                    publish = threading.Thread(
                                        self.manager.send_data(self.table, "+1"))
                                else:
                                    self.persons_in -= 1
                                    publish = threading.Thread(
                                        self.manager.send_data(self.table, "-1"))

                            elif self.line_trail[objectID][1][1] < int(line1) and self.line_trail[objectID][0][1] > int(
                                    line1):
                                if self.flag_inverted:
                                    self.persons_in -= 1
                                    publish = threading.Thread(
                                        self.manager.send_data(self.table, "-1"))
                                else:
                                    self.persons_in += 1
                                    publish = threading.Thread(
                                        self.manager.send_data(self.table, "+1"))
                    except Exception as Ex:
                        print(Ex)

                if self.video_status:
                    frame = cv2.copyMakeBorder(frame, top=0, bottom=48, left=0, right=0, borderType=cv2.BORDER_CONSTANT,
                                               value=self.video_back_color)
                    cv2.putText(frame, "Binnen: %s" % self.persons_in, (10, height + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                                self.video_foreground_color, lineType=cv2.LINE_AA, thickness=2)
                    cv2.putText(frame, "FPS: %d" % (1. / (time.time() - t1)), (260, height + 32),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.0, self.video_foreground_color, lineType=cv2.LINE_AA, thickness=2)
                if self.crossing: cv2.line(frame, (0, line1), (width, line1), (self.crossing_color), 2)
            self.frame = cv2.imencode('.jpg', frame)[1].tostring()

    def get_frame(self):
        return self.frame

    def toggle_video_status(self):
        self.video_status = not self.video_status

    def toggle_bbox(self):
        self.bbox = not self.bbox

    def toggle_accuracy(self):
        self.accuracy = not self.accuracy

    def toggle_crossing(self):
        self.crossing = not self.crossing

    def set_video_background_color(self, color):
        self.video_back_color = color

    def set_video_foreground_color(self, color):
        self.video_foreground_color = color

    def set_bbox_color(self, color):
        self.bbox_color = color

    def set_crossing_color(self, color):
        self.crossing_color = color
