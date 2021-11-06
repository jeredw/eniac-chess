import { html, Component } from './preact.mjs'

const registerNames = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'PC', 'RR', 'IR'];

export class Registers extends Component {
  render({ regs }) {
    return html`
      <h3>Registers</h3>
      <table class="regs table-dump">
        <${RegistersHeader} />
        <${RegistersData} regs=${regs} />
      </table>
    `;
  }
}

function RegistersHeader() {
  return html`
    <tr>
      ${registerNames.map(name => html`<th>${name}</th>`)}
    </tr>
  `;
}

function RegistersData({ regs }) {
  const values = registerNames.map(name => regs[name]);
  return html`
    <tr>
      ${values.map(value => html`<td>${value}</td>`)}
    </tr>
  `;
}

export function extractRegs(acc) {
  const rf = 12; // a13 is RF
  const ls = 3;  // a4 is LS
  const pc = 0;  // a1 is PC
  const ir = 1;  // a2 is IR
  return {
    A: getWord(acc, rf, 0),
    B: getWord(acc, rf, 1),
    C: getWord(acc, rf, 2),
    D: getWord(acc, rf, 3),
    E: getWord(acc, rf, 4),
    F: getWord(acc, ls, 0),
    G: getWord(acc, ls, 1),
    H: getWord(acc, ls, 2),
    I: getWord(acc, ls, 3),
    J: getWord(acc, ls, 4),
    PC: getField(acc, pc, 3, 0),
    RR: getField(acc, pc, 7, 4),
    IR: getField(acc, ir, 9, 0),
  };
}

function getField(acc, a, start, downTo) {
  const result = [];
  for (let d = start; d >= downTo; d--) {
    result.push('' + acc[a].decade[d]);
  }
  return result.join('');
}

function getWord(acc, a, n) {
  const d = 9 - 2*n;
  return getField(acc, a, d, d-1);
}
