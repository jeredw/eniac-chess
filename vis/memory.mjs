import { html, Component } from './preact.mjs'

export class MemoryDump extends Component {
  render({ memory }) {
    return html`
      <table class="table-dump memory-dump">
        <${MemoryDumpHeader} />
        <${MemoryDumpRows} memory=${memory} />
      </table>
    `;
  }
}

function MemoryDumpHeader() {
  const columns = [''];
  for (let i = 0; i < 10; i++) {
    columns.push(`x${i}`);
  }
  return html`<tr>${columns.map(label => html`<th>${label}</th>`)}</tr>`;
}

function MemoryDumpRows({ memory }) {
  const rows = [];
  for (let i = 0; i <= 7; i++) {
    const values = [];
    for (let j = 0; j < 10; j++) {
      values.push(memory[10 * i + j] || '--');
    }
    rows.push(html`
      <tr>
        <td>${i}x</td>
        ${values.map(value => html`<td>${value}</td>`)}
      </tr>
    `)
  }
  return rows;
}

function wordIterator(acc) {
  let a = 4; // a5 is the first memory accumulator
  let d = 9; // decades 9,8 have word 0
  return () => {
    if (a >= acc.length) {
      return '00';
    }
    const word = ('' + acc[a].decade[d]) + ('' + acc[a].decade[d-1]);
    d -= 2;
    if (d <= 0) {
      d = 9;
      a++;
      if (a == 12) { // skip a13 which is RF
        a++;
      }
    }
    return word;
  };
}

export function extractLinearMemory(acc) {
  const nextWord = wordIterator(acc);
  const memory = [];
  for (let i = 0; i < 75; i++) {
    memory.push(nextWord());
  }
  return memory;
}
