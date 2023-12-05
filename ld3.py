import tkinter as tk
from tkinter import ttk
import threading
import queue
import time

def is_prime(number):
    if number <= 1:
        return False
    for i in range(2, int(number**0.5) + 1):
        if number % i == 0:
            return False
    return True

def producer(file_queue, file_names):
    for file_name in file_names:
        with open(file_name, 'r') as file:
            numbers = [int(line.strip()) for line in file]
            file_queue.put(numbers)
    # Do not put a stop signal in the producer

def consumer(file_queue, stats, consumer_control):
    while True:
        with consumer_control['lock']:
            if consumer_control['active'] > consumer_control['desired']:
                break
        task = file_queue.get()
        if task is None:  # Ignore None tasks, continue processing
            file_queue.task_done()
            continue
        for number in task:
            if is_prime(number):
                with stats_lock:
                    stats['min_prime'] = min(stats['min_prime'], number)
                    stats['max_prime'] = max(stats['max_prime'], number)
        with stats_lock:
            stats['files_done'] += 1
        file_queue.task_done()
    with consumer_control['lock']:
        consumer_control['active'] -= 1

def adjust_threads(desired_num_threads):
    with consumer_control['lock']:
        consumer_control['desired'] = desired_num_threads
        while consumer_control['active'] < consumer_control['desired']:
            t = threading.Thread(target=consumer, args=(file_queue, stats, consumer_control))
            t.daemon = True
            t.start()
            consumer_control['active'] += 1

# Shared resources and initial setup
file_names = [f'file{i}.txt' for i in range(1, 1001)]  # Replace with actual file names
file_queue = queue.Queue()
stats = {'num_threads': 0, 'files_done': 0, 'min_prime': float('inf'), 'max_prime': 0}
stats_lock = threading.Lock()
consumer_control = {'active': 0, 'desired': 0, 'lock': threading.Lock()}
max_consumer_threads = 10

# GUI class
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
        adjust_threads(new_thread_count)
        self.update_thread_count()

    def decrease_threads(self):
        new_thread_count = max(0, consumer_control['desired'] - 1)
        adjust_threads(new_thread_count)
        self.update_thread_count()

    def update_thread_count(self):
        with consumer_control['lock']:
            self.thread_count_var.set(f"Threads: {consumer_control['active']}")

    def update_stats(self):
        with stats_lock:
            self.files_done_var.set(f"Files Done: {stats['files_done']}")
            max_prime = stats['max_prime'] if stats['max_prime'] != 0 else "N/A"
            self.max_prime_var.set(f"Max Prime: {max_prime}")
            min_prime = stats['min_prime'] if stats['min_prime'] != float('inf') else "N/A"
            self.min_prime_var.set(f"Min Prime: {min_prime}")
        self.root.after(1000, self.update_stats)

# Start producer and initial consumer threads
producer_thread = threading.Thread(target=producer, args=(file_queue, file_names))
producer_thread.start()
adjust_threads(1)  # Start with 1 consumer thread

# Start the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = PrimeNumberApp(root)
    root.mainloop()
