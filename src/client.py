"""
Multiplayer Wordle Client
Architecture: JSON over TCP Protocol with Tkinter GUI
All players guess the same word. Every guess is broadcast to all clients.
"""
import socket
import json
import sys
import threading
import tkinter as tk

HOST = '127.0.0.1'
PORT = 5050

# --- Constants ---
WORD_LENGTH = 5
MAX_GUESSES = 6

# Colors
BG_COLOR = "#121213"
TILE_CORRECT = "#538d4e"
TILE_PRESENT = "#b59f3b"
TILE_ABSENT = "#3a3a3c"
TILE_BORDER = "#565758"
TEXT_COLOR = "#ffffff"
KEY_BG = "#818384"
INPUT_BG = "#2a2a2c"

# --- Global State ---
client = None
root = None
current_row = 0
game_over = False

# UI references (set during build)
grid_labels = [[None for _ in range(WORD_LENGTH)] for _ in range(MAX_GUESSES)]
grid_frames = [[None for _ in range(WORD_LENGTH)] for _ in range(MAX_GUESSES)]
key_buttons = {}
key_states = {}
input_var = None
status_label = None
entry = None


# ─── Network Functions ──────────────────────────────────────────

def send_to_server(msg_dict):
    """
    Serialize a dictionary to JSON and send it to the server.
    Always appends the '\\n' boundary before encoding to bytes.
    """
    data = json.dumps(msg_dict) + '\n'
    client.sendall(data.encode('utf-8'))


def listen_to_server():
    """
    Background thread: continuously listens for server messages.
    TCP STREAM BUFFERING FIX:
    OS-level TCP buffers might combine multiple JSON packets into one string.
    We split by the predefined '\\n' boundary to process them sequentially.
    """
    while True:
        try:
            data = client.recv(4096).decode('utf-8')
            if not data:
                root.after(0, lambda: update_status("Disconnected from server.", "#e06c6c"))
                break

            for chunk in data.strip().split('\n'):
                if not chunk:
                    continue
                # Deserialize the JSON packet
                msg = json.loads(chunk)

                # Action: Server confirmed connection
                if msg["type"] == "WELCOME":
                    handle_welcome(msg)

                # Action: A guess was made — server broadcasts feedback to all
                elif msg["type"] == "FEEDBACK":
                    handle_feedback(msg)

                # Action: Game over — server reveals the answer
                elif msg["type"] == "GAME_OVER":
                    handle_game_over(msg)

                # Action: New round — server resets the game
                elif msg["type"] == "NEW_ROUND":
                    handle_new_round(msg)

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            root.after(0, lambda: update_status("Connection lost.", "#e06c6c"))
            break


# ─── Message Handlers ───────────────────────────────────────────

def handle_welcome(msg):
    """Process WELCOME message: server confirms we joined."""
    root.after(0, lambda: update_status("Connected! Start guessing.", TILE_CORRECT))


def handle_feedback(msg):
    """
    Process FEEDBACK message: apply color results to the shared board.
    Every client receives this for every guess made by any player.
    Expected payload:
        {"type": "FEEDBACK", "guess": "CRANE", "feedback": ["correct", "absent", ...]}
    """
    guess = msg["guess"].upper()
    feedback = msg["feedback"]
    solved = all(f == "correct" for f in feedback)

    def apply():
        global current_row, game_over
        apply_feedback(guess, feedback)

        if solved:
            game_over = True
            update_status("Solved!", TILE_CORRECT)
        elif current_row >= MAX_GUESSES:
            game_over = True
            update_status("Out of guesses!", "#e06c6c")

    root.after(0, apply)


def handle_game_over(msg):
    """Process GAME_OVER message: reveal the answer."""
    global game_over
    game_over = True
    answer = msg.get("answer", "?????").upper()
    root.after(0, lambda: update_status(f"The word was: {answer}", TILE_PRESENT))


def handle_new_round(msg):
    """Process NEW_ROUND message: reset the board for a new game."""
    root.after(0, reset_game)
    root.after(0, lambda: update_status("New round!", TILE_CORRECT))


