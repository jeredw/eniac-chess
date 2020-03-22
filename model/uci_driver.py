#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runs a chess engine over UCI."""

import math
import threading
import time
import logging

from game import Position
from cheetah import CheetahEngine

def _uci_driver(engine):
  logging.basicConfig(level=logging.DEBUG,
                      format="%(process)d %(asctime)s %(name)-12s	%(levelname)-8s %(message)s",
                      filename="/tmp/chess.log",
                      filemode="w")
  engine.start()
  next_position = None
  logger = logging.getLogger("driver")
  logger.info("starting up!")
  while True:
    command = input()
    logger.debug(command)
    if command == "uci":
      print("id name {}".format(engine.name))
      print("id author {}".format(engine.author))
      print("uciok")
    elif command == "ucinewgame":
      engine.stop.set()
    elif command == "isready":
      print("readyok")
    elif command.startswith("position "):
      args = command[len("position "):]
      if args.startswith("startpos"):
        args = args[len("startpos"):]
        next_position = Position.initial()
        if args.startswith(" moves "):
          args = args[len(" moves "):]
          moves = [Move.lan(x) for x in args.split()]
          for move in moves:
            next_position = make_move(next_position, move)
      elif args.startswith("fen "):
        args = args[len("fen "):]
        next_position = Position.fen(args)
      logger.debug("next position: {}".format(str(next_position)))
    elif command == "go" or command.startswith("go "):
      engine.position = next_position
      engine.wait_for_stop = "infinite" in command
      engine.go.set()
    elif command == "stop":
      engine.stop.set()
    elif command.startswith("debug "):
      pass
    elif command.startswith("setoption "):
      pass
    elif command == "register":
      pass
    elif command == "quit":
      break
  logger.info("quitting!")
  engine.stop.set()
  engine.go.set()
  engine.quit.set()
  engine.join()
  logger.info("shutdown cleanly")


if __name__ == "__main__":
  engine = CheetahEngine()
  _uci_driver(engine)
