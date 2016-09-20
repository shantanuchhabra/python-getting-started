# tic-slack-toe

The Heroku Python template was used as starter code to build this slash command.

This is the server-side code to run the slash command, /ttt on slack channels. 
There can only be one game at a time in a channel.
Options:
`/ttt @opponent`: start a new 3x3 tic-tac-toe game with opponent
`/ttt @opponent size N`: start a new NxN tic-tac-toe game with opponent
`/ttt whoseturn`: which user must play next
`/ttt i,j`: Make a move at the cell in the i'th row and the j'th col
`/ttt giveup`: Give up and let the other user win
`/ttt help`: sends help to you just like this
*SECRET*: You can also type in a single number to make a move on a cell to be quick. For example, for a 3x3 board, you can refer to cells the way you would on your phone's keypad, i.e.
```
|---|---|---|
| 1 | 2 | 3 |
|---+---+---|
| 4 | 5 | 6 |
|---+---+---|
| 7 | 8 | 9 |
|---|---|---|
```
Your move would look like `/ttt 5` if you want to make a move in the center cell


