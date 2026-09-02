export type PlayerId = 'p1' | 'p2';
export type Visibility = 'face_down' | 'revealed' | 'opened';
export type CardKind = 'magic' | 'figure' | 'bomb' | 'frog' | 'empty' | 'unknown';
export type BoardKind = Exclude<CardKind, 'unknown'>;
export type BoardDistribution = Record<BoardKind, number>;
export type HandCard = { index: number; id: number; name: string; description: string; effect_type: string; effect_data: Record<string, string | number>; cursed: boolean };
export type Figure = { id: number; name: string; description: string; used: boolean };
export type Player = { id: PlayerId; name: string; hp: number; max_hp: number; figure: Figure; hand: HandCard[] };
export type BoardCell = { index: number; visibility: Visibility; barrier: boolean; kind: CardKind | null; id: number | null; name: string; description: string; effect_type?: string };
export type GameState = {
  phase: 'setup' | 'step_start' | 'action' | 'turn_end' | 'game_over';
  turn: number;
  step: number;
  step_order: PlayerId[];
  current_player_id: PlayerId | null;
  forced_hand_index: number | null;
  result: string | null;
  step_start: { foreteller_count: number; barrier_player_ids: PlayerId[] };
  players: Player[];
  board_distribution: { current: BoardDistribution; next: BoardDistribution };
  board: BoardCell[];
  selectable_indices: number[];
  log: string[];
};

type EffectData = Record<string, string | number>;
type MagicDefinition = { id: number; name: string; description: string; effectType: string; data: EffectData };
type FigureDefinition = { id: number; name: string; description: string; pattern?: string[]; drawable?: boolean };
type InternalHandCard = { id: number; cursed: boolean };
type InternalPlayer = {
  id: PlayerId;
  name: string;
  hp: number;
  maxHp: number;
  hand: InternalHandCard[];
  figureId: number;
  figureLockTurns: number;
  usedFigureAbilities: Set<number>;
  stepsTakenThisTurn: number;
};
type InternalCell = { kind: BoardKind; index: number; id: number | null; visibility: Visibility; barrier: boolean; temporaryReveal: boolean };
type ActionBody = Record<string, unknown>;

const BOARD_SIZE = 25;
const HAND_LIMIT = 3;
const CARD_TYPES: BoardKind[] = ['bomb', 'frog', 'empty', 'magic', 'figure'];
const DEFAULT_DISTRIBUTION: BoardDistribution = { bomb: 5, frog: 5, empty: 8, magic: 5, figure: 2 };

function magic(id: number, name: string, description: string, effectType: string, data: EffectData = {}): MagicDefinition {
  return { id, name, description, effectType, data };
}

export const MAGIC_CARDS: Record<number, MagicDefinition> = {
  1: magic(1, 'bubble tea', 'Self: +1 HP', 'heal', { user: 1 }),
  2: magic(2, 'sanshoku dango', 'Self: +3 HP', 'heal', { user: 3 }),
  3: magic(3, 'wine', 'Opponent: +1 HP; self: +2 HP', 'heal_dual', { user: 2, opponent: 1 }),
  4: magic(4, 'beep', 'Next turn: Bomb +1, Empty -1', 'board_delta', { bomb: 1, empty: -1 }),
  5: magic(5, 'beep boom', 'Next turn: Bomb +2, Empty -2', 'board_delta', { bomb: 2, empty: -2 }),
  6: magic(6, "let's be nice", 'Next turn: Bomb -1, Empty +1', 'board_delta', { bomb: -1, empty: 1 }),
  7: magic(7, 'peace!', 'Next turn: Bomb -2, Empty +2', 'board_delta', { bomb: -2, empty: 2 }),
  8: magic(8, 'one more please', 'Next turn: Magic +1, Empty -1', 'board_delta', { magic: 1, empty: -1 }),
  9: magic(9, 'becoming tricky!', 'Next turn: Magic +2, Empty -2', 'board_delta', { magic: 2, empty: -2 }),
  10: magic(10, '"CARD"iovascular', 'Next turn: Magic -2, Empty +2; self: +2 HP', 'heal_and_board_delta', { user: 2, magic: -2, empty: 2 }),
  11: magic(11, 'Ribbit! Ribbit! Ribbit!', 'Next turn: Frog +3, Empty -3', 'board_delta', { frog: 3, empty: -3 }),
  12: magic(12, 'THE NUKE', 'Next turn: all Empty become Bomb', 'convert_all', { source: 'empty', target: 'bomb' }),
  13: magic(13, "IT'S RAINING FROGS AND FROGS", 'Next turn: all Empty become Frog', 'convert_all', { source: 'empty', target: 'frog' }),
  14: magic(14, 'WHO ARE YOU?', 'Next turn: all Empty become Figure', 'convert_all', { source: 'empty', target: 'figure' }),
  15: magic(15, "THAT'S FUN!", 'Next turn: all Empty become Magic', 'convert_all', { source: 'empty', target: 'magic' }),
  16: magic(16, 'Shuffle!', 'Shuffle the same 25 cards', 'shuffle'),
  17: magic(17, 'Take a look!', 'Choose 1 row or column; Reveal every face-down card in that line', 'reveal_line'),
  18: magic(18, 'Take 3 looks!', 'Reveal 3 chosen cards', 'reveal', { count: 3 }),
  19: magic(19, 'the birth of BOB', "Change either player's figure to Bob", 'change_figure', { figure_id: 200 }),
  20: magic(20, 'const figure', 'Prevent figure changes for 3 turns', 'protect_figure', { turns: 3 }),
  21: magic(21, 'shredder', 'Requires another card in both hands; user chooses both discards', 'discard'),
  22: magic(22, 'REVEAL!', 'Reveal all Magic Cards this turn', 'reveal_all_magic'),
  23: magic(23, 'This is curse!', 'Force one chosen opponent card on their next step', 'curse'),
  24: magic(24, 'Frog bomb', 'Next turn: change 1 Frog to Bomb', 'convert_one', { source: 'frog', target: 'bomb' }),
  25: magic(25, 'Swap', 'Swap hands with opponent', 'swap_hand'),
};

