'''
This is our main driver file.
It handles gameplay orchestration while application.py owns rendering/UI concerns.
'''
import pygame as p

import smartMoveFinder, FlagsEngine, application, Zobrist, progression
from multiprocessing import Queue, Process


BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSTION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSTION  # 64
MAX_FPS = 30
IMAGES = {}


def loadImages():
    IMAGES['wP'] = p.transform.scale(p.image.load("images/wP.png"), (SQ_SIZE, SQ_SIZE))
    IMAGES['bP'] = p.transform.scale(p.image.load("images/bP.png"), (SQ_SIZE, SQ_SIZE))


'''
The main driver for our code. This keeps game rules/engine untouched and delegates UI to application.GameUI.
'''
# if a human is playing white, then playerOne will be True. If an AI is playing, then it will be False
# playerTwo as above but for black
def main(t, playerOne, playerTwo, setup=None, difficulty="Moderate", language="en", progression_mgr=None):
    p.init()
    p.display.set_caption(application.t(language, "two_flags"))
    moveLog = []
    Round = 0
    timer_font = p.font.SysFont('Consolas', 30)
    moveLogFont = p.font.SysFont("Arial", 12, False, False)
    clock = p.time.Clock()

    loadImages()
    ui = application.GameUI(BOARD_WIDTH, BOARD_HEIGHT, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT,
                            SQ_SIZE, DIMENSTION, IMAGES, language=language)
    min_window_w = ui.total_width
    min_window_h = ui.total_height
    screen = p.display.set_mode((min_window_w, min_window_h), p.RESIZABLE)
    game_surface = p.Surface((ui.total_width, ui.total_height))

    gs = FlagsEngine.GameState()
    gs.setTimer(t)
    if setup is not None:
        gs.setBoard(setup)

    validMoves = gs.getValidMoves()
    moveMade = False
    animate = False
    running = True
    sqSelected = ()
    playerClicks = []
    gameOver = False
    gameOverMessage = ""
    whiteTurn = bool(gs.whiteToMove)
    zb = Zobrist.zobrist()
    zb.computeHash(gs.whiteBoard, gs.blackBoard)
    AIThinking = False
    moveFinderProcess = None
    moveUndone = None
    agent = smartMoveFinder.Agent()
    coach_enabled = False
    coach_best_move = "--"
    coach_grade = "--"
    coach_explanation = _msg(language, "coach_press_c")
    coach_status = _msg(language, "coach_controls")
    last_player_context = None
    last_human_move_ply = None
    coach_xp_net = 0
    analyzed_player_plies = set()
    progression_result = None
    progression_applied = False

    is_human_vs_ai = (playerOne != playerTwo)
    human_is_white = playerOne and not playerTwo
    human_is_black = playerTwo and not playerOne

    mins, secs = divmod(int(gs.whiteTimer), 60)
    gs.textWhiteTimer = '{:02d}:{:02d}'.format(mins, secs)
    mins, secs = divmod(int(gs.blackTimer), 60)
    gs.textBlackTimer = '{:02d}:{:02d}'.format(mins, secs)

    def reset_game_state():
        nonlocal gs, validMoves, sqSelected, playerClicks, moveMade, gameOver, gameOverMessage
        nonlocal AIThinking, moveUndone, whiteTurn, zb
        nonlocal coach_best_move, coach_grade, coach_explanation, coach_status, last_player_context, last_human_move_ply
        nonlocal coach_xp_net, analyzed_player_plies, progression_result, progression_applied
        gs = FlagsEngine.GameState()
        gs.setTimer(t)
        if setup is not None:
            gs.setBoard(setup)
        validMoves = gs.getValidMoves()
        sqSelected = ()
        playerClicks = []
        gs.moveLog = []
        moveMade = True
        gameOver = False
        gameOverMessage = ""
        if AIThinking and moveFinderProcess is not None:
            moveFinderProcess.terminate()
            AIThinking = False
        moveUndone = True
        whiteTurn = bool(gs.whiteToMove)
        zb = Zobrist.zobrist()
        zb.computeHash(gs.whiteBoard, gs.blackBoard)
        coach_best_move = "--"
        coach_grade = "--"
        coach_explanation = _msg(language, "coach_after_move")
        coach_status = _msg(language, "coach_reset")
        last_player_context = None
        last_human_move_ply = None
        coach_xp_net = 0
        analyzed_player_plies = set()
        progression_result = None
        progression_applied = False

    def switch_language(new_language):
        nonlocal language, coach_status, coach_explanation, coach_grade, gameOverMessage
        if new_language == language:
            return
        language = new_language
        ui.language = new_language
        p.display.set_caption(application.t(new_language, "two_flags"))
        coach_grade = _translate_grade(coach_grade, new_language)
        if coach_status:
            coach_status = _msg(new_language, "coach_enabled") if coach_enabled else _msg(new_language, "coach_disabled")
        if coach_explanation:
            coach_explanation = _msg(new_language, "coach_enabled_explain") if coach_enabled else _msg(new_language, "coach_press_c")
        if gameOver:
            if gs.blackTimer <= 0:
                gameOverMessage = _msg(new_language, "white_wins_time")
            elif gs.whiteTimer <= 0:
                gameOverMessage = _msg(new_language, "black_wins_time")
            elif gs.checkmate:
                gameOverMessage = _msg(new_language, "black_wins_promo") if gs.whiteToMove else _msg(new_language, "white_wins_promo")
            elif gs.noValidMoves:
                gameOverMessage = (_msg(new_language, "black_wins_no_moves")
                                   if gs.whiteToMove else _msg(new_language, "white_wins_no_moves"))

    def coach_best_move_and_score_safe():
        """
        Defensive wrapper: coach search must never alter live game state.
        If anything changes unexpectedly, restore from snapshot.
        """
        snapshot = {
            "whiteBoard": gs.whiteBoard.copy(),
            "blackBoard": gs.blackBoard.copy(),
            "whiteToMove": gs.whiteToMove,
            "enPassantPossible": gs.enPassantPossible,
            "whiteScoreBoard": gs.whiteScoreBoard,
            "blackScoreBoard": gs.blackScoreBoard,
            "moveLog": gs.moveLog.copy(),
            "checkmate": gs.checkmate,
            "noValidMoves": gs.noValidMoves,
        }
        best_move, best_score = agent.best_move_and_score(gs, validMoves, difficulty)

        state_changed = (
            gs.whiteBoard != snapshot["whiteBoard"] or
            gs.blackBoard != snapshot["blackBoard"] or
            gs.whiteToMove != snapshot["whiteToMove"] or
            gs.enPassantPossible != snapshot["enPassantPossible"] or
            gs.whiteScoreBoard != snapshot["whiteScoreBoard"] or
            gs.blackScoreBoard != snapshot["blackScoreBoard"] or
            len(gs.moveLog) != len(snapshot["moveLog"]) or
            gs.checkmate != snapshot["checkmate"] or
            gs.noValidMoves != snapshot["noValidMoves"]
        )
        if state_changed:
            gs.whiteBoard = snapshot["whiteBoard"]
            gs.blackBoard = snapshot["blackBoard"]
            gs.whiteToMove = snapshot["whiteToMove"]
            gs.enPassantPossible = snapshot["enPassantPossible"]
            gs.whiteScoreBoard = snapshot["whiteScoreBoard"]
            gs.blackScoreBoard = snapshot["blackScoreBoard"]
            gs.moveLog = snapshot["moveLog"]
            gs.checkmate = snapshot["checkmate"]
            gs.noValidMoves = snapshot["noValidMoves"]
        return best_move, best_score

    def viewport_offset():
        win_w, win_h = screen.get_size()
        return max(0, (win_w - ui.total_width) // 2), max(0, (win_h - ui.total_height) // 2)

    def to_local(pos, offset):
        return pos[0] - offset[0], pos[1] - offset[1]

    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        offset = viewport_offset()

        if AIThinking or humanTurn:
            if whiteTurn:
                mins, secs = divmod(int(gs.whiteTimer), 60)
                gs.textWhiteTimer = '{:02d}:{:02d}'.format(mins, secs)
                gs.whiteTimer -= 1 / MAX_FPS
            else:
                mins, secs = divmod(int(gs.blackTimer), 60)
                gs.textBlackTimer = '{:02d}:{:02d}'.format(mins, secs)
                gs.blackTimer -= 1 / MAX_FPS

        for e in p.event.get():
            if e.type == p.QUIT:
                if AIThinking and moveFinderProcess is not None:
                    moveFinderProcess.terminate()
                return "quit"
            if e.type == p.VIDEORESIZE:
                # Keep minimum size equal to designed board/panels to avoid layout overlap.
                new_w = max(min_window_w, e.w)
                new_h = max(min_window_h, e.h)
                screen = p.display.set_mode((new_w, new_h), p.RESIZABLE)
                continue

            elif e.type == p.MOUSEBUTTONDOWN:
                local_pos = to_local(e.pos, offset)
                if local_pos[0] < 0 or local_pos[1] < 0 or local_pos[0] >= ui.total_width or local_pos[1] >= ui.total_height:
                    continue

                if ui.lang_en_button.contains(local_pos):
                    switch_language("en")
                    continue
                if ui.lang_ar_button.contains(local_pos):
                    switch_language("ar")
                    continue

                if gameOver:
                    if ui.over_restart_button.contains(local_pos):
                        reset_game_state()
                    elif ui.over_menu_button.contains(local_pos):
                        if AIThinking and moveFinderProcess is not None:
                            moveFinderProcess.terminate()
                        return "menu"
                    continue

                if ui.restart_button.contains(local_pos):
                    reset_game_state()
                    continue
                if ui.menu_button.contains(local_pos):
                    if AIThinking and moveFinderProcess is not None:
                        moveFinderProcess.terminate()
                    return "menu"
                if ui.coach_hint_button.contains(local_pos):
                    if not coach_enabled:
                        coach_status = _msg(language, "coach_off")
                    elif not humanTurn:
                        coach_status = _msg(language, "coach_hint_turn")
                    else:
                        hint_move, _ = coach_best_move_and_score_safe()
                        coach_best_move = _format_move(hint_move)
                        coach_grade = "--"
                        coach_explanation = _msg(language, "coach_hint_text")
                        coach_status = _msg(language, "coach_hint_ready")
                    continue
                if ui.coach_analyze_button.contains(local_pos):
                    if not coach_enabled:
                        coach_status = _msg(language, "coach_off")
                    elif last_player_context is None:
                        coach_status = _msg(language, "coach_play_then_analyze")
                    else:
                        loss = max(0.0, last_player_context["best_score"] - last_player_context["after_score"])
                        coach_grade = _grade_from_loss(loss, language)
                        coach_best_move = _format_move(last_player_context["best_move"])
                        coach_explanation = _explanation(last_player_context, coach_grade, language)
                        coach_status = _msg(language, "coach_analysis_done").format(loss=loss)
                        if last_human_move_ply is not None and last_human_move_ply not in analyzed_player_plies:
                            analyzed_player_plies.add(last_human_move_ply)
                            coach_xp_net += _coach_bonus_from_grade(coach_grade, language)
                    continue
                if ui.coach_try_again_button.contains(local_pos):
                    if last_human_move_ply is None:
                        coach_status = _msg(language, "coach_no_move_undo")
                        continue
                    if AIThinking and moveFinderProcess is not None:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    while len(gs.moveLog) >= last_human_move_ply and gs.moveLog:
                        zb.undoHashKey(gs.moveLog[-1], gs)
                        gs.undoMove()
                        whiteTurn = not whiteTurn
                    validMoves = gs.getValidMoves()
                    moveLog = gs.moveLog.copy()
                    moveMade = True
                    animate = False
                    moveUndone = True
                    gameOver = False
                    gameOverMessage = ""
                    coach_grade = "--"
                    coach_best_move = "--"
                    coach_explanation = _msg(language, "coach_try_again_done")
                    coach_status = _msg(language, "coach_try_again_status")
                    last_player_context = None
                    last_human_move_ply = None
                    coach_xp_net = 0
                    analyzed_player_plies = set()
                    continue

                col = local_pos[0] // SQ_SIZE
                row = local_pos[1] // SQ_SIZE
                if sqSelected == (row, col) or col >= 8:
                    sqSelected = ()
                    playerClicks = []
                else:
                    sqSelected = (row, col)
                    playerClicks.append(sqSelected)
                if len(playerClicks) == 2 and humanTurn:
                    move = FlagsEngine.Move(playerClicks[0], playerClicks[1], gs.whiteBoard, gs.blackBoard,
                                            whiteToMove=gs.whiteToMove)
                    chosen_move = None
                    for i in range(len(validMoves)):
                        if move == validMoves[i]:
                            chosen_move = validMoves[i]
                            break
                    if chosen_move is not None:
                        context = None
                        if coach_enabled:
                            best_move, best_score = coach_best_move_and_score_safe()
                            context = {
                                "best_move": best_move,
                                "best_score": best_score,
                                "player_is_white": gs.whiteToMove,
                                "best_is_capture": bool(best_move and (best_move.pieceCaptured != 0 or best_move.isEnPassantMove)),
                            }
                        gs.makeMove(chosen_move)
                        if coach_enabled and context is not None:
                            white_eval = agent.evaluate_position(gs)
                            after_score = white_eval if context["player_is_white"] else -white_eval
                            opponent_moves = gs.getValidMoves()
                            last_player_context = {
                                "best_move": context["best_move"],
                                "best_score": context["best_score"],
                                "after_score": after_score,
                                "player_move": chosen_move,
                                "player_is_white": context["player_is_white"],
                                "best_is_capture": context["best_is_capture"],
                                "player_captured": (chosen_move.pieceCaptured != 0 or chosen_move.isEnPassantMove),
                                "opponent_has_capture": any(m.pieceCaptured != 0 or m.isEnPassantMove for m in opponent_moves),
                                "opponent_has_promo": any(m.isPawnPromotion for m in opponent_moves),
                            }
                            last_human_move_ply = len(gs.moveLog)
                            coach_best_move = _format_move(context["best_move"])
                            coach_grade = "--"
                            coach_explanation = _msg(language, "coach_press_analyze")
                            coach_status = _msg(language, "coach_move_recorded")
                        whiteTurn = not whiteTurn
                        moveLog = gs.moveLog.copy()
                        moveMade = True
                        animate = True
                        sqSelected = ()
                        playerClicks = []
                    if not moveMade:
                        playerClicks = [sqSelected]

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z and gs.moveLog:
                    zb.undoHashKey(gs.moveLog[-1], gs)
                    gs.undoMove()
                    whiteTurn = not whiteTurn
                    moveLog = gs.moveLog.copy()
                    moveMade = True
                    animate = False
                    gameOver = False
                    gameOverMessage = ""
                    if AIThinking and moveFinderProcess is not None:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                    last_player_context = None
                    last_human_move_ply = None
                    coach_xp_net = 0
                    analyzed_player_plies = set()
                    coach_grade = "--"
                    coach_explanation = _msg(language, "coach_undo_play_new")

                if e.key == p.K_r:
                    reset_game_state()
                if e.key == p.K_ESCAPE:
                    if AIThinking and moveFinderProcess is not None:
                        moveFinderProcess.terminate()
                    return "menu"
                if e.key == p.K_c:
                    coach_enabled = not coach_enabled
                    if coach_enabled:
                        coach_status = _msg(language, "coach_enabled")
                        coach_explanation = _msg(language, "coach_enabled_explain")
                    else:
                        coach_status = _msg(language, "coach_disabled")
                        coach_explanation = _msg(language, "coach_press_c")

        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                Round += 1
                AIThinking = True
                print("Thinking... Round", Round)
                returnQueue = Queue()
                moveFinderProcess = Process(
                    target=agent.findBestMove,
                    args=(gs, validMoves, zb, returnQueue, difficulty)
                )
                moveFinderProcess.start()

            if moveFinderProcess is not None and not moveFinderProcess.is_alive():
                AIMove = returnQueue.get()
                if AIMove is None:
                    AIMove = agent.firstMoveFromMoveOrdering(validMoves)
                    print("i think i will lose.. so i picked the first you ordered for me")
                    print(AIMove.getFlagsNotation() + "----->rating of the move: " + str(AIMove.moveRate))
                else:
                    print(AIMove.getFlagsNotation() + "----->rating of the move: " + str(AIMove.moveRate))
                gs.makeMove(AIMove)
                whiteTurn = not whiteTurn
                moveLog = gs.moveLog.copy()
                moveMade = True
                animate = True
                AIThinking = False

        mouse_local = to_local(p.mouse.get_pos(), offset)
        game_surface.fill((246, 248, 251))
        ui.draw_game_state(game_surface, moveLog, gs, validMoves, sqSelected, moveLogFont)
        ui.draw_side_panel(game_surface, timer_font, gs.textWhiteTimer, gs.textBlackTimer,
                           progression_data=_progression_ui_data(progression_mgr, difficulty), mouse_pos=mouse_local)
        ui.draw_coach_panel(game_surface, {
            "enabled": coach_enabled,
            "best_move": coach_best_move,
            "grade": coach_grade,
            "explanation": coach_explanation,
            "status": coach_status,
        }, mouse_pos=mouse_local)

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, game_surface, gs, clock, ui, offset)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        if not gameOver:
            if gs.blackTimer <= 0:
                gameOver = True
                gameOverMessage = _msg(language, "white_wins_time")
            elif gs.whiteTimer <= 0:
                gameOver = True
                gameOverMessage = _msg(language, "black_wins_time")
            elif gs.checkmate and not AIThinking:
                gameOver = True
                gameOverMessage = _msg(language, "black_wins_promo") if gs.whiteToMove else _msg(language, "white_wins_promo")
            elif gs.noValidMoves and not AIThinking:
                gameOver = True
                gameOverMessage = (_msg(language, "black_wins_no_moves")
                                   if gs.whiteToMove else _msg(language, "white_wins_no_moves"))

            if gameOver and progression_mgr is not None and is_human_vs_ai and not progression_applied:
                winner_is_white = not gs.whiteToMove if (gs.checkmate or gs.noValidMoves) else (gs.blackTimer <= 0)
                human_won = (winner_is_white and human_is_white) or ((not winner_is_white) and human_is_black)
                progression_result = progression_mgr.apply_game_result(
                    difficulty=difficulty,
                    human_won=human_won,
                    coach_bonus_points=coach_xp_net,
                )
                progression_applied = True

        if gameOver:
            ui.draw_game_over(game_surface, gameOverMessage, progression_result=progression_result, mouse_pos=mouse_local)

        screen.fill((32, 40, 50))
        screen.blit(game_surface, offset)
        p.event.pump()
        clock.tick(MAX_FPS)
        p.display.flip()

    return "quit"


