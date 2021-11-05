import { html, Component, render } from './preact.mjs'
import { Registers, extractRegs } from './regs.mjs'
import { MemoryDump, extractLinearMemory } from './memory.mjs'
import { Connect4Board, Connect4Stack } from './c4.mjs'
import { LifeGrid } from './life.mjs'
import { ChessBoard, ChessStack, extractChessBoardState } from './chess.mjs'

class App extends Component {
  constructor() {
    super()
    this.state = { memory: [], regs: {}, chessBoard: [] };
    this.eventSource = null;
  }

  componentDidMount() {
    this.eventSource = new EventSource('/events');
    this.eventSource.addEventListener('message', (e) => {
      const simState = JSON.parse(e.data);
      const memory = extractLinearMemory(simState.acc);
      this.setState({
        memory: memory,
        regs: extractRegs(simState.acc),
        chessBoard: extractChessBoardState(memory),
      });
    });
  }

  componentWillUnmount() {
    this.eventSource = null;
  }

  render() {
    return html`
      <${ChessBoard} chessBoard=${this.state.chessBoard} />
      <div class="memory">
        <${Registers} regs=${this.state.regs} />
        <${ChessStack} memory=${this.state.memory} />
        <${MemoryDump} memory=${this.state.memory} />
      </div>
    `;
    //<${Connect4Board} memory=${this.state.memory} />
    //<${Connect4Stack} memory=${this.state.memory} />
    //<${LifeGrid} generation=${this.state.regs.E} memory=${this.state.memory} />
  }
}

render(html`<${App}/>`, document.body);