export const FIGURE_CARDS: Record<number, FigureDefinition> = {
  200: { id: 200, name: 'bob', description: 'No special ability' },
  201: { id: 201, name: 'pawn', description: '10% chance each turn to evolve' },
  202: { id: 202, name: 'queen', description: 'Open own W: self +1 HP and opponent -1 HP once per turn', pattern: ['WOWOW', 'OWWWO', 'WWQWW', 'OWWWO', 'WOWOW'], drawable: false },
  203: { id: 203, name: 'bishop', description: 'Open own W: self +0.5 HP and opponent -0.5 HP once per turn', pattern: ['WOOOW', 'OWOWO', 'OOBOO', 'OWOWO', 'WOOOW'], drawable: false },
  204: { id: 204, name: 'knight', description: 'Open own W: self +0.5 HP and opponent -0.5 HP once per turn', pattern: ['OWOWO', 'WOOOW', 'OOKOO', 'WOOOW', 'OWOWO'], drawable: false },
  205: { id: 205, name: 'rook', description: 'Open own W: self +0.5 HP and opponent -0.5 HP once per turn', pattern: ['OOWOO', 'OOWOO', 'WWRWW', 'OOWOO', 'OOWOO'], drawable: false },
  206: { id: 206, name: 'foreteller', description: 'Reveal 3 cards at the start of your first step' },
  207: { id: 207, name: 'princess', description: 'Open Frog: +1 HP once per turn' },
  208: { id: 208, name: 'witch', description: 'Opponent loses 1 HP at turn start' },
  209: { id: 209, name: 'tic-tac-toeR', description: 'May place an X barrier before each step' },
  211: { id: 211, name: 'alcoholic', description: 'Must open a random selectable card' },
  212: { id: 212, name: 'copy cat', description: "Copy opponent's current figure once" },
  213: { id: 213, name: 'abusive lover', description: 'HP changes affect both players equally' },
  214: { id: 214, name: 'gambler', description: 'Bomb: self -2 HP; Frog: opponent -1 HP' },
  215: { id: 215, name: 'psychopath', description: 'Bomb damage becomes 3 HP' },
  216: { id: 216, name: 'magician', description: 'May shuffle once per turn' },
  217: { id: 217, name: 'lucky bob', description: '30% chance to avoid damage' },
  218: { id: 218, name: 'unlucky bob', description: '30% chance to double damage' },
  219: { id: 219, name: 'Politician', description: 'Invert revealed states at turn start' },
};

const DRAWABLE_FIGURE_IDS = Object.values(FIGURE_CARDS).filter(card => card.drawable !== false).map(card => card.id);

export class GameActionError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(message: string, code = 'invalid_action', details: Record<string, unknown> = {}) {
    super(message);
    this.name = 'GameActionError';
    this.code = code;
    this.details = details;
  }
}

function numberArray(value: unknown): number[] {
  return Array.isArray(value) ? value.filter((item): item is number => Number.isInteger(item)) : [];
}

function seededRandom(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value += 0x6d2b79f5;
    let result = value;
    result = Math.imul(result ^ (result >>> 15), result | 1);
    result ^= result + Math.imul(result ^ (result >>> 7), result | 61);
    return ((result ^ (result >>> 14)) >>> 0) / 4294967296;
  };
}

export class BrowserGameSession {
  private players: Record<PlayerId, InternalPlayer>;
  private board: InternalCell[] = [];
  private turn = 0;
  private step = 0;
  private stepOrder: PlayerId[] = [];
  private pendingBoardEffects: number[] = [];
  private phase: GameState['phase'] = 'setup';
  private stepStart: GameState['step_start'] = { foreteller_count: 0, barrier_player_ids: [] };
  private log: string[] = [];
  private random: () => number = Math.random;

  constructor() {
    this.players = { p1: this.createPlayer('p1', 'Player 1'), p2: this.createPlayer('p2', 'Player 2') };
    this.newGame();
  }

