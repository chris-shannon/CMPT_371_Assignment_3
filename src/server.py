"""
CMPT 371 A3: Multiplayer Tic-Tac-Toe Server
Architecture: TCP Sockets with Multithreaded Session Management
Reference: Socket boilerplate adapted from "TCP Echo Server" tutorial.
"""

import socket
import threading
import json

# Server configuration
HOST = '127.0.0.1'
PORT = 5050

# Matchmaking Queue: Temporarily holds connected client sockets until 
# two players are available to form a GameSession.
matchmaking_queue = []

def check_winner(board):
    """
    Basic win and draw validation.
    Enforces the "Single Source of Truth" rule: the server calculates wins 
    so clients cannot cheat by modifying their local memory.
    """
    # Check rows and columns for a match
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != ' ': return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != ' ': return board[0][i]

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != ' ': return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != ' ': return board[0][2]

    # Check for a draw (no empty spaces left)
    if all(cell != ' ' for row in board for cell in row): return 'Draw'
    return None

def game_session(conn_x, conn_o):
    """
    Isolated game loop for two matched players running on a background thread.
    This guarantees concurrent sessions do not block each other.
    """
    # Protocol: Assign roles using the "WELCOME" message.
    # Note: \n is appended to act as a TCP message boundary.
    conn_x.sendall((json.dumps({"type": "WELCOME", "payload": "Player X"}) + '\n').encode('utf-8'))
    conn_o.sendall((json.dumps({"type": "WELCOME", "payload": "Player O"}) + '\n').encode('utf-8'))
    
    # Initialize the authoritative game state
    board = [[' ', ' ', ' '], [' ', ' ', ' '], [' ', ' ', ' ']]
    turn = 'X'
    
    # Broadcast initial empty board to both players
    update_msg = json.dumps({"type": "UPDATE", "board": board, "turn": turn, "status": "ongoing"}) + '\n'
    conn_x.sendall(update_msg.encode('utf-8'))
    conn_o.sendall(update_msg.encode('utf-8'))
    
    # Map roles to their respective socket objects
    sockets = {'X': conn_x, 'O': conn_o}
    
    while True:
        active_socket = sockets[turn]
        # Block and wait for the active player to send their move
        data = active_socket.recv(1024).decode('utf-8')
        
        # If multiple messages arrive buffered together in the TCP stream, 
        # we only process the first valid one using the \n boundary.
        clean_data = data.strip().split('\n')[0]
        msg = json.loads(clean_data)
        
        # Protocol: Process the "MOVE" action
        if msg["type"] == "MOVE":
            r, c = msg["row"], msg["col"]
            # Update authoritative state
            board[r][c] = turn  
            
            # Check for win/draw after the move
            winner = check_winner(board)
            status = "ongoing"
            if winner:
                status = "Draw!" if winner == 'Draw' else f"Player {winner} wins!"
            else:
                # Swap turns if the game is still ongoing
                turn = 'O' if turn == 'X' else 'X'
                
            # Broadcast the updated state to both clients simultaneously
            update_msg = json.dumps({"type": "UPDATE", "board": board, "turn": turn, "status": status}) + '\n'
            conn_x.sendall(update_msg.encode('utf-8'))
            conn_o.sendall(update_msg.encode('utf-8'))
            
            # Terminate the loop if the game has concluded
            if winner:
                break
                
    # Safely close the sockets when the session ends
    conn_x.close()
    conn_o.close()

def start_server():
    """
    Main server event loop. Binds the socket and populates the matchmaking queue.
    """
    # Initialize an IPv4 (AF_INET) TCP (SOCK_STREAM) socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[STARTING] Server is listening on {HOST}:{PORT}")
    
    try:
        while True:
            # Block until a new client connects
            conn, addr = server.accept()
            data = conn.recv(1024).decode('utf-8')
            
            # Protocol: Check for the initial "CONNECT" handshake
            if "CONNECT" in data:
                matchmaking_queue.append(conn)
                print(f"[QUEUE] Player added. Queue size: {len(matchmaking_queue)}")
                
                # Session Management: When 2 players are queued, match them up
                if len(matchmaking_queue) >= 2:
                    player_x = matchmaking_queue.pop(0)
                    player_o = matchmaking_queue.pop(0)
                    # Spawn an isolated GameSession thread for the matched pair
                    print("[MATCH] 2 Players found. Spawning GameSession thread.")
                    threading.Thread(target=game_session, args=(player_x, player_o)).start()
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print("\n[SHUTDOWN] Server closing...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()