import threading
import pygame as p
import socket
import FlagsEngine, smartMoveFinder, Zobrist
from multiprocessing import Queue, Process

# here you should use FlagsMain
alphabetic = "abcdefghijklmnopqrstuvwxyz"
numeric = "0123456789"

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSTION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSTION  # 64
MAX_FPS = 30
IMAGES = {}

ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
               "5": 3, "6": 2, "7": 1, "8": 0}
filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
               "e": 4, "f": 5, "g": 6, "h": 7}


def loadImages():
    IMAGES['wP'] = p.transform.scale(p.image.load("images/wP.png"), (SQ_SIZE, SQ_SIZE))
    IMAGES['bP'] = p.transform.scale(p.image.load("images/bP.png"), (SQ_SIZE, SQ_SIZE))


class Client:

    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = "local host"
        self.port = 9999
        self.minutes = 2
        self.gs = FlagsEngine.GameState()
        self.agent = smartMoveFinder.Agent()
        self.serverTurn = False
        self.serverMove = None
        self.clientMove = None
        self.zb = Zobrist.zobrist()
        self.begin = False
        self.validMoves = self.gs.getValidMoves()
        self.moveLog = []
        self.whiteTurn = bool(self.gs.whiteToMove)

    def Game(self, clientThread):

        p.init()
        clientThread.start()
        self.zb.computeHash(self.gs.whiteBoard, self.gs.blackBoard)
        font = p.font.SysFont('Consolas', 30)
        moveLogFont = p.font.SysFont("Arial", 12, False, False)
        Timer = MAX_FPS * self.minutes * 60
        screen = p.display.set_mode((BOARD_WIDTH + 128 + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
        clock = p.time.Clock()
        screen.fill(p.Color("white"))
        # validMoves = self.gs.getValidMoves()
        moveMade = False  # flag variable for when a move is made.
        animate = False  # flag variable for when we should animate
        loadImages()
        running = True
        gameOver = False
        # gs.setTimer(Timer, MAX_FPS)
        text = ""
        clientThinking = False
        serverThinking = False


        while running:
            if self.begin or self.serverTurn:
                self.begin = True
                # white to move
                if self.whiteTurn:
                    mins, secs = divmod(int(self.gs.whiteTimer), 60)
                    self.gs.textWhiteTimer = '{:02d}:{:02d}'.format(mins, secs)
                    self.gs.whiteTimer -= 1 / MAX_FPS

                else:
                    mins, secs = divmod(int(self.gs.blackTimer), 60)
                    self.gs.textBlackTimer = '{:02d}:{:02d}'.format(mins, secs)
                    self.gs.blackTimer -= 1 / MAX_FPS
                    '''
                    Here we bring all valid moves begin a process so that AI will think while we still running the loop 
                    so the timer will still running
                    '''
                if not gameOver and not (self.serverMove is None):
                    self.serverMove.moveRate = self.gs.evaluate(self.serverMove.endRow, self.serverMove.endCol,self.serverMove)
                    self.gs.makeMove(self.serverMove)
                    self.whiteTurn = not self.whiteTurn

                    self.moveLog = self.gs.moveLog.copy()
                    print("server move is: " + self.serverMove.getFlagsNotation())
                    self.serverMove = None
                    moveMade = True
                    animate = True
                    self.serverTurn = not self.serverTurn

                elif not gameOver and not self.serverTurn:
                    if not clientThinking:
                        clientThinking = True
                        # print("client is thinking")
                        returnQueue = Queue()  # used to pass data between threads
                        Round = 1
                        moveFinderProcess = Process(target=self.agent.findBestMove,
                                                             args=(self.gs, self.validMoves, self.zb, returnQueue))
                        moveFinderProcess.start()  # call findBestMove(gs, validMoves returnQueue)

                    if not moveFinderProcess.is_alive():
                        self.clientMove = returnQueue.get()
                        if self.clientMove is None:
                            self.sendMessage("exit")
                            break
                            # self.clientMve = self.agent.findRandomMove(validMoves)
                        print(self.clientMove.getFlagsNotation() + "----->rating of the move: " + str(
                            self.clientMove.moveRate))
                        self.gs.makeMove(self.clientMove)
                        self.whiteTurn = not self.whiteTurn
                        self.moveLog = self.gs.moveLog.copy()
                        self.sendMessage(self.clientMove.getFlagsNotation())
                        moveMade = True
                        animate = True
                        clientThinking = False
                        self.serverTurn = not self.serverTurn

                if moveMade:
                    if animate:
                        self.animateMove(screen, clock)
                    self.validMoves = self.gs.getValidMoves()
                    moveMade = False
                    animate = False

                screen.fill((255, 255, 255))
                screen.blit(font.render(self.gs.textBlackTimer, True, (0, 0, 0)), (BOARD_WIDTH + 32, 96))
                screen.blit(font.render(self.gs.textWhiteTimer, True, (0, 0, 0)),
                            (BOARD_WIDTH + 32, BOARD_HEIGHT - 128))
                self.drawGameStatet(screen, (), moveLogFont)

                if self.gs.blackTimer <= 0:
                    self.drawText(screen, 'White wins by time')
                    gameOver = True
                elif self.gs.whiteTimer <= 0:
                    gameOver = True
                    self.drawText(screen, 'Black wins by time')

                if self.gs.checkmate and not clientThinking:
                    gameOver = True
                    if self.gs.whiteToMove:
                        self.drawText(screen, 'Black wins by promotion')
                    else:
                        self.drawText(screen, 'White wins by promotion')
                elif self.gs.noValidMoves and not clientThinking:
                    gameOver = True
                    if self.gs.whiteToMove:
                        self.drawText(screen, 'Black wins white has no available move')
                    else:
                        self.drawText(screen, 'White wins black has no available move')

                p.event.pump()
                clock.tick(MAX_FPS)
                p.display.flip()

    '''
    Highlight square selected and moves for piece selected 
    '''

    def highlightSquares(self, screen, sqSelected):
        if sqSelected != ():
            r, c = sqSelected

            if self.gs.whiteBoard[r * 8 + c] == 1 or self.gs.blackBoard[
                r * 8 + c] == 1:  # sqSelected is a piece that can be moved
                # highlight selected square
                s = p.Surface((SQ_SIZE, SQ_SIZE))
                s.set_alpha(100)  # transparancy value -> 0 transparent; 255 opaque
                s.fill(p.Color('blue'))
                screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
                # highlight move from that square
                s.fill(p.Color('yellow'))
                for move in self.validMoves:
                    if move.startRow == r and move.startCol == c:
                        screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))

    '''
    Responsible for all the graphics within a curren game state.
    '''

    def drawGameStatet(self, screen, sqSelected, moveLogFont):
        self.drawBoard(screen)
        self.highlightSquares(screen, sqSelected)
        self.drawPieces(screen)
        self.drawMoveLog(screen, moveLogFont)

    def drawMoveLog(self, screen, font):
        moveLogRect = p.Rect(128 + BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
        p.draw.rect(screen, p.Color("black"), moveLogRect)

        moveText = []  # modify this later
        for i in range(0, len(self.moveLog), 2):
            moveString = str(i // 2 + 1) + ". " + self.moveLog[i].getFlagsNotation() + " "
            if i + 1 < len(self.moveLog):  # make sure black made a move
                moveString += self.moveLog[i + 1].getFlagsNotation()
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

    def drawBoard(self, screen):
        global colors
        colors = [p.Color("white"), p.Color("gray")]
        for r in range(DIMENSTION):
            for c in range(DIMENSTION):
                color = colors[((r + c) % 2)]
                p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    '''
    Draw the pices on the board using the current GameState.board
    '''

    def drawPieces(self, screen):
        for r in range(DIMENSTION):
            for c in range(DIMENSTION):
                piece = self.gs.whiteBoard[r * 8 + c]
                if piece == 1:
                    piece = "wP"
                    screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                piece = self.gs.blackBoard[r * 8 + c]
                if piece == 1:
                    piece = "bP"
                    screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    def animateMove(self, screen, clock):
        global colors
        coords = []  # list of coords that the animation will move through
        dR = self.gs.moveLog[-1].endRow - self.gs.moveLog[-1].startRow
        dC = self.gs.moveLog[-1].endCol - self.gs.moveLog[-1].startCol
        framesPerSquare = 10  # frames to move one square
        frameCount = (abs(dR) + abs(dC)) * framesPerSquare
        for frame in range(frameCount + 1):
            r, c = (self.gs.moveLog[-1].startRow + dR * frame / frameCount,
                    self.gs.moveLog[-1].startCol + dC * frame / frameCount)
            self.drawBoard(screen)
            # drawPieces(screen, board)
            self.drawPieces(screen)
            # erase the piece moved from its ending square
            color = colors[(self.gs.moveLog[-1].endRow + self.gs.moveLog[-1].endCol) % 2]
            endSquare = p.Rect(self.gs.moveLog[-1].endCol * SQ_SIZE, self.gs.moveLog[-1].endRow * SQ_SIZE, SQ_SIZE,
                               SQ_SIZE)
            p.draw.rect(screen, color, endSquare)
            # draw captured piece onto rectangle
            if self.gs.moveLog[-1].pieceCaptured != 0:
                screen.blit(IMAGES[self.gs.moveLog[-1].pieceCaptured], endSquare)
            # draw moving piece
            screen.blit(IMAGES[self.gs.moveLog[-1].pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            p.display.flip()
            clock.tick(60)

    def drawText(self, screen, text):
        font = p.font.SysFont("Helvitca", 32, True, False)
        textObject = font.render(text, False, p.Color('Gray'))
        textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - textObject.get_width() / 2,
                                                                    BOARD_HEIGHT / 2 - textObject.get_height() / 2)
        screen.blit(textObject, textLocation)
        textObject = font.render(text, False, p.Color('Black'))
        screen.blit(textObject, textLocation.move(2, 2))

    def sendMessage(self, text):
        try:
            self.s.send(bytes(text, 'utf-8'))

        except:
            print("Connection lost with server")


    def connection(self):
        self.s.connect((self.ip, self.port))
        while True:
            try:
                text = self.s.recv(4000).decode('utf-8')
                text = text.split()
                if text[0] == "Connected":
                    self.s.send(b"OK")
                    print("i am connected with server, 'OK' sent")
                elif text[0] == "Time":
                    print("server give time to the game, 'OK' sent")
                    self.gs.setTimer(int(text[1]) * 60)
                    self.s.send(b"OK")
                elif text[0] == "Setup":
                    print("server gave me setup for the game, 'OK' sent")
                    self.gs.setBoard(text)
                    self.validMoves = self.gs.getValidMoves()

                    self.s.send(b"OK")
                elif text[0] == "Begin":
                    print("server told me to begin the game")
                    self.begin = True
                elif text[0][0] in alphabetic and text[0][1] in numeric:
                    moving = []
                    selected = (ranksToRows[text[0][1]], filesToCols[text[0][0]])
                    moving.append(selected)
                    selected = (ranksToRows[text[0][3]], filesToCols[text[0][2]])
                    moving.append(selected)

                    self.serverMove = FlagsEngine.Move(moving[0], moving[1], self.gs.whiteBoard,
                                           self.gs.blackBoard,
                                           whiteToMove=self.gs.whiteToMove)

                    self.serverTurn = True
                else:
                    print("the server send message i didn't understand!!!!!!!!!!!!")
                    continue
            except:
                print("Connection lost with server")
                break


if __name__ == "__main__":
    client = Client()
    clientThread = threading.Thread(target=client.connection)
    client.Game(clientThread)