  dispatch(path: string, body: ActionBody = {}): GameState {
    if (path === '/state') return this.state();
    if (path === '/new-game') return this.newGame(String(body.p1_name || 'Player 1'), String(body.p2_name || 'Player 2'), typeof body.seed === 'number' ? body.seed : undefined);
    if (path === '/begin-step') return this.beginStep(numberArray(body.foreteller_indices), (body.barrier_indices ?? {}) as Record<string, number>);
    if (path === '/open') return this.openCard(body.index as number, numberArray(body.discard_indices));
    if (path === '/play-magic') return this.playMagic(body.hand_index as number, (body.choices ?? {}) as ActionBody);
    if (path === '/activate-figure') return this.activateFigure();
    if (path === '/continue-turn') return this.continueTurn();
    throw new GameActionError('unknown game action', 'not_found');
  }

  private createPlayer(id: PlayerId, name: string): InternalPlayer {
    return { id, name, hp: 5, maxHp: 5, hand: [], figureId: 200, figureLockTurns: 0, usedFigureAbilities: new Set(), stepsTakenThisTurn: 0 };
  }

  private newGame(p1Name = 'Player 1', p2Name = 'Player 2', seed?: number): GameState {
    this.random = seed === undefined ? Math.random : seededRandom(seed);
    this.players = { p1: this.createPlayer('p1', p1Name || 'Player 1'), p2: this.createPlayer('p2', p2Name || 'Player 2') };
    this.turn = 0;
    this.step = 0;
    this.stepOrder = [];
    this.pendingBoardEffects = [];
    this.board = this.buildBoard(DEFAULT_DISTRIBUTION);
    this.log = ['A new game begins.'];
    this.record(this.startTurn());
    this.prepareCurrentStep();
    return this.state();
  }

  private shuffle<T>(items: T[]): T[] {
    for (let index = items.length - 1; index > 0; index -= 1) {
      const target = Math.floor(this.random() * (index + 1));
      [items[index], items[target]] = [items[target], items[index]];
    }
    return items;
  }

  private choice<T>(items: T[]): T {
    return items[Math.floor(this.random() * items.length)];
  }

  private buildBoard(distribution: BoardDistribution): InternalCell[] {
    this.validateDistribution(distribution);
    const kinds = CARD_TYPES.flatMap(kind => Array.from({ length: distribution[kind] }, () => kind));
    this.shuffle(kinds);
    return kinds.map((kind, index) => ({ kind, index, id: kind === 'magic' ? this.choice(Object.keys(MAGIC_CARDS).map(Number)) : kind === 'figure' ? this.choice(DRAWABLE_FIGURE_IDS) : null, visibility: 'face_down', barrier: false, temporaryReveal: false }));
  }

  private validateDistribution(distribution: BoardDistribution): void {
    if (CARD_TYPES.some(kind => !Number.isInteger(distribution[kind]) || distribution[kind] < 0) || CARD_TYPES.reduce((sum, kind) => sum + distribution[kind], 0) !== BOARD_SIZE) {
      throw new GameActionError(`distribution must contain exactly ${BOARD_SIZE} cards`);
    }
  }

  private currentPlayerId(): PlayerId | null {
    return this.gameResult() !== null || this.step >= this.stepOrder.length ? null : this.stepOrder[this.step];
  }

  private currentPlayer(): InternalPlayer {
    const id = this.currentPlayerId();
    if (!id) throw new GameActionError('the game is not waiting for a main action');
    return this.players[id];
  }

  private other(player: InternalPlayer): InternalPlayer {
    return this.players[player.id === 'p1' ? 'p2' : 'p1'];
  }

  private record(messages: string[]): void {
    this.log.push(...messages);
    this.log = this.log.slice(-40);
  }

  private startTurn(): string[] {
    this.clearTemporaryReveals();
    this.board.forEach(cell => { cell.barrier = false; });
    if (this.turn > 0) {
      this.board = this.buildBoard(this.resolveNextDistribution());
      this.pendingBoardEffects = [];
    }
    this.turn += 1;
    this.step = 0;
    Object.values(this.players).forEach(player => {
      player.usedFigureAbilities.clear();
      player.stepsTakenThisTurn = 0;
      if (player.figureLockTurns > 0) player.figureLockTurns -= 1;
    });
    const messages = this.resolveTurnStartFigures();
    this.stepOrder = this.gameResult() === null ? this.shuffle(['p1', 'p1', 'p1', 'p2', 'p2', 'p2'] as PlayerId[]) : [];
    return messages;
  }

  private prepareCurrentStep(): void {
    if (this.gameResult() !== null) {
      this.phase = 'game_over';
      this.stepStart = { foreteller_count: 0, barrier_player_ids: [] };
      return;
    }
    const player = this.currentPlayer();
    const faceDown = this.board.filter(cell => cell.visibility === 'face_down').length;
    const foretellerCount = player.stepsTakenThisTurn === 0 && player.figureId === 206 ? Math.min(3, faceDown) : 0;
    const barrierPlayerIds = [player, this.other(player)].filter(owner => owner.figureId === 209).map(owner => owner.id);
    this.stepStart = { foreteller_count: foretellerCount, barrier_player_ids: barrierPlayerIds };
    if (foretellerCount || barrierPlayerIds.length) {
      this.phase = 'step_start';
      return;
    }
    this.phase = 'action';
    this.resolveImpossibleCurse();
  }

