from edgetpu.detection.engine import DetectionEngine
import argparse
from PIL import Image
from timeit import time
import cv2
import warnings
from tools.CentroidTracker import CentroidTracker
from collections import deque
import threading

warnings.filterwarnings('ignore')


def main(options):
    flag_invert = options.invert
    fullscreen = options.fullscreen

    persons_in = 0
    line_trail = dict()

    engine = DetectionEngine('model_tflite/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite')
    ct = CentroidTracker()

    # capture videocamera
    cap = cv2.VideoCapture(1)

    while True:
        ret, frame = cap.read()
        t1 = time.time()

        if ret:
            img = Image.fromarray(frame)
            width, height = img.size
            line1 = int(height / 2 - 50)

            # Run inference.
            detections = engine.detect_with_image(img, threshold=options.threshold, keep_aspect_ratio=True,
                                                  relative_coord=False, top_k=10, resample=Image.NEAREST)  # BICUBIC
            boxs = []

            # Display result.
            for obj in detections:
                if obj.label_id == 0:
                    box = obj.bounding_box.flatten().tolist()
                    cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 255), 5)
                    cv2.putText(frame, str(obj.score), (int(box[0]) + 10, int(box[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 255, 255), 2)
                    boxs.append(box)

            objects = ct.update(boxs)

            for (objectID, centroid) in objects.items():
                if objectID not in line_trail.keys():
                    line_trail[objectID] = deque(maxlen=2)
                cv2.putText(frame, str(objectID), (centroid[0] - 10, centroid[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 255), 4)
                cv2.circle(frame, (centroid[0], centroid[1]), 4, "#00ff00", -1)
                center = (centroid[1], centroid[2])
                line_trail[objectID].appendleft(center)
                try:
                    diff = abs(line_trail[objectID][0][0] - line_trail[objectID][1][0])
                    if diff < 60:
                        if line_trail[objectID][0][1] < int(line1) and line_trail[objectID][1][1] > int(line1):
                            if flag_invert:
                                persons_in += 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("+1,%s,%s" % (datetime.datetime.now(),device)))))
                            else:
                                persons_in -= 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("-1,%s,%s" % (datetime.datetime.now(),device)))))

                        elif line_trail[objectID][1][1] < int(line1) and line_trail[objectID][0][1] > int(line1):
                            if flag_invert:
                                persons_in -= 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("-1,%s,%s" % (datetime.datetime.now(),device)))))
                            else:
                                persons_in += 1
                                # publish = threading.Thread(target=(lambda: publisher.publish_to_topic(data = ("+1,%s,%s" % (datetime.datetime.now(),device)))))
                        # if publish:
                        # publish.start()
                        # publish = None
                except Exception as Ex:
                    pass  # niet nodig om heir iets af te handelen :)

            frame = cv2.copyMakeBorder(frame, top=0, bottom=48, left=0, right=0, borderType=cv2.BORDER_CONSTANT,
                                       value=0)
            cv2.putText(frame, "Binnen: %s" % persons_in, (10, height + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (255, 255, 255), lineType=cv2.LINE_AA, thickness=2)
            cv2.putText(frame, "FPS: %d" % (1. / (time.time() - t1)), (260, height + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (255, 255, 255), lineType=cv2.LINE_AA, thickness=2)
            cv2.line(frame, (0, line1), (width, line1), (255, 0, 144), 2)

            if fullscreen:
                cv2.namedWindow("Visualisation", cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty("Visualisation", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow('Visualisation', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--invert', type=bool, default=True, help='binnen <-> buiten --> buiten <-> binnen')
    parser.add_argument('--fullscreen', type=bool, default=False, help='Fullscreen the video output')
    parser.add_argument('--threshold', type=float, default=0.65, help='minimum allowed value for the threshold')
    options = parser.parse_args()
    main(options)
