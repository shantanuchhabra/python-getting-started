from django.db import models

class Game(models.Model):
    channel_id = models.CharField(max_length = 30, primary_key=True)
    player1 = models.CharField(max_length = 30)
    player2 = models.CharField(max_length = 30)
    next_to_move = models.CharField(max_length = 30)
    size = models.IntegerField()
    board = models.CharField(max_length = 100)

    def board_to_string(self):
        def character(c):
            if   (c == 'x'): return 'X'
            elif (c == 'o'): return 'O'
            return ' '
        board = self.board
        printable = "```" + "    |" + " |".join(["{0: >2}".format(i) for i in xrange(1,self.size+1)]) + " |\n"
        printable += ("    |" + "---|" * (self.size)) + "\n"
        for row in xrange(self.size):
            for col in xrange(self.size):
                if (col == 0):
                    printable += ("{0: >3} ".format(row+1) + "| " + character(board[self.size * row + col]) + " ")
                else:
                    printable += ("| " + character(board[self.size * row + col]) + " ")
            if (row == self.size - 1):
                printable += ("|\n    |" + ("---|" * (self.size)) + "```")
            else: 
                printable += ("|\n    |" + ("---+" * (self.size-1)) + "---|\n")
        return printable
    
    def make_move(self, player, move):
        assert(player == self.next_to_move)
        board = self.board
        idx = move - 1
        c = 'x' if player == self.player1 else 'o'
        if (self.board[idx] == '#'):
            # empty spot so we're good
            self.board = self.board[:idx] + c + self.board[idx+1:]
            self.next_to_move = self.player1 if player == self.player2 else self.player2
            self.save()
            if (self.has_won()):
                self.delete()
                return ("GAME OVER! " + player + " wins!")
            elif (self.all_slots_filled()):
                self.delete()
                return ("GAME OVER! Match drawn")
            return self.next_to_move + ", it's your turn"
        else:
            return "Space already occupied!"

    def has_won(self):
        # returns username of winner if there is one, else returns None
        def is_non_empty_singleton_set(S):
            return ('#' not in S and len(S) == 1)
        for row in xrange(self.size):
            idx = self.size * row
            same_row = set(self.board[idx : idx + self.size])
            if is_non_empty_singleton_set(same_row):
                # row is all one element but not '#'
                return True
        for col in xrange(self.size):
            idx = col
            same_col = set(self.board[idx : : self.size])
            if is_non_empty_singleton_set(same_col): 
                # col is all one element but not '#'
                return True
        first_diag = set(self.board[0 : : self.size + 1])
        secon_diag = set(self.board[self.size-1 : len(self.board)-1 : self.size-1])
        return (is_non_empty_singleton_set(first_diag) or 
            is_non_empty_singleton_set(secon_diag))

    def all_slots_filled(self):
        # returns True if all slots in board are filled
        for i in xrange(self.size * self.size):
            if (self.board[i] == "#"):
                return False
        return True