  private beginStep(foretellerIndices: number[], barrierIndices: Record<string, number>): GameState {
    if (this.phase !== 'step_start') throw new GameActionError('the current step has already started');
    const player = this.currentPlayer();
    const messages: string[] = [];
    if (player.stepsTakenThisTurn === 0 && player.figureId === 206) {
      const eligible = this.board.filter(cell => cell.visibility === 'face_down').map(cell => cell.index);
      const required = Math.min(3, eligible.length);
      if (foretellerIndices.length !== required) throw new GameActionError(`Foreteller must Reveal exactly ${required} cards`);
      if (new Set(foretellerIndices).size !== foretellerIndices.length || foretellerIndices.some(index => !eligible.includes(index))) throw new GameActionError('Foreteller targets must be different Face-down cards');
      this.reveal(foretellerIndices);
      messages.push(`${player.name}'s Foreteller Reveals ${foretellerIndices.length} cards`);
    }
    const planned: { owner: InternalPlayer; index: number }[] = [];
    for (const owner of [player, this.other(player)]) {
      if (owner.figureId !== 209) continue;
      const index = barrierIndices[owner.id];
      if (index === undefined || index === null) continue;
      const cell = this.requireCell(index);
      if (cell.visibility === 'opened' || cell.barrier || planned.some(item => item.index === index)) throw new GameActionError('X requires a different card that is not Opened or already blocked');
      planned.push({ owner, index });
    }
    planned.forEach(({ owner, index }) => {
      this.requireCell(index).barrier = true;
      messages.push(`${owner.name} places X on #${index}`);
    });
    this.record(messages);
    this.phase = 'action';
    this.stepStart = { foreteller_count: 0, barrier_player_ids: [] };
    this.resolveImpossibleCurse();
    return this.state();
  }

  private requireActionPhase(): void {
    if (this.phase !== 'action' || !this.currentPlayerId()) throw new GameActionError('the game is not waiting for a main action');
  }

  private forcedMagicIndex(player: InternalPlayer): number | null {
    const index = player.hand.findIndex(card => card.cursed);
    return index === -1 ? null : index;
  }

  private resolveImpossibleCurse(): void {
    const player = this.currentPlayer();
    const forcedIndex = this.forcedMagicIndex(player);
    if (forcedIndex === null || this.canResolveMagic(player, forcedIndex, true)) return;
    const card = this.handCardAt(player, forcedIndex);
    player.hand.splice(forcedIndex, 1);
    this.record([`Cursed ${MAGIC_CARDS[card.id].name} has no legal resolution; it is discarded`]);
    this.finishStep(player);
  }

  private openCard(requestedIndex: number, discardIndices: number[]): GameState {
    this.requireActionPhase();
    const player = this.currentPlayer();
    if (this.forcedMagicIndex(player) !== null) throw new GameActionError('this step is cursed; the marked Magic Card must be played');
    const choices = this.selectableIndices();
    const chosen = player.figureId === 211 ? this.choice(choices) : requestedIndex;
    if (player.figureId === 211 && !choices.length) throw new GameActionError('there are no cards Alcoholic can Open');
    if (!Number.isInteger(chosen)) throw new GameActionError('a board index is required');
    const cell = this.requireCell(chosen);
    if (cell.kind === 'magic' && player.hand.length === HAND_LIMIT && discardIndices.length === 0) {
      throw new GameActionError('Your hand is full. Choose exactly two cards to discard.', 'discard_required', { hand_indices: player.hand.map((card, index) => card.cursed ? -1 : index).filter(index => index >= 0), board_index: chosen });
    }
    this.record(this.resolveOpenCard(player, chosen, discardIndices));
    this.finishStep(player);
    return this.state();
  }

  private resolveOpenCard(player: InternalPlayer, index: number, discardIndices: number[]): string[] {
    const preview = this.requireCell(index);
    if (preview.kind === 'magic' && player.hand.length === HAND_LIMIT) this.validateFullHandDiscard(player, discardIndices);
    const cell = this.openCell(index);
    const opponent = this.other(player);
    const messages = [`Opened ${cell.kind} at #${index}`];
    this.applyWPattern(player, index, messages);
    if (cell.kind === 'bomb') {
      const amount = player.figureId === 214 ? 2 : player.figureId === 215 ? 3 : 1;
      messages.push(this.formatChanges(this.damage(player, amount), 'damage'));
    } else if (cell.kind === 'frog') {
      if (player.figureId === 214) messages.push(this.formatChanges(this.damage(opponent, 1), 'damage'));
      else if (player.figureId === 207 && !player.usedFigureAbilities.has(207)) {
        player.usedFigureAbilities.add(207);
        messages.push(this.formatChanges(this.heal(player, 1), 'healing'));
      }
    } else if (cell.kind === 'magic') {
      const discarded = this.receiveMagic(player, cell.id!, discardIndices);
      messages.push(`${player.name} receives ${MAGIC_CARDS[cell.id!].name}`);
      if (discarded.length) messages.push(`Discarded: ${discarded.map(card => MAGIC_CARDS[card.id].name).join(', ')}`);
    } else if (cell.kind === 'figure') {
      const oldId = player.figureId;
      const newId = cell.id === 212 ? opponent.figureId : cell.id!;
      if (this.changeFigure(player, newId)) messages.push(`${FIGURE_CARDS[oldId].name} changed to ${FIGURE_CARDS[newId].name}`);
      else messages.push('Figure change blocked by Const Figure');
    }
    return messages;
  }

