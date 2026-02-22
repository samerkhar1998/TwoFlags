import random
import time

import Zobrist


WIN_SCORE = 1_000_000
INFINITY = 10_000_000

# Difficulty presets control depth, randomness, and whether iterative deepening is enabled.
DIFFICULTY_SETTINGS = {
    "beginner": {
        "depth": 2,
        "top_n": 4,
        "randomness": 0.45,
        "iterative": False,
        "time_ms": 800,
        "max_depth": 2,
    },
    "moderate": {
        "depth": 4,
        "top_n": 2,
        "randomness": 0.12,
        "iterative": False,
        "time_ms": 1200,
        "max_depth": 4,
    },
    "hard": {
        "depth": 6,
        "top_n": 1,
        "randomness": 0.0,
        "iterative": True,
        "time_ms": 1500,
        "max_depth": 12,
    },
}

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2


class SearchTimeout(Exception):
    """Raised when iterative deepening reaches its time budget."""


class Agent:

    def __init__(self):
        # Transposition table keeps best-known scores and suggested best move by depth.
        self.transposition_table = {}
        # Simple move ordering enhancements.
        self.killer_moves = [[None, None] for _ in range(64)]
        self.history_scores = {}
        self.nodes = 0

    def find_best_move(self, gs, valid_moves, difficulty="moderate"):
        """Primary API used by the game loop.

        Args:
            gs: current GameState.
            valid_moves: precomputed legal root moves.
            difficulty: beginner | moderate | hard.

        Returns:
            Best move object from valid_moves (or None if no legal moves).
        """
        if not valid_moves:
            return None

        settings = self._get_settings(difficulty)
        self.nodes = 0

        # Keep existing Zobrist integration and make sure the root hash matches current board.
        zb = Zobrist.zobrist()
        self._sync_zobrist(gs, zb)

        color = 1 if gs.whiteToMove else -1
        deadline = time.perf_counter() + (settings["time_ms"] / 1000.0)

        best_move = self.firstMoveFromMoveOrdering(valid_moves)
        scored_moves = []

        if settings["iterative"]:
            max_depth = settings["max_depth"]
            for depth in range(1, max_depth + 1):
                try:
                    score, candidate, scored = self._search_root(gs, valid_moves, depth, color, zb, deadline)
                except SearchTimeout:
                    break

                if candidate is not None:
                    best_move = candidate
                    scored_moves = scored

                # If a forced win/loss horizon is found, deeper search is usually unnecessary.
                if abs(score) >= WIN_SCORE - 2000:
                    break
        else:
            depth = settings["depth"]
            score, candidate, scored = self._search_root(gs, valid_moves, depth, color, zb, deadline)
            if candidate is not None:
                best_move = candidate
                scored_moves = scored

        return self._choose_move_by_difficulty(best_move, scored_moves, settings)

    # Backward-compatible wrapper for existing multiprocessing call sites.
    def findBestMove(self, gs, validMoves, zb, returnQueue, difficulty="moderate"):
        move = self.find_best_move(gs, validMoves, difficulty=difficulty)
        if returnQueue is None:
            return move
        returnQueue.put(move)

    def _search_root(self, gs, valid_moves, depth, color, zb, deadline):
        self._check_timeout(deadline)

        alpha = -INFINITY
        beta = INFINITY
        best_score = -INFINITY
        best_move = None
        scored = []

        tt_entry = self.transposition_table.get(self._tt_key(zb, gs))
        tt_move_id = tt_entry[3] if tt_entry else None
        ordered_moves = self._order_moves(valid_moves, 0, tt_move_id)

        for move in ordered_moves:
            self._check_timeout(deadline)
            gs.makeMove(move)
            zb.updateHashKey(move, gs)

            score = -self._alpha_beta(gs, depth - 1, -beta, -alpha, -color, 1, zb, deadline)

            zb.undoHashKey(gs.moveLog[-1], gs)
            gs.undoMove()

            scored.append((score, move))

            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score

        scored.sort(key=lambda item: item[0], reverse=True)
        return best_score, best_move, scored

    def _alpha_beta(self, gs, depth, alpha, beta, color, ply, zb, deadline):
        self._check_timeout(deadline)
        self.nodes += 1

        key = self._tt_key(zb, gs)
        alpha_original = alpha

        tt_entry = self.transposition_table.get(key)
        if tt_entry is not None and tt_entry[0] >= depth:
            entry_depth, entry_score, entry_flag, _ = tt_entry
            if entry_flag == TT_EXACT:
                return entry_score
            if entry_flag == TT_LOWER:
                alpha = max(alpha, entry_score)
            elif entry_flag == TT_UPPER:
                beta = min(beta, entry_score)
            if alpha >= beta:
                return entry_score

        valid_moves = gs.getValidMoves()

        if depth == 0 or not valid_moves or gs.checkmate or gs.noValidMoves:
            if not valid_moves or gs.checkmate or gs.noValidMoves:
                return color * self._terminal_white_score(gs, ply)
            return color * self._evaluate_position(gs)

        best_score = -INFINITY
        best_move_id = None

        tt_move_id = tt_entry[3] if tt_entry else None
        ordered_moves = self._order_moves(valid_moves, ply, tt_move_id)

        for move in ordered_moves:
            gs.makeMove(move)
            zb.updateHashKey(move, gs)

            score = -self._alpha_beta(gs, depth - 1, -beta, -alpha, -color, ply + 1, zb, deadline)

            zb.undoHashKey(gs.moveLog[-1], gs)
            gs.undoMove()

            if score > best_score:
                best_score = score
                best_move_id = move.moveID

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Store quiet cutoffs for killer/history heuristics.
                if move.pieceCaptured == 0 and not move.isEnPassantMove and not move.isPawnPromotion:
                    self._record_killer(ply, move.moveID)
                    self.history_scores[move.moveID] = self.history_scores.get(move.moveID, 0) + depth * depth
                break

        entry_flag = TT_EXACT
        if best_score <= alpha_original:
            entry_flag = TT_UPPER
        elif best_score >= beta:
            entry_flag = TT_LOWER

        self.transposition_table[key] = (depth, best_score, entry_flag, best_move_id)
        return best_score

    def _evaluate_position(self, gs):
        """Evaluation from white perspective. Positive means white is better."""
        white_positions = self._pawn_positions(gs.whiteBoard)
        black_positions = self._pawn_positions(gs.blackBoard)

        material = (len(white_positions) - len(black_positions)) * 130
        scoreboard_component = (gs.whiteScoreBoard - gs.blackScoreBoard) * 22

        white_adv = sum(7 - row for row, _ in white_positions)
        black_adv = sum(row for row, _ in black_positions)
        advancement = (white_adv - black_adv) * 9

        white_passed = self._count_passed_pawns(white_positions, black_positions, True)
        black_passed = self._count_passed_pawns(black_positions, white_positions, False)
        passed_pawns = (white_passed - black_passed) * 34

        white_connected = self._count_connected_pawns(white_positions)
        black_connected = self._count_connected_pawns(black_positions)
        connected = (white_connected - black_connected) * 12

        white_promo_threat = self._promotion_threat_score(white_positions, gs.blackBoard, True)
        black_promo_threat = self._promotion_threat_score(black_positions, gs.whiteBoard, False)
        promotion_threat = (white_promo_threat - black_promo_threat) * 70

        white_progress = self._flag_progress(white_positions, True)
        black_progress = self._flag_progress(black_positions, False)
        flag_progress = (white_progress - black_progress) * 18

        mobility = self._mobility_score(gs)

        return (material + scoreboard_component + advancement + passed_pawns + connected
                + promotion_threat + flag_progress + mobility)

    def _mobility_score(self, gs):
        # Mobility is measured as legal move count difference, while preserving original state fields.
        original_turn = gs.whiteToMove
        original_en_passant = gs.enPassantPossible
        original_checkmate = gs.checkmate
        original_no_valid_moves = gs.noValidMoves

        white_mobility = 0
        black_mobility = 0
        try:
            gs.whiteToMove = True
            white_mobility = len(gs.getValidMoves())
            gs.whiteToMove = False
            black_mobility = len(gs.getValidMoves())
        finally:
            gs.whiteToMove = original_turn
            gs.enPassantPossible = original_en_passant
            gs.checkmate = original_checkmate
            gs.noValidMoves = original_no_valid_moves

        return (white_mobility - black_mobility) * 6

    def _terminal_white_score(self, gs, ply):
        # If no legal move/checkmate for side to move, that side loses in this variant.
        if gs.whiteToMove:
            return -WIN_SCORE + ply
        return WIN_SCORE - ply

    def _order_moves(self, valid_moves, ply, tt_move_id=None):
        def score_move(move):
            score = 0

            if tt_move_id is not None and move.moveID == tt_move_id:
                score += 1_000_000

            if move.isPawnPromotion:
                score += 500_000

            if move.pieceCaptured != 0 or move.isEnPassantMove:
                score += 220_000
                score += int(move.moveRate or 0) * 50

            killers = self.killer_moves[ply] if ply < len(self.killer_moves) else [None, None]
            if move.moveID == killers[0]:
                score += 140_000
            elif move.moveID == killers[1]:
                score += 120_000

            score += self.history_scores.get(move.moveID, 0)
            score += int(move.moveRate or 0)
            return score

        return sorted(valid_moves, key=score_move, reverse=True)

    def _choose_move_by_difficulty(self, best_move, scored_moves, settings):
        if not scored_moves or settings["top_n"] <= 1:
            return best_move

        top_n = min(settings["top_n"], len(scored_moves))
        if random.random() >= settings["randomness"]:
            return best_move

        # Pick among top-N weighted by score rank to keep play plausible at lower difficulties.
        pool = [move for _, move in scored_moves[:top_n]]
        weights = list(range(top_n, 0, -1))
        return random.choices(pool, weights=weights, k=1)[0]

    def _record_killer(self, ply, move_id):
        if ply >= len(self.killer_moves):
            return
        first, second = self.killer_moves[ply]
        if move_id == first:
            return
        self.killer_moves[ply][1] = first
        self.killer_moves[ply][0] = move_id

    def _tt_key(self, zb, gs):
        # Include side-to-move so opposite turns do not collide.
        return (zb.Hash << 1) ^ (1 if gs.whiteToMove else 0)

    def _sync_zobrist(self, gs, zb):
        # Rebuild hash for current board using existing Zobrist table/state.
        current = 0
        for row in range(8):
            for col in range(8):
                idx = row * 8 + col
                if gs.whiteBoard[idx] == 1:
                    current ^= zb.Table[row][col][2]
                elif gs.blackBoard[idx] == 1:
                    current ^= zb.Table[row][col][1]
        zb.Hash = current

    def _check_timeout(self, deadline):
        if deadline is not None and time.perf_counter() > deadline:
            raise SearchTimeout()

    def _pawn_positions(self, board):
        positions = []
        for idx in range(64):
            if board[idx] == 1:
                positions.append((idx // 8, idx % 8))
        return positions

    def _count_connected_pawns(self, positions):
        pos_set = set(positions)
        connected = 0
        for row, col in positions:
            if (row, col - 1) in pos_set or (row, col + 1) in pos_set:
                connected += 1
        return connected

    def _count_passed_pawns(self, own_positions, enemy_positions, own_is_white):
        enemy_set = set(enemy_positions)
        passed = 0
        for row, col in own_positions:
            blocked = False
            files = [f for f in (col - 1, col, col + 1) if 0 <= f < 8]
            if own_is_white:
                rows = range(row - 1, -1, -1)
            else:
                rows = range(row + 1, 8)
            for r in rows:
                for f in files:
                    if (r, f) in enemy_set:
                        blocked = True
                        break
                if blocked:
                    break
            if not blocked:
                passed += 1
        return passed

    def _promotion_threat_score(self, own_positions, enemy_board, own_is_white):
        threat = 0
        for row, col in own_positions:
            if own_is_white and row == 1:
                if enemy_board[(row - 1) * 8 + col] == 0:
                    threat += 1
                if col > 0 and enemy_board[(row - 1) * 8 + (col - 1)] == 1:
                    threat += 1
                if col < 7 and enemy_board[(row - 1) * 8 + (col + 1)] == 1:
                    threat += 1
            elif not own_is_white and row == 6:
                if enemy_board[(row + 1) * 8 + col] == 0:
                    threat += 1
                if col > 0 and enemy_board[(row + 1) * 8 + (col - 1)] == 1:
                    threat += 1
                if col < 7 and enemy_board[(row + 1) * 8 + (col + 1)] == 1:
                    threat += 1
        return threat

    def _flag_progress(self, positions, own_is_white):
        if not positions:
            return -8
        distances = []
        for row, _ in positions:
            distance = row if own_is_white else (7 - row)
            distances.append(distance)
        return 8 - min(distances)

    def firstMoveFromMoveOrdering(self, validMoves):
        validMoves = sorted(validMoves, key=lambda x: x.moveRate if x.moveRate is not None else 0, reverse=True)
        return validMoves[0] if validMoves else None

    def _get_settings(self, difficulty):
        if not isinstance(difficulty, str):
            return DIFFICULTY_SETTINGS["moderate"]
        return DIFFICULTY_SETTINGS.get(difficulty.lower(), DIFFICULTY_SETTINGS["moderate"])


_DEFAULT_AGENT = Agent()


def find_best_move(gs, valid_moves, difficulty="moderate"):
    """Module-level convenience API requested by the game integration."""
    return _DEFAULT_AGENT.find_best_move(gs, valid_moves, difficulty)
