import sys
sys.path.append("./Histogram Model")
from flask import Flask, render_template, Response, jsonify, request, flash, abort
from flask_socketio import SocketIO, join_room, emit
import cv2
import base64
import numpy as np
from werkzeug.utils import secure_filename
import os
from recognize_gesture import recognize
from keras.models import load_model
from base64 import b64encode
import subprocess

app = Flask(__name__, template_folder='.')
app.config['imgdir'] = 'abcd/upload'
socketio = SocketIO(app)

def readb64(encoded_data):
    nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def emit64(img):
    x = 'data:image/png;base64,'
    g = cv2.imencode('.png', img)[1].tostring()
    return x+base64.b64encode(g).decode('ascii')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream', methods=['GET'])
def stream():
    with open('output.mp4', 'rb') as o:
        x=o.read()
    return Response(x, 206, mimetype='video/mp4', content_type='video/mp4', direct_passthrough=True)

@app.route('/upload', methods=['POST'])
def upload():
    print(request.files)
    if 'data' not in request.files:
        #flash('No file part')
        abort(404)
    file = request.files['data']
    print(type(file))
    print(file.filename)
    print('--------------------------')
    filename = secure_filename(file.filename) # save file 
    filepath = os.path.join(app.config['imgdir'], filename) + '.webm'
    print(filepath)
    file.save(filepath)
    model_path = os.path.join(app.config['imgdir'], 'cnn_model_keras2.h5')
    print(model_path)
    model = load_model('cnn_model_keras2.h5')

    #with open('output.mp4', 'rb') as o:
    #    x=o.read()
    #return Response(x, 206, mimetype='video/mp4', content_type='video/mp4', direct_passthrough=True)
    m = recognize(filepath)

    subprocess.Popen("[ -e static/output.mp4 ] && rm static/output.mp4", shell=True,stdout=subprocess.PIPE).wait()
    command = "ffmpeg -i 'static/output.avi' -ac 2 -b:v 2000k -c:a aac -c:v libx264 -b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 'static/output.mp4'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()
    return jsonify({"a": m})

    """
    cap = cv2.VideoCapture(filepath)
    if (cap.isOpened()== False):
        print('shobhit')
        abort(404)
    while(cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == True:
            # Display the resulting frame
            #cv2.imshow('Frame',frame)
            # Press Q on keyboard to  exit
            #if cv2.waitKey(25) & 0xFF == ord('q'):
                #break
        # Break the loop
            break
        else:
            break
    cap.release()
    return jsonify({"a":2});
    """

#not used currently
def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@socketio.on('create')
def on_create(data):
    x = 'data:image/png;base64,'
    image = readb64(data[len(x):])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    emit('join_room', emit64(gray))


if __name__ == '__main__':
    app.run(threaded=False)
    #socketio.run(app, debug=True)
