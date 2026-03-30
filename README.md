# **CMPT 371 A3 Socket Programming `Tic-Tac-Toe`**

**Course:** CMPT 371 \- Data Communications & Networking  
**Instructor:** Mirza Zaeem Baig  
**Semester:** Spring 2026  
<span style="color: purple;">***RUBRIC NOTE: As per submission guidelines, only one group member will submit the link to this repository on Canvas.***

## **Group Members**

| Name | Student ID | Email |
| :---- | :---- | :---- |
| Jane Doe | 301111111 | jane.doe@university.edu |
| John Smith | 301222222 | john.smith@university.edu |

## **1\. Project Overview & Description**

This project is a multiplayer Tic-Tac-Toe game built using Python's Socket API (TCP). It allows two distinct clients to connect to a central server, be matched into a game lobby, and play against each other in real-time. The server handles the game logic, board state validation, and win-condition checking, ensuring that clients cannot cheat by modifying their local game state.

## **2\. System Limitations & Edge Cases**

As required by the project specifications, we have identified and handled (or defined) the following limitations and potential issues within our application scope:

* **Handling Multiple Clients Concurrently:** 
  * <span style="color: green;">*Solution:*</span> We utilized Python's threading module. When two clients connect, they are popped from the matchmaking\_queue and assigned to an isolated game\_session daemon thread. This ensures concurrent games do not block the main server event listener.  
  * <span style="color: red;">*Limitation:*</span> Thread creation is limited by system resources. An enterprise application would eventually need a thread pool or asynchronous I/O (like asyncio) to handle tens of thousands of connections.  
* **TCP Stream Buffering:** 
  * <span style="color: green;">*Solution:*</span> TCP is a continuous byte stream, meaning multiple JSON messages can be mashed together if sent rapidly. We implemented an application-layer fix by appending a newline \\n to all JSON payloads and splitting the buffer on the client/server side to process them atomically.  
* **Input Validation & Security:** 
  * <span style="color: red;">*Limitation:*</span> The client side uses a basic try/except ValueError to prevent crashes from bad user input (like typing letters instead of numbers). However, malicious users could still theoretically modify the client script to send invalid coordinates. Our server assumes well-formatted JSON integers in this basic implementation.

## **3\. Video Demo**

<span style="color: purple;">***RUBRIC NOTE: Include a clickable link.***</span>  
Our 2-minute video demonstration covering connection establishment, data exchange, real-time gameplay, and process termination can be viewed below:  
[**▶️ Watch Project Demo on YouTube**](https://www.youtube.com/watch?v=dQw4w9WgXcQ)

## **4\. Prerequisites (Fresh Environment)**

To run this project, you need:

* **Python 3.10** or higher.  
* No external pip installations are required (uses standard socket, threading, json, sys libraries).  
* (Optional) VS Code or Terminal.

<span style="color: purple;">***RUBRIC NOTE: No external libraries are required. Therefore, a requirements.txt file is not strictly necessary for dependency installation, though one might be included for environment completeness.***</span>

## **4\. Step-by-Step Run Guide**

<span style="color: purple;">***RUBRIC NOTE: The grader must be able to copy-paste these commands.***</span>


### **Step 1: Start the Server**

Open your terminal and navigate to the project folder. The server binds to 127.0.0.1 on port 5050\.  
```bash
python server.py  
# Console output: "[STARTING] Server is listening on 127.0.0.1:5050"
```

### **Step 2: Connect Player 1 (X)**

Open a **new** terminal window (keep the server running). Run the client script to start the first client.  
```bash
python client.py  
# Console output: "Connected. Waiting for opponent..."
```

### **Step 3: Connect Player 2 (O)**

Open a **third** terminal window. Run the client script again to start the second client.  
```bash
python client.py  
# Console output: "Connected. Waiting for opponent..."
# Console output: "Match found! You are Player O."
```

### **Step 4: Gameplay**

1. **Player X** will be prompted: Enter row and col (e.g., '1 1'):.  
2. Type two numbers separated by a space (from 0 to 2\) and press Enter.  
3. The server updates the board on both screens.  
4. **Player O** takes their turn.  
5. The connection naturally terminates when a win/draw is achieved.

## **5\. Technical Protocol Details (JSON over TCP)**

We designed a custom application-layer protocol for data exchange usin JSON over TCP:

* **Message Format:** `{"type": <string>, "payload": <data>}`  
* **Handshake Phase:** \* Client sends: `{"type": "CONNECT"}`  
  * Server responds: `{"type": "WELCOME", "payload": "Player X"}`  
* **Gameplay Phase:**  
  * Client sends: `{"type": "MOVE", "row": 1, "col": 1}`  
  * Server broadcasts: `{"type": "UPDATE", "board": [[...], [...], [...]], , "turn": "O", "status": "ongoing"}`


## **6\. Academic Integrity & References**

<span style="color: purple;">***RUBRIC NOTE: List all references used and help you got. Below is an example.***</span>

* **Code Origin:**  
  * The socket boilerplate was adapted from the course tutorial "TCP Echo Server". The core multithreaded game logic, protocol, and state management were written by the group.  
* **GenAI Usage:**  
  * ChatGPT was used to assist in generating the Unicode box-drawing characters for the CLI interface, and to help structure the TCP buffer-splitting logic (`\n delimiter`).  
  * Gemini was used to help in `README.md` writing and polishing.  
  * GitHub Copilot was used to help plan the workflow of the application.   
* **References:**  
  * [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)  
  * [Real Python: Intro to Python Threading](https://realpython.com/intro-to-python-threading/)