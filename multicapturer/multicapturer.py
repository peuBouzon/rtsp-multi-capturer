
from typing import List
import cv2 as cv
import threading
import time
import queue
from data.frame import Frame


class Capturer:
    RECONNECTION_PERIOD = 30

    def __init__(self, conn_str: str, max_failures_to_shutdown: int) -> None:
        self.conn_str = conn_str
        self.max_failures_to_shutdown = max_failures_to_shutdown
        self.thread = threading.Thread(target=self.target, daemon=True)
        self.retrieve_event = threading.Event()
        self.done_event = threading.Event()
        self.stop_event = threading.Event()
        self.queue = queue.Queue(maxsize=1)
        self.thread.start()

    def target(self):
        capturer = cv.VideoCapture(self.conn_str)
        closed = not capturer.isOpened()
        last_reconnection_try = time.time()
        fails = self.max_failures_to_shutdown if closed else 0
        while not self.stop_event.is_set():
            if self.retrieve_event.is_set():
                if closed or not ret:
                    self.queue.put_nowait(Frame(ret, None, self.conn_str))
                else:
                    ret, frame = capturer.retrieve()
                    self.queue.put_nowait(Frame(ret, frame, self.conn_str))

                self.retrieve_event.clear()
                self.done_event.set()

            ret = capturer.grab()
            fails = 0 if ret else fails + 1
            if fails >= self.max_failures_to_shutdown and (time.time() - last_reconnection_try) > Capturer.RECONNECTION_PERIOD:
                capturer.release()
                capturer = cv.VideoCapture(self.conn_str)
                closed = not capturer.isOpened()
                if closed:
                    # TODO: log error
                    pass
                last_reconnection_try = time.time()


class MultiCapturer:
    MAX_FAILURES_TO_SHUTDOWN_CAPTURER = 30

    def __init__(self, conn_strs: List, frame_rate: int) -> None:
        self.conn_strs = conn_strs
        self.frame_rate = frame_rate
        self.capturers = [Capturer(
            conn_str=c, max_failures_to_shutdown=MultiCapturer.MAX_FAILURES_TO_SHUTDOWN_CAPTURER*frame_rate) for c in conn_strs]
        self.thread = threading.Thread(target=self.target)
        self.stop_event = threading.Event()
        self.queue = queue.Queue(maxsize=10)
        self.thread.start()

    def target(self) -> None:
        period = 1/self.frame_rate
        last = 0
        while not self.stop_event.is_set():
            now = time.time()
            if (now - last) > period:
                try:
                    for capturer in self.capturers:
                        capturer.retrieve_event.set()
                    frames = []
                    for capturer in self.capturers:
                        capturer.done_event.wait(timeout=period)
                        frames.append(
                            capturer.queue.get_nowait(timeout=period))
                        capturer.done_event.clear()
                    self.queue.put_nowait(frames)
                # TODO: log errors
                except queue.Full:
                    pass
                except queue.Empty:
                    pass
                except:
                    pass
            last = now

    def stop(self):
        self.stop_event.set()