  private playMagic(handIndex: number, choices: ActionBody): GameState {
    this.requireActionPhase();
    const player = this.currentPlayer();
    const forcedIndex = this.forcedMagicIndex(player);
    const forced = forcedIndex !== null;
    if (forced && handIndex !== forcedIndex) throw new GameActionError('the cursed card is the only legal action this step');
    const { handCard, definition } = this.validateMagic(player, handIndex, choices, forced);
    const opponent = this.other(player);
    const ownDiscard = definition.effectType === 'discard' ? this.handCardAt(player, choices.own_index as number) : null;
    const opponentDiscard = definition.effectType === 'discard' ? this.handCardAt(opponent, choices.opponent_index as number) : null;
    const curseTarget = definition.effectType === 'curse' ? this.handCardAt(opponent, choices.opponent_index as number) : null;
    this.removeHandCard(player, handCard);
    const data = definition.data;
    const messages = [`${player.name} plays ${definition.name}`];
    if (definition.effectType === 'heal') messages.push(this.formatChanges(this.heal(player, data.user as number), 'healing'));
    else if (definition.effectType === 'heal_dual') {
      messages.push(this.formatChanges(this.heal(player, data.user as number), 'healing'));
      messages.push(this.formatChanges(this.heal(opponent, data.opponent as number), 'healing'));
    } else if (definition.effectType === 'heal_and_board_delta') {
      messages.push(this.formatChanges(this.heal(player, data.user as number), 'healing'));
      this.pendingBoardEffects.push(definition.id);
    } else if (['board_delta', 'convert_all', 'convert_one'].includes(definition.effectType)) this.pendingBoardEffects.push(definition.id);
    else if (definition.effectType === 'shuffle') this.shuffleBoard();
    else if (definition.effectType === 'reveal') this.reveal(numberArray(choices.indices));
    else if (definition.effectType === 'reveal_line') this.reveal(this.lineIndices(choices.axis as string, choices.line as number).filter(index => this.board[index].visibility === 'face_down'));
    else if (definition.effectType === 'reveal_all_magic') this.reveal(this.board.filter(cell => cell.kind === 'magic' && cell.visibility !== 'opened').map(cell => cell.index));
    else if (definition.effectType === 'change_figure') this.changeFigure(this.playerById(choices.target), data.figure_id as number);
    else if (definition.effectType === 'protect_figure') this.playerById(choices.target).figureLockTurns = data.turns as number;
    else if (definition.effectType === 'discard') {
      this.removeHandCard(player, ownDiscard!);
      this.removeHandCard(opponent, opponentDiscard!);
    } else if (definition.effectType === 'curse') curseTarget!.cursed = true;
    else if (definition.effectType === 'swap_hand') [player.hand, opponent.hand] = [opponent.hand, player.hand];
    this.record(messages);
    this.finishStep(player);
    return this.state();
  }

  private validateMagic(player: InternalPlayer, handIndex: number, choices: ActionBody, forced: boolean): { handCard: InternalHandCard; definition: MagicDefinition } {
    const handCard = this.handCardAt(player, handIndex);
    if (handCard.cursed && !forced) throw new GameActionError('a cursed card cannot be played voluntarily');
    const definition = MAGIC_CARDS[handCard.id];
    const opponent = this.other(player);
    if (definition.effectType === 'reveal') {
      const indices = numberArray(choices.indices);
      if (indices.length !== definition.data.count) throw new GameActionError(`${definition.name} requires exactly ${definition.data.count} targets`);
      if (new Set(indices).size !== indices.length) throw new GameActionError('Reveal targets must be different');
      indices.forEach(index => { if (this.requireCell(index).visibility !== 'face_down') throw new GameActionError('Reveal targets must be Face-down'); });
    } else if (definition.effectType === 'reveal_line') {
      const axis = choices.axis;
      const line = choices.line;
      if (!['row', 'column'].includes(axis as string) || !Number.isInteger(line) || (line as number) < 0 || (line as number) >= 5) throw new GameActionError('Take a look! requires one row or column from 0 to 4');
      if (!this.lineIndices(axis as string, line as number).some(index => this.board[index].visibility === 'face_down')) throw new GameActionError('that line has no face-down cards to Reveal');
    } else if (['change_figure', 'protect_figure'].includes(definition.effectType)) this.playerById(choices.target);
    else if (definition.effectType === 'discard') {
      const ownCard = this.handCardAt(player, choices.own_index as number);
      const opponentCard = this.handCardAt(opponent, choices.opponent_index as number);
      if (ownCard === handCard || ownCard.cursed || opponentCard.cursed) throw new GameActionError('Shredder requires one other non-cursed card from each player');
    } else if (definition.effectType === 'curse') {
      if (opponent.hand.some(card => card.cursed)) throw new GameActionError('opponent already has a cursed card');
      const target = this.handCardAt(opponent, choices.opponent_index as number);
      if (target.cursed || target.id === 23) throw new GameActionError('This is curse! cannot target that card');
    } else if (definition.effectType === 'swap_hand') {
      if (player.hand.some(card => card !== handCard && card.cursed) || opponent.hand.some(card => card.cursed)) throw new GameActionError('Swap cannot be played while either hand contains a cursed card');
    }
    return { handCard, definition };
  }

