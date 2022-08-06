
from typing import List
import cv2 as cv
import threading
import time
import queue
from data.frame import Frame
import logging


class Capturer:
    """
    A class used to read a rtsp stream whenever triggered

    ...

    Attributes
    ----------
    RECONNECTION_PERIOD: int
        the period to retry reconnections to the camera.
    conn_str : str
        the rtsp connection string
    max_failures_to_shutdown : int
        the maximum number of failures to read before try to reconnect
    thread : threading.Thread
        the capturer thread
    retrieve_event : threading.Event
        the event that triggers the camera reading
    done_event: threading.Event
        the event that indicates that a new frame is available
    stop_event: threading.Event
        the event that stop the capturer thread execution
    queue: queue.Queue
        the queue that stores the new frames

    Methods
    -------
    target()
        The capturer's thread target function. It puts a new frame on the
        capturer's queue whenever the retrieve_event is set and the result is
        indicated by the done_event.
    stop()
        Stops the capturer's thread.
    """
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
        capturer = cv.VideoCapture(
            self.conn_str if not self.conn_str.isdigit() else int(self.conn_str))
        closed = not capturer.isOpened()
        last_reconnection_try = time.time()
        fails = self.max_failures_to_shutdown if closed else 0
        ret = capturer.grab()
        while not self.stop_event.is_set():
            if self.retrieve_event.is_set():
                if closed:
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
                    logging.error(
                        f'Reconnection of the camera {self.conn_str} failed.', exc_info=True)
                last_reconnection_try = time.time()

    def stop(self):
        self.stop_event.set()


class MultiCapturer:
    """
    A class used to read multiple rtsp stream synchronously.

    ...

    Attributes
    ----------
    MAX_FAILURES_TO_SHUTDOWN_CAPTURER : int
        the maximum number of failures to read before try to reconnect
    frame_rate : int
        the frame retrieval rate
    capturers : list
        the list of multicapturer.Capturer
    thread : threading.Thread
        the multi capturer thread
    retrieve_event : threading.Event
        the event that triggers the camera reading
    stop_event: threading.Event
        the event that stop the multi capturer thread execution
    queue: queue.Queue
        the queue that stores the batch of frames

    Methods
    -------
    target()
        The multi capturer's thread target function.
    stop()
        Stops the multi capturer's thread.
    """
    MAX_FAILURES_TO_SHUTDOWN_CAPTURER = 30

    def __init__(self, conn_strs: List, frame_rate: int) -> None:
        self.conn_strs = conn_strs
        self.frame_rate = frame_rate
        self.capturers = [Capturer(
            conn_str=c, max_failures_to_shutdown=MultiCapturer.MAX_FAILURES_TO_SHUTDOWN_CAPTURER*frame_rate) for c in conn_strs]
        self.thread = threading.Thread(target=self.target, daemon=True)
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
                        try:
                            frames.append(
                                capturer.queue.get(timeout=0.9*period))
                        except queue.Empty:
                            logging.error(
                                f'Failed to read camera {capturer.conn_str}. Empty Buffer.', exc_info=True)

                        capturer.done_event.clear()
                    self.queue.put_nowait(frames)

                    last = now
                    time_remaining = period + now - time.time()
                    if time_remaining < 0:
                        logging.error(
                            'The application is losing frames, please consider upgrading your hardware or lowering the frame_rate')
                    else:
                        time.sleep(0.95*time_remaining)
                except queue.Full:
                    logging.error(
                        f'Failed to push frames to output queue. The queue is full.', exc_info=True)
                except Exception as e:
                    logging.critical(
                        f'Application failed unexpectedly.', exc_info=True)
                    raise e

    def stop(self):
        for capturer in self.capturers:
            capturer.stop()
        self.stop_event.set()
