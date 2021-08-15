import { html, Component } from './preact.mjs'

export class LifeGrid extends Component {
  render({ memory }) {
    return html`
      <div class="life-grid">
        <${LifeRows} memory=${memory} />
      </div>
    `;
  }
}

function LifeRows({ memory }) {
  const rows = [];
  for (let y = 0; y < 8; y++) {
    const cols = [];
    for (let x = 0; x < 8; x++) {
      const address = Math.floor((y * 8 + x) / 2);
      const state = memory[address];
      const cur = state ? (x%2 == 0 ? state[0] : state[1]) : '';
      switch (cur) {
        case '0':
          cols.push(html`<div class="life-square life-dead"></div>`);
          break;
        case '1':
          cols.push(html`<div class="life-square life-alive"></div>`);
          break;
        default:
          cols.push(html`<div class="life-square life-undef"></div>`);
          break;
      }
    }
    rows.push(html`
      <div class="life-row">
        ${cols}
      </div>
    `);
  }
  return rows;
}
