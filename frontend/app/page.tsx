'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

type Visibility = 'face_down' | 'revealed' | 'opened';
type CardKind = 'magic' | 'figure' | 'bomb' | 'frog' | 'empty' | 'unknown';
type HandCard = { index: number; id: number; name: string; description: string; effect_type: string; effect_data: Record<string, string | number>; cursed: boolean };
type Figure = { id: number; name: string; description: string; used: boolean };
type Player = { id: 'p1' | 'p2'; name: string; hp: number; max_hp: number; figure: Figure; hand: HandCard[] };
type BoardCell = { index: number; visibility: Visibility; barrier: boolean; kind: CardKind | null; id: number | null; name: string; description: string; effect_type?: string };
type GameState = {
  phase: 'setup' | 'step_start' | 'action' | 'turn_end' | 'game_over'; turn: number; step: number;
  step_order: ('p1' | 'p2')[]; current_player_id: 'p1' | 'p2' | null; forced_hand_index: number | null; result: string | null;
  step_start: { foreteller_count: number; barrier_player_ids: ('p1' | 'p2')[] };
  players: Player[]; board: BoardCell[]; selectable_indices: number[]; log: string[];
};
type Selection = { source: 'board'; index: number } | { source: 'hand'; playerId: 'p1' | 'p2'; index: number } | { source: 'figure'; playerId: 'p1' | 'p2' };
type Pending =
  | { kind: 'reveal'; handIndex: number; count: number; indices: number[] }
  | { kind: 'line'; handIndex: number; anchorIndex?: number; axis?: 'row' | 'column' }
  | { kind: 'target'; handIndex: number; target?: 'p1' | 'p2' }
  | { kind: 'curse'; handIndex: number; opponentIndex?: number }
  | { kind: 'discard'; handIndex: number; ownIndex?: number; opponentIndex?: number }
  | { kind: 'draw-discard'; boardIndex: number; ownIndices: number[] };

const API = 'http://127.0.0.1:8000/api';
const kindMark: Record<CardKind, string> = { magic: 'M', figure: 'F', bomb: '!', frog: 'R', empty: '·', unknown: '55' };
const visibilityLabel: Record<Visibility, string> = { face_down: 'Face-down', revealed: 'Revealed', opened: 'Opened' };

function artwork(kind: CardKind, id: number | null) {
  if (kind === 'unknown') return '/cards/card-back-1.png';
  if (kind === 'bomb') return '/cards/bomb.png';
  if (kind === 'frog') return '/cards/frog.png';
  if (kind === 'figure') return '/cards/figure_test.png';
  if (kind === 'magic' && id === 1) return '/cards/bubble_milk_tea.png';
  if (kind === 'magic') return '/cards/empty_magic_card.png';
  return null;
}

async function request(path: string, body?: object): Promise<GameState> {
  const response = await fetch(`${API}${path}`, { method: body ? 'POST' : 'GET', headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined });
  const data = await response.json();
  if (!response.ok) throw data;
  return data;
}

function MiniCard({ card, selected, disabled, onClick }: { card: HandCard; selected: boolean; disabled?: boolean; onClick: () => void }) {
  return <button title={card.name} className={`mini-card ${selected ? 'selected' : ''} ${card.cursed ? 'cursed' : ''}`} disabled={disabled} onClick={onClick}><span>M</span><b>{card.name}</b><small>#{String(card.id).padStart(3, '0')}{card.cursed ? ' · CURSED' : ' · MAGIC'}</small></button>;
}

