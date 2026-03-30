"""
CMPT 371 A3: Multiplayer Tic-Tac-Toe Client
Architecture: JSON over TCP Protocol
Reference: ChatGPT used to help generate clean ASCII art for the board.
"""

import socket
import json
import sys


HOST = '127.0.0.1'
PORT = 5050

def print_board(board):
    """
    Displays the board with coordinates and clean Unicode box-drawing characters.
    """
    # Column headers
    print("\n    0   1   2 ")
    print("  ┌───┬───┬───┐")
    
    for i, row in enumerate(board):
        # Row data with the row index on the left
        print(f"{i} │ {row[0]} │ {row[1]} │ {row[2]} │")
        
        # Row separators or the bottom border
        if i < 2:
            print("  ├───┼───┼───┤")
        else:
            print("  └───┴───┴───┘\n")

def start_client():
    """
    Main client execution loop. Handles connection, JSON serialization/deserialization,
    and user input routing.
    """
    # Initialize an IPv4 (AF_INET) TCP (SOCK_STREAM) socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    
    # Handshake Protocol: Send initial connection request to join matchmaking
    client.sendall(json.dumps({"type": "CONNECT"}).encode('utf-8'))
    print("Connected. Waiting for opponent...")
    
    my_role = None
    
    while True:
        # Await data broadcasted from the GameSession server thread
        data = client.recv(1024).decode('utf-8')
            
        # TCP STREAM BUFFERING FIX:
        # OS-level TCP buffers might combine multiple JSON packets into one string.
        # We split by the predefined '\n' boundary to process them sequentially.
        for chunk in data.strip().split('\n'):
            if not chunk: continue
            # Deserialize the JSON packet
            msg = json.loads(chunk)
            
            # Action: Initial Role Assignment
            if msg["type"] == "WELCOME":
                # Payload format is "Player X" or "Player O"
                my_role = msg["payload"][-1]
                print(f"Match found! You are Player {my_role}.")
                
            # Action: Game State Update
            elif msg["type"] == "UPDATE":
                print_board(msg["board"])
                
                # Check for termination conditions broadcasted by the server
                if msg["status"] != "ongoing":
                    print(f"Game Over: {msg['status']}")
                    client.close()
                    sys.exit(0)
                    
                # Print whose turn it is
                if msg["turn"] == my_role:
                    print("It's your turn!")
                    # State Validation: Prompt for input only if the server says it is our turn
                    r_str, c_str = input("Enter row and col (e.g., '1 1'): ").split()
                    
                    # Protocol: Package coordinates into a MOVE packet.
                    # Always append the \n boundary before encoding to bytes.
                    move_msg = json.dumps({"type": "MOVE", "row": int(r_str), "col": int(c_str)}) + '\n'
                    client.sendall(move_msg.encode('utf-8'))
                else:
                    print("Waiting for opponent...")

    client.close()

if __name__ == "__main__":
    start_client()