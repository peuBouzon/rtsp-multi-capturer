# rtsp-multi-capturer
Package to read multiple cameras with no delay between them. Based on OpenCV.

Features:
- Asynchronous capture of rtsp streams or webcams,
- Ajustable frame frate,
- Automatic reconnection.

## Installation

Please make sure you have python 3.8 or latter installed.

#### Create a virtual environment

On the console, navigate to the project folder and do the following:

`mkdir venv`

`python3 -m venv ./venv`

`source ./venv/bin/activate`

You should see a (venv) displayed in your terminal.

#### Install the dependencies

The dependencies of the project are listed in the requirements.txt file. To install them, do the following:

`pip3 install -r requirements.txt`

That's it!

## Run the project

To run the project, please make sure you have activated your virtual environment and do the following:

`python3 app.py 0 --fps 1`

![Screenshot from 2022-08-06 15-27-08](https://user-images.githubusercontent.com/44006813/183261462-15ad502b-1284-4bad-87e5-56caededa9d6.png)
