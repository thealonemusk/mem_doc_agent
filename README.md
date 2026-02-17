# Memory Doctor 🩺

Memory Doctor is an AI-powered static analysis CLI tool designed specifically for embedded C codebases (like FreeRTOS). It uses Abstract Syntax Tree (AST) parsing to extract complex memory operations and feeds them into an LLM agent to accurately detect memory leaks, dropped pointers, and unhandled thread handoffs.

## Features

* **Smart AST Extraction:** Uses `tree-sitter` to parse C code and isolate only the functions dealing with memory allocation (`pvPortMalloc`) and IPC queues (`xQueueSend`, `xQueueReceive`).
* **Multi-Thread Aware:** Understands the producer-consumer pattern and tracks pointers as they escape local scope into RTOS queues.
* **AI-Powered Analysis:** Leverages the Gemini 1.5 Pro model to evaluate control flow, catching early returns, unhandled timeouts, and complex conditional leaks that traditional static analyzers miss.
* **Minimal Context Window:** Keeps AI costs low and speeds up response times by only sending targeted, relevant code blocks rather than entire files.

## Prerequisites

* Python 3.x
* A valid Google Gemini API Key

## Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd memory_doctor

```


2. **Install the required Python dependencies:**
```bash
pip install tree-sitter tree-sitter-c google-generativeai python-dotenv

```


3. **Set up your environment variables:**
Create a file named `.env` in the root directory of the project and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here

```



## Usage

1. Place your embedded C codebase (`.c` and `.h` files) inside a folder named `src` in the root directory.
2. Run the tool:
```bash
python mem_doc.py

```



## Example Output

The CLI will parse the `src` directory, extract the relevant memory-handling functions, and output an AI-generated analysis for each suspect block:

```text
--- [Memory Doctor AI] Analyzing network_task.c ---
STATUS: LEAK DETECTED
REASON: The allocated pointer `pNetPacket` is not freed if `xQueueSend` fails and drops the packet.
FIX: Add a `vPortFree(pNetPacket)` inside the failed queue send condition block.

```
