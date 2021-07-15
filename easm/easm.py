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
# p     program line, 1-1 to 26-11
# d     data trunk, 1-20
# f     function table, 1-3
# r     accumulator receiver, 1-5 on each accumulator
# t     accumulator transciever, 6-12 on each accumulator
# t     selective clear transceiver, 1-6 on init unit
# t     function table transceiver, 1-11 on each function table
# t     constant transceiver, 2-25 (1, 26-30 are manual)
# ad    adapter, 1-40 (simulator limitation) for each type
# pa    pulse amplifier channel, 8x11
# da    debug assertions
# db    debug breakpoints
# dd    debug dumps
import sys
import os
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
      'd':      Resource('digit trunks', 20, {}),
      'p':      Resource('program lines', 26*11, {}),
      'a':      Resource('accumulators', 20, {}),
      'f':      Resource('function tables', 3, {}),
      'i.t':    Resource('selective clear transceivers', 6, {}),
      'c.t':    Resource('constant transceivers', 24, {}),
      'ad.s':   Resource('shift adapters', 80, {}),
      'ad.d':   Resource('deleter adapters', 80, {}),
      'ad.dp':  Resource('digit pulse adapters', 80, {}),
      'ad.sd':  Resource('special digit adapters', 80, {}),
      'ad.permute':  Resource('permutation adapters', 80, {}),
      'pa':     Resource('pulse amplifier channels', 88, {}),
      'da':     Resource('debug asserts', 40, {}),
      'db':     Resource('debug breakpoints', 40, {}),
      'dd':     Resource('debug dumps', 40, {}),
    }
    # per accumulator
    self.sym_acc = [ 
      { 
        'r':    Resource('receiver programs', 4, {}),
        't':    Resource('transceiver programs', 8, {}),
        'i':    Resource('accumulator inputs', 5, {})
      } 
      for i in range(20) ]
    # per ft
    self.sym_ft = [
      {
        't':    Resource('ft transceiver programs', 11, {}),
      }
      for i in range(3) ]

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
    '''Lookup/allocate a named global resource of given type. 
       Name should include resource type e.g. d-name.'''
    r = self.sym_global[resource_type]
    return self._lookup(r, name)

  def lookup_acc(self, acc_idx, resource_type, name):
    '''Lookup/allocate a named resource on a particular accumulator'''
    r = self.sym_acc[acc_idx][resource_type]
    return self._lookup(r, name)

  def lookup_ft(self, ft_idx, resource_type, name):
    '''Lookup/allocate a named resource on a particular ft'''
    r = self.sym_ft[ft_idx][resource_type]
    return self._lookup(r, name)

  def summarize_resource_usage(self):
    def bitmap(alloc):
      result = ["."] * alloc.limit
      for r in alloc.symbols.values():
        result[r] = "*"
      return ''.join(result)

    num_ts_used = 0
    num_ts_avail = 0
    per_acc = []
    for acc in range(20):
      inputs = self.sym_acc[acc]['i']
      transceivers = self.sym_acc[acc]['t']
      receivers = self.sym_acc[acc]['r']
      num_ts_used += len(transceivers.symbols)
      num_ts_avail += transceivers.limit
      per_acc.append(f"a{acc+1:<2d} {bitmap(inputs)} {bitmap(receivers)}{bitmap(transceivers)}")

    pa = self.sym_global['pa']
    pa_summary = f"{len(pa.symbols)}/{pa.limit}"
    t_summary = f"{num_ts_used}/{num_ts_avail}"
    it = self.sym_global['i.t']
    it_summary = f"{len(it.symbols)}/{it.limit}"
    num_fts_used = 0
    num_fts_avail = 0
    for ft in range(3):
      transceivers = self.sym_ft[ft]['t']
      num_fts_used += len(transceivers.symbols)
      num_fts_avail += transceivers.limit
    ft_summary = f'{num_fts_used}/{num_fts_avail}'
    ct = self.sym_global['c.t']
    ct_summary = f"{len(ct.symbols)}/{ct.limit}"
    print(f"pas {pa_summary} ts {t_summary} its {it_summary} fts {ft_summary} cts {ct_summary}")
    for row in range(10):
      print(f"{per_acc[2*row]}   {per_acc[2*row+1]}")


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
    self.uniqueid = 1  # unique id for making up names
    self.deferred = []  # lines deferred til insert-deferred
    self.enables = {}  # bools defined by enable/disable directives
    self.if_stack = []


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


  def patch_debug(self, arg):
    if arg == 'debug.quit':
      return arg, {}
    m = re.match(r'debug\.(?P<kind>(assert|bp|dump))\.(?P<name>(\d+|{[A-Za-z0-9-]+}))', arg)
    if not m:
      raise SyntaxError('bad debug syntax')

    kind, name = m.group('kind'), m.group('name')
    if not '{' in name:
      # literal debug resource number
      return arg, {}

    name = name[1:-1] # strip off curly braces
    resource = {'assert': 'da', 'bp': 'db', 'dump': 'dd'}
    n = self.symbols.lookup(resource[kind], name)
    text = f'debug.{kind}.{n+1}'
    return text, {name: text}


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


  # Translates a literal ft number or named ft into fX
  # Handles cases:
  #   f1
  #   f{f-name}
  # returns text, symbols pair
  def lookup_ft(self, ft):
    if '{f-' in ft:
      # it's a name like {f-foo}
      name = ft[1:-1] # strip braces
      n = self.symbols.lookup('f', name)
      fttext = 'f' + str(n+1)
      return fttext, {name: fttext }
    else:
      # it's a literal like 'f1'
      return ft, {}


  # Translates [prefix]{transciever}[suffix] into text, symbol
  # using prefix and suffix. Handles cases:
  #   rp{t-name}
  #   11i
  #   {t-name}i
  # returns text,symbols pair
  def lookup_ft_arg(self, fttext, arg):
    if 't-' in arg:
      m = re.match('(?P<prefix>[^{\d]*)(?P<name>{t-[A-Za-z0-9-]+})(?P<suffix>.*)', arg)

      prefix = m.group('prefix')
      suffix = m.group('suffix')
      name = m.group('name')[1:-1]    # strip braces
      ft_idx = int(fttext[1:])-1      # strip 'f', convert to 0-based

      n = self.symbols.lookup_ft(ft_idx, 't', name)
      argtext = prefix + str(1+n) + suffix
      return argtext, {name: argtext}
    else:
      # literal
      return arg, {}


  def patch_ft(self, arg):
    m = re.match('(?P<ft>(f\d|{f-[A-Za-z0-9-]+}))\.(?P<terminal>((\d\d?|{t-[A-Za-z0-9-]+})[io]|[AB]|arg))', arg)
    if not m:
      raise SyntaxError('bad ft terminal')

    fttext, symbols = self.lookup_ft(m.group('ft'))
    argtext, symbols2 = self.lookup_ft_arg(fttext, m.group('terminal'))
    symbols.update(symbols2)

    # put it all back together
    text = fttext + '.' + argtext
    return text, symbols


  def patch_init(self, arg):
    # patch selective clear transceiver
    m = re.match(r'i\.C(?P<prefix>[io])(?P<terminal>\d|{t-[A-Za-z0-9-]+})', arg)
    if not m:
      raise SyntaxError('bad init clear terminal')
    prefix = m.group('prefix')
    terminal = m.group('terminal')
    if '{' in terminal:
      terminal = terminal[1:-1]  # strip {}
      n = 1 + self.symbols.lookup('i.t', terminal)
      text = f'i.C{prefix}{n}'
      return text, {terminal: text}
    else:
      return arg, {}  # literal


  def patch_constant(self, arg):
    # patch constant transceiver
    m = re.match(r'c\.(?P<terminal>\d\d?|{t-[A-Za-z0-9-]+})(?P<suffix>[io])', arg)
    if not m:
      raise SyntaxError('bad constant terminal')
    terminal = m.group('terminal')
    suffix = m.group('suffix')
    if '{' in terminal:
      terminal = terminal[1:-1]  # strip {}
      # 1 is reserved for READ
      n = 2 + self.symbols.lookup('c.t', terminal)
      text = f'c.{n}{suffix}'
      return text, {terminal: text}
    else:
      return arg, {}  # literal


  def patch_pulseamp(self, arg):
    # only individual pulseamp channel allocation is supported
    m = re.match(r"{pa-(?P<side>[ab])-(?P<name>[A-Za-z0-9-]+)}", arg)
    if not m:
      raise SyntaxError('bad pulseamp')
    name = m.group('name')
    side = m.group('side')
    n = self.symbols.lookup('pa', name)
    box = 1 + math.floor(n / 11)
    channel = 1 + (n % 11)
    text = f'pa.{box}.s{side}.{channel}'
    return text, {name: text}


  def patch_argument(self, arg):
    patch_dispatch = {
        re.compile(r"\d\d?"):             self.arg_literal,   # digit trunk literal
        re.compile(r"{d-[A-Za-z0-9-]+}"): self.patch_d,       # named digit trunk     
        re.compile(r"\d\d?-\d\d?"):       self.arg_literal,   # program line literal
        re.compile(r"{p-[A-Za-z0-9-]+}"): self.patch_p,       # named program line
        re.compile(r"ad\..+"):            self.patch_adapter, # adapter
        re.compile(r"(a\d\d?|{a-[A-Za-z0-9-]+})\..+"): self.patch_accum,   # accumulator, more complex handling
        re.compile(r"(f\d|{f-[A-Za-z0-9-]+})\..+"): self.patch_ft,   # ft transceiver
        re.compile(r"{pa-[ab]-[A-Za-z0-9-]+}"): self.patch_pulseamp, # pulse amplifiers
        re.compile(r"debug\..+"):         self.patch_debug,   # debug resource
        re.compile(r"i\.C.+"):            self.patch_init,    # initiating unit (selective clear)
        re.compile(r"c\.(\d\d?|{t-).+"):  self.patch_constant, # constant transceivers
        re.compile(r".+"):                self.arg_literal    # etc. (all else)
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


  def line_p(self, line, **kwargs):
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

  # e.g. s {f-name}.rp{t-name} n
  def line_s_ft(self, leading_ws, arg1, arg2, comment):

    # do we need to lookup accumulator name?
    fttext = None
    m = re.match(r'(?P<ft>(f\d|{f-[A-Za-z0-9-]+}))\.(?P<prog>.+)', arg1)
    if not m:
      raise SyntaxError('bad ft switch setting')

    fttext, symbols1 = self.lookup_ft(m.group('ft'))
    progtext, symbols2 = self.lookup_ft_arg(fttext, m.group('prog'))
    symbols1.update(symbols2)
    arg1 = fttext + '.' + progtext

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


  # e.g. s debug.assert.1 {a-ex}~Mxxxxxxxxxx
  def line_s_debug(self, leading_ws, arg1, arg2, comment):
    accumtext = None
    m = re.match(r'(?P<accum>(a\d\d?|{a-[A-Za-z0-9-]+}))(?P<pattern>~.+)?', arg2)
    if not m:
      raise SyntaxError('bad debug switch setting')

    accumtext, symbols = self.lookup_accum(m.group('accum'))
    arg2 = accumtext + (m.group('pattern') or '')

    arg1, symbols2 = self.patch_debug(arg1)
    symbols.update(symbols2)

    comment = self.symbols_to_comment(symbols, {}, comment)
    return format_comment(leading_ws + ' ' + arg1 + ' ' + arg2, comment)


  # for switch settings, we can lookup accumuators and permute adapters
  def line_s(self, line, **kwargs):
    m = re.match(r'(\s*s)\s+([^\s]+)\s+([^\s]+)\s*(#.*)?', line)
    leading_ws, arg1, arg2, comment = m.groups()

    if re.match(r'a\d\d?|{a-[A-Za-z0-9-]+}',arg1):
      return self.line_s_accum(leading_ws, arg1, arg2, comment)

    if re.match(r'f\d|{f-[A-Za-z0-9-]+}',arg1):
      return self.line_s_ft(leading_ws, arg1, arg2, comment)

    if re.match(r'c\.s{t-[A-Za-z0-9-]+}',arg1):
      raise SyntaxError(f"can't set constants for auto constant t-s")

    if re.match(r'ad\.permute\.{ad-[0-9a-zA-Z-]+}',arg1):
      return self.line_s_permute(leading_ws, arg1, arg2, comment)
      
    if re.match(r'debug.(assert|dump)', arg1):
      return self.line_s_debug(leading_ws, arg1, arg2, comment)

    if re.search(r'{[a-zA-z]+-.+}', arg1+arg2):
      raise SyntaxError(f'bad switch setting {arg1+arg2}')

    return self.line_literal(line)


  # Handles symbol assignments both to constants and to other symbols 
  # {a-xyz}=a3
  # {f-awesome}=f2
  # {p-foo}={p-bar}
  def line_assign(self, line, **kwargs):
    m = re.match(r'{(?P<name>[apdf]-[A-Za-z0-9-]+)}\s*=\s*(?P<value>[^\s]+)\s*(#.*)?', line)
    if not m:
      raise SyntaxError('bad assignment left hand side')
    name = m.group('name')
    res_type = name[0]
    value = m.group('value')

    m = re.match(r'{[apdf]-[A-Za-z0-9-]+}', value)
    if m:
      is_symbol = True
      value = value[1:-1]              # strip braces
      if value[0] != res_type:
        raise SyntaxError('symbol type mismatch')
      value = self.symbols.lookup(res_type, value)
    else:
      if res_type=='d':
        if not re.match(r'\d\d?',value):
          raise SyntaxError('bad data trunk value')
        value = int(value)-1
      elif res_type=='a':
        if not re.match(r'a\d\d?',value):
          raise SyntaxError('bad accumulator value')
        value = int(value[1:])-1          # 'a1' -> 0
      elif res_type=='f':
        if not re.match(r'f\d',value):
          raise SyntaxError('bad ft value')
        value = int(value[1:])-1          # 'f1' -> 0
      else: # res_type=='p'
        if not re.match(r'\d\d?-\d\d?',value):
          raise SyntaxError('bad program line value')
        a,b = value.split('-')
        value = (int(a)-1)*11 + int(b)-1

    self.symbols.define(res_type, name, value)

    return '# ' + line  # echo the define statement, commented out


  def line_literal(self, line, **kwargs):
    return line


  def line_defmacro(self, line, **kwargs):
    m = re.match(r'\s*defmacro\s+(?P<name>[^\s]+)\s*(?P<args>[^#]*)(#.*)?', line)
    if not m:
      raise SyntaxError('bad defmacro')
    name = m.group('name')
    args = m.group('args').strip().split()
    self.defmacro = Macro(name=name, args=args, lines=[])
    return f"# (elided '{name}' macro definition)"


  def line_domacro(self, line, **kwargs):
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

    # temporary values like %foo referenced in the macro
    temps = {}
    def lookup_temp(m):
      name = m.group('name')
      if name in temps: return temps[name]
      temps[name] = f'--tmp-{self.uniqueid}'
      self.uniqueid += 1
      return temps[name]

    # simple arithmetic expressions (rpn)
    def evaluate_expr(m):
      expr = m.group('expr').split()
      s = []
      for x in expr:
        if x == '+':   s.append(s.pop() + s.pop())
        elif x == '-': s.append(s.pop() - s.pop())
        elif x == '*': s.append(s.pop() * s.pop())
        elif x == '/': s.append(s.pop() // s.pop())
        else:          s.append(int(x))
      assert len(s) == 1
      return str(s[0])

    # output macro lines with appropriate substitutions
    for line in macro.lines:
      line = re.sub(r'%(?P<name>[A-Za-z0-9-]+)', lookup_temp, line)
      for name, value in arg_values.items():
        if value == '${}': value = ''
        line = line.replace(f'${name}', value)
      line = re.sub(r'\${(?P<expr>[^}]+)}', evaluate_expr, line)
      # in case people want to say $macro {arg} instead of $macro arg
      line = line.replace('{{', '{')
      line = line.replace('}}', '}')
      outlines += self.assemble_line(line, **kwargs) + '\n'
    return outlines.strip()  # '\n' will be added by _scan


  def line_inmacro(self, line, **kwargs):
    # add lines to macro until reaching endmacro
    if re.match(r'\s*endmacro', line):
      self.macros[self.defmacro.name] = self.defmacro
      self.defmacro = None
      return
    self.defmacro.lines.append(line)


  def line_inif(self, line, **kwargs):
    if re.match(r'\s*if', line):
      return self.line_if(line, **kwargs)
    elif re.match(r'\s*endif', line):
      if not self.if_stack:
        raise SyntaxError('mismatched endif')
      self.if_stack.pop()
      return '# endif'
    elif re.match(r'\s*else', line):
      return self.line_else(line, **kwargs)
    elif all(self.if_stack):
      return self.assemble_line(line, **kwargs)


  def line_include(self, line, **kwargs):
    # include another source file. 
    # Look first in current directory, then relative to path of source file
    m = re.match(r'\s*include\s+(?P<filename>.*)(#.*)?', line)
    if not m:
      raise SyntaxError('bad include directive')

    filename = m.group('filename')
    if os.path.isfile(filename):
      text = open(filename).read()
    else:
      path = os.path.dirname(kwargs['filename'])
      filename2 = path + '/' + filename
      if os.path.isfile(filename2): 
        text = open(filename2).read()
        filename = filename2
      else:
        raise Exception(f'Could not find include file {filename} or {filename2}')

    outlines = self._scan(filename, text)
    return f'# begin {filename}\n{outlines}\n# end {filename}\n'


  def line_defer(self, line, **kwargs):
    # defer a line til insert-deferred (used for reserving dummies)
    m = re.match(r'\s*defer\s+(?P<text>\S.*)', line)
    if not m:
      raise SyntaxError('bad defer directive')
    text = m.group('text')
    self.deferred.append((text, kwargs))
    return ''


  def line_insert_deferred(self, line, **kwargs):
    # insert deferred lines (used for reserving dummies)
    out = ''
    for line, context in self.deferred:
      try:
        outlines = self.assemble_line(line)
      except Exception as e:
        print(f'(deferred from {context["filename"]}:{context["line_number"]+1})')
        raise
      if outlines != None:
        out += outlines + '\n'
    return out


  def line_allocate_dummy(self, line, **kwargs):
    # allocate an accumulator transceiver to a dummy program
    # allocate-dummy foo -{a1},{a2},{a3} -{a4} -{a5},{a6}
    m = re.match(r'\s*allocate-dummy\s+(?P<name>[A-Za-z0-9-]+)\s+(?P<args>[^#]*)(#.*)?', line)
    if not m:
      raise SyntaxError('bad allocate-dummy directive')
    name = m.group('name')

    allowed_accums = set('a' + str(n+1) for n in range(20))
    excluded_accums = set()
    args = m.group('args').strip().split()
    for spec in args:
      if not spec.startswith('-'):
        raise SyntaxError(f"allocate-dummy: expecting -accum found `{spec}'")
      exclusions = spec[1:].split(',')
      for exclusion in exclusions:
        m = re.match(r'(?P<accum>(a\d\d?|{a-[A-Za-z0-9-]+}))', exclusion)
        if not m:
          raise SyntaxError(f"allocate-dummy: expecting accum found `{exclusion}'")
        accum = m.group('accum')
        accumtext, _ = self.lookup_accum(m.group('accum'))
        allowed_accums.discard(accumtext)
        excluded_accums.add(accumtext)

    transceiver = -1
    # try accums in a deterministic order so dummies are somewhat consistent
    for accum in reversed(sorted(allowed_accums, key=lambda name: int(name[1:]))):
      try:
        transceiver, _ = self.lookup_accum_arg(accum, f'{{t-{name}}}')
        accum_index = int(accum[1:])-1  # 'a1' -> 0
        self.symbols.define('a', f'a-{name}', accum_index)
        break
      except OutOfResources:
        continue
    if transceiver == -1:
      raise OutOfResources(f'dummy transceivers exhausted for {allowed_accums}')

    return f'# dummy {name} = {accum}.{transceiver}i (excluded {excluded_accums})'


  def line_allocate_ft_dummy(self, line, **kwargs):
    # allocate an ft transceiver to a dummy program
    # allocate-ft-dummy foo -{f1},{f2}
    m = re.match(r'\s*allocate-ft-dummy\s+(?P<name>[A-Za-z0-9-]+)\s+(?P<args>[^#]*)(#.*)?', line)
    if not m:
      raise SyntaxError('bad allocate-ft-dummy directive')
    name = m.group('name')

    allowed_fts = set('f' + str(n+1) for n in range(3))
    excluded_fts = set()
    args = m.group('args').strip().split()
    for spec in args:
      if not spec.startswith('-'):
        raise SyntaxError(f"allocate-ft-dummy: expecting -ft found `{spec}'")
      exclusions = spec[1:].split(',')
      for exclusion in exclusions:
        m = re.match(r'(?P<ft>(f\d|{f-[A-Za-z0-9-]+}))', exclusion)
        if not m:
          raise SyntaxError(f"allocate-ft-dummy: expecting ft found `{exclusion}'")
        ft = m.group('ft')
        fttext, _ = self.lookup_ft(m.group('ft'))
        allowed_fts.discard(fttext)
        excluded_fts.add(fttext)

    transceiver = -1
    # try fts in a deterministic order so dummies are somewhat consistent
    for ft in reversed(sorted(allowed_fts, key=lambda name: int(name[1:]))):
      try:
        transceiver, _ = self.lookup_ft_arg(ft, f'{{t-{name}}}')
        ft_index = int(ft[1:])-1  # 'f1' -> 0
        self.symbols.define('f', f'f-{name}', ft_index)
        break
      except OutOfResources:
        continue
    if transceiver == -1:
      raise OutOfResources(f'dummy transceivers exhausted for {allowed_fts}')

    return f'# ft-dummy {name} = {ft}.{transceiver}i (excluded {excluded_fts})'


  def line_enable_disable(self, line, **kwargs):
    m = re.match(r'\s*(?P<cmd>enable|disable)\s+(?P<what>\S+)(?P<comment>\s*#.*)?', line)
    if not m:
      raise SyntaxError('bad enable/disable directive')
    cmd = m.group('cmd')
    what = m.group('what')
    comment = m.group('comment')
    self.enables[what] = (cmd == 'enable')
    return f"# {cmd} {what} {comment}"


  def line_if(self, line, **kwargs):
    m = re.match(r'\s*if\s+(?P<what>\S+)(#.*)?', line)
    if not m:
      raise SyntaxError('bad if directive')
    what = m.group('what')
    if not what in self.enables:
      raise SyntaxError(f'unrecognized if condition {what}')
    self.if_stack.append(self.enables[what])
    state = 'enabled' if all(self.if_stack) else 'disabled'
    return f"# if {what}  ({what} is {state})"


  def line_else(self, line, **kwargs):
    m = re.match(r'\s*else', line)
    if not m:
      raise SyntaxError('bad else directive')
    if not self.if_stack:
      raise SyntaxError('else not in if')
    self.if_stack[-1] = not self.if_stack[-1]
    state = 'enabled' if all(self.if_stack) else 'disabled'
    return f"# else  ({state})"


  def assemble_line(self, line, **kwargs):
    # The types of lines we understand
    line_dispatch = {
      re.compile(r'\s*p\s+([^\s]+)\s+([^\s]+)\s*(#.*)?'): self.line_p,
      re.compile(r'\s*s\s+([^\s]+)\s+([^\s]+)\s*(#.*)?'): self.line_s,
      re.compile(r'\s*{[apdf]-[A-Za-z0-9-]+}\s*=.+'):     self.line_assign,
      re.compile(r'\s*defmacro.*'):                       self.line_defmacro,
      re.compile(r'\s*\$([^\s]+).*'):                     self.line_domacro,
      re.compile(r'\s*include.*'):                        self.line_include,
      re.compile(r'\s*defer.*'):                          self.line_defer,
      re.compile(r'\s*insert-deferred.*'):                self.line_insert_deferred,
      re.compile(r'\s*allocate-dummy.*'):                 self.line_allocate_dummy,
      re.compile(r'\s*allocate-ft-dummy.*'):              self.line_allocate_ft_dummy,
      re.compile(r'\s*(enable|disable).*'):               self.line_enable_disable,
      re.compile(r'\s*if.*'):                             self.line_if,
      re.compile(r'\s*else.*'):                           self.line_else,
      re.compile(r'.*'):                                  self.line_literal
    }

    for pattern, handler in line_dispatch.items():
      if pattern.match(line):
        return handler(line, **kwargs)
        break


  def _scan(self, filename, text):
    out = ''
    for line_number, line in enumerate(text.splitlines()):
      try:
        if self.defmacro:
          outlines = self.line_inmacro(line)
        elif self.if_stack:
          outlines = self.line_inif(line, filename=filename, line_number=line_number)
        else:
          outlines = self.assemble_line(line, filename=filename, line_number=line_number)
      except Exception as e:
        print(line)
        print(f'{filename}:{line_number+1}: {str(e)}')
        return None
      if outlines != None:
        out += outlines + '\n'
    if self.defmacro:
      print(f'unterminated macro {self.defmacro.name}')
      return None
    if self.if_stack:
      print(f'unterminated if')
      return None
    return out


  def assemble(self, filename, intext):
    return self._scan(filename, intext)

  def summarize_resource_usage(self):
    self.symbols.summarize_resource_usage()


def main():
  if len(sys.argv) < 3:
    usage()
    sys.exit(1)

  filename = sys.argv[1]
  intext = open(filename).read()

  a = Assembler()
  outtext = a.assemble(filename, intext)

  if outtext:
    open(sys.argv[2], 'w+').write(outtext)
    a.summarize_resource_usage()

if __name__ == "__main__":
  main()


