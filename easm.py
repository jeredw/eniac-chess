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
from dataclasses import dataclass
from typing import Dict

def usage():
  print("easm.py infile.ea outfile.e")

class OutOfResources(Exception):
  pass

class SyntaxError(Exception):
  pass

# Possible arguments to p (things that can be patched)
# N,M = unsigned integers



@dataclass
class Resource:
  '''A single type of enumerated resource, and the allocated items'''
  desc: str
  limit: int
  symbols: Dict[str,int]

class SymbolTable:
  def __init__(self):
    # shared across entire machine
    self.sym_global = {
      'd':      Resource('digit trunks', 9, {}),
      'p':      Resource('program lines', 121, {}),
      'a':      Resource('accumulators', 20, {}),
      'ad.s':   Resource('shift adapters', 40, {}),
      'ad.d':   Resource('deleter adapters', 40, {}),
      'ad.dp':  Resource('digit pulse adapters', 40, {}),
      'ad.sd':  Resource('special digit adapters', 40, {})
    }
    # per accumulator
    self.sym_acc = [ 
      { 
        'r':    Resource('receiver programs', 4, {}),
        't':    Resource('transciever programs', 8, {}),
        'i':    Resource('accumulator inputs', 5, {})
      } 
      for i in range(20) ]

  def _lookup(self, r:Resource, name:str):
    # is this symbol defined already?
    if name in r.symbols:
      return r.symbols[name]

    # not found, allocate the next available
    allocated = r.symbols.values()
    for i in range(1,r.limit+1):        # 1 based resource numbers 
      if i not in allocated:
        r.symbols[name] = i
        return i
    
    raise OutOfResources(r.desc)

  def define(self, resource_type, name, idx):
    '''Define a name to refer to a given resource'''
    r = self.sym_global[resource_type]
    r.symbols[name] = idx

  def lookup(self, resource_type, name):
    '''Lookup/allocate a named global resource of given type'''
    r = self.sym_global[resource_type]
    return self._lookup(r, name)

  def lookup_acc(self, acc_idx, resource_type, name):
    '''Lookup/allocate a named resource on a particular accumulator'''
    r = self.sym_acc[acc_idx][resource_type]
    return self._lookup(r, name)



def patch_literal(arg):
  return arg, {}  # empty dictionary meaning no named substitutions


def patch_d(arg):
  name = arg[1:-1]  # strip off curly braces
  d = names['d']
  if name in d:
    n = d[name]
  else:
    n = allocate_global('d',name)
  text = str(n+1)
  return text, {name: text}


def patch_p(arg):
  name = arg[1:-1]  # strip off curly braces
  p = names['p']
  if name in p:
    n = p[name]
  else:
    n = allocate_global('p',name)
  text = f'{Math.floor(x/11)+1}-{x%11+1}'
  return text, {name: text}


def patch_adapter(arg):
  m = re.match('(?P<type>ad\.(s|d|dp|sd))\.{(?P<name>ad-[A-Za-z0-9-]+)}\.(?P<param>-?\d\d?)', arg)
  if not m:
    raise SyntaxError('bad adapter syntax')
  adtype = m.group('name')
  name = m.group('type')
  ad = names[adtype]
  if name in ad:
    n = ad[name]
  else:
    n = allocate_global(adtype, name)
  text = f"{adtype}.{n}.{m.group('param')}"
  return text, {name: text}


def patch_accum(arg):
  # we can do up to two lookups per accumulator patch: accumulator and program/input
  m = re.match('a(?P<accum>(\d\d?|{a-[A-Za-z0-9-]+}))\.(?P<connection>((\d\d?|{[rt]-[A-Za-z0-9-]+})[io]|[abgdeAS]))', arg)
  if not m:
    raise SyntaxError('bad accumulator syntax')

  symbols = {}
  text = 'a'

  # is the accumulator named or literal?
  accum = m.groups('accum')
  if '-' in accum: 
    # it's an accumulator name, lookup
    a = names['a']
    if accum in a:
      n = a[accum]
    else:
      n = allocate_global('a',accum)
    text = 'a' + str(n+1)
    symbols[accum] = text
  else:
    # it's a literal
    text = accum    

  text += '.'

  # does the connection contain a name?
  accum = m.groups('connection')
  if '-' in accum: 
    # it's a program (transceiver/reciever) name, lookup
    pass
  else:
    # it's a literal
    text += connection    

  return text, symbols


patch_dispatch = {
  re.compile(r"\d\d?"):           patch_literal,      # digit trunk
  re.compile(r"{d-[a-z-]+}"):     patch_d,            
  re.compile(r"\d\d?-\d\d?"):     patch_literal,      # program line
  re.compile(r"{p-[a-z-]+}"):     patch_p,
  re.compile(r"a.+\..+"):         patch_accum,        # accumulator, more complex handling
  re.compile(r"ad\..+"):          patch_adapter       # adapter
}


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


