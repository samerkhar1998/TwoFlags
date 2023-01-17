'''
This class is responsible for storing all the information about the current state of a flags game. It will be
responsible for determining the valid moves at the current state. It will also keep a move log.
'''
import random

WIN = 10000

whitePawnScores = [[WIN, WIN, WIN, WIN, WIN, WIN, WIN, WIN],
                   [WIN, WIN, WIN, WIN, WIN, WIN, WIN, WIN],
                   [1, 1, 1, 1, 1, 1, 1, 1],
                   [1, 1, 1, 1, 1, 1, 1, 1],
                   [1, 1, 1, 1, 1, 1, 1, 1],
                   [1, 1, 1, 1, 1, 1, 1, 1],
                   [1, 1, 1, 1, 1, 1, 1, 1],
                   [1, 1, 1, 1, 1, 1, 1, 1]]

blackPawnScores = whitePawnScores[::-1]

piecePositionScores = {"bP": blackPawnScores, "wP": whitePawnScores}

from bitarray import bitarray

ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
               "5": 3, "6": 2, "7": 1, "8": 0}
rowsToRanks = {v: k for k, v, in ranksToRows.items()}
filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
               "e": 4, "f": 5, "g": 6, "h": 7}
colsToFiles = {v: k for k, v in filesToCols.items()}

fileA = bitarray("1000000010000000100000001000000010000000100000001000000010000000")
row1 = bitarray("1111111100000000000000000000000000000000000000000000000000000000")
filesAndRows = {}
for i in range(8):
    filesAndRows["file" + colsToFiles[i]] = fileA.__rshift__(i)
    filesAndRows["row" + rowsToRanks[i]] = row1.__rshift__(i * 8)