  private canResolveMagic(player: InternalPlayer, handIndex: number, forced: boolean): boolean {
    const handCard = this.handCardAt(player, handIndex);
    if (handCard.cursed && !forced) return false;
    const definition = MAGIC_CARDS[handCard.id];
    const opponent = this.other(player);
    if (definition.effectType === 'reveal') return this.board.filter(cell => cell.visibility === 'face_down').length >= Number(definition.data.count);
    if (definition.effectType === 'reveal_line') return this.board.some(cell => cell.visibility === 'face_down');
    if (definition.effectType === 'discard') return player.hand.some(card => card !== handCard && !card.cursed) && opponent.hand.some(card => !card.cursed);
    if (definition.effectType === 'curse') return !opponent.hand.some(card => card.cursed) && opponent.hand.some(card => !card.cursed && card.id !== 23);
    if (definition.effectType === 'swap_hand') return !player.hand.some(card => card !== handCard && card.cursed) && !opponent.hand.some(card => card.cursed);
    return true;
  }

  private activateFigure(): GameState {
    this.requireActionPhase();
    const player = this.currentPlayer();
    if (this.forcedMagicIndex(player) !== null) throw new GameActionError('a cursed Magic Card must resolve first');
    if (player.figureId !== 216) throw new GameActionError('player is not Magician');
    if (player.usedFigureAbilities.has(216)) throw new GameActionError('Magician already shuffled this turn');
    player.usedFigureAbilities.add(216);
    this.shuffleBoard();
    this.record([`${player.name} uses Magician Shuffle`]);
    this.finishStep(player);
    return this.state();
  }

  private continueTurn(): GameState {
    if (this.phase !== 'turn_end') throw new GameActionError('the current turn is not waiting to continue');
    this.record(this.startTurn());
    this.prepareCurrentStep();
    return this.state();
  }

  private finishStep(player: InternalPlayer): void {
    player.stepsTakenThisTurn += 1;
    this.step += 1;
    const result = this.gameResult();
    if (result !== null) {
      this.phase = 'game_over';
      this.log.push(result === 'draw' ? 'The game ends in a draw.' : `${result} wins.`);
      return;
    }
    if (this.step >= this.stepOrder.length) {
      this.phase = 'turn_end';
      this.stepStart = { foreteller_count: 0, barrier_player_ids: [] };
      this.log.push(`Turn ${this.turn} is complete. Review the final board before continuing.`);
      return;
    }
    this.prepareCurrentStep();
  }

  private requireCell(index: number): InternalCell {
    if (!Number.isInteger(index) || index < 0 || index >= this.board.length) throw new GameActionError('card index must be between 0 and 24');
    return this.board[index];
  }

  private openCell(index: number): InternalCell {
    const cell = this.requireCell(index);
    if (cell.barrier) throw new GameActionError('that card is protected by an X barrier');
    if (cell.visibility === 'opened') throw new GameActionError('that card is already Opened');
    cell.visibility = 'opened';
    cell.temporaryReveal = false;
    return cell;
  }

  private reveal(indices: number[]): void {
    if (new Set(indices).size !== indices.length) throw new GameActionError('Reveal targets must be different');
    const cells = indices.map(index => this.requireCell(index));
    if (cells.some(cell => cell.visibility === 'opened')) throw new GameActionError('an Opened card cannot be Revealed');
    cells.forEach(cell => { cell.visibility = 'revealed'; cell.temporaryReveal = true; });
  }

  private clearTemporaryReveals(): void {
    this.board.forEach(cell => {
      if (cell.visibility === 'revealed' && cell.temporaryReveal) {
        cell.visibility = 'face_down';
        cell.temporaryReveal = false;
      }
    });
  }

  private shuffleBoard(): void {
    this.shuffle(this.board);
    this.board.forEach((cell, index) => { cell.index = index; cell.visibility = 'face_down'; cell.barrier = false; cell.temporaryReveal = false; });
  }

  private selectableIndices(): number[] {
    return this.board.filter(cell => cell.visibility !== 'opened' && !cell.barrier).map(cell => cell.index);
  }

  private handCardAt(player: InternalPlayer, index: number): InternalHandCard {
    if (!Number.isInteger(index) || index < 0 || index >= player.hand.length) throw new GameActionError('magic card index is outside the hand');
    return player.hand[index];
  }

  private removeHandCard(player: InternalPlayer, card: InternalHandCard): void {
    const index = player.hand.indexOf(card);
    if (index === -1) throw new GameActionError('magic card is no longer in the hand');
    player.hand.splice(index, 1);
  }