def animateMove(move, screen, game_surface, gs, clock, ui, offset):
    coords = []
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR * frame / frameCount, move.startCol + dC * frame / frameCount)
        game_surface.fill((246, 248, 251))
        ui._draw_board(game_surface)
        ui._draw_pieces(game_surface, gs)
        color = ui.colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(game_surface, color, endSquare)
        if move.pieceCaptured != 0:
            game_surface.blit(IMAGES[move.pieceCaptured], endSquare)
        game_surface.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        screen.fill((32, 40, 50))
        screen.blit(game_surface, offset)
        p.display.flip()
        clock.tick(60)


def _format_move(move):
    if move is None:
        return "--"
    notation = move.getFlagsNotation()
    if len(notation) == 4:
        return notation[:2] + " -> " + notation[2:]
    return notation


def _grade_from_loss(loss, language="en"):
    """
    Loss thresholds are in pawn units.
    Internal engine score is scaled by 100, so coach compares normalized values.
    """
    if loss <= 0.1:
        return _msg(language, "grade_best")
    if loss <= 0.5:
        return _msg(language, "grade_good")
    if loss <= 1.2:
        return _msg(language, "grade_inaccuracy")
    if loss <= 2.5:
        return _msg(language, "grade_mistake")
    return _msg(language, "grade_blunder")


