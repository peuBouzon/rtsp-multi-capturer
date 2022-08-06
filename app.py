from multicapturer.multicapturer import MultiCapturer
import cv2 as cv
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('rtsp', nargs='+')
    parser.add_argument('--fps', type=int, default=1)
    args = parser.parse_args()

    multi_capturer = MultiCapturer(conn_strs=args.rtsp, frame_rate=args.fps)

    while True:
        windows = [cv.namedWindow(
            f'Frame {i}', cv.WINDOW_NORMAL) for i in len(args.rtsp)]
        frames = multi_capturer.queue.get()
        for i, frame in enumerate(frames):
            if (frame.ret):
                cv.imshow(f'Frame {i}', frame.frame)
            if cv.waitKey(1) & 0xFF == ord('q'):
                cv.destroyAllWindows()
                break
