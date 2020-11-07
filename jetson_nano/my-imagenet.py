#!/usr/bin/python3
#
# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditi./my-imagenet --log-level=verbose --headless --camera=/dev/video0  --model=/home/nano/i375x1kh/resnet18.onnx --input_blob=input_0 --output_blob=output_0 --labels=/home/nano/i375x1kh/labelsons:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,# print out the result

# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import jetson.inference
import jetson.utils

import argparse
import sys
import RPi.GPIO as GPIO
import time

# To run this program, assuming that your model is in the /home/nano/models/i375x1kh directory
#
# ./my-imagenet.py --log-level=silent --headless --camera=/dev/video0  --model=/home/nano/models/i375x1kh/resnet18.onnx --input_blob=input_0 --output_blob=output_0 --labels=/home/nano/models/i375x1kh/labels.txt

# Pin Definitions
class_0_pin = 12  # BCM pin 18, BOARD pin 12
class_1_pin = 16  
class_2_pin = 18  


# parse the command line
parser = argparse.ArgumentParser(description="Classify a live camera stream using an image recognition DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.imageNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())

parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="googlenet", help="pre-trained model to load (see below for options)")
parser.add_argument("--camera", type=str, default="0", help="index of the MIPI CSI camera to use (e.g. CSI camera 0)\nor for VL42 cameras, the /dev/video device to use.\nby default, MIPI CSI camera 0 will be used.")
parser.add_argument("--width", type=int, default=1280, help="desired width of camera stream (default is 1280 pixels)")
parser.add_argument("--height", type=int, default=720, help="desired height of camera stream (default is 720 pixels)")
parser.add_argument('--headless', action='store_true', default=(), help="run without display")

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

try:
	opt = parser.parse_known_args()[0]
except:
	parser.print_help()
	sys.exit(0)

# load the recognition network
net = jetson.inference.imageNet(opt.network, sys.argv)

# create video sources & outputs
input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)
output = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv+is_headless)

# Pin Setup:
GPIO.setmode(GPIO.BOARD)  # BCM pin-numbering scheme from Raspberry Pi
# set pin as an output pin with optional initial state of HIGH
GPIO.setup(class_0_pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(class_1_pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(class_2_pin, GPIO.OUT, initial=GPIO.LOW)

try:
	# process frames until the user exits
	while True:
		# capture the next image
		img = input.Capture()

		# classify the image
		class_id, confidence = net.Classify(img)

		# Switch on/off the LEDs
		GPIO.output(class_0_pin, class_id==0)
		GPIO.output(class_1_pin, class_id==1)
		GPIO.output(class_2_pin, class_id==2)

		# find the object description
		class_desc = net.GetClassDesc(class_id)

		# print out the result
		print("image is recognized as '{:s}' (class #{:d}) with {:f}% confidence".format(class_desc, class_id, confidence * 100))

		time.sleep(1)  # One inference per second
finally:
	GPIO.cleanup()
	


