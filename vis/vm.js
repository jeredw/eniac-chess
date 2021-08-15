import { html, Component, render } from './preact.mjs'
import { Registers, extractRegs } from './regs.mjs'
import { MemoryDump, extractLinearMemory } from './memory.mjs'
import { Connect4Board, Connect4Stack } from './c4.mjs'
import { LifeGrid } from './life.mjs'

class App extends Component {
  constructor() {
    super()
    this.state = { memory: [], regs: {} };
    this.eventSource = null;
  }

  componentDidMount() {
    this.eventSource = new EventSource('/events');
    this.eventSource.addEventListener('message', (e) => {
      const simState = JSON.parse(e.data);
      this.setState({
        memory: extractLinearMemory(simState.acc),
        regs: extractRegs(simState.acc),
      });
    });
  }

  componentWillUnmount() {
    this.eventSource = null;
  }

  render() {
    return html`
      <${MemoryDump} memory=${this.state.memory} />
      <${Registers} regs=${this.state.regs} />
      <${Connect4Board} memory=${this.state.memory} />
      <${Connect4Stack} memory=${this.state.memory} />
      <${LifeGrid} generation=${this.state.regs.E} memory=${this.state.memory} />
    `
  }
}

render(html`<${App}/>`, document.body);
