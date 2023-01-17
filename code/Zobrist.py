import random

from bitarray import bitarray


class zobrist():
    def __init__(self):
        self.Table = [[[random.randint(1, 2**64 - 1) for i in range(3)]for j in range(8)]for k in range(8)]
        self.Hash = bitarray(64)
        self.Hash.setall(0)
        self.Hash = int(self.Hash.to01())

    def indexing(self, piece):
        if piece == 'b':
            return 1
        if piece == 'w':
            return 2
        else:
            return 0

    def computeHash(self, whiteBoard, blackBoard):
        for row in range(8):
            for col in range(8):
                if whiteBoard[row*8 + col] == 1:
                    piece = self.indexing('w')
                    self.Hash = self.Hash.__xor__(self.Table[row][col][piece])
                if blackBoard[row*8 + col] == 1:
                    piece = self.indexing('b')
                    Hash = self.Hash.__xor__(self.Table[row][col][piece])
        return self.Hash

    def updateHashKey(self, move, gs):
        captureMove = gs.isCapturingMove(move)
        if gs.whiteToMove:
            # to be replaced (xor out)
            if captureMove:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][1])
            else:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][0])
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][2])
            # original place(xor out)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][2])
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][0])

        else:
            # to be replaced(xor out)
            if captureMove:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][2])
            else:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][0])
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][1])
            # original place(xor out)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][1])
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][0])

    def undoHashKey(self, move, gs):
        captureMove = gs.isCapturingMove(move)
        if gs.whiteToMove:
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][0])
            # original place(xor out)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][2])
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][2])
            # to be replaced (xor out)
            if captureMove:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][1])
            else:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][0])

        else:
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][0])
            # original place(xor out)
            self.Hash = self.Hash.__xor__(self.Table[move.startRow][move.startCol][1])
            # replace with (xor in)
            self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][1])

            # to be replaced(xor out)
            if captureMove:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][2])
            else:
                self.Hash = self.Hash.__xor__(self.Table[move.endRow][move.endCol][0])
