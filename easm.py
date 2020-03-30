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
import math
from dataclasses import dataclass
from typing import Dict

def usage():
  print("easm.py infile.ea outfile.e")

class OutOfResources(Exception):
  pass

class SyntaxError(Exception):
  pass

# Handles tabbing the comment out. Used also by the test suite
def format_comment(line, comment):
  if not comment or comment=='':
    return line

  comment_col = 30
  l = len(line)

  if l>=comment_col:
    return line + ' ' + comment # always at least one space

  while l<comment_col:
    line += ' '
    l += 1
  return line + comment



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
    for i in range(r.limit):
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



class Assembler(object):
  def __init__(self):
    self.context = Context('filename')
    self.out = Output(context=self.context)
    self.symbols = SymbolTable()


  # Each argument processor fn maps from 0-based resource ids to strings
  # All return (string to output, table of symbol substitutions)
  def arg_literal(self, arg):
    return arg, {}  # empty dictionary meaning no named substitutions


  def patch_d(self, arg):
    name = arg[1:-1]  # strip off curly braces
    n = self.symbols.lookup('d', name)
    text = str(n+1)
    return text, {name: text}


  def patch_p(self, arg):
    name = arg[1:-1]  # strip off curly braces
    n = self.symbols.lookup('p', name)
    text = f'{math.floor(n/11)+1}-{n%11+1}'
    return text, {name: text}


  def patch_adapter(self, arg):
    m = re.match('(?P<type>ad\.(s|d|dp|sd))\.{(?P<name>ad-[A-Za-z0-9-]+)}\.(?P<param>-?\d\d?)', arg)
    if not m:
      raise SyntaxError('bad adapter syntax')

    adtype = m.group('type')
    name = m.group('name')
    n = self.symbols.lookup(adtype, name)
    text = f"{adtype}.{n+1}.{m.group('param')}"
    return text, {name: str(n+1)}


  # translates a literal accumulator number or named accumulator into aXX
  # handles:
  #   a13
  #   a{a-name}
  # returns text, symbols pair
  def lookup_accum(self, accum):
    if '{a-' in accum:
      # it's a name like {a-foo}
      name = accum[1:-1] # strip braces
      n = self.symbols.lookup('a', name)
      accumtext = 'a' + str(n+1)
      return accumtext, {name: accumtext }
    else:
      # it's just a number like 12
      return 'a' + accum, {}


  # translates [prefix]{reciever, transciever, or input}[suffix] into text, symbol
  # using prefix and suffix this handles cases like:
  #   op5
  #   op{t-name}
  #   12i
  #   {t-name}i
  #   {i-name}
  #   b
  # returns text,symbols pair 
  def lookup_accum_arg(self, accumtext, arg):
    if '-' in arg:
      m = re.match('(?P<prefix>[^{\d]*)(?P<name>{[rti]-[A-Za-z0-9-]+})(?P<suffix>.*)', arg)

      name = m.group('name')[1:-1]  # strip braces
      acc_idx = int(accumtext[1:])
      res_type = name[0]            # r or t

      n = self.symbols.lookup_acc(acc_idx, res_type, name)
      if res_type=='r':
        argtext = str(n+1)
      elif res_type=='t':
        argtext = str(n+5)          # transcievers start at 5
      else:
        argtext = ['a','b','g','d','e'][n]

      argtext = m.group('prefix')+argtext+m.group('suffix')
      return argtext, {name: argtext}
    else:
      # literal
      return arg, {}


  def patch_accum(self, arg):
    # up to two lookups per accumulator patch: acc idx and program/input
    # long regex for terminal ensures that i, o, or None suffix matches t,r,i
    m = re.match('a(?P<accum>(\d\d?|{a-[A-Za-z0-9-]+}))\.(?P<terminal>((\d\d?|{t-[A-Za-z0-9-]+})[io]|(\d\d?|{r-[A-Za-z0-9-]+})i|{i-[A-Za-z0-9-]+}|[abgdeAS]))', arg)
    if not m:
      raise SyntaxError('bad accumulator terminal')

    accumtext, symbols = self.lookup_accum(m.group('accum'))
    argtext, symbols2 = self.lookup_accum_arg(accumtext, m.group('terminal'))
    symbols.update(symbols2)

    # put it all back together
    text = accumtext + '.' + argtext
    return text, symbols


  def patch_argument(self, arg):
    patch_dispatch = {
        re.compile(r"\d\d?"):             self.arg_literal,   # digit trunk literal
        re.compile(r"{d-[A-Za-z0-9-]+}"): self.patch_d,       # named digit trunk     
        re.compile(r"\d\d?-\d\d?"):       self.arg_literal,   # program line literal
        re.compile(r"{p-[A-Za-z0-9-]+}"): self.patch_p,       # named program line
        re.compile(r"ad\..+"):            self.patch_adapter, # adapter
        re.compile(r"a.+\..+"):           self.patch_accum,   # accumulator, more complex handling
        re.compile(r"f[123]\..+"):        self.arg_literal    # function table 
    }

    for pattern, handler in patch_dispatch.items():
      if pattern.match(arg):
        return handler(arg)

    raise SyntaxError(f"unknown patch terminal '{arg}'")


  def symbols_to_comment(self, symbols1, symbols2, comment):
    symbols = list(symbols1.items()) + list(symbols2.items())
    symbol_comment = ', '.join([f'{k}={v}' for k,v in symbols])
    if symbol_comment != '':
      symbol_comment = '# ' + symbol_comment

    if comment:
      return symbol_comment + '; ' + comment[1:] # strip leading # on comment
    else:
      return symbol_comment


  def line_p(self, arg1, arg2, comment):
    text1, symbols1 = self.patch_argument(arg1)
    text2, symbols2 = self.patch_argument(arg2)

    comment = self.symbols_to_comment(symbols1, symbols2, comment)

    return format_comment('p ' + text1 + ' ' + text2, comment)
  

  def line_s(self, arg1, arg2, comment): 
    accumtext = None

    # accumulator switches are the only place we currently replace
    m = re.match('a(?P<accum>(\d\d?|{a-[A-Za-z0-9-]+}))\.(?P<prog>.+)',arg1)
    if m: 
      accumtext, symbols1 = self.lookup_accum(m.group('accum'))
      progtext, symbols2 = self.lookup_accum_arg(accumtext, m.group('prog'))
      symbols1.update(symbols2)
      arg1 = accumtext + '.' + progtext
    
    else:
      # it's not an accumulator, no replacement
      symbols1 = {}

    # arg2 may be an input name
    if '{i-' in arg2:
      name = arg2[1:-1]  # strip braces
      if not accumtext:
        raise SyntaxError('switch cannot be set to an accumulator input')
      arg2, symbols2 = self.lookup_accum_arg(accumtext, arg2)
    else:
      symbols2 = {}

    comment = self.symbols_to_comment(symbols1, symbols2, comment)
    return format_comment('s ' + arg1 + ' ' + arg2, comment)


  def line_blank(self, arg1, arg2, comment): 
    self.out.emit(line)


  def assemble_line(self,line):
    # The types of lines we understand
    line_dispatch = {
      re.compile(r"p\s+(?P<arg1>[^\s]+)\s+(?P<arg2>[^\s]+)(?P<comment>\s+#.*)?"): self.line_p,
      re.compile(r"s\s+(?P<arg1>[^\s]+)\s+(?P<arg2>[^\s]+)(?P<comment>\s+#.*)?"): self.line_s,
      re.compile(r".*(#.*)?") : self.line_blank
    }

    for pattern, handler in line_dispatch.items():
      m = pattern.match(line)
      if m:
        arg1, arg2, comment = m.groups()
        return handler(arg1, arg2, comment)
        break


  def assemble(self, file):
    text = file.read()
    self._scan(text)


  def _scan(self, text):
    for line_number, line in enumerate(text.splitlines()):
      self.context.line_number = line_number
      self.assemble_line()



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
    #print(line) 
    pass


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


