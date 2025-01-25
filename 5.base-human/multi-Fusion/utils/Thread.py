#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import time, sys
import ctypes
import threading
import inspect
from threading import Thread


class MyThreadFunc(object):
    """
    手动终止线程的方法
    """

    def __init__(self, func, args):
        self.myThread = threading.Thread(target=func, args=args, daemon=True)

    def start(self):
        if sys.gettrace():
            active_threads = threading.enumerate()
            # print(f"Active threads: {len(active_threads)}")
        if not self.myThread.is_alive():
            self.myThread.start()

    def stop(self):
        try:
            for i in range(5):
                self._async_raise(self.myThread.ident, SystemExit)
                time.sleep(0.5)
        except:
            pass

    def _async_raise(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")


class MyThread(Thread):
    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None
    ):
        Thread.__init__(
            self,
            group=group,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon,
        )
        add_thread(self)

    def get_id(self):
        # returns id of the respective thread
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(SystemExit)
        )
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print("Exception raise failure")


__thread_list = []


def add_thread(thread: MyThread):
    if thread not in __thread_list:
        __thread_list.append(thread)


def remove_thread(thread: MyThread):
    if thread in __thread_list:
        __thread_list.remove(thread)


def stopAll():
    for thread in __thread_list:
        thread.raise_exception()
        thread.join()