def _explanation(ctx, grade, language="en"):
    move = ctx["player_move"]
    advanced = (move.endRow < move.startRow) if ctx["player_is_white"] else (move.endRow > move.startRow)

    bad = {_msg(language, "grade_inaccuracy"), _msg(language, "grade_mistake"), _msg(language, "grade_blunder")}
    good = {_msg(language, "grade_best"), _msg(language, "grade_good")}
    if ctx["opponent_has_promo"] and grade in {_msg(language, "grade_mistake"), _msg(language, "grade_blunder")}:
        return _msg(language, "exp_flag_threat")
    if ctx["best_is_capture"] and not ctx["player_captured"]:
        return _msg(language, "exp_missed_capture")
    if ctx["opponent_has_capture"] and grade in bad:
        return _msg(language, "exp_allowed_capture")
    if ctx["player_captured"] and grade in good:
        return _msg(language, "exp_good_capture")
    if advanced and grade in good:
        return _msg(language, "exp_advancement")
    if not ctx["opponent_has_capture"] and grade in good:
        return _msg(language, "exp_defense")

    neutral_templates = {
        _msg(language, "grade_best"): _msg(language, "exp_best"),
        _msg(language, "grade_good"): _msg(language, "exp_good"),
        _msg(language, "grade_inaccuracy"): _msg(language, "exp_inaccuracy"),
        _msg(language, "grade_mistake"): _msg(language, "exp_mistake"),
        _msg(language, "grade_blunder"): _msg(language, "exp_blunder"),
    }
    return neutral_templates.get(grade, _msg(language, "exp_generic"))


