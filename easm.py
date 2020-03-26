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
# ad    adapter, 1-40 (simulator limitation) for each type
import sys
import re

def usage():
  print("easm.py infile.ea outfile.e")

class OutOfResources(Exception):
  pass

class SyntaxError(Exception):
  pass

# Possible arguments to p (things that can be patched)
# N,M = unsigned integers

"a(\d\d?|{a-[az-]+}).((\d\d?|{[rt]-[az-]+})[io]|op(\d\d?|{[rt]-[az-]+})|[abgdeAS]|)"

# this is effectively the symbol table
names = {
  'd':  {},
  'p':  {},
  'a':  {},
  'ad': {},
}


patch_dispatch = {
  re.compile(r"\d\d?"):           patch_literal,      # digit trunk
  re.compile(r"{d-[az-]+}"):      patch_d,            
  re.compile(r"\d\d?-\d\d?"):     patch_literal,      # program line
  re.compile(r"{p-[az-]+}"):      patch_p,
  re.compile(r"a.+\..+"):         patch_accum,        # accumulator, more complex handling
  re.compile(r"ad\..+"):          patch_adapter       # adapter
}

def patch_literal(arg):
  return arg, {}  # empty dictionary meaning no named substitutions

# Allocate one of the global resources
def allocate_global(resource, name):
  things = {
    'd': ("digit trunks", 9)
    'p': ("program lines", 121
    'a': ("accumulators", 20),
    'ad.s': ("shift adapters", 20),
    'ad.d': ("deleter adapters", 20),
    'ad.dp': ("digit pulse adapters", 20),
    'ad.sd': ("special digit adapters", 20)
  }

  limit = things[resource][1]
  error = things[resource][0]
  n = names[resource]
  if n == limit:
    raise OutOfResources(error)

  number = n+1
  d[name] = number
  return number


def patch_d(arg):
  name = arg[1:-1]  # strip off curly braces
  d = names['d']
  if name in d:
    n = d[name]
  else:
    n = allocate_global('d',name))
  text = str(n)
  return text, {name: text}


def patch_p(arg):
  name = arg[1:-1]  # strip off curly braces
  p = names['p']
  if name in p:
    n = p[name]
  else:
    n = allocate_global('p',name))
  text = f'{Math.floor(x/11)+1}-{x%11+1}'
  return text, {name: text}

def patch_adapter(arg):
  m = re.match('(?P<type>ad\.(s|d|dp|sd))\.{(?P<name>ad-[az-]+)}\.(?P<param>-?\d\d?)',arg)
  if not m:
    raise SyntaxError('bad adapter syntax')
  adtype = m.group('name')
  name = m.group('type')
  ad = names[adtype]
  if name in ad:
    n = ad[name]
  else
    n = allocate_global(adtype, name)
  text = f'{adtype}.{n}.{m.group(\'param\')}'
  return text, {name: text}



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
  re.compile(r"p\s+(?P<arg1>[^\s]+)\s+(?P<arg2>[^\s]+)(?P<comment>\s+#.*)?"): line_p,
  re.compile(r"s\s+(?P<arg1>[^\s]+)\s+(?P<arg2>[^\s]+)(?P<comment>\s+#.*)?"): line_s,
  re.compile(r".*(#.*)?") : line_blank
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


