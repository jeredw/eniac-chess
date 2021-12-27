import threading
import logging

class UCIEngine(threading.Thread):
  """Base class for wrapping engines to work over UCI.

  Engine wrappers can mostly ignore threading and just implement
  evaluate(position), but to respect the protocol they should bail with the
  current best move if self.stop.is_set().
  """

  def __init__(self, name="name", author="author"):
    super().__init__()
    self.log = logging.getLogger("{} engine".format(name))
    self.name = name
    self.author = author
    self.position = None
    self.wait_for_stop = False
    self.quit = threading.Event()
    self.go = threading.Event()
    self.stop = threading.Event()

  def run(self):
    while not self.quit.is_set():
      self.log.debug("waiting for go")
      self.go.wait()
      if self.quit.is_set():
        self.log.debug("quitting")
        break
      self.stop.clear()
      self.go.clear()
      self.log.debug("evaluate {}".format(str(self.position)))
      move = self.evaluate(self.position)
      if self.wait_for_stop:
        self.log.debug("waiting for stop event")
        self.stop.wait()
      self.stop.clear()
      print("bestmove {}".format(move), flush=True)
      self.log.debug("bestmove {}".format(move))

  def evaluate(position):
    raise NotImplementedError
