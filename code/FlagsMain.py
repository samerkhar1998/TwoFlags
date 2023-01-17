'''
This is our main driver file.
It will be responsible for handling user input and displaying the current GameState object.
'''
import threading
import pygame as p

import smartMoveFinder, FlagsEngine, application, client, Zobrist
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
The main driver for our code.This will handle user input and updating the graphics
'''
# if a human is playing white, then playerOne will be True. If an AI is playing, then it will be False
# playerTwo as above but for black
def main(t, playerOne, playerTwo, setup=None):
    global firstDrawWhileThinking
    firstDrawWhileThinking = False
    print("the setup of the board is : ", setup)
    moveLog = []
    Round = 0
    p.init()
    font = p.font.SysFont('Consolas', 30)
    # timer = MAX_FPS * t * 60
    screen = p.display.set_mode((BOARD_WIDTH + 128 + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    moveLogFont = p.font.SysFont("Arial", 12, False, False)
    clock = p.time.Clock()
    screen.fill(p.Color("white"))

    gs = FlagsEngine.GameState()

    gs.setTimer(t)
    if not setup is None:
        gs.setBoard(setup)
    validMoves = gs.getValidMoves()
    moveMade = False  # flag variable for when a move is made.
    animate = False  # flag variable for when we should animate
    loadImages()
    running = True
    sqSelected = ()  # no square is selected, keep track of the last clicked of the user (tuple:(row,col))
    playerClicks = []  # keep track of player clicks(two tuples:[(6,4),(4,4)])
    gameOver = False
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
                running = False

            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = p.mouse.get_pos()  # (x,y) location of mouse.
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    if sqSelected == (row, col) or col >= 8:  # The user clicked the same square twice
                        sqSelected = ()  # deselect
                        playerClicks = []  # clear player clicks
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)  # append for both 1st and 2nd clicks
                    if len(playerClicks) == 2 and humanTurn:  # after 2nd click
                        # move = FlagsEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        move = FlagsEngine.Move(playerClicks[0], playerClicks[1], gs.whiteBoard, gs.blackBoard,
                                    whiteToMove=gs.whiteToMove)
                        print(move.getFlagsNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                whiteTurn = not whiteTurn

                                moveLog = gs.moveLog.copy()

                                moveMade = True
                                animate = True
                                sqSelected = ()  # reset user clicks.
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            # key handlers
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo when 'z' is pressed
                    zb.undoHashKey(gs.moveLog[-1], gs)
                    gs.undoMove()
                    whiteTurn = not whiteTurn
                    moveLog = gs.moveLog.copy()
                    whiteBoard = gs.whiteBoard.copy()
                    blackBoard = gs.blackBoard.copy()
                    moveMade = True
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                if e.key == p.K_r:  # restart when 'r' is pressed
                    # gs = FlagsEngine.GameState()
                    print("========================")
                    print("Starting a new game !!!!!")
                    gs = FlagsEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    gs.moveLog = []
                    moveMade = True
                    gameOver = False
                    gs.setTimer(t)
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True

        # AI move finder
        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                Round += 1
                AIThinking = True
                print("Thinking...")

                returnQueue = Queue()  # used to pass data between threads
                moveFinderProcess = Process(target=agent.findBestMove, args=(gs, validMoves, zb, returnQueue))
                moveFinderProcess.start()  # call findBestMove(gs, validMoves returnQueue)

            if not moveFinderProcess.is_alive():
                AIMove = returnQueue.get()
                # print("Done thinking and the rate of the move is " + str(AIMove.moveRate))
                if AIMove is None:

                    AIMove = agent.firstMoveFromMoveOrdering(validMoves)
                    print("i think i will lose.. so i picked the first you ordered for me")
                    print(AIMove.getFlagsNotation() + "----->rating of the move: " + str(AIMove.moveRate))
                else:
                    print(AIMove.getFlagsNotation() + "----->rating of the move: " + str(AIMove.moveRate))
                gs.makeMove(AIMove)
                print("evaluation functiion = " , gs.whiteScoreBoard - gs.blackScoreBoard)
                whiteTurn = not whiteTurn
                moveLog = gs.moveLog.copy()

                moveMade = True
                animate = True
                AIThinking = False
        # if not AIThinking:
        screen.fill((255, 255, 255))
        screen.blit(font.render(gs.textBlackTimer, True, (0, 0, 0)), (BOARD_WIDTH + 32, 96))
        screen.blit(font.render(gs.textWhiteTimer, True, (0, 0, 0)), (BOARD_WIDTH + 32, BOARD_HEIGHT - 128))
        drawGameStatet(screen, moveLog, gs, validMoves, sqSelected, moveLogFont, AIThinking)
        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        if gs.blackTimer <= 0:
            drawText(screen, 'White wins by time')
            gameOver = True
        elif gs.whiteTimer <= 0:
            gameOver = True
            drawText(screen, 'Black wins by time')

        if gs.checkmate and not AIThinking:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, 'Black wins by promotion')
            else:
                drawText(screen, 'White wins by promotion')
        elif gs.noValidMoves and not AIThinking:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, 'Black wins white has no available move')
            else:
                drawText(screen, 'White wins black has no available move')

        p.event.pump()
        clock.tick(MAX_FPS)
        p.display.flip()


'''
Highlight square selected and moves for piece selected 
'''


def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected

        if gs.whiteBoard[r * 8 + c] == 1 or gs.blackBoard[r * 8 + c] == 1:  # sqSelected is a piece that can be moved
            # highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparancy value -> 0 transparent; 255 opaque
            s.fill(p.Color('blue'))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            # highlight move from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))


'''
Responsible for all the graphics within a curren game state.
'''


def drawGameStatet(screen, moveLog, gs, validMoves, sqSelected, moveLogFont, AIThinking):

    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs)
    drawMoveLog(screen, moveLog, moveLogFont)


def drawMoveLog(screen, moveLog, font):
    moveLogRect = p.Rect(128 + BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("black"), moveLogRect)

    moveText = []  # modify this later
    for i in range(0, len(moveLog), 2):
        moveString = str(i // 2 + 1) + ". " + moveLog[i].getFlagsNotation() + " "
        if i + 1 < len(moveLog):  # make sure black made a move
            moveString += moveLog[i + 1].getFlagsNotation()
        moveText.append(moveString)

    movePerRow = 3
    padding = 5
    lineSpacing = 2
    textY = padding
    for i in range(0, len(moveText), movePerRow):
        text = ""
        for j in range(movePerRow):
            if i + j < len(moveText):
                text += moveText[i + j] + "    "
        textObject = font.render(text, True, p.Color('white'))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing


'''
Draw the squares on the board.
'''


def drawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSTION):
        for c in range(DIMENSTION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
Draw the pices on the board using the current GameState.board
'''


