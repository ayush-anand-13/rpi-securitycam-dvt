#from MotionDetector import MotionDetector
from camera.RaspberryCamera import RaspberryCamera
from runner.TimeRunner import TimeRunner
from runner.AlwaysOnRunner import AlwaysOnRunner
from database.S3database import S3database
from time import sleep
import argparse

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

def file_save(camera, database,runner):

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    encoded_filename = '{}.h264'.format(timestamp)

    print('Saving to database')
    database.save_footage(recorded_stream, encoded_filename)

    camera.start_recording()
    camera.start_preview()
    startTime = time.time()

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
            file_save(camera, database,runner)

    camera.close()
    database.close()

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
    # create two new threads
    t1 = Thread(target=run, args=[camera, database,runner])
    t2 = Thread(target=file_save, args=[camera, database,runner])

    # start the threads
    t1.start()
    t2.start()

    # wait for the threads to complete
    t1.join()
    t2.join()

    end_time = perf_counter()

    print(f'It took {end_time- start_time: 0.2f} second(s) to complete.')