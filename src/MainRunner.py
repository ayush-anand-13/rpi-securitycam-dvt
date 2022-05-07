from camera.RaspberryCamera import RaspberryCamera
from runner.TimeRunner import TimeRunner
from runner.AlwaysOnRunner import AlwaysOnRunner
from database.S3database import S3database
from time import sleep
import argparse
from cv2 import cv2
from PIL import Image
import boto3
from botocore.exceptions import NoCredentialsError
import time
import datetime
import base64
import json



import numpy as np
from camera.MotionCamera import MotionCamera
from database.Database import Database
from runner.Runner import Runner

import io
import time
import asyncio
from typing import Optional
from ffmpeg import FFmpeg
from time import sleep, perf_counter
from threading import Thread

def vid_save(recorded_stream,encoded_filename):

    print('Saving to database')
    database.save_footage(recorded_stream, encoded_filename)

def img_save(encoded_filename,timestamp):

    print('Saving image to database')
    cap = cv2.VideoCapture(encoded_filename)
    ret, img = cap.read()
    cap.release()

    image = Image.fromarray(img)

    fileName = '{}.png'.format(timestamp)
    image = image.resize((160,160))
    image.save(fileName)
    lambda_client = boto3.client('lambda')
    fh = open(fileName, "rb").read()
    encoded_img = base64.b64encode(fh).decode('utf-8')
    #encoded_img = encoded_img.decode('utf-8')
    input = {
    'name': fileName,
    'image':encoded_img
    }
    response = lambda_client.invoke(
    FunctionName = 'dockerApi',
    InvocationType='Event',
    Payload=json.dumps(input))

    print(response==None)

    #t = response['Payload']
    #print(t)
    t = (response['Payload']['status_code'])
    print(t)
    f = response['Payload'].read().decode("utf-8")
    print(f)

    #database.save_footage(recorded_stream, encoded_filename)



def run(camera, database,runner):

    image_pair = [None, camera.capture_next_image()]
    last_motion_triggered = time.time()
    database.connect()

    runner.start()
    startTime = time.time()
    camera.start_recording()
    camera.start_preview()


    while runner.should_run():

        if time.time() - startTime > 0.5:
            camera.stop_recording()
            camera.stop_preview()
            recorded_stream = camera.get_video_stream()
            recorded_stream.seek(0)
            #file_save(camera, database,runner,recorded_stream)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            encoded_filename = '{}.h264'.format(timestamp)
            encoded_filename1 = '{}.h264'.format(timestamp)
            with open(encoded_filename, 'wb') as outfile:
                outfile.write(recorded_stream.getbuffer())



    # create two new threads
            t1 = Thread(target=img_save, args=[encoded_filename1,timestamp])
            t2 = Thread(target=vid_save, args=[recorded_stream,encoded_filename])

            # start the threads
            t1.start()
            t2.start()


            camera.start_recording()
            camera.start_preview()
            startTime = time.time()


    camera.close()
    database.close()


def get_result():
    sqs_client = boto3.client('sqs')
    output_queue = 'https://sqs.us-east-1.amazonaws.com/451636408257/outputMessageQueue'
    while True:
        response = sqs_client.receive_message(QueueUrl=output_queue,
                                              MaxNumberOfMessages=10
                                              )

        messages = response.get('Messages', [])
        endtime = time.time()

        for message in messages:
            receipt_handle = message['ReceiptHandle']

            result = message['Body']
            values = result.split(',')
            #print(values)
            dateVal = values[0].split('.')
            timeStart = datetime.datetime.strptime(dateVal[0], "%Y%m%d-%H%M%S").timestamp()

            print("Year:"+values[1]+' '+ "Name:" + values[2] +' '+ "Major:" + values[3])




            print("Latency = ", (endtime - timeStart))
            sqs_client.delete_message(QueueUrl=output_queue, ReceiptHandle=receipt_handle)
            #print('Message deleted.')

if __name__ == '__main__':

    start_time = perf_counter()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--time',
        type=int,
        help='Puts security camera on timed mode. Will run for this time before shutting down.',
        default=60
    )

    parser.add_argument(
        '-a',
        '--always-on',
        action='store_true',
        help='Puts security camera on always-on mode. Will run until interrupted.'
    )

    args = parser.parse_args()

    camera = RaspberryCamera()
    sleep(1)

    if args.always_on:
        runner = AlwaysOnRunner()
    else:
        runner = TimeRunner(args.time)

    database = S3database()
    #detector = MotionDetector(cam, s3db, runner)
    #detector.run(camera, database,runner)



    run(camera,database,runner)

    end_time = perf_counter()

    print(f'It took {end_time- start_time: 0.2f} second(s) to complete.')


    s3_client1 = boto3.client('s3')
    timestamp2 = time.strftime("%Y%m%d-%H%M%S")
    encoded_filename1 = '{}.png'.format(timestamp2)
    s3_client1.upload_file(
            fileName,
            'inputcse546pi',
            encoded_filename1
        )



    #database.save_footage(recorded_stream, encoded_filename)