def drawPieces(screen, gd):
    for r in range(DIMENSTION):
        for c in range(DIMENSTION):
            piece = gd.whiteBoard[r * 8 + c]
            if piece == 1:
                piece = "wP"
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            piece = gd.blackBoard[r * 8 + c]
            if piece == 1:
                piece = "bP"
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def animateMove(move, screen, gs, clock):
    global colors
    coords = []  # list of coords that the animation will move through
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10  # frames to move one square
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR * frame / frameCount, move.startCol + dC * frame / frameCount)
        drawBoard(screen)
        # drawPieces(screen, board)
        drawPieces(screen, gs)
        # erase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != 0:
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def drawText(screen, text):
    font = p.font.SysFont("Helvitca", 32, True, False)
    textObject = font.render(text, False, p.Color('Gray'))
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - textObject.get_width() / 2,
                                                                BOARD_HEIGHT / 2 - textObject.get_height() / 2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, False, p.Color('Black'))
    screen.blit(textObject, textLocation.move(2, 2))


if __name__ == "__main__":
    app = application.startApp()
    app.Begin()
    if not app.Online:
        main(app.time * 60, app.playerOne, app.playerTwo, app.setup.split())
    else:
        client = client.Client()
        client.ip = app.Ip
        client.port = app.Port
        clientThread = threading.Thread(target=client.connection)
        client.Game(clientThread)