  private validateFullHandDiscard(player: InternalPlayer, indices: number[]): void {
    if (indices.length !== 2 || new Set(indices).size !== 2) throw new GameActionError('opening Magic with a full hand requires two discard indices');
    if (indices.map(index => this.handCardAt(player, index)).some(card => card.cursed)) throw new GameActionError('a cursed card cannot be discarded');
  }

  private receiveMagic(player: InternalPlayer, id: number, discardIndices: number[]): InternalHandCard[] {
    if (player.hand.length < HAND_LIMIT) {
      if (discardIndices.length) throw new GameActionError('discarding is only allowed when the hand is full');
      player.hand.push({ id, cursed: false });
      return [];
    }
    this.validateFullHandDiscard(player, discardIndices);
    const selected = discardIndices.map(index => this.handCardAt(player, index));
    selected.forEach(card => this.removeHandCard(player, card));
    player.hand.push({ id, cursed: false });
    return selected;
  }

  private playerById(value: unknown): InternalPlayer {
    if (value !== 'p1' && value !== 'p2') throw new GameActionError('target player must be p1 or p2');
    return this.players[value];
  }

  private changeFigure(player: InternalPlayer, figureId: number): boolean {
    if (player.figureLockTurns > 0) return false;
    player.figureId = figureId;
    return true;
  }

  private abusiveActive(): boolean {
    return Object.values(this.players).some(player => player.figureId === 213);
  }

  private heal(player: InternalPlayer, amount: number): Map<InternalPlayer, number> {
    const actual = Math.min(amount, player.maxHp - player.hp);
    const changes = new Map<InternalPlayer, number>([[player, actual]]);
    if (this.abusiveActive()) changes.set(this.other(player), Math.min(actual, this.other(player).maxHp - this.other(player).hp));
    changes.forEach((value, target) => { target.hp += value; });
    return changes;
  }

  private modifiedDamage(player: InternalPlayer, amount: number): number {
    if (player.figureId === 217 && this.random() < 0.3) return 0;
    if (player.figureId === 218 && this.random() < 0.3) return amount * 2;
    return amount;
  }

  private damage(player: InternalPlayer, amount: number): Map<InternalPlayer, number> {
    return this.damageBatch(new Map([[player, amount]]));
  }

  private damageBatch(requested: Map<InternalPlayer, number>): Map<InternalPlayer, number> {
    const original = new Map<InternalPlayer, number>();
    requested.forEach((amount, player) => { if (amount > 0) original.set(player, Math.min(player.hp, this.modifiedDamage(player, amount))); });
    const losses = new Map(original);
    if (this.abusiveActive()) original.forEach((actual, player) => losses.set(this.other(player), (losses.get(this.other(player)) ?? 0) + actual));
    const applied = new Map<InternalPlayer, number>();
    losses.forEach((amount, player) => applied.set(player, Math.min(player.hp, amount)));
    applied.forEach((amount, player) => { player.hp -= amount; });
    return applied;
  }

  private applyWPattern(player: InternalPlayer, index: number, messages: string[]): void {
    const figure = FIGURE_CARDS[player.figureId];
    if (!figure.pattern || player.usedFigureAbilities.has(player.figureId)) return;
    const row = Math.floor(index / 5);
    const column = index % 5;
    if (figure.pattern[row][column] !== 'W') return;
    player.usedFigureAbilities.add(player.figureId);
    const amount = player.figureId === 202 ? 1 : 0.5;
    messages.push(this.formatChanges(this.heal(player, amount), 'healing'));
    messages.push(this.formatChanges(this.damage(this.other(player), amount), 'damage'));
  }

  private resolveTurnStartFigures(): string[] {
    const messages: string[] = [];
    Object.values(this.players).forEach(player => {
      if (player.figureId === 201 && this.random() < 0.1) {
        const newId = this.choice([202, 203, 204, 205]);
        if (this.changeFigure(player, newId)) messages.push(`${player.name}'s Pawn evolves into ${FIGURE_CARDS[newId].name}`);
      }
    });
    Object.values(this.players).forEach(player => {
      if (player.figureId === 219) {
        this.board.forEach(cell => { cell.visibility = cell.visibility === 'face_down' ? 'revealed' : 'face_down'; cell.temporaryReveal = false; });
        messages.push(`${player.name}'s Politician inverts the board`);
      }
    });
    const witchDamage = new Map<InternalPlayer, number>();
    Object.values(this.players).forEach(player => {
      if (player.figureId === 208) witchDamage.set(this.other(player), (witchDamage.get(this.other(player)) ?? 0) + 1);
    });
    if (witchDamage.size) messages.push(this.formatChanges(this.damageBatch(witchDamage), 'damage'));
    return messages;
  }