# ─── GUI: Board Update Functions ────────────────────────────────

def apply_feedback(guess, feedback):
    """Apply color feedback to the current grid row and update the keyboard."""
    global current_row

    color_map = {
        "correct": TILE_CORRECT,
        "present": TILE_PRESENT,
        "absent": TILE_ABSENT,
    }
    priority = {"correct": 3, "present": 2, "absent": 1, None: 0}

    for col in range(WORD_LENGTH):
        letter = guess[col]
        state = feedback[col]
        color = color_map[state]

        # Update grid tile
        grid_frames[current_row][col].config(
            highlightbackground=color, highlightthickness=2, bg=color
        )
        grid_labels[current_row][col].config(text=letter, bg=color)

        # Update keyboard (only upgrade colors, never downgrade)
        key = letter.upper()
        if key in key_buttons:
            current_state = key_states.get(key)
            if priority[state] > priority[current_state]:
                key_buttons[key].config(bg=color)
                key_states[key] = state

    current_row += 1
    input_var.set("")
    entry.focus_set()


def update_status(text, color="#e06c6c"):
    """Update the status label below the input field."""
    status_label.config(text=text, fg=color)


def reset_game():
    """Reset the board for a new round."""
    global current_row, game_over
    current_row = 0
    game_over = False
    input_var.set("")
    status_label.config(text="", fg="#e06c6c")

    for row in range(MAX_GUESSES):
        for col in range(WORD_LENGTH):
            grid_labels[row][col].config(text="", bg=BG_COLOR)
            grid_frames[row][col].config(bg=BG_COLOR, highlightbackground=TILE_BORDER)

    for key in key_buttons:
        key_buttons[key].config(bg=KEY_BG)
        key_states[key] = None


# ─── GUI: Input Handling ────────────────────────────────────────

def on_input_change(*args):
    """Mirror typed text into the current grid row as a live preview."""
    if game_over:
        return
    value = input_var.get().upper()[:WORD_LENGTH]
    input_var.set(value)
    for col in range(WORD_LENGTH):
        letter = value[col] if col < len(value) else ""
        grid_labels[current_row][col].config(text=letter)
        border_color = TEXT_COLOR if letter else TILE_BORDER
        grid_frames[current_row][col].config(highlightbackground=border_color)


def on_key_press(event):
    """Handle physical keyboard input."""
    if game_over:
        return
    if event.keysym == "Return":
        submit_guess()
    elif event.keysym == "BackSpace":
        current = input_var.get()
        input_var.set(current[:-1])


def on_key_click(key):
    """Handle on-screen keyboard click."""
    if game_over:
        return
    current = input_var.get()
    if len(current) < WORD_LENGTH:
        input_var.set(current + key)
    entry.focus_set()


def submit_guess():
    """
    Validate the guess locally, then package it into a GUESS packet
    and send it to the server. Always append the \\n boundary.
    """
    if game_over:
        return

    guess = input_var.get().upper()

    if len(guess) != WORD_LENGTH:
        update_status(f"Word must be {WORD_LENGTH} letters!")
        return

    if not guess.isalpha():
        update_status("Only letters allowed!")
        return

    update_status("")

    # Protocol: Package guess into a GUESS packet
    send_to_server({"type": "GUESS", "guess": guess})


# ─── GUI: Build Functions ───────────────────────────────────────

def build_grid(parent):
    """Construct the 6x5 Wordle letter grid."""
    for row in range(MAX_GUESSES):
        row_frame = tk.Frame(parent, bg=BG_COLOR)
        row_frame.pack(pady=2)
        for col in range(WORD_LENGTH):
            cell_frame = tk.Frame(
                row_frame, width=56, height=56, bg=BG_COLOR,
                highlightbackground=TILE_BORDER, highlightthickness=2
            )
            cell_frame.pack(side=tk.LEFT, padx=2)
            cell_frame.pack_propagate(False)

            label = tk.Label(
                cell_frame, text="", font=("Helvetica Neue", 22, "bold"),
                fg=TEXT_COLOR, bg=BG_COLOR, justify=tk.CENTER
            )
            label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            grid_frames[row][col] = cell_frame
            grid_labels[row][col] = label