function PlayerStrip({ player, active, selection, forcedIndex, onCard, onFigure }: { player: Player; active: boolean; selection: Selection | null; forcedIndex: number | null; onCard: (index: number) => void; onFigure: () => void }) {
  const figureUsable = active && player.figure.id === 216 && !player.figure.used && forcedIndex === null;
  return <section className={`player-strip player-${player.id} ${active ? 'is-active' : ''}`}>
    <div className="player-identity"><span className="avatar">{player.figure.name.slice(0, 1)}</span><div><span className="eyebrow">{active ? 'ACTIVE PLAYER' : 'WAITING'}</span><h2>{player.name}</h2></div></div>
    <div className="health" aria-label={`${player.hp} of ${player.max_hp} health`}><span>HP</span><strong>{player.hp.toFixed(1)}</strong><div className="health-track"><i style={{ width: `${player.hp / player.max_hp * 100}%` }} /></div></div>
    <button className={`figure-chip ${figureUsable ? 'usable' : ''}`} onClick={onFigure}><span>FIGURE {figureUsable ? '· READY' : ''}</span><strong>{player.figure.name}</strong></button>
    <div className="hand" aria-label={`${player.name} hand`}>{player.hand.map(card => <MiniCard key={card.index} card={card} selected={selection?.source === 'hand' && selection.playerId === player.id && selection.index === card.index} disabled={active && forcedIndex !== null && forcedIndex !== card.index} onClick={() => onCard(card.index)} />)}{Array.from({ length: Math.max(0, 3 - player.hand.length) }, (_, index) => <div className="empty-slot" key={index}>EMPTY</div>)}</div>
  </section>;
}

function BoardCard({ card, selected, target, onClick }: { card: BoardCell; selected: boolean; target: boolean; onClick: () => void }) {
  const hidden = card.visibility === 'face_down'; const kind = card.kind ?? 'unknown';
  return <button className={`board-card ${card.visibility.replace('_', '-')} kind-${kind} ${selected ? 'selected' : ''} ${target ? 'targeted' : ''}`} onClick={onClick}>
    <span className="card-index">{String(card.index).padStart(2, '0')}</span>{card.barrier && <span className="barrier">X</span>}
    {hidden ? <><span className="back-mark">5×5</span><small>UNKNOWN</small></> : <><span className="kind-mark">{kindMark[kind]}</span><strong>{card.name}</strong><small>{card.visibility.toUpperCase()}</small></>}
  </button>;
}

