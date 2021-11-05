import { html, Component } from './preact.mjs'

export class ChessBoard extends Component {
  render({ chessBoard }) {
    return html`
      <div class="chess-board">
        <${ChessBoardRows} chessBoard=${chessBoard} />
      </div>
    `;
  }
}

export function extractChessBoardState(memory) {
  const others = {
    'whiteKing': decodePosition(memory[32]),
    'blackKing': decodePosition(memory[33]),
    'whiteRook1': decodePosition(memory[34]),
    'whiteRook2': decodePosition(memory[45]),
  };
  const board = [];
  for (let y = 0; y < 8; y++) {
    const rank = [];
    for (let x = 0; x < 8; x++) {
      const address = Math.floor((y * 8 + x) / 2);
      const digits = memory[address];
      const square = digits ? ((x % 2) == 0 ? digits[0] : digits[1]) : '';
      rank.push(decodePiece(square, y, x, others));
    }
    board.push(rank);
  }
  return board;
}

function ChessBoardRows({ chessBoard }) {
  if (chessBoard.length == 0) {
    return '';
  }
  const rows = [];
  for (let y = 7; y >= 0; y--) {
    const cols = [];
    for (let x = 0; x < 8; x++) {
      const piece = chessBoard[y][x];
      const squareColor = (x % 2) != (y % 2) ? 'chess-square-white' : 'chess-square-black';
      cols.push(html`<div class="chess-square ${squareColor}">${piece}</div>`);
    }
    const rank = y + 1;
    cols.push(html`<div class="chess-row-label">${rank}</div>`);
    rows.push(html`<div class="chess-row">${cols}</div>`);
  }
  const fileLabels = [];
  for (let x = 0; x < 8; x++) {
    const file = "abcdefgh"[x];
    fileLabels.push(html`<div class="chess-file-label">${file}</div>`);
  }
  rows.push(html`<div class="chess-row">${fileLabels}</div>`);
  return rows;
}

function decodePosition(pos) {
  const illegal = pos[0] == '9' || pos[1] == '9' || pos[0] == '0' || pos[1] == '0';
  if (illegal) {
    return [undefined, undefined];
  }
  return [+pos[0] - 1, +pos[1] - 1];
}

function decodePiece(square, squareY, squareX, others) {
  switch (square) {
    case '0':  // empty
      return '';
    case '1':  // other
      for (const [piece, [pieceY, pieceX]] of Object.entries(others)) {
        if (squareY == pieceY && squareX == pieceX) {
          switch (piece) {
            case 'whiteKing':
              return '♔';
            case 'blackKing':
              return '♚';
            case 'whiteRook1':
            case 'whiteRook2':
              return '♖';
          }
        }
      }
      // black rook by default
      return '♜';
    case '2':  // white pawn
      return '♙';
    case '3':  // white knight
      return '♘';
    case '4':  // white bishop
      return '♗';
    case '5':  // white queen
      return '♕';
    case '6':  // black pawn
      return '♟';
    case '7':  // black knight
      return '♞';
    case '8':  // black bishop
      return '♝';
    case '9':  // black queen
      return '♛';
  }
  return '?';
}

export class ChessStack extends Component {
  render({ memory }) {
    const depth = parseInt(memory[65], 10);
    return html`
      <table class="chess-stack table-dump">
        <${ChessStackHeader} />
        <${ChessStackEntry} isTop=1 active=${depth >= 1} data=${memory.slice(36, 45)} />
        <${ChessStackEntry} isTop=0 active=${depth >= 2} data=${memory.slice(46, 55)} />
        <${ChessStackEntry} isTop=0 active=${depth >= 3} data=${memory.slice(56, 65)} />
        <${ChessStackEntry} isTop=0 active=${depth >= 4} data=${memory.slice(66, 75)} />
      </table>
    `;
  }
}

function ChessStackHeader() {
  return html`
    <tr>
      <th></th>
      <th>target</th>
      <th>from</th>
      <th>to</th>
      <th>movestate</th>
      <th>bestfrom</th>
      <th>bestto</th>
      <th>bestscore</th>
      <th>α</th>
      <th>β</th>
    </tr>
  `;
}

function ChessStackEntry({ isTop, active, data }) {
  return html`
    <tr class=${active ? "active" : "inactive"}>
      <td>${+isTop ? ">" : " "}</td>
      ${data.map(item => html`<td>${item}</td>`)}
    </tr>
  `;
}