  private resolveNextDistribution(): BoardDistribution {
    const distribution = { ...DEFAULT_DISTRIBUTION };
    const numerical = this.pendingBoardEffects.map(id => MAGIC_CARDS[id]).filter(card => ['board_delta', 'heal_and_board_delta'].includes(card.effectType));
    const conversions = this.pendingBoardEffects.map(id => MAGIC_CARDS[id]).filter(card => ['convert_all', 'convert_one'].includes(card.effectType));
    const totals = Object.fromEntries(CARD_TYPES.map(kind => [kind, 0])) as BoardDistribution;
    numerical.forEach(card => CARD_TYPES.forEach(kind => { if (typeof card.data[kind] === 'number') totals[kind] += card.data[kind] as number; }));
    const removals = Object.fromEntries(CARD_TYPES.map(kind => [kind, totals[kind] < 0 ? Math.min(distribution[kind], -totals[kind]) : 0])) as BoardDistribution;
    const additions = CARD_TYPES.filter(kind => totals[kind] > 0);
    const available = CARD_TYPES.reduce((sum, kind) => sum + removals[kind], 0);
    const requested = additions.reduce((sum, kind) => sum + totals[kind], 0);
    CARD_TYPES.forEach(kind => { distribution[kind] -= removals[kind]; });
    let remaining = available;
    additions.forEach((kind, position) => {
      const granted = position === additions.length - 1 ? remaining : Math.min(totals[kind], Math.floor(available * totals[kind] / requested));
      distribution[kind] += granted;
      remaining -= granted;
    });
    conversions.forEach(card => {
      const source = card.data.source as BoardKind;
      const target = card.data.target as BoardKind;
      const amount = card.effectType === 'convert_all' ? distribution[source] : Math.min(1, distribution[source]);
      distribution[source] -= amount;
      distribution[target] += amount;
    });
    this.validateDistribution(distribution);
    return distribution;
  }

  private lineIndices(axis: string, line: number): number[] {
    return Array.from({ length: 5 }, (_, offset) => axis === 'row' ? line * 5 + offset : offset * 5 + line);
  }

  private formatChanges(changes: Map<InternalPlayer, number>, kind: string): string {
    return changes.size ? [...changes].map(([player, amount]) => `${player.name}: ${amount} ${kind}`).join(', ') : `No ${kind}`;
  }

  private gameResult(): string | null {
    const p1Dead = this.players.p1.hp <= 0;
    const p2Dead = this.players.p2.hp <= 0;
    if (p1Dead && p2Dead) return 'draw';
    if (p1Dead) return this.players.p2.name;
    if (p2Dead) return this.players.p1.name;
    return null;
  }

  state(): GameState {
    const currentId = this.currentPlayerId();
    const currentDistribution = Object.fromEntries(CARD_TYPES.map(kind => [kind, this.board.filter(cell => cell.kind === kind).length])) as BoardDistribution;
    return {
      phase: this.phase,
      turn: this.turn,
      step: this.step,
      step_order: [...this.stepOrder],
      current_player_id: currentId,
      forced_hand_index: currentId && this.phase === 'action' ? this.forcedMagicIndex(this.players[currentId]) : null,
      result: this.gameResult(),
      step_start: { foreteller_count: this.stepStart.foreteller_count, barrier_player_ids: [...this.stepStart.barrier_player_ids] },
      players: (['p1', 'p2'] as PlayerId[]).map(id => {
        const player = this.players[id];
        const figure = FIGURE_CARDS[player.figureId];
        return {
          id,
          name: player.name,
          hp: player.hp,
          max_hp: player.maxHp,
          figure: { id: figure.id, name: figure.name, description: figure.description, used: player.usedFigureAbilities.has(figure.id) },
          hand: player.hand.map((card, index) => ({ index, id: card.id, name: MAGIC_CARDS[card.id].name, description: MAGIC_CARDS[card.id].description, effect_type: MAGIC_CARDS[card.id].effectType, effect_data: { ...MAGIC_CARDS[card.id].data }, cursed: card.cursed })),
        };
      }),
      board_distribution: { current: currentDistribution, next: this.resolveNextDistribution() },
      board: this.board.map(cell => this.serializeCell(cell)),
      selectable_indices: this.selectableIndices(),
      log: [...this.log],
    };
  }

  private serializeCell(cell: InternalCell): BoardCell {
    if (cell.visibility === 'face_down') return { index: cell.index, visibility: cell.visibility, barrier: cell.barrier, kind: null, id: null, name: 'Unknown card', description: 'This card is face-down. Open it to reveal and resolve it.' };
    if (cell.kind === 'magic') {
      const card = MAGIC_CARDS[cell.id!];
      return { index: cell.index, visibility: cell.visibility, barrier: cell.barrier, kind: cell.kind, id: cell.id, name: card.name, description: card.description, effect_type: card.effectType };
    }
    if (cell.kind === 'figure') {
      const card = FIGURE_CARDS[cell.id!];
      return { index: cell.index, visibility: cell.visibility, barrier: cell.barrier, kind: cell.kind, id: cell.id, name: card.name, description: card.description };
    }
    const descriptions: Record<'bomb' | 'frog' | 'empty', string> = { bomb: 'Take 1 damage before figure modifiers.', frog: 'No base effect; some figures change what Frog does.', empty: 'No base effect.' };
    return { index: cell.index, visibility: cell.visibility, barrier: cell.barrier, kind: cell.kind, id: null, name: cell.kind[0].toUpperCase() + cell.kind.slice(1), description: descriptions[cell.kind] };
  }
}
