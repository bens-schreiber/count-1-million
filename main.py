import queue
import threading
import time
from flask import Flask, render_template
from flask_sock import Sock

COUNT_SPEED = 100_000


app = Flask(__name__)
sock = Sock(app)


counter = [0]
counter_mtx = threading.Lock()

q: queue.Queue[threading.Thread] = queue.Queue()


def worker() -> None:
    while True:
        task = q.get()
        task.start()
        task.join()
        q.task_done()


threading.Thread(target=worker, daemon=True).start()


def work(ws) -> None:
    def send(msg: str = "You are counting to 1,000,000: "):
        """
        Update the client with the current count
        Thread safe
        """
        with counter_mtx:
            ws.send(f"""<div id="ws"><h1>{msg}</h1> {counter[0]}</div>""")

    def count():
        """
        Count to 1,000,000 at a rate of COUNT_SPEED per 0.01s
        Reset the counter to 0 when it reaches 1,000,000
        Thread safe
        """

        with counter_mtx:
            counter[0] = 0
        send()

        while counter[0] < 100_000_000:
            with counter_mtx:
                counter[0] += COUNT_SPEED
            send()
            time.sleep(0.01)

    def get_position(item) -> int:
        with q.mutex:
            try:
                return q.queue.index(item) + 1
            except ValueError:
                return 1

    # Create a job and add it to the queue
    # Interestingly, the "daemon" flag allows us to kill the thread when the parent thread dies,
    # which is useful for our use case because a web socket connection could be closed at any time
    thread = threading.Thread(target=count, daemon=True)
    q.put(thread)

    # While the job is not being worked on, send the user their position in the queue
    while not thread.is_alive():
        send(f"Somebody else is counting, you're in position: {get_position(thread)} ")

        # Block the thread
        time.sleep(0.01)

    # The job is being worked on, wait for it to finish
    thread.join()


@app.route("/")
def hello_world():
    return render_template("index.html")


@sock.route("/ws")
def ws(ws):
    while True:
        work(ws)


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    try:
        app.run(debug=True, threaded=True)
    except KeyboardInterrupt:
        sock.close_all()
