from multicapturer.multicapturer import MultiCapturer
import cv2 as cv
import argparse
import logging
from datetime import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('rtsp', nargs='+')
    parser.add_argument('--fps', type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(filename='multi-camera.log', level=logging.DEBUG)
    logging.info(f'Application started on {datetime.now()}')

    multi_capturer = MultiCapturer(conn_strs=args.rtsp, frame_rate=args.fps)
    stop_execution = False
    while True:
        windows = [cv.namedWindow(
            f'Frame {i}', cv.WINDOW_NORMAL) for i in range(len(args.rtsp))]
        frames = multi_capturer.queue.get()
        for i, frame in enumerate(frames):
            if (frame.ret):
                cv.imshow(f'Frame {i}', frame.frame)
            if cv.waitKey(1) & 0xFF == ord('q'):
                stop_execution = True
        if stop_execution:
            multi_capturer.stop()
            cv.destroyAllWindows()
            break
    logging.info(f'Application finished on {datetime.now()}')
