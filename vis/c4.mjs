import { html, Component } from './preact.mjs'

export class Connect4Board extends Component {
  render({ memory }) {
    return html`
      <div class="c4-board">
        <${Connect4Rows} memory=${memory} />
      </div>
      <div class="c4-meta">
        Winner: ${memory[42]}
      </div>
    `;
  }
}

function Connect4Rows({ memory }) {
  const rows = [];
  for (let y = 0; y < 6; y++) {
    const cols = [];
    for (let x = 0; x < 7; x++) {
      const address = y * 7 + x;
      const piece = memory[address];
      switch (piece) {
        case '00':
          cols.push(html`<div class="c4-square c4-empty"></div>`);
          break;
        case '01':
          cols.push(html`<div class="c4-square c4-red"></div>`);
          break;
        case '02':
          cols.push(html`<div class="c4-square c4-yellow"></div>`);
          break;
        default:
          break;
      }
    }
    rows.push(html`
      <div class="c4-row">
        ${cols}
      </div>
    `);
  }
  return rows;
}

export class Connect4Stack extends Component {
  render({ memory }) {
    const sp = parseInt(memory[44], 10);
    return html`
      <table>
        <${Connect4StackHeader} />
        <${Connect4StackEntry} isTop=${sp == 9}  data=${memory.slice(45, 50)} />
        <${Connect4StackEntry} isTop=${sp == 10} data=${memory.slice(50, 55)} />
        <${Connect4StackEntry} isTop=${sp == 11} data=${memory.slice(55, 60)} />
        <${Connect4StackEntry} isTop=${sp == 12} data=${memory.slice(60, 65)} />
        <${Connect4StackEntry} isTop=${sp == 13} data=${memory.slice(65, 70)} />
        <${Connect4StackEntry} isTop=${sp == 14} data=${memory.slice(70, 75)} />
      </table>
    `;
  }
}

function Connect4StackHeader() {
  return html`
    <tr>
      <th></th>
      <th>player<br />best_move</th>
      <th>last_move</th>
      <th>best_score</th>
      <th>α</th>
      <th>β</th>
    </tr>
  `;
}

function Connect4StackEntry({ isTop, data }) {
  return html`
    <tr>
      <td>${isTop ? ">" : " "}</td>
      ${data.map(item => html`<td>${item}</td>`)}
    </tr>
  `;
}
