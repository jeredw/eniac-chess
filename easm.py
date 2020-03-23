#!/usr/bin/env python
# Assembler for B. Stuart's ENIAC simulator
# Rewrites resource labels to numbers, tracking resources on the machine. 
#
# Usage: python easm.py infile.ea outfile.e
#
# Replaces [resourcetype-name] with a corresponding resource number,
# allocated on first appearance.
#
# Resources which can be allocated:
# a     accumulator, 1-20
# p     program line, 1-1 to 11-11
# d     data trunk, 1-9
# r     accumulator receiver, 1-5 on each accumulator
# t     accumulator transciever, 6-12 on each accumulator
# as    shift adapter, 1-40 (simulator limitation)
# ad    deleter adapter, 1-40
# adp   digit pulse adapter, 1-40
# asd   "specical digit" adapter, 1-40
import sys
import re

def usage():
  print("easm.py infile.ea outfile.e")


# Possible arguments to p (things that can be patched)
# N,M = unsigned integers
# aN.Mo
# aN.Mi
# aN.[abcde]
# aN.[AS]
# N-M           # program line
# N             # data trunk
# ad.dp.N.M
# ad.s.N.M
# ad.d.N.M
# ad.sd.N.M


def line_p(line, m, out):
  arg1,arg2,comment = m.groups()
  if not comment:
    comment=""
  out.emit("PPP arg1=" + arg1 + " arg2=" + arg2 + " " + comment)

def line_s(line, m, out): 
  out.emit("SSS " +  line)

def line_blank(line, m, out): 
  out.emit(line)


# The types of lines we understand
dispatch_table_line = {
  re.compile(r"p\s+(?P<arg1>[^\s]+)\s+(?P<arg2>[^\s]+)(?P<comment>\s+#.*)?")   : line_p,
  re.compile(r"s\s+(?P<arg1>[^\s]+)\s+(?P<arg2>[^\s]+)(?P<comment>\s+#.*)?")   : line_s,
  re.compile(r".*(#.*)?")     : line_blank
}


class Assembler(object):
  def __init__(self,
               filename,
               print_errors=True):
    self.context = Context(filename)
    self.out = Output(context=self.context)

  def assemble(self, file):
    text = file.read()
    self._scan(text)

  def _scan(self, text):
    for line_number, line in enumerate(text.splitlines()):
      self.context.line_number = line_number

      for pattern, handler in dispatch_table_line.items():
        m = pattern.match(line)
        if m:
          handler(line, m, self.out)
          break



class Context(object):
  def __init__(self, filename):
    self.filename = filename
    self.line_number = 0
    self.had_fatal_error = False


class Output(object):
  def __init__(self,
               context=None,
               print_errors=True):
    self.print_errors = print_errors
    self.errors = []
    self.output = ""

  def error(self, what):
    self.errors.append((self.context.filename, 1 + self.context.line_number, what))
    if self.print_errors:
      print("{}:{}: {}".format(self.context.filename, 1 + self.context.line_number, what))

  def emit(self, line):
    print(line) 





def main():
  if len(sys.argv) == 1:
    usage()
    sys.exit(1)

  infile = sys.argv[1]
  f = open(infile)
  asm = Assembler(infile)
  out = asm.assemble(f)

if __name__ == "__main__":
  main()