function Inspector({ state, selection, pending, busy, onAction, onTarget, onAxis, onCancel }: { state: GameState; selection: Selection | null; pending: Pending | null; busy: boolean; onAction: () => void; onTarget: (id: 'p1' | 'p2') => void; onAxis: (axis: 'row' | 'column') => void; onCancel: () => void }) {
  let name = 'Choose a card'; let kind: CardKind = 'unknown'; let description = 'Select a board, hand, or figure card to inspect its real rule text.'; let id: number | null = null; let statusLabel = 'Ready';
  if (selection?.source === 'board') { const card = state.board[selection.index]; name = card.name; kind = card.kind ?? 'unknown'; description = card.description; id = card.id; statusLabel = visibilityLabel[card.visibility]; }
  else if (selection?.source === 'hand') { const card = state.players.find(item => item.id === selection.playerId)!.hand[selection.index]; if (card) { name = card.name; kind = 'magic'; description = card.description; id = card.id; statusLabel = card.cursed ? 'Cursed' : card.effect_type.replaceAll('_', ' '); } }
  else if (selection?.source === 'figure') { const figure = state.players.find(item => item.id === selection.playerId)!.figure; name = figure.name; kind = 'figure'; description = figure.description; id = figure.id; statusLabel = figure.used ? 'Used this turn' : 'Available'; }
  const pendingText = pending?.kind === 'reveal' ? `Choose ${pending.count} face-down card(s): ${pending.indices.length}/${pending.count}` : pending?.kind === 'line' ? pending.anchorIndex === undefined ? 'Choose any card in the row or column you want to reveal.' : `Card #${String(pending.anchorIndex).padStart(2, '0')} selected. Now choose ROW or COLUMN.` : pending?.kind === 'target' ? 'Choose which player becomes the target.' : pending?.kind === 'curse' ? 'Select one card in the opponent’s hand.' : pending?.kind === 'discard' ? 'Select one other card from each hand.' : pending?.kind === 'draw-discard' ? `Discard two hand cards: ${pending.ownIndices.length}/2` : null;
  const selectedBoard = selection?.source === 'board' ? state.board[selection.index] : null;
  const selectedHandOwner = selection?.source === 'hand' ? state.players.find(player => player.id === selection.playerId) : null;
  const selectedFigureOwner = selection?.source === 'figure' ? state.players.find(player => player.id === selection.playerId) : null;
  const canUseFigure = selectedFigureOwner?.id === state.current_player_id && selectedFigureOwner.figure.id === 216 && !selectedFigureOwner.figure.used && state.forced_hand_index === null;
  const disabled = busy || !selection || state.phase !== 'action' || selectedBoard?.visibility === 'opened' || (selectedHandOwner && selectedHandOwner.id !== state.current_player_id) || (selection?.source === 'hand' && state.forced_hand_index !== null && selection.index !== state.forced_hand_index) || (selection?.source === 'figure' && !canUseFigure);
  const actionLabel = busy ? 'RESOLVING…' : pending ? 'CONFIRM CHOICES' : selection?.source === 'board' ? selectedBoard?.visibility === 'opened' ? 'ALREADY OPENED' : 'OPEN THIS CARD' : selection?.source === 'hand' ? selectedHandOwner?.id === state.current_player_id ? 'PLAY THIS MAGIC' : 'OPPONENT CARD' : canUseFigure ? 'USE FIGURE ABILITY' : 'VIEW FIGURE ONLY';
  const art = artwork(kind, id);
  return <aside className="inspector"><span className="panel-label">CARD DETAILS</span><div className={`art-frame kind-${kind}`} style={art ? { backgroundImage: `linear-gradient(#06100c22,#06100c66), url(${art})` } : undefined}><span>{kindMark[kind]}</span></div>
    <div className="inspector-title"><div><span>{kind.toUpperCase()}</span><h2>{name}</h2></div>{id !== null && <b>#{String(id).padStart(3, '0')}</b>}</div><p className="description">{description}</p>
    <dl><div><dt>STATUS</dt><dd>{statusLabel}</dd></div><div><dt>RULE</dt><dd>Resolves after confirmation</dd></div></dl>{pendingText && <div className="choice-note">{pendingText}</div>}
    {pending?.kind === 'target' && <div className="target-buttons">{state.players.map(player => <button key={player.id} className={pending.target === player.id ? 'chosen' : ''} onClick={() => onTarget(player.id)}>{player.name}</button>)}</div>}
    {pending?.kind === 'line' && pending.anchorIndex !== undefined && <div className="target-buttons"><button className={pending.axis === 'row' ? 'chosen' : ''} onClick={() => onAxis('row')}>REVEAL ROW {Math.floor(pending.anchorIndex! / 5) + 1}</button><button className={pending.axis === 'column' ? 'chosen' : ''} onClick={() => onAxis('column')}>REVEAL COLUMN {(pending.anchorIndex! % 5) + 1}</button></div>}
    <button className="primary-action" disabled={disabled} onClick={onAction}>{actionLabel}</button>{pending && <button className="cancel-action" onClick={onCancel}>CANCEL SELECTION</button>}<p className="action-note">Selecting is safe. Nothing happens until you confirm here.</p>
  </aside>;
}

export default function Home() {
  const [state, setState] = useState<GameState | null>(null); const [selection, setSelection] = useState<Selection | null>({ source: 'board', index: 0 }); const [pending, setPending] = useState<Pending | null>(null);
  const [stepTargets, setStepTargets] = useState<number[]>([]); const [barriers, setBarriers] = useState<Record<string, number>>({}); const [barrierOwner, setBarrierOwner] = useState<'p1' | 'p2' | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const [resetArmed, setResetArmed] = useState(false);
  const acceptState = useCallback((next: GameState) => { setState(next); setPending(null); setStepTargets([]); setBarriers({}); setBarrierOwner(null); setError(''); }, []);
  const call = useCallback(async (path: string, body?: object) => { setBusy(true); setError(''); try { acceptState(await request(path, body)); } catch (problem) { const apiError = problem as { error?: string; code?: string; details?: { board_index?: number } }; if (apiError.code === 'discard_required' && apiError.details?.board_index !== undefined) setPending({ kind: 'draw-discard', boardIndex: apiError.details.board_index, ownIndices: [] }); setError(apiError.error ?? 'The local Python API is not running.'); } finally { setBusy(false); } }, [acceptState]);
  useEffect(() => {
    let active = true;
    request('/state').then(next => { if (active) acceptState(next); }).catch(() => { if (active) setError('The local Python API is not running.'); });
    return () => { active = false; };
  }, [acceptState]);
  const current = state?.players.find(player => player.id === state.current_player_id) ?? null; const orderedPlayers = state ? [state.players[1], state.players[0]] : [];
  const selectedBoard = selection?.source === 'board' ? selection.index : -1;
  function toggle(values: number[], value: number, limit: number) { if (values.includes(value)) return values.filter(item => item !== value); return values.length < limit ? [...values, value] : values; }
  function chooseBoard(index: number) { if (!state) return; const card = state.board[index]; if (state.phase === 'step_start') { if (barrierOwner) { if (card.visibility === 'opened' || card.barrier || Object.values(barriers).includes(index)) return; setBarriers(previous => ({ ...previous, [barrierOwner]: index })); setBarrierOwner(null); return; } if (state.step_start.foreteller_count && card.visibility === 'face_down') setStepTargets(previous => toggle(previous, index, state.step_start.foreteller_count)); return; } if (pending?.kind === 'reveal' && card.visibility === 'face_down') { setPending({ ...pending, indices: toggle(pending.indices, index, pending.count) }); return; } if (pending?.kind === 'line' && card.visibility !== 'opened') { setPending({ ...pending, anchorIndex: index, axis: undefined }); return; } setSelection({ source: 'board', index }); }
  function chooseHand(playerId: 'p1' | 'p2', index: number) { if (!state) return; if (pending?.kind === 'curse' && playerId !== state.current_player_id) { setPending({ ...pending, opponentIndex: index }); return; } if (pending?.kind === 'discard') { if (playerId === state.current_player_id && index !== pending.handIndex) setPending({ ...pending, ownIndex: index }); if (playerId !== state.current_player_id) setPending({ ...pending, opponentIndex: index }); return; } if (pending?.kind === 'draw-discard' && playerId === state.current_player_id) { setPending({ ...pending, ownIndices: toggle(pending.ownIndices, index, 2) }); return; } setSelection({ source: 'hand', playerId, index }); }
  async function takeAction() { if (!state || !selection || !current) return; if (pending) { if (pending.kind === 'reveal' && pending.indices.length === pending.count) return void call('/play-magic', { hand_index: pending.handIndex, choices: { indices: pending.indices } }); if (pending.kind === 'line' && pending.anchorIndex !== undefined && pending.axis) return void call('/play-magic', { hand_index: pending.handIndex, choices: { axis: pending.axis, line: pending.axis === 'row' ? Math.floor(pending.anchorIndex / 5) : pending.anchorIndex % 5 } }); if (pending.kind === 'target' && pending.target) return void call('/play-magic', { hand_index: pending.handIndex, choices: { target: pending.target } }); if (pending.kind === 'curse' && pending.opponentIndex !== undefined) return void call('/play-magic', { hand_index: pending.handIndex, choices: { opponent_index: pending.opponentIndex } }); if (pending.kind === 'discard' && pending.ownIndex !== undefined && pending.opponentIndex !== undefined) return void call('/play-magic', { hand_index: pending.handIndex, choices: { own_index: pending.ownIndex, opponent_index: pending.opponentIndex } }); if (pending.kind === 'draw-discard' && pending.ownIndices.length === 2) return void call('/open', { index: pending.boardIndex, discard_indices: pending.ownIndices }); setError('Finish the highlighted choice first.'); return; }
    if (selection.source === 'board') return void call('/open', { index: selection.index }); if (selection.source === 'figure') return void call('/activate-figure', {}); if (selection.playerId !== current.id) { setError('Only the active player can use a hand card.'); return; } const card = current.hand[selection.index]; if (!card) return;
    if (card.effect_type === 'reveal') return setPending({ kind: 'reveal', handIndex: card.index, count: Number(card.effect_data.count), indices: [] }); if (card.effect_type === 'reveal_line') return setPending({ kind: 'line', handIndex: card.index }); if (card.effect_type === 'change_figure' || card.effect_type === 'protect_figure') return setPending({ kind: 'target', handIndex: card.index }); if (card.effect_type === 'curse') return setPending({ kind: 'curse', handIndex: card.index }); if (card.effect_type === 'discard') return setPending({ kind: 'discard', handIndex: card.index }); void call('/play-magic', { hand_index: card.index, choices: {} }); }
  const stepReady = state ? stepTargets.length === state.step_start.foreteller_count : false; const selectableCount = state?.selectable_indices.length ?? 0; const targeted = useMemo(() => pending?.kind === 'reveal' ? pending.indices : pending?.kind === 'line' && pending.anchorIndex !== undefined && pending.axis ? state!.board.filter(card => card.visibility === 'face_down' && (pending.axis === 'row' ? Math.floor(card.index / 5) === Math.floor(pending.anchorIndex! / 5) : card.index % 5 === pending.anchorIndex! % 5)).map(card => card.index) : pending?.kind === 'line' && pending.anchorIndex !== undefined ? [pending.anchorIndex] : pending?.kind === 'draw-discard' ? [] : stepTargets, [pending, state, stepTargets]);
  function resetGame() { if (!resetArmed) { setResetArmed(true); return; } setResetArmed(false); void call('/new-game', {}); }
  if (!state) return <main className="loading-screen"><div><span className="brand-mark">55</span><h1>Connecting to the table…</h1><p>{error || 'Waiting for the local Python game server on port 8000.'}</p><button onClick={() => void call('/state')}>RETRY CONNECTION</button></div></main>;
  const nextStepIndex = state.phase === 'turn_end' || state.step + 1 >= state.step_order.length ? 0 : state.step + 1;
  const nextPlayerId = state.phase === 'game_over' ? null : state.step_order[nextStepIndex];
  const boardCounts = state.board.reduce((counts, card) => ({ ...counts, [card.visibility]: counts[card.visibility] + 1 }), { face_down: 0, revealed: 0, opened: 0 } as Record<Visibility, number>);
  const phaseLabel = state.phase === 'turn_end' ? 'TURN REVIEW' : state.phase === 'step_start' ? 'STEP SETUP' : state.phase === 'game_over' ? 'GAME OVER' : 'CHOOSE ACTION';
  return <main className="game-shell"><header className="topbar"><div><span className="brand-mark">55</span><div><b>FIVE BY FIVE</b><small>ONE SCREEN · TWO PLAYERS</small></div></div><strong className="table-callout">READ THE TABLE · TAKE YOUR STEP</strong><button className={`rules-button ${resetArmed ? 'reset-armed' : ''}`} onClick={resetGame}>{resetArmed ? 'CONFIRM RESET' : 'RESET GAME'}</button></header>
    {state.phase === 'step_start' && <section className="phase-banner"><div><b>STEP-START CHOICES</b><span>{state.step_start.foreteller_count ? `Foreteller must reveal ${state.step_start.foreteller_count} cards (${stepTargets.length}/${state.step_start.foreteller_count}).` : 'Optional X barriers may be placed now.'}</span></div><div className="barrier-controls">{state.step_start.barrier_player_ids.map(id => <button key={id} className={barriers[id] !== undefined ? 'chosen' : ''} onClick={() => setBarrierOwner(id)}>{id.toUpperCase()} X: {barriers[id] ?? 'SKIP'}</button>)}</div><button disabled={!stepReady || busy} onClick={() => void call('/begin-step', { foreteller_indices: stepTargets, barrier_indices: barriers })}>CONFIRM</button></section>}{error && <div className="error-banner">{error}<button onClick={() => setError('')}>×</button></div>}
    {state.phase === 'turn_end' && <section className="phase-banner turn-summary"><div><b>TURN {state.turn} COMPLETE</b><span>The sixth step stays visible. Review the board and action log before replacing it.</span></div><button disabled={busy} onClick={() => void call('/continue-turn', {})}>START TURN {state.turn + 1}</button></section>}
    <PlayerStrip player={orderedPlayers[0]} active={orderedPlayers[0].id === state.current_player_id} selection={selection} forcedIndex={orderedPlayers[0].id === state.current_player_id ? state.forced_hand_index : null} onCard={index => chooseHand(orderedPlayers[0].id, index)} onFigure={() => setSelection({ source: 'figure', playerId: orderedPlayers[0].id })} />
    <div className="table-layout"><aside className="log-panel"><span className="panel-label">WHAT JUST HAPPENED</span><ol>{state.log.slice(-6).reverse().map((entry, index) => <li className={index === 0 ? 'latest' : ''} key={`${entry}-${index}`}><time>{index === 0 ? 'NOW' : `${index} AGO`}</time><p>{entry}</p></li>)}</ol><div className="legend"><span><i className="dot revealed-dot" />Visible, not triggered</span><span><i className="dot opened-dot" />Opened and resolved</span><span><i className="x-mini">X</i>Cannot be opened</span></div></aside>
      <section className="board-wrap"><div className="board-heading"><div><span className="panel-label">SHARED TABLE</span><h1>{state.phase === 'game_over' ? state.result === 'draw' ? 'Draw game.' : `${state.result} wins.` : state.phase === 'turn_end' ? 'Review the final step.' : pending || state.phase === 'step_start' ? 'Choose the highlighted targets.' : `${current?.name ?? 'No player'}, choose your risk.`}</h1></div><p><b>{selectableCount}</b> can open</p></div><div className="board-stage"><aside className="board-status" aria-label="Turn and board status"><div className="status-head"><span>TURN</span><strong>{String(state.turn).padStart(2, '0')}</strong><em>{phaseLabel}</em></div><div className="step-order" aria-label={`Step ${Math.min(state.step + 1, 6)} of 6`}>{state.step_order.map((id, index) => <i key={index} className={`${id} ${index === state.step && state.phase !== 'turn_end' ? 'current' : index < state.step || state.phase === 'turn_end' ? 'done' : ''}`}><small>{index + 1}</small><b>{id.toUpperCase()}</b></i>)}</div><div className="player-flow"><div className={state.current_player_id ?? 'neutral'}><span>CURRENT STEP</span><strong>{current?.name ?? (state.phase === 'turn_end' ? 'Review board' : 'Game over')}</strong></div><div className={nextPlayerId ?? 'neutral'}><span>NEXT STEP</span><strong>{nextPlayerId ? state.players.find(player => player.id === nextPlayerId)?.name : '—'}</strong></div></div><div className="board-counts"><span>BOARD NOW</span><p><b>{boardCounts.face_down}</b> hidden</p><p><b>{boardCounts.revealed}</b> revealed</p><p><b>{boardCounts.opened}</b> opened</p></div>{state.phase === 'turn_end' && <div className="next-turn"><span>NEXT TURN</span><strong>New 5 × 5 board</strong><small>Starts only after confirmation</small></div>}</aside><div className="board-grid">{state.board.map(card => <BoardCard key={card.index} card={card} selected={card.index === selectedBoard} target={targeted.includes(card.index) || Object.values(barriers).includes(card.index)} onClick={() => chooseBoard(card.index)} />)}</div></div></section>
      <Inspector state={state} selection={selection} pending={pending} busy={busy} onAction={() => void takeAction()} onTarget={id => pending?.kind === 'target' && setPending({ ...pending, target: id })} onAxis={axis => pending?.kind === 'line' && setPending({ ...pending, axis })} onCancel={() => { setPending(null); setError(''); }} /></div>
    <PlayerStrip player={orderedPlayers[1]} active={orderedPlayers[1].id === state.current_player_id} selection={selection} forcedIndex={orderedPlayers[1].id === state.current_player_id ? state.forced_hand_index : null} onCard={index => chooseHand(orderedPlayers[1].id, index)} onFigure={() => setSelection({ source: 'figure', playerId: orderedPlayers[1].id })} />
    {state.phase === 'game_over' && <div className={`victory-overlay ${state.result === 'draw' ? 'is-draw' : ''}`} role="status" aria-live="assertive"><div className="confetti" aria-hidden="true">{Array.from({ length: 18 }, (_, index) => <i key={index} style={{ left: `${4 + (index * 17) % 92}%`, animationDelay: `${(index % 6) * -.18}s`, backgroundColor: ['#c59a39', '#b74339', '#4b9188'][index % 3] }} />)}</div><div className="victory-card"><span>{state.result === 'draw' ? 'SIMULTANEOUS DEFEAT' : 'GAME OVER'}</span><h2>{state.result === 'draw' ? 'IT’S A DRAW' : `${state.result} WINS!`}</h2><p>{state.result === 'draw' ? 'Both players fell to the same indivisible effect.' : 'The table remembers the last move.'}</p><button onClick={() => void call('/new-game', {})}>PLAY AGAIN</button></div></div>}
  </main>;
}