MESSAGES = {
    "en": {
        "coach_press_c": "Press C to enable Coach Mode.",
        "coach_controls": "Hint / Analyze / Try Again",
        "coach_after_move": "Play a move then press Analyze.",
        "coach_reset": "Coach reset.",
        "coach_off": "Coach is OFF. Press C to enable.",
        "coach_hint_turn": "Hint is available on your turn.",
        "coach_hint_text": "This is the best move in this position.",
        "coach_hint_ready": "Hint ready.",
        "coach_play_then_analyze": "Play a move first, then press Analyze.",
        "coach_analysis_done": "Analysis done (loss={loss:.2f}).",
        "coach_no_move_undo": "No player move available to undo.",
        "coach_try_again_done": "Move undone. Try a better plan.",
        "coach_try_again_status": "Try Again complete.",
        "coach_press_analyze": "Press Analyze to grade your move.",
        "coach_move_recorded": "Move recorded for coach review.",
        "coach_undo_play_new": "Undone. Play a new move then Analyze.",
        "coach_enabled": "Coach enabled. Use Hint or Analyze.",
        "coach_enabled_explain": "Coach is on. Play a move then Analyze.",
        "coach_disabled": "Coach disabled.",
        "white_wins_time": "White wins by time",
        "black_wins_time": "Black wins by time",
        "white_wins_promo": "White wins by promotion",
        "black_wins_promo": "Black wins by promotion",
        "white_wins_no_moves": "White wins, black has no available move",
        "black_wins_no_moves": "Black wins, white has no available move",
        "grade_best": "Best",
        "grade_good": "Good",
        "grade_inaccuracy": "Inaccuracy",
        "grade_mistake": "Mistake",
        "grade_blunder": "Blunder",
        "exp_flag_threat": "This move allowed a fast flag threat.",
        "exp_missed_capture": "You missed an important capture opportunity.",
        "exp_allowed_capture": "This move left your pawn open to capture.",
        "exp_good_capture": "Strong capture that improved your position.",
        "exp_advancement": "Good advancement toward promotion pressure.",
        "exp_defense": "Solid defensive move that reduced opponent threats.",
        "exp_best": "Excellent move aligned with the top engine plan.",
        "exp_good": "Good move that keeps your position healthy.",
        "exp_inaccuracy": "Playable move, but there was a more accurate option.",
        "exp_mistake": "This move weakened your position noticeably.",
        "exp_blunder": "Major error; re-check tactical threats first.",
        "exp_generic": "Look for safer moves with better pawn coordination.",
    },
    "ar": {
        "coach_press_c": "اضغط C لتفعيل وضع المدرب.",
        "coach_controls": "تلميح / تحليل / حاول مرة أخرى",
        "coach_after_move": "العب نقلة ثم اضغط تحليل.",
        "coach_reset": "تمت إعادة ضبط المدرب.",
        "coach_off": "وضع المدرب غير مفعل. اضغط C للتفعيل.",
        "coach_hint_turn": "التلميح متاح فقط في دورك.",
        "coach_hint_text": "هذه أفضل نقلة مقترحة في هذا الموقف.",
        "coach_hint_ready": "تم تجهيز التلميح.",
        "coach_play_then_analyze": "العب نقلة أولًا ثم اضغط تحليل.",
        "coach_analysis_done": "اكتمل التحليل (الخسارة={loss:.2f}).",
        "coach_no_move_undo": "لا توجد نقلة لاعب للتراجع عنها.",
        "coach_try_again_done": "تم التراجع عن النقلة. جرّب خطة أفضل.",
        "coach_try_again_status": "تم تنفيذ حاول مرة أخرى.",
        "coach_press_analyze": "اضغط تحليل لتقييم نقلتك.",
        "coach_move_recorded": "تم حفظ النقلة لمراجعة المدرب.",
        "coach_undo_play_new": "تم التراجع. العب نقلة جديدة ثم حلّل.",
        "coach_enabled": "تم تفعيل المدرب. استخدم تلميح أو تحليل.",
        "coach_enabled_explain": "وضع المدرب مفعل. العب نقلة ثم اضغط تحليل.",
        "coach_disabled": "تم إيقاف وضع المدرب.",
        "white_wins_time": "فاز الأبيض بانتهاء الوقت",
        "black_wins_time": "فاز الأسود بانتهاء الوقت",
        "white_wins_promo": "فاز الأبيض بالترقية",
        "black_wins_promo": "فاز الأسود بالترقية",
        "white_wins_no_moves": "فاز الأبيض لأن الأسود بلا نقلات متاحة",
        "black_wins_no_moves": "فاز الأسود لأن الأبيض بلا نقلات متاحة",
        "grade_best": "الأفضل",
        "grade_good": "جيد",
        "grade_inaccuracy": "عدم دقة",
        "grade_mistake": "خطأ",
        "grade_blunder": "خطأ فادح",
        "exp_flag_threat": "هذه النقلة سمحت بتهديد سريع للراية.",
        "exp_missed_capture": "فوتّ فرصة مهمة لأخذ بيدق.",
        "exp_allowed_capture": "النقلة تركت بيدقك مكشوفًا للأخذ.",
        "exp_good_capture": "أخذ قوي حسّن موقفك في الرقعة.",
        "exp_advancement": "تقدم جيد نحو ضغط الترقية.",
        "exp_defense": "نقلة دفاعية قوية قللت تهديدات الخصم.",
        "exp_best": "نقلة ممتازة ومتوافقة مع أفضل خطة.",
        "exp_good": "نقلة جيدة وتحافظ على توازن موقفك.",
        "exp_inaccuracy": "النقلة مقبولة لكن كان هناك خيار أدق.",
        "exp_mistake": "هذه النقلة أضعفت موقفك بشكل واضح.",
        "exp_blunder": "خطأ كبير؛ راجع التهديدات التكتيكية أولًا.",
        "exp_generic": "ابحث عن نقلات أكثر أمانًا وتنسيقًا.",
    },
}


