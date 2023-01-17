import random

WIN = 1000
scoreWhite = 10
scoreBlack = 10
NOT_SAFE = 1
THRESHOLD = 4 # if threshold is bigger then will store less in the Zobrist Hash, therefore, will think more(smarter)
DEPTH = 4
QUITDEPTH = 3

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

'''
smartMoveClass
'''

class Agent:

    def __init__(self):
        self.zobHash = {}
        self.hash = {}
        self.threshold = THRESHOLD

    def findBestMove(self, gs, validMoves, zb, returnQueue):
        gs1 = gs

        global nextMove, counter, counter1, counter2, branchingFactor, counter3
        branchingFactor = 0
        nextMove = None
        # self.zobHash = {}
        counter1 = 0
        counter2 = 0

        random.shuffle(validMoves)

        validMoves = sorted(validMoves, key=lambda x: x.moveRate, reverse=True)

        print("===================================================")
        print("There are", len(validMoves), "valid moves")
        for move in validMoves:
            print(move.getFlagsNotation(), end="-->")
            print(move.moveRate, end="|")
        print("")
        print("===================================================")

        self.findMoveNegaMaxAlphaBeta(gs1, validMoves, DEPTH, -WIN, WIN, 1 if gs1.whiteToMove else -1, zb)


        if returnQueue is None:
            return nextMove
        else:
            returnQueue.put(nextMove)

    def findMoveNegaMaxAlphaBeta(self, gs, validMoves, depth, alpha, beta, turnMultiplier, zb, moveMade=None):
        global nextMove, counter1, counter2

        if depth == 0:
            return turnMultiplier * self.scoreBoard(gs, moveMade)

        maxScore = -WIN
        for move in validMoves:
            gs.makeMove(move)
            zb.updateHashKey(move, gs)

            nextMoves = gs.getValidMoves()
            counter2 += len(nextMoves)
            counter1 += 1
            if zb.Hash in self.zobHash.keys():
                score = self.zobHash[zb.Hash]
            else:
                score = -self.findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier, zb,
                                                       moveMade=move)

                if depth < self.threshold:
                    self.zobHash[zb.Hash] = score

            if score > maxScore:
                maxScore = score
                if depth == DEPTH:
                    nextMove = move

            zb.undoHashKey(gs.moveLog[-1], gs)
            gs.undoMove()

            if maxScore > alpha:  # pruning happens
                alpha = maxScore
            if alpha >= beta:
                break
        return maxScore

    '''
    A positive score is good for white, a negative score is good for black
    '''

    def scoreBoard(self, gs, move):
        if gs.checkmate or gs.noValidMoves:
            if gs.whiteToMove:
                return -WIN  # black wins
            else:
                return WIN  # white wins
        # return gs.whiteBoard.count(1) - gs.blackBoard.count(1)

        return gs.whiteScoreBoard - gs.blackScoreBoard

    def firstMoveFromMoveOrdering(self, validMoves):
        validMoves = sorted(validMoves, key=lambda x: x.moveRate, reverse=True)
        return validMoves[0]

