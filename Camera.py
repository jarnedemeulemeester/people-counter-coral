import threading
from edgetpu.detection.engine import DetectionEngine
from PIL import Image
from timeit import time
import cv2
from tools.CentroidTracker import CentroidTracker
from tools.data_manager import DataManager
from collections import deque
from threading import Thread
from multiprocessing import Process
from dotenv import load_dotenv
import os


class VideoCamera(object):
    """
    Video camera class:
    this class all the video processing, the received frames are sent to the web interface.
    """

    def __init__(self, threshold=0.65, inverted=False, bbox=False, crossing=False, accuracy=False, video_status=False,
                 back_color=0, fore_color=(255, 255, 255), bbox_color=(0, 0, 255), crossing_color=(255, 255, 0)):
        """
        This function initializes the VideoCamera class, this class will capture and handle the video stream for the
        flask web server (debugging tool)
        :param threshold: This is used to specify what threshold you want the detection to run on.
        :param inverted: This is used to invert the order in which the camera is detecting people going in or out
        :param bbox: This is used as flag to show or hide the bounding boxes
        :param crossing: This is used as flag to show or hide the crossing line
        :param accuracy: This is used to show the accuracy (it is currently not implemented)
        :param video_status: This flag is used to show more video stats.
        :param back_color: This is used to change the color of the video stats background (it is currently not implemented)
        :param fore_color: This is used to change the color of the videos tats text (also currently not implemented)
        :param bbox_color: This is used to change the color of the bounding boxes
        :param crossing_color: This is used to change the color of the crossing line.
        """
        load_dotenv()

        # Open a camera
        self.cap = cv2.VideoCapture(1)

        # DataController
        self.manager = DataManager(nsdb_host=os.getenv('NSDB_HOST'), nsdb_port=os.getenv('NSDB_PORT'), redis_host=os.getenv('REDIS_HOST'), redis_port=os.getenv('REDIS_HOST'), database='pc', namespace='pc', metric='people')

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
        Thread(target=lambda: self._run_loop()).start()

    def __del__(self):
        """
        In the case that you delete the class instance, it will release the camera so you don't have to completely shut
        down the flask web server to regain access to your camera
        :return: No return
        """
        self.cap.release()

    def _run_loop(self):
        """
        This is the heart of the code, all the video processing happens here. If you want more clarification feel free
        to check the readme on our github: https://github.com/DemeulemeesterJarne/people-counter (however this is
        currently still documentation on the outdated concept code)
        :return: No return
        """
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
                                                           resample=Image.NEAREST)
                boxs = []

                # Display result.
                for obj in detections:
                    if obj.label_id == 0:
                        box = obj.bounding_box.flatten().tolist()
                        if self.bbox:
                            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])),
                                          self.bbox_color, 5)
                            # if self.accuracy:
                            cv2.putText(frame, str(round(obj.score, 2)), (int(box[0]) + 10, int(box[1] +30)),
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
                                    Process(self.manager.send_data(1)).start()
                                else:
                                    self.persons_in -= 1
                                    Process(self.manager.send_data(-1)).start()

                            elif self.line_trail[objectID][1][1] < int(line1) and self.line_trail[objectID][0][1] > int(
                                    line1):
                                if self.flag_inverted:
                                    self.persons_in -= 1
                                    Process(self.manager.send_data(-1)).start()
                                else:
                                    self.persons_in += 1
                                    Process(self.manager.send_data(+1)).start()
                    except:
                        pass
                    # we don't handle the thrown error since it is not needed, if we would handle it we would only
                    # waste processing power for something irrelevant

                if self.video_status:
                    frame = cv2.copyMakeBorder(frame, top=0, bottom=48, left=0, right=0, borderType=cv2.BORDER_CONSTANT,
                                               value=self.video_back_color)
                    cv2.putText(frame, "Binnen: %s" % self.persons_in, (10, height + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                                self.video_foreground_color, lineType=cv2.LINE_AA, thickness=2)
                    cv2.putText(frame, "FPS: %d" % (1. / (time.time() - t1)), (260, height + 32),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.0, self.video_foreground_color, lineType=cv2.LINE_AA, thickness=2)
                if self.crossing: cv2.line(frame, (0, line1), (width, line1), self.crossing_color, 2)
            self.frame = cv2.imencode('.jpg', frame)[1].tostring()

    def get_frame(self):
        """
        This method is created so you can retrieve the data from the video processing loop.
        :return: The last frame from the loop
        """
        return self.frame

    def toggle_video_status(self):
        """
        This method is used to update the video status flag
        :return: No return
        """
        self.video_status = not self.video_status

    def toggle_bbox(self):
        """
        This method is used to update the bounding box flag
        :return: No return
        """
        self.bbox = not self.bbox

    def toggle_accuracy(self):
        """
        This method is used to update the accuracy flag
        :return:
        """
        self.accuracy = not self.accuracy

    def toggle_crossing(self):
        """
        This method is used to update the visual crossing flag
        :return: No return
        """
        self.crossing = not self.crossing

    def set_video_background_color(self, color):
        """
        This method is used to change the video background color
        :param color: This is the specified BGR color which we want to change to.
        :return: No return
        """
        self.video_back_color = color

    def set_video_foreground_color(self, color):
        """
        This method is used to change the video foreground color
        :param color: This is the specified BGR color which we want to change to.
        :return: No return
        """
        self.video_foreground_color = color

    def set_bbox_color(self, color):
        """
        This method is used to change the bounding box color
        :param color: This is the specified BGR color which we want to change to.
        :return: No return
        """
        self.bbox_color = color

    def set_crossing_color(self, color):
        """
        This method is used to change the crossing color
        :param color: This is the specified BGR color which we want to change to.
        :return: No return
        """
        self.crossing_color = color
