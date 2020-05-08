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
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return 'Out of ' + self.msg

class SyntaxError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return 'Syntax error: ' + self.msg

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
      'ad.sd':  Resource('special digit adapters', 40, {}),
      'ad.permute':  Resource('permutation adapters', 40, {})
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


@dataclass
class Macro:
  '''A text macro that substitutes args for bound values in lines.'''
  name: str
  args: [str]
  lines: [str]


class Assembler(object):
  def __init__(self):
    self.symbols = SymbolTable()
    self.defmacro = None  # Macro object currently being defined
    self.macros = {}  # name -> Macro


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
    m = re.match(r'(?P<type>ad\.(s|d|dp|sd|permute))\.(?P<name>(\d\d?|{ad-[A-Za-z0-9-]+}))(?P<param>\.-?\d\d?)?', arg)
    if not m:
      raise SyntaxError('bad adapter syntax')

    name = m.group('name')
    if '{ad-' in name:
      name = name[1:-1] # strip off curly braces       
      adtype = m.group('type')
      n = self.symbols.lookup(adtype, name)
      if adtype != 'ad.permute':
        text = f"{adtype}.{n+1}{m.group('param')}"  # param includes leading '.'
      else:
        text = f"{adtype}.{n+1}"  # permute adapters have no params, set by "switch" instead
      return text, {name: str(n+1)}
    else:
      # literal adapter number
      return arg, {}


  # Translates a literal accumulator number or named accumulator into aXX
  # Handles cases:
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
      # it's a literal like 'a12'
      return accum, {}


  # Translates [prefix]{reciever, transciever, or input}[suffix] into text, symbol
  # using prefix and suffix. Handles cases:
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

      prefix = m.group('prefix')
      suffix = m.group('suffix')
      name = m.group('name')[1:-1]    # strip braces
      acc_idx = int(accumtext[1:])-1  # strip 'a', convert to 0-based
      res_type = name[0]              # r or t

      n = self.symbols.lookup_acc(acc_idx, res_type, name)
      if res_type=='r':
        argtext = str(n+1)
      elif res_type=='t':
        argtext = str(n+5)          # transcievers start at 5
      else:
        if prefix!='':
          raise SyntaxError(f"extra characters '{prefix}' before input specifier")
        argtext = ['a','b','g','d','e'][n]

      argtext = prefix + argtext + suffix 
      return argtext, {name: argtext}
    else:
      # literal
      return arg, {}


  def patch_accum(self, arg):
    # up to two lookups per accumulator patch: acc idx and program/input
    # long regex for terminal ensures that i, o, or None suffix matches t,r,i
    m = re.match('(?P<accum>(a\d\d?|{a-[A-Za-z0-9-]+}))\.(?P<terminal>((\d\d?|{t-[A-Za-z0-9-]+})[io]|(\d\d?|{r-[A-Za-z0-9-]+})i|{i-[A-Za-z0-9-]+}|[abgdeAS]))', arg)
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
        re.compile(r"(a\d\d?|{a-[A-Za-z0-9-]+})\..+"): self.patch_accum,   # accumulator, more complex handling
        re.compile(r".+"):                self.arg_literal    # function table, initiating unit, etc. (all else)
    }

    for pattern, handler in patch_dispatch.items():
      if pattern.match(arg):
        return handler(arg)

    raise SyntaxError(f"unknown patch terminal '{arg}'")


  def symbols_to_comment(self, symbols1, symbols2, comment):
    symbols = list(symbols1.items()) + list(symbols2.items())
    symbol_comment = ', '.join([f'{v}={k}' for k,v in symbols])

    if symbol_comment == '':
      return comment

    symbol_comment = '# ' + symbol_comment
    if comment:
      return symbol_comment + '; ' + comment[1:] # strip leading # on comment
    else:
      return symbol_comment


  def line_p(self, line):
    m = re.match(r'(\s*p)\s+([^\s]+)\s+([^\s]+)\s*(#.*)?', line)
    leading_ws, arg1, arg2, comment = m.groups()

    text1, symbols1 = self.patch_argument(arg1)
    text2, symbols2 = self.patch_argument(arg2)

    comment = self.symbols_to_comment(symbols1, symbols2, comment)

    return format_comment(leading_ws + ' ' + text1 + ' ' + text2, comment)
  

  # e.g. s {a-name}.op{t-name} {i-name}
  def line_s_accum(self, leading_ws, arg1, arg2, comment):

    # do we need to lookup accumulator name?
    accumtext = None
    m = re.match(r'(?P<accum>(a\d\d?|{a-[A-Za-z0-9-]+}))\.(?P<prog>.+)',arg1)
    if not m: 
      raise SyntaxError('bad accumulator switch setting') # probably can't get here due to match in caller

    accumtext, symbols1 = self.lookup_accum(m.group('accum'))
    progtext, symbols2 = self.lookup_accum_arg(accumtext, m.group('prog'))
    symbols1.update(symbols2)
    arg1 = accumtext + '.' + progtext

    # do we need to look up an acc input name? e.g. {i-name}
    if '{i-' in arg2:
      name = arg2[1:-1]  # strip braces
      arg2, symbols2 = self.lookup_accum_arg(accumtext, arg2)
    else:
      symbols2 = {}

    comment = self.symbols_to_comment(symbols1, symbols2, comment)
    return format_comment(leading_ws + ' ' + arg1 + ' ' + arg2, comment)


  # e.g. s ad.permute.{ad-my-permuter} 11.10.9.8.7.6.5.4.3.2.1
  def line_s_permute(self, leading_ws, arg1, arg2, comment):
    m = re.match(r'ad.permute.{(?P<name>ad-[A-Za-z0-9-]+)}',arg1)
    if not m: 
      raise SyntaxError('bad permute switch setting') # probably can't get here due to match in caller

    name = m.group('name')
    n = self.symbols.lookup('ad.permute', name)
    symbols = {name: str(n+1)}
    arg1 = 'ad.permute.' + str(n+1)

    comment = self.symbols_to_comment(symbols, {}, comment)
    return format_comment(leading_ws + ' ' + arg1 + ' ' + arg2, comment)


  # for switch settings, we can lookup accumuators and permute adapters
  def line_s(self, line): 
    m = re.match(r'(\s*s)\s+([^\s]+)\s+([^\s]+)\s*(#.*)?', line)
    leading_ws, arg1, arg2, comment = m.groups()

    if re.match(r'a\d\d?|{a-[A-Za-z0-9-]+}',arg1):
      return self.line_s_accum(leading_ws, arg1, arg2, comment)

    if re.match(r'ad\.permute\.{ad-[0-9a-zA-Z-]+}',arg1):
      return self.line_s_permute(leading_ws, arg1, arg2, comment)
      
    if re.search(r'{[a-zA-z]+-.+}', arg1+arg2):
      raise SyntaxError('bad switch setting')

    return self.line_literal(line)


  # Handles symbol definitions e.g. {p-foo}=3-1
  def line_define(self, line):
    m = re.match(r'{(?P<name>[apd]-[A-Za-z0-9-]+)}\s*=\s*(?P<value>a?\d\d?(-\d\d?)?)\s*(#.*)?', line)
    if not m:
      raise SyntaxError('bad definition value')
    name = m.group('name')
    value = m.group('value')
    res_type = name[0]

    if res_type=='d':
      if not re.match(r'\d\d?',value):
        raise SyntaxError('bad data trunk value')
      value = int(value)-1
    elif res_type=='a':
      if not re.match(r'a\d\d?',value):
        raise SyntaxError('bad accumulator value')
      value = int(value[1:])-1          # 'a1' -> 0
    else:
      if not re.match(r'\d\d?-\d\d?',value):
        raise SyntaxError('bad program line value')
      a,b = value.split('-')
      value = (int(a)-1)*11 + int(b)-1

    self.symbols.define(res_type, name, value)

    return '# ' + line  # echo the define statement, commented out


  def line_literal(self, line): 
    return line


  def line_defmacro(self, line):
    m = re.match(r'\s*defmacro\s+(?P<name>[^\s]+)\s*(?P<args>[^#]*)(#.*)?', line)
    if not m:
      raise SyntaxError('bad defmacro')
    name = m.group('name')
    args = m.group('args').strip().split()
    self.defmacro = Macro(name=name, args=args, lines=[])
    return f"# (elided '{name}' macro definition)"


  def line_domacro(self, line):
    m = re.match(r'\s*\$(?P<name>[^\s]+)\s*(?P<args>[^#]*)(#.*)?', line)
    if not m:
      raise SyntaxError('bad macro invocation')
    name = m.group('name')
    args = m.group('args').strip().split()
    if not name in self.macros:
      raise SyntaxError(f"undefined macro '{name}'")
    macro = self.macros[name]
    if len(args) != len(macro.args):
      raise SyntaxError(f'macro argument count mismatch')

    # comment macro invocation and output it
    outlines = '# ' + line + '\n'

    # map from argument names to values
    arg_values = dict(zip(macro.args, args))

    # output macro lines with appropriate substitutions
    for line in macro.lines:
      for name, value in arg_values.items():
        line = line.replace(f'${name}', value)
      # in case people want to say $macro {arg} instead of $macro arg
      line = line.replace('{{', '{')
      line = line.replace('}}', '}')
      outlines += self.assemble_line(line) + '\n'
    return outlines.strip()  # '\n' will be added by _scan


  def line_inmacro(self, line):
    # add lines to macro until reaching endmacro
    if re.match(r'\s*endmacro', line):
      self.macros[self.defmacro.name] = self.defmacro
      self.defmacro = None
      return
    self.defmacro.lines.append(line)


  def assemble_line(self,line):
    # The types of lines we understand
    line_dispatch = {
      re.compile(r'\s*p\s+([^\s]+)\s+([^\s]+)\s*(#.*)?'): self.line_p,
      re.compile(r'\s*s\s+([^\s]+)\s+([^\s]+)\s*(#.*)?'): self.line_s,
      re.compile(r'\s*{[apd]-[A-Za-z0-9-]+}\s*=.+'):      self.line_define,
      re.compile(r'\s*defmacro.*'):                       self.line_defmacro,
      re.compile(r'\s*\$([^\s]+).*'):                     self.line_domacro,
      re.compile(r'.*'):                                  self.line_literal
    }

    for pattern, handler in line_dispatch.items():
      if pattern.match(line):
        return handler(line)
        break


  def _scan(self, text):
    out = ''
    for line_number, line in enumerate(text.splitlines()):
      try:
        if self.defmacro:
          outlines = self.line_inmacro(line)
        else:
          outlines = self.assemble_line(line)
      except Exception as e:
        print(line)
        print(str(e) + ' at line ' + str(line_number+1) )
        return None
      if outlines != None:
        out += outlines + '\n'
    if self.defmacro:
      print(f'unterminated macro {self.defmacro.name}')
      return None
    return out


  def assemble(self, intext):
    return self._scan(intext)


def main():
  if len(sys.argv) < 3:
    usage()
    sys.exit(1)

  intext = open(sys.argv[1]).read()

  a = Assembler()
  outtext = a.assemble(intext)

  if outtext:
    open(sys.argv[2], 'w+').write(outtext)

if __name__ == "__main__":
  main()


