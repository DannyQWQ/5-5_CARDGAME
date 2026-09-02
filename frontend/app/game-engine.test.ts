import assert from 'node:assert/strict';
import test from 'node:test';

import { BrowserGameSession, GameActionError } from './game-engine.ts';

test('a new browser game has a complete board and turn', () => {
  const session = new BrowserGameSession();
  const state = session.dispatch('/new-game', { seed: 55 });

  assert.equal(state.board.length, 25);
  assert.equal(state.step_order.length, 6);
  assert.equal(Object.values(state.board_distribution.current).reduce((sum, count) => sum + count, 0), 25);
  assert.equal(state.current_player_id, state.step_order[0]);
  assert.equal(state.phase, 'action');
});

test('six browser actions complete a turn unless the game ends first', () => {
  const session = new BrowserGameSession();
  let state = session.dispatch('/new-game', { seed: 55 });

  for (let action = 0; action < 6 && state.phase !== 'turn_end' && state.phase !== 'game_over'; action += 1) {
    const index = state.selectable_indices[0];
    try {
      state = session.dispatch('/open', { index });
    } catch (problem) {
      assert.ok(problem instanceof GameActionError);
      assert.equal(problem.code, 'discard_required');
      state = session.dispatch('/open', { index, discard_indices: (problem.details.hand_indices as number[]).slice(0, 2) });
    }
  }

  assert.ok(state.phase === 'turn_end' || state.phase === 'game_over');
  assert.ok(state.log.some(entry => entry.startsWith('Opened ')));
});

test('invalid actions return structured errors without an HTTP server', () => {
  const session = new BrowserGameSession();
  assert.throws(() => session.dispatch('/open', { index: 99 }), GameActionError);
  assert.throws(() => session.dispatch('/missing'), (problem: unknown) => problem instanceof GameActionError && problem.code === 'not_found');
});
