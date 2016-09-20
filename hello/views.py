import string
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

from .models import Game

ALLOWED_TOKEN = "PPOQted1FDzSuPJYGdIwM6KN" # Generated
ALLOWED_TEAM_IDS = set(["T2ATGN3PG"]) # Allowed Team ID just Team 942

NO_GAME_STRING = "No game in progress! Start one by typing in `/ttt @opponent`"

ASK_FOR_HELP_STRING = "Type in `/ttt help` for allowable commands."

HELP_STRING = ("Welcome!\nThere can only be one game at a time in a channel.\n" +
    "Options:\n" + 
    "`/ttt @opponent`: start a new 3x3 tic-tac-toe game with opponent\n" +
    "`/ttt @opponent size N`: start a new NxN tic-tac-toe game with opponent\n" +
    "`/ttt whoseturn`: which user must play next\n" + 
    "`/ttt i,j`: Make a move at the cell in the i'th row and the j'th col\n" +
    "`/ttt giveup`: Give up and let the other user win\n" +
    "`/ttt help`: sends help to you just like this\n" +
    "*SECRET*: You can also type in a single number to make a move on a cell to be quick. For example, for a 3x3 board, you can refer to cells the way you would on your phone's keypad, i.e.\n" + 
    "```| 1 | 2 | 3 |\n|---+---+---|\n| 4 | 5 | 6 |\n|---+---+---|\n| 7 | 8 | 9 |```\n" +
    "Your move would look like `/ttt 5` if you want to make a move in the center cell")

ONGOING_GAME_STRING = ("Sorry, there is an ongoing Tic-Tac-Toe game" + 
" in the channel. Hang out and spectate until they finish and then challenge!")

class Payload(object):
    def __init__(self, request):
        self.method = request.method
        self.token = request.GET.get('token', 'None')
        self.team_id = request.GET.get('team_id', 'None')
        self.team_domain = request.GET.get('team_domain', 'None')
        self.channel_id = request.GET.get('channel_id', 'None')
        self.channel_name = request.GET.get('channel_name', 'None')
        self.user_id = request.GET.get('user_id', 'None')
        self.user_name = request.GET.get('user_name', 'None')
        self.command = request.GET.get('command', 'None')
        self.text = request.GET.get('text', 'None')
        self.response_url = request.GET.get('response_url', 'None')

    def is_authorized(self):        
        return (self.token == ALLOWED_TOKEN 
            and self.team_id in ALLOWED_TEAM_IDS)

def new_game(channel_id, player1, player2, size = 3):
    try:
        Game.objects.get(channel_id = channel_id)
        return False
    except ObjectDoesNotExist:
        init_board = '#' * (size * size)
        G = Game.objects.create(channel_id = channel_id, player1 = player1, 
            player2 = player2, next_to_move = player1, board = init_board,
            size = size)
        G.save()
        return G

def get_next_to_move(channel_id):
    try:
        G = Game.objects.get(channel_id = channel_id)
        return G.next_to_move
    except ObjectDoesNotExist:
        return None

def validate_mover(channel_id, mover):
    # returns ongoing game row from database
    try:
        ongoing = Game.objects.get(channel_id = channel_id)
        if (ongoing.next_to_move == mover):
            return ongoing
        return None
    except ObjectDoesNotExist:
        return None

def get_board(channel_id):
    try:
        ongoing = Game.objects.get(channel_id = channel_id)
        return ongoing.board_to_string()
    except ObjectDoesNotExist:
        return None

def find_opponent(text):
    for i in xrange(len(text)):
        elem = text[i]
        if elem.startswith("@"):
            # found opponent
            return elem[1:]

def get_size(text):
    # scenarios:
    # 1. user writes size = 3
    # 2. user writes size=3
    # 3. user writes size 3
    # We're not doing exception handling because the function that calls this
    # is handling exceptions
    for i in xrange(len(text)):
        if (text[i] == "size"):
            # either 1 or 2
            if text[i+1] == "=":
                size_val = text[i+2]
                return int(size_val)
            return int(text[i+1])
        elif (text[i].startswith("size")):
            size_kv = text[i]
            size_arr = size_kv.split("=")
            size_val = size_arr[1]
            return int(size_val)

def validate_player(channel_id, player):
    try:
        ongoing = Game.objects.get(channel_id = channel_id)
        if (ongoing.player1 == player or ongoing.player2 == player):
            return ongoing
        return None
    except ObjectDoesNotExist:
        return None

def end_game_through_give_up(channel_id, loser):
    validated = validate_player(channel_id, loser)
    if (validated != None):
        try:
            # to avoid concurrency issues (what if winner made a move
            # that won him before loser gave up)
            winner = validated.player1 if (validated.player2 == loser) else validated.player2
            message = loser + " gave up, " + winner + " wins! \n"
            validated.delete()
            return JsonResponse({
                "response_type": "in_channel",
                "text": message
                })
        except:
            return HttpResponse("Invalid move!")
    else:
        return HttpResponse("Invalid move!")

