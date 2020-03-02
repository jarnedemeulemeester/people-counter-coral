import threading
from edgetpu.detection.engine import DetectionEngine
import argparse
from PIL import Image
from timeit import time
import cv2
from tools.CentroidTracker import CentroidTracker
from collections import deque


class RecordingThread(threading.Thread):
    def __init__(self, name, camera):
        threading.Thread.__init__(self)
        self.name = name
        self.isRunning = True
        self.forceRestart = False

        self.cap = camera
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.out = cv2.VideoWriter('./static/video.avi', fourcc, 30.0, (640, 480))

    def run(self):
        while self.isRunning:
            ret, frame = self.cap.read()
            if ret:
                self.out.write(frame)

        self.out.release()

    def stop(self):
        self.isRunning = False

    def __del__(self):
        self.out.release()


class VideoCamera(object):
    def __init__(self, threshold=0.65, inverted=False, bbox=False,crossing = False, accuracy=False, video_status = False):
        # Open a camera
        self.cap = cv2.VideoCapture(1)

        self.flag_inverted = inverted
        self.threshold = threshold
        self.bbox = bbox
        self.accuracy = accuracy
        self.video_status = video_status
        self.crossing = crossing
        self.persons_in = 0
        self.line_trail = dict()
        self.engine = DetectionEngine('model_tflite/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite')
        self.ct = CentroidTracker()

        # Initialize video recording environment
        self.is_record = False
        self.out = None

        # Thread for recording
        self.recordingThread = None

    def __del__(self):
        self.cap.release()

    def get_frame(self):
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
                        cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 255), 5)
                    if self.bbox and self.accuracy:
                        cv2.putText(frame, str(obj.score), (int(box[0]) + 10, int(box[1] - 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    boxs.append(box)

            objects = self.ct.update(boxs)

            for (objectID, centroid) in objects.items():
                if objectID not in self.line_trail.keys():
                    self.line_trail[objectID] = deque(maxlen=2)
                if self.bbox:
                    cv2.putText(frame, str(objectID), (centroid[0] - 10, centroid[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 255), 4)
                    cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)
                center = (centroid[1], centroid[2])
                self.line_trail[objectID].appendleft(center)
                try:
                    diff = abs(self.line_trail[objectID][0][0] - self.line_trail[objectID][1][0])
                    if diff < 60:
                        if self.line_trail[objectID][0][1] < int(line1) and self.line_trail[objectID][1][1] > int(line1):
                            if self.flag_inverted:
                                self.persons_in += 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("+1,%s,%s" % (datetime.datetime.now(),device)))))
                            else:
                                self.persons_in -= 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("-1,%s,%s" % (datetime.datetime.now(),device)))))

                        elif self.line_trail[objectID][1][1] < int(line1) and self.line_trail[objectID][0][1] > int(line1):
                            if self.flag_inverted:
                                self.persons_in -= 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("-1,%s,%s" % (datetime.datetime.now(),device)))))
                            else:
                                self.persons_in += 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("+1,%s,%s" % (datetime.datetime.now(),device)))))
                        # if publish:
                        # publish.start()
                        # publish = None
                except Exception as Ex:
                    print(Ex)

            if self.video_status:
                frame = cv2.copyMakeBorder(frame, top=0, bottom=48, left=0, right=0, borderType=cv2.BORDER_CONSTANT,
                                           value=0)
                cv2.putText(frame, "Binnen: %s" % self.persons_in, (10, height + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (255, 255, 255), lineType=cv2.LINE_AA, thickness=2)
                cv2.putText(frame, "FPS: %d" % (1. / (time.time() - t1)), (260, height + 32), cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (255, 255, 255), lineType=cv2.LINE_AA, thickness=2)
            if self.crossing: cv2.line(frame, (0, line1), (width, line1), (255, 0, 144), 2)
        return cv2.imencode('.jpg', frame)[1].tostring()

    def toggle_video_status(self):
        self.video_status = not self.video_status

    def toggle_bbox(self):
        self.bbox = not self.bbox

    def toggle_accuracy(self):
        self.accuracy = not self.accuracy

    def toggle_crossing(self):
        self.crossing = not self.crossing


def start_record(self):
    self.is_record = True
    self.recordingThread = RecordingThread("Video Recording Thread", self.cap)
    self.recordingThread.start()


def stop_record(self):
    self.is_record = False

    if self.recordingThread != None:
        self.recordingThread.stop()
