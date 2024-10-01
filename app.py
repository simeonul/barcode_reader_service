import cv2
import numpy as np
from flask import Flask, request, jsonify

from scanners.detection_decoding import DetectionDecoding
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/scan', methods=['POST'])
def scan():
    file = request.files['image'].read()
    nparr = np.frombuffer(file, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    barcode = DetectionDecoding.detect_decode(img)
    if barcode is None:
        return jsonify({'search_message': 'No barcode detected'}), 204

    return jsonify({'barcode': barcode}), 200


@app.route('/validate/<string:barcode>', methods=['GET'])
def validate(barcode):
    is_valid = DetectionDecoding.validate(barcode)
    if is_valid:
        return jsonify({'validation_message': 'Valid'}), 200
    return jsonify({'validation_message': 'Invalid'}), 400


@app.route('/test-scan', methods=['POST'])
def test_scan():
    img = cv2.imread("results/initial_image.png", cv2.IMREAD_COLOR)

    barcode = DetectionDecoding.detect_decode(img)
    if barcode is None:
        return jsonify({'search_message': 'No barcode detected'}), 204

    return jsonify({'barcode': barcode}), 200