def make_move_using_coordinates(channel_id, mover, rowIdx, colIdx):
    validated = validate_mover(channel_id, mover)
    if ((validated != None) 
        and (0 < rowIdx <= validated.size and 0 < colIdx <= validated.size)):
            position = (rowIdx-1) * validated.size + colIdx
            message = validated.make_move(mover, position)
            printable_board = validated.board_to_string()
            return JsonResponse({
                "response_type": "in_channel",
                "text": message + "\n" + printable_board
                })
    else:
        return HttpResponse("Invalid move!")

@csrf_exempt
def index(request):
    P = Payload(request)
    authorized = P.is_authorized()
    if not authorized:
        return HttpResponse("Sorry, you are not authorized to play this game!")
    assert(authorized)
    text = P.text.strip()
    text = text.split(" ")
    if (len(text) == 1):
        text = text[0]
        if (text == ""):
            # invalid input
            return HttpResponse("Invalid command! " + ASK_FOR_HELP_STRING)
        elif (text == "help"):
            # send help
            return HttpResponse(HELP_STRING)
        elif (text == "board"):
            # show board
            board = get_board(P.channel_id)
            if (board):
                return HttpResponse(board)
            return HttpResponse(NO_GAME_STRING)
        elif (text == "whoseturn"):
            # whose turn?
            ans = get_next_to_move(P.channel_id)
            if (not ans):
                return HttpResponse(NO_GAME_STRING)
            return HttpResponse("It is " + ans + "'s turn!")
        elif (text == "giveup"):
            return end_game_through_give_up(P.channel_id, P.user_name)
        elif (text[0] == "@"):
            # possibly new game
            challenger = P.user_name
            opponent = text[1:]
            succ = new_game(P.channel_id, P.user_name, opponent)
            if (succ):
                printable_board = succ.board_to_string()
                return JsonResponse({
                    "response_type": "in_channel",
                    "text": ("3.. 2.. 1.. Game between " + challenger + " and " 
                        + opponent + " begins... " + challenger 
                        + ", it's your turn!\n" + printable_board)
                    })
            return HttpResponse(ONGOING_GAME_STRING)
        elif ("," not in text):
            # making a move
            try:
                parsedInt = int(text)
            except:
                if ("size" in text):
                    return HttpResponse("You must enter an opponent's" + 
                        " username to challenge")
                return HttpResponse("Please enter a number in the range")
            mover = P.user_name
            validated = validate_mover(P.channel_id, mover)
            if (validated != None and 0 < parsedInt <= (validated.size * 
                validated.size)):
                position = parsedInt
                message = validated.make_move(mover, position)
                printable_board = validated.board_to_string()
                return JsonResponse({
                    "response_type": "in_channel",
                    "text": message + "\n" + printable_board
                    })
            else:
                return HttpResponse("Invalid move!")
        elif ("," in text):
            # making a move (r,c) or r,c
            text = text.strip(string.punctuation) # gets rid of ()
            text = text.split(",")
            (rowIdx, colIdx) = (text[0], text[1])
            try:
                rowIdx, colIdx = int(rowIdx), int(colIdx)
            except:
                return HttpResponse("Please enter a coordinate in the range")
            return make_move_using_coordinates(P.channel_id, P.user_name, 
                rowIdx, colIdx)
        else:
            return HttpResponse("Invalid command! " + ASK_FOR_HELP_STRING)
    elif "size" in P.text:
        # size mentioned so should be starting new game
        try:
            opponent = find_opponent(text)
            size = get_size(text)
            challenger = P.user_name
            succ = new_game(P.channel_id, challenger, opponent, size)
            if (succ):
                printable_board = succ.board_to_string()
                return JsonResponse({
                    "response_type": "in_channel",
                    "text": ("3.. 2.. 1.. Game between " + challenger + " and " 
                        + opponent + " begins... " + challenger 
                        + ", it's your turn!\n" + printable_board)
                    })
            return HttpResponse(ONGOING_GAME_STRING)
        except:
            return HttpResponse("Invalid command! " + ASK_FOR_HELP_STRING)
    else:
        # move in the form of:
        # "(r, c)" or "r c", i.e. text = ["(r,", "c)"] or ["r", "c"]
        text = map((lambda s: s.strip(string.punctuation)), text)
        # now we have ["r", "c"]
        (rowIdx, colIdx) = (text[0], text[1])
        try:
            rowIdx, colIdx = int(rowIdx), int(colIdx)
        except:
            return HttpResponse("Please enter a coordinate in the range")
        return make_move_using_coordinates(P.channel_id, P.user_name, 
            rowIdx, colIdx)
