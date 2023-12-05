import tkinter as tk
from tkinter import ttk
import threading
import queue
import time
import random

def is_prime(number):
    if number <= 1:
        return False
    for i in range(2, int(number**0.5) + 1):
        if number % i == 0:
            return False
    return True

def producer(file_queue, consumer_control):
    workload_size = 100000  # Increased workload size
    while True:
        if consumer_control['desired'] > 0:
            workload = [random.randint(1, 100000) for _ in range(workload_size)]
            file_queue.put(workload)
            time.sleep(0.5)  # Added a delay to prevent overloading the queue
        else:
            time.sleep(0.1)

def consumer(file_queue, stats, consumer_control, thread_id):
    while True:
        with consumer_control['lock']:
            if thread_id >= consumer_control['desired']:
                consumer_control['active'] -= 1
                break
        task = file_queue.get()
        for number in task:
            if is_prime(number):
                with stats_lock:
                    stats['min_prime'] = min(stats['min_prime'], number)
                    stats['max_prime'] = max(stats['max_prime'], number)
        with stats_lock:
            stats['files_done'] += 1
        file_queue.task_done()

def adjust_threads(desired_num_threads, consumer_control):
    with consumer_control['lock']:
        consumer_control['desired'] = desired_num_threads
        while consumer_control['active'] < consumer_control['desired']:
            thread_id = consumer_control['active']
            t = threading.Thread(target=consumer, args=(file_queue, stats, consumer_control, thread_id))
            t.daemon = True
            t.start()
            consumer_control['active'] += 1

file_queue = queue.Queue()
stats = {'num_threads': 0, 'files_done': 0, 'min_prime': float('inf'), 'max_prime': 0}
stats_lock = threading.Lock()
consumer_control = {'active': 0, 'desired': 0, 'lock': threading.Lock()}
max_consumer_threads = 10

class PrimeNumberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Prime Number Processor")

        self.thread_count_var = tk.StringVar(value="Threads: 0")
        self.files_done_var = tk.StringVar(value="Files Done: 0")
        self.max_prime_var = tk.StringVar(value="Max Prime: N/A")
        self.min_prime_var = tk.StringVar(value="Min Prime: N/A")

        ttk.Button(root, text="+", command=self.increase_threads).pack()
        ttk.Button(root, text="-", command=self.decrease_threads).pack()

        ttk.Label(root, textvariable=self.thread_count_var).pack()
        ttk.Label(root, textvariable=self.files_done_var).pack()
        ttk.Label(root, textvariable=self.max_prime_var).pack()
        ttk.Label(root, textvariable=self.min_prime_var).pack()

        self.update_stats()

    def increase_threads(self):
        new_thread_count = min(max_consumer_threads, consumer_control['desired'] + 1)
        adjust_threads(new_thread_count, consumer_control)
        self.update_thread_count()

    def decrease_threads(self):
        new_thread_count = max(0, consumer_control['desired'] - 1)
        adjust_threads(new_thread_count, consumer_control)
        self.update_thread_count()

    def update_thread_count(self):
        with consumer_control['lock']:
            self.thread_count_var.set(f"Threads: {consumer_control['desired']}")

    def update_stats(self):
        with stats_lock:
            self.files_done_var.set(f"Files Done: {stats['files_done']}")
            max_prime = stats['max_prime'] if stats['max_prime'] != 0 else "N/A"
            self.max_prime_var.set(f"Max Prime: {max_prime}")
            min_prime = stats['min_prime'] if stats['min_prime'] != float('inf') else "N/A"
            self.min_prime_var.set(f"Min Prime: {min_prime}")
        self.root.after(1000, self.update_stats)

if __name__ == "__main__":
    root = tk.Tk()
    app = PrimeNumberApp(root)
    producer_thread = threading.Thread(target=producer, args=(file_queue, consumer_control))
    producer_thread.daemon = True
    producer_thread.start()
    root.mainloop()