class GameState():
    def __init__(self):
        # white has bitmap.
        # black has bitmap.
        # Presence of knowledge is represented by setting the bit for the square to 1
        # Absence of knowledge is represented by setting the bit for the square to 0
        self.whiteTimer = 10
        self.blackTimer = 10
        self.textWhiteTimer = ""
        self.textBlackTimer = ""
        self.whiteScoreBoard = 8
        self.blackScoreBoard = 8
        self.whiteBoard = bitarray("0000000000000000000000000000000000000000000000001111111100000000")
        self.blackBoard = bitarray("0000000011111111000000000000000000000000000000000000000000000000")
        self.whiteFirstMoves = bitarray("0000000000000000000000000000000011111111000000000000000000000000")
        self.blackFirstMoves = bitarray("0000000000000000000000001111111100000000000000000000000000000000")
        self.fileA = bitarray("0111111101111111011111110111111101111111011111110111111101111111")
        self.fileH = bitarray("1111111011111110111111101111111011111110111111101111111011111110")
        self.blackAttacks = bitarray(64)
        self.whiteAttacks = bitarray(64)
        self.leftCaptureMoves = bitarray(64)
        self.rightCaptureMoves = bitarray(64)
        self.leftEnPassantMoves = bitarray(64)
        self.rightEnPassantMoves = bitarray(64)
        self.captureMoves = []

        self.whiteToMove = True
        self.moveLog = []

        self.gameOver = False
        self.checkmate = False
        self.noValidMoves = False
        self.enPassantPossible = ()  # coordinates for square where en passant capture is possible.

    '''
    Takes a Move as a parameter and executes it.
    '''

    def setTimer(self, t):
        self.blackTimer = t
        self.whiteTimer = t

    '''
    setting the board from a given setup
    '''

    def setBoard(self, STR):
        self.whiteBoard.setall(0)
        self.blackBoard.setall(0)

        for word in STR:
            if word == "Setup":
                continue
            else:
                if word[0].lower() == 'w':
                    self.whiteBoard[ranksToRows[word[2]] * 8 + filesToCols[word[1]]] = 1
                else:
                    self.blackBoard[ranksToRows[word[2]] * 8 + filesToCols[word[1]]] = 1

    '''

    making the move, restoring it in the moveLog and swap turns
    '''

    def makeMove(self, move):
        if self.whiteToMove:

            self.whiteBoard[move.startRow * 8 + move.startCol] = 0
            self.whiteBoard[move.endRow * 8 + move.endCol] = 1
            if move.pieceCaptured != 0:
                self.blackBoard[move.endRow * 8 + move.endCol] = 0
            move.moveRate = self.evaluate(move.endRow, move.endCol, move)
            self.whiteScoreBoard += move.moveRate
        else:

            self.blackBoard[move.startRow * 8 + move.startCol] = 0
            self.blackBoard[move.endRow * 8 + move.endCol] = 1
            if move.pieceCaptured != 0:
                self.whiteBoard[move.endRow * 8 + move.endCol] = 0
            move.moveRate = self.evaluate(move.endRow, move.endCol, move)
            self.blackScoreBoard += move.moveRate
        self.moveLog.append(move)

        # pawn to end
        if move.isPawnPromotion:
            self.checkmate = True
        # en passant
        if move.isEnPassantMove and self.whiteToMove:
            self.blackBoard[move.startRow * 8 + move.endCol] = 0  # capturing the black pawn
        elif move.isEnPassantMove and not self.whiteToMove:
            # else:
            self.whiteBoard[move.startRow * 8 + move.endCol] = 0  # capturing the white pawn

        # update enPassantPossible variable
        if abs(move.startRow - move.endRow) == 2:  # only on 2 square pawn advances
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        else:
            self.enPassantPossible = ()

        self.whiteToMove = not self.whiteToMove  # swap players

    '''
    Undo the last move made
    '''

    def undoMove(self):
        if len(self.moveLog) != 0:  # make sure that there is a move to undo
            if not self.whiteToMove:

                move = self.moveLog.pop()
                self.whiteBoard[move.startRow * 8 + move.startCol] = move.pieceMoved if move.pieceMoved == 0 else 1
                self.whiteBoard[move.endRow * 8 + move.endCol] = 0
                self.blackBoard[
                    move.endRow * 8 + move.endCol] = 0 if move.pieceCaptured == 0 or move.isEnPassantMove else 1
                self.whiteScoreBoard -= move.moveRate
                # undo enPassant move
                if move.isEnPassantMove:
                    self.whiteBoard[move.endRow * 8 + move.endCol] = 0  # leave landing square blank
                    self.blackBoard[
                        move.startRow * 8 + move.endCol] = move.pieceCaptured if move.pieceCaptured == 0 else 1
                    self.enPassantPossible = (move.endRow, move.endCol)
                # undo a 2 square pawn advance
                if abs(move.startRow - move.endRow) == 2:
                    self.enPassantPossible = ()
            else:
                move = self.moveLog.pop()
                self.blackScoreBoard -= move.moveRate
                self.blackBoard[move.startRow * 8 + move.startCol] = move.pieceMoved if move.pieceMoved == 0 else 1
                self.blackBoard[move.endRow * 8 + move.endCol] = 0
                self.whiteBoard[
                    move.endRow * 8 + move.endCol] = 0 if move.pieceCaptured == 0 or move.isEnPassantMove else 1

                # undo enPassant move
                if move.isEnPassantMove:
                    self.blackBoard[move.endRow * 8 + move.endCol] = 0  # leave landing square blank
                    self.whiteBoard[
                        move.startRow * 8 + move.endCol] = move.pieceCaptured if move.pieceCaptured == 0 else 1
                    self.enPassantPossible = (move.endRow, move.endCol)
                # undo a 2 square pawn advance
                if abs(move.startRow - move.endRow) == 2:
                    self.enPassantPossible = ()

            self.checkmate = False
            self.noValidMoves = False
            self.whiteToMove = not self.whiteToMove  # switch turns back

    def squareUnderAttack(self, row, col):
        """
        Determine if enemy can attack the square row col
        """
        self.whiteToMove = not self.whiteToMove
        firstAttacker, secondAttacker = self.squareIsProtected(row, col)
        self.whiteToMove = not self.whiteToMove
        return firstAttacker, secondAttacker

    def toTouchLineMove(self, row, col):
        '''
        check if the pawn on given square can go all the way to the touch line
        '''
        if self.whiteToMove:
            if row == 0:
                return True
            for i in range(row, 0, -1):
                first, two = self.squareUnderAttack(i, col)
                if first or two:
                    return False
                elif (i != row and self.blackBoard[i * 8 + col] == 1) or (
                        i != row and self.whiteBoard[i * 8 + col] == 1):
                    return False
            return True
        else:
            if row == 7:
                return True
            for i in range(row, 8):
                first, two = self.squareUnderAttack(i, col)
                if first or two:
                    return False
                elif (i != row and self.blackBoard[i * 8 + col]) == 1 or (
                        i != row and self.whiteBoard[i * 8 + col]) == 1:
                    return False
            return True

    def squareIsProtected(self, row, col):
        '''
        check if a given square is protected by one or two on neither
        '''
        one = two = False
        if self.thereIsPawn(row + 1 if self.whiteToMove else row - 1, col - 1):
            one = True
        if self.thereIsPawn(row + 1 if self.whiteToMove else row - 1, col + 1):
            two = True

        return one, two

    def thereIsPawn(self, row, col):
        '''
        checks if there is a pawn on a given square
        '''
        if row < 0 or row > 7 or col < 0 or col > 7:
            return False
        elif self.whiteToMove and self.whiteBoard[row * 8 + col] == 1:
            return True
        elif self.blackBoard[row * 8 + col] == 1:
            return True

        return False

    '''
    this function gives a rating value for each move...
    this function is heuristic function
    '''

    def evaluate(self, row, col, move, captured=None):
        '''
        :param row: end row of the move
        :param col: end col of the move
        :param captured: checks if there is a capture
        :return: rate of the move
        '''
        '''
        This function evaluate each pawn on the board
        '''

        '''
        if the pawn going to the touch line safely
        '''
        if self.toTouchLineMove(row, col):
            return WIN * (8 - row) if self.whiteToMove else WIN * row

        # we might check more than once if a square is under attack
        firstAttacker, secondAttacker = self.squareUnderAttack(row, col)
        '''
        if pawn is under attack and not protected, or
        if move is under attack and protected 
        '''

        if firstAttacker or secondAttacker:
            rate = 0
            if firstAttacker:
                rate -= 6
            if secondAttacker:
                rate -= 6

            firstDefender, secondDefender = self.squareIsProtected(row, col)
            if firstDefender:
                rate += 12
            if secondDefender:
                rate += 12
            return rate
        '''
        if its safe capturing 
        '''

        if move.startCol != move.endCol:
            rate = 25
            if firstAttacker or secondAttacker:
                return rate - 20
            return rate

        '''
        if the move is safe
        '''
        if not (firstAttacker or secondAttacker):
            return 1

        '''
        if the move is not safe
        '''
        if firstAttacker or secondAttacker:
            return -5

        return 0

    def getValidMoves(self):
        tempEnPassantPossible = self.enPassantPossible
        moves = self.getAllPossibleMoves()

        if len(moves) == 0:
            if self.checkmate == False:
                self.noValidMoves = True
        else:
            self.checkmate = False
            self.noValidMoves = False
            self.enPassantPossible = tempEnPassantPossible
        return self.getAllPossibleMoves()

    def getAllPossibleMoves(self):
        moves = []
        self.captureMoves = []
        enPassantArr = possibleTwoSteps = oneStep = bitarray(
            "0000000000000000000000000000000000000000000000000000000000000000")
        self.whiteAttacks.setall(0)
        self.blackAttacks.setall(0)
        self.rightEnPassantMoves.setall(0)
        self.leftEnPassantMoves.setall(0)
        self.rightCaptureMoves.setall(0)
        self.leftCaptureMoves.setall(0)

        if self.isPawnPromoted():
            return moves

        '''
        check white moves...
        '''
        if self.whiteToMove:

            # here we check if pawns can go one or two steps ahead
            oneStep = ((self.whiteBoard.__lshift__(8)).__xor__(
                self.blackBoard.__and__(self.whiteBoard.__lshift__(8)))).__and__(
                (self.whiteBoard.__lshift__(8)).__xor__(
                    self.whiteBoard.__and__(self.whiteBoard.__lshift__(8))))

            possibleTwoSteps = ((oneStep.__lshift__(8)).__xor__(
                self.blackBoard.__and__(oneStep.__lshift__(8)))).__and__(self.whiteFirstMoves)

            # here we check if there is any capture moves for the white
            self.rightCaptureMoves = self.whiteBoard.__lshift__(7).__and__(self.blackBoard).__and__(self.fileA)
            self.leftCaptureMoves = self.whiteBoard.__lshift__(9).__and__(self.blackBoard).__and__(self.fileH)

            # here we check enPassant moves
            if self.enPassantPossible != ():
                enPassantArr[self.enPassantPossible[0] * 8 + self.enPassantPossible[1]] = 1
                self.rightEnPassantMoves = self.whiteBoard.__lshift__(7).__and__(enPassantArr).__and__(self.fileA)
                self.leftEnPassantMoves = self.whiteBoard.__lshift__(9).__and__(enPassantArr).__and__(self.fileH)

        else:
            # here we check if pawns can go one or two steps ahead
            oneStep = ((self.blackBoard.__rshift__(8)).__xor__(
                self.whiteBoard.__and__(self.blackBoard.__rshift__(8)))).__and__(
                (self.blackBoard.__rshift__(8)).__xor__(
                    self.blackBoard.__and__(self.blackBoard.__rshift__(8))))

            possibleTwoSteps = ((oneStep.__rshift__(8)).__xor__(
                self.whiteBoard.__and__(oneStep.__rshift__(8)))).__and__(self.blackFirstMoves)

            # here we check if there is any capture moves for the white
            self.rightCaptureMoves = self.blackBoard.__rshift__(7).__and__(self.whiteBoard).__and__(self.fileH)
            self.leftCaptureMoves = self.blackBoard.__rshift__(9).__and__(self.whiteBoard).__and__(self.fileA)

            # here we check enPassant moves
            if self.enPassantPossible != ():
                enPassantArr[self.enPassantPossible[0] * 8 + self.enPassantPossible[1]] = 1
                self.rightEnPassantMoves = self.blackBoard.__rshift__(7).__and__(enPassantArr).__and__(self.fileH)
                self.leftEnPassantMoves = self.blackBoard.__rshift__(9).__and__(enPassantArr).__and__(self.fileA)

        for i in range(64):
            if oneStep[i] == 1:
                if self.whiteToMove:
                    moves.append(Move(((i + 8) // 8, i % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                else:
                    moves.append(Move(((i - 8) // 8, i % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
            if possibleTwoSteps[i] == 1:
                if self.whiteToMove:
                    moves.append(Move(((i + 16) // 8, i % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                else:
                    moves.append(Move(((i - 16) // 8, i % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
            if self.leftCaptureMoves[i] == 1:
                if self.whiteToMove:
                    moves.append(Move(((i + 9) // 8, (i + 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])
                else:
                    moves.append(Move(((i - 9) // 8, (i - 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])
            if self.rightCaptureMoves[i] == 1:
                if self.whiteToMove:
                    moves.append(Move(((i + 7) // 8, (i - 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])
                else:
                    moves.append(Move(((i - 7) // 8, (i + 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])
            if self.leftEnPassantMoves[i] == 1:
                if self.whiteToMove:
                    moves.append(Move(((i + 9) // 8, (i + 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      isEnPassantMove=True, whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])
                else:
                    moves.append(Move(((i - 9) // 8, (i - 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      isEnPassantMove=True, whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])
            if self.rightEnPassantMoves[i] == 1:
                if self.whiteToMove:
                    moves.append(Move(((i + 7) // 8, (i - 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      isEnPassantMove=True, whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])
                else:
                    moves.append(Move(((i - 7) // 8, (i + 1) % 8), (i // 8, i % 8), self.whiteBoard, self.blackBoard,
                                      isEnPassantMove=True, whiteToMove=self.whiteToMove))
                    moves[-1].moveRate = self.evaluate(moves[-1].endRow, moves[-1].endCol,moves[-1],
                                                       captured=moves[-1].pieceCaptured)
                    self.captureMoves.append(moves[-1])

        return moves

    def isCapturingMove(self, move):
        return not move.startCol == move.endCol

    def isPawnPromoted(self):
        for i in range(8):
            if self.whiteBoard[i] == 1 or self.blackBoard[63 - i] == 1:
                self.checkmate = True
                return True
        return False


'''
Get all the pawn moves for the pawn located at row, col and add these moves to list
'''


class Move():

    def __init__(self, startSq, endSq, whiteBoard, blackBoard, isEnPassantMove=False, whiteToMove=False):
        self.moveRate = None
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceCaptured = None
        if whiteToMove:
            self.pieceMoved = whiteBoard[self.startRow * 8 + self.startCol]
            if self.pieceMoved == 1:
                self.pieceMoved = 'wP'
            self.pieceCaptured = blackBoard[self.endRow * 8 + self.endCol]
            if self.pieceCaptured == 1:
                self.pieceCaptured = 'bP'
        else:
            self.pieceMoved = blackBoard[self.startRow * 8 + self.startCol]
            if self.pieceMoved == 1:
                self.pieceMoved = 'bP'
            self.pieceCaptured = whiteBoard[self.endRow * 8 + self.endCol]
            if self.pieceCaptured == 1:
                self.pieceCaptured = 'wP'

        # pawn promotion
        self.isPawnPromotion = (self.pieceMoved == 'wP' and self.endRow == 0) or (
                self.pieceMoved == 'bP' and self.endRow == 7)
        # en Passant
        self.isEnPassantMove = isEnPassantMove
        if self.isEnPassantMove:
            self.pieceCaptured = 'wP' if self.pieceMoved == 'bP' else 'bP'

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    '''
    Overriding the equals method
    '''

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getFlagsNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return colsToFiles[c] + rowsToRanks[r]
