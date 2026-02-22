'''
This is our main driver file.
It handles gameplay orchestration while application.py owns rendering/UI concerns.
'''
import pygame as p

import smartMoveFinder, FlagsEngine, application, Zobrist
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
def main(t, playerOne, playerTwo, setup=None, difficulty="Moderate"):
    p.init()
    p.display.set_caption("Two-Flags")
    moveLog = []
    Round = 0
    timer_font = p.font.SysFont('Consolas', 30)
    moveLogFont = p.font.SysFont("Arial", 12, False, False)
    clock = p.time.Clock()

    loadImages()
    ui = application.GameUI(BOARD_WIDTH, BOARD_HEIGHT, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT,
                            SQ_SIZE, DIMENSTION, IMAGES)
    screen = p.display.set_mode((ui.total_width, ui.total_height))

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

    mins, secs = divmod(int(gs.whiteTimer), 60)
    gs.textWhiteTimer = '{:02d}:{:02d}'.format(mins, secs)
    mins, secs = divmod(int(gs.blackTimer), 60)
    gs.textBlackTimer = '{:02d}:{:02d}'.format(mins, secs)

    def reset_game_state():
        nonlocal gs, validMoves, sqSelected, playerClicks, moveMade, gameOver, gameOverMessage
        nonlocal AIThinking, moveUndone, whiteTurn, zb
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

    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

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

            elif e.type == p.MOUSEBUTTONDOWN:
                if gameOver:
                    if ui.over_restart_button.contains(e.pos):
                        reset_game_state()
                    elif ui.over_menu_button.contains(e.pos):
                        if AIThinking and moveFinderProcess is not None:
                            moveFinderProcess.terminate()
                        return "menu"
                    continue

                if ui.restart_button.contains(e.pos):
                    reset_game_state()
                    continue
                if ui.menu_button.contains(e.pos):
                    if AIThinking and moveFinderProcess is not None:
                        moveFinderProcess.terminate()
                    return "menu"

                location = p.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                if sqSelected == (row, col) or col >= 8:
                    sqSelected = ()
                    playerClicks = []
                else:
                    sqSelected = (row, col)
                    playerClicks.append(sqSelected)
                if len(playerClicks) == 2 and humanTurn:
                    move = FlagsEngine.Move(playerClicks[0], playerClicks[1], gs.whiteBoard, gs.blackBoard,
                                            whiteToMove=gs.whiteToMove)
                    for i in range(len(validMoves)):
                        if move == validMoves[i]:
                            gs.makeMove(validMoves[i])
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

                if e.key == p.K_r:
                    reset_game_state()
                if e.key == p.K_ESCAPE:
                    if AIThinking and moveFinderProcess is not None:
                        moveFinderProcess.terminate()
                    return "menu"

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

        screen.fill((246, 248, 251))
        ui.draw_game_state(screen, moveLog, gs, validMoves, sqSelected, moveLogFont)
        ui.draw_side_panel(screen, timer_font, gs.textWhiteTimer, gs.textBlackTimer)

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs, clock, ui)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        if not gameOver:
            if gs.blackTimer <= 0:
                gameOver = True
                gameOverMessage = 'White wins by time'
            elif gs.whiteTimer <= 0:
                gameOver = True
                gameOverMessage = 'Black wins by time'
            elif gs.checkmate and not AIThinking:
                gameOver = True
                gameOverMessage = 'Black wins by promotion' if gs.whiteToMove else 'White wins by promotion'
            elif gs.noValidMoves and not AIThinking:
                gameOver = True
                gameOverMessage = ('Black wins white has no available move'
                                   if gs.whiteToMove else 'White wins black has no available move')

        if gameOver:
            ui.draw_game_over(screen, gameOverMessage)

        p.event.pump()
        clock.tick(MAX_FPS)
        p.display.flip()

    return "quit"


def animateMove(move, screen, gs, clock, ui):
    coords = []
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR * frame / frameCount, move.startCol + dC * frame / frameCount)
        ui._draw_board(screen)
        ui._draw_pieces(screen, gs)
        color = ui.colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        if move.pieceCaptured != 0:
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    while True:
        app = application.startApp()
        app.Begin()
        if app.exit_requested:
            break

        result = main(app.time * 60, app.playerOne, app.playerTwo, app.setup.split(), app.difficulty)
        if result != "menu":
            break

    p.quit()
