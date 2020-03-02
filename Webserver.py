from flask import Flask, render_template, Response, jsonify, request
from Camera import VideoCamera


app = Flask(__name__)

video_camera = None
global_frame = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/record_status', methods=['POST'])
def record_status():
    global video_camera
    if video_camera == None:
        video_camera = VideoCamera()

    json = request.get_json()

    status = json['status']

    if status == "true":
        video_camera.start_record()
        return jsonify(result="started")
    else:
        video_camera.stop_record()
        return jsonify(result="stopped")


def video_stream():
    global video_camera
    global global_frame

    if video_camera == None:
        video_camera = VideoCamera()

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
    return Response(video_stream(),mimetype='multipart/x-mixed-replace; boundary=frame')

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
    return  jsonify({'success':True}), 200, {'ContentType':'application/json'}





if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)