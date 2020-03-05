from flask import Flask, render_template, Response, jsonify, request
from Camera import VideoCamera
import os
import logging
from threading import Thread

app = Flask(__name__)

global_frame = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/board_status', methods=['post'])
def device_handler():
    json = request.get_json()
    status = json['status']

    if status == "Shutdown":
        os.system('sudo shutdown now')
    elif status == "Reboot":
        os.system('sudo reboot')

    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


def video_stream():
    global video_camera
    global global_frame

    while True:
        frame = video_camera.get_frame()

        if frame != None:
            global_frame = frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n\r\n')


@app.route('/video_viewer')
def video_viewer():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/toggle', methods=['POST'])
def toggle_video():
    json = request.get_json()
    toggle = json['toggle']
    if toggle == "VideoStats":
        video_camera.toggle_video_status()
    elif toggle == "Bbox":
        video_camera.toggle_bbox()
    elif toggle == "Crossing":
        video_camera.toggle_crossing()
    elif toggle == "Accuracy":
        video_camera.toggle_accuracy()
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/color', methods=['POST'])
def change_color():
    json = request.get_json()
    ColorPicker = json['ColorPicker'].rstrip(" ")
    Color = json['Color']
    if ColorPicker == "VideoStatsFgColor":
        video_camera.set_video_foreground_color(Color)
    elif ColorPicker == "VideoStatsBgColor":
        video_camera.set_video_background_color(Color)
    elif ColorPicker == "BboxColor":
        video_camera.set_bbox_color(Color)
    elif ColorPicker == "CrossingColor":
        video_camera.set_crossing_color(Color)
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


if __name__ == '__main__':
    video_camera = VideoCamera()
    app.run(host='0.0.0.0', threaded=True)