def build_input(parent):
    """Construct the text input field and submit button."""
    global input_var, entry, status_label

    input_var = tk.StringVar()
    input_var.trace_add("write", on_input_change)

    input_label = tk.Label(
        parent, text="Type your guess:",
        font=("Helvetica Neue", 11), fg="#808080", bg=BG_COLOR
    )
    input_label.pack(pady=(0, 3))

    entry_frame = tk.Frame(parent, bg=BG_COLOR)
    entry_frame.pack()

    entry = tk.Entry(
        entry_frame, textvariable=input_var,
        font=("Helvetica Neue", 16, "bold"),
        fg=TEXT_COLOR, bg=INPUT_BG,
        insertbackground=TEXT_COLOR,
        relief=tk.FLAT, width=12, justify=tk.CENTER
    )
    entry.pack(side=tk.LEFT, padx=(0, 8), ipady=5)
    entry.focus_set()

    submit_btn = tk.Button(
        entry_frame, text="ENTER",
        font=("Helvetica Neue", 11, "bold"),
        fg=TEXT_COLOR, bg=TILE_CORRECT,
        activebackground="#6aad5e", activeforeground=TEXT_COLOR,
        relief=tk.FLAT, padx=15, pady=5,
        command=submit_guess
    )
    submit_btn.pack(side=tk.LEFT)

    status_label = tk.Label(
        parent, text="Connecting to server...",
        font=("Helvetica Neue", 11), fg="#808080", bg=BG_COLOR
    )
    status_label.pack(pady=(5, 0))


def build_keyboard(parent):
    """Construct the on-screen keyboard."""
    rows = [
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        list("ZXCVBNM")
    ]
    for row_keys in rows:
        row_frame = tk.Frame(parent, bg=BG_COLOR)
        row_frame.pack(pady=2)
        for key in row_keys:
            btn = tk.Button(
                row_frame, text=key,
                font=("Helvetica Neue", 12, "bold"),
                fg="#000000", bg=KEY_BG,
                activebackground="#9a9a9c", activeforeground="#000000",
                highlightbackground=KEY_BG,
                width=3, height=2,
                command=lambda k=key: on_key_click(k)
            )
            btn.pack(side=tk.LEFT, padx=2)
            key_buttons[key] = btn
            key_states[key] = None


def build_ui():
    """Assemble the complete GUI layout."""
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.pack(padx=10, pady=10)

    # Title
    title = tk.Label(
        main_frame, text="GROUDLE",
        font=("Helvetica Neue", 28, "bold"),
        fg=TEXT_COLOR, bg=BG_COLOR
    )
    title.pack(pady=(0, 10))

    # Guess grid
    grid_frame = tk.Frame(main_frame, bg=BG_COLOR)
    grid_frame.pack(pady=(0, 15))
    build_grid(grid_frame)

    # Input area
    input_frame = tk.Frame(main_frame, bg=BG_COLOR)
    input_frame.pack(pady=(0, 10))
    build_input(input_frame)

    root.bind("<Key>", on_key_press)


# ─── Client Entry Point ────────────────────────────────────────

def start_client():
    """
    Main client execution. Initializes the socket, builds the GUI,
    and starts the listener thread.
    """
    global client, root

    # Initialize an IPv4 (AF_INET) TCP (SOCK_STREAM) socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # Handshake Protocol: Send initial connection request
    send_to_server({"type": "CONNECT"})

    # Build Tkinter GUI
    root = tk.Tk()
    root.title("Multiplayer Wordle")
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)
    build_ui()

    # Start listener thread (daemon so it dies with the main thread)
    listener = threading.Thread(target=listen_to_server, daemon=True)
    listener.start()

    # Run the Tkinter main loop
    root.mainloop()

    # Cleanup on window close
    client.close()


if __name__ == "__main__":
    start_client()

 