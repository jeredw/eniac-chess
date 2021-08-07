import { html, Component, render } from './preact.mjs'
import { MemoryDump, extractLinearMemory } from './memory.mjs'
import { Connect4Board, Connect4Stack } from './c4.mjs'

class App extends Component {
  constructor() {
    super()
    this.state = { memory: [] };
    this.eventSource = null;
  }

  componentDidMount() {
    this.eventSource = new EventSource('/events');
    this.eventSource.addEventListener('message', (e) => {
      const simState = JSON.parse(e.data);
      this.setState({
        memory: extractLinearMemory(simState.acc),
      });
    });
  }

  componentWillUnmount() {
    this.eventSource = null;
  }

  render() {
    return html`
      <${MemoryDump} memory=${this.state.memory} />
      <${Connect4Board} memory=${this.state.memory} />
      <${Connect4Stack} memory=${this.state.memory} />
    `
  }
}

render(html`<${App}/>`, document.body);