def _msg(language, key):
    return MESSAGES.get(language, MESSAGES["en"]).get(key, key)


def _translate_grade(current, language):
    if current in ("--", "", None):
        return "--"
    known = {
        "Best": "grade_best",
        "Good": "grade_good",
        "Inaccuracy": "grade_inaccuracy",
        "Mistake": "grade_mistake",
        "Blunder": "grade_blunder",
        "الأفضل": "grade_best",
        "جيد": "grade_good",
        "عدم دقة": "grade_inaccuracy",
        "خطأ": "grade_mistake",
        "خطأ فادح": "grade_blunder",
    }
    key = known.get(current)
    if key is None:
        return current
    return _msg(language, key)


def _coach_bonus_from_grade(grade_label, language):
    good_set = {_msg(language, "grade_best"), _msg(language, "grade_good")}
    blunder = _msg(language, "grade_blunder")
    if grade_label in good_set:
        return 2
    if grade_label == blunder:
        return -1
    return 0


def _progression_ui_data(progression_mgr, difficulty):
    if progression_mgr is None:
        return None
    profile = progression_mgr.profile
    return {
        "username": profile.get("username", "Player"),
        "level": profile.get("level", 1),
        "xp": profile.get("xp", 0),
        "next_level_xp": progression.next_level_xp(profile.get("level", 1)),
        "rating": progression_mgr.current_difficulty_rating(difficulty),
        "difficulty": str(difficulty).lower(),
        "stats": profile.get("stats", {}),
    }


if __name__ == "__main__":
    progression_mgr = progression.Progression()
    while True:
        app = application.startApp(username=progression_mgr.profile.get("username", "Player"))
        app.Begin()
        if app.exit_requested:
            break

        if app.username != progression_mgr.profile.get("username", "Player"):
            progression_mgr.set_username(app.username)

        result = main(
            app.time * 60,
            app.playerOne,
            app.playerTwo,
            app.setup.split(),
            app.difficulty,
            app.language,
            progression_mgr,
        )
        if result != "menu":
            break

    p.quit()
