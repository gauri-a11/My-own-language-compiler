import json
from flask import Flask, jsonify, request

app = Flask(__name__)

# Global variable to hold program lines received from the frontend
program_lines = []

# Route to receive the code input from the frontend (POST request)
@app.route('/api/data', methods=['POST'])
def process_data():
    data = request.json
    global program_lines
    received_data = data.get('data', None)

    if not received_data:
        return jsonify({'error': 'No data received'}), 400

    program_lines = received_data.split('\n')
    return jsonify({'status': 'Code received successfully'})

# Route to process the received code and return the output (GET request)
@app.route('/api/data2', methods=['GET'])
def process_code():
    global program_lines
    output = []  # Store output to be sent back to the frontend
    label_tracker = {}

    # Simple stack implementation
    class Stack:
        def __init__(self, size):
            self.buf = [None] * size
            self.sp = -1  # Stack pointer

        def push(self, value):
            self.sp += 1
            self.buf[self.sp] = value

        def pop(self):
            if self.sp < 0:
                raise IndexError("Stack underflow")
            value = self.buf[self.sp]
            self.sp -= 1
            return value

        def top(self):
            if self.sp < 0:
                raise IndexError("Stack is empty")
            return self.buf[self.sp]

    # Program execution logic
    stack = Stack(256)  # Initialize the stack with size 256
    pc = 0  # Program counter
    loop_stack = []  # Stack to manage loops
    current_char = '*'  # Default character for printing

    while pc < len(program_lines):
        line = program_lines[pc].strip()
        pc += 1

        if not line:
            continue  # Skip empty lines

        parts = line.split(" ")
        opcode = parts[0]

        if opcode.endswith(":"):  # Handle labels
            label_tracker[opcode[:-1]] = pc
            continue

        if opcode == "SET_CHAR":
            if len(parts) < 2:
                output.append("Error: SET_CHAR requires a character argument.")
                break
            current_char = parts[1].strip('"')  # Set the character for printing
        elif opcode == "PUSH":
            if len(parts) < 2:
                output.append("Error: PUSH requires a value.")
                break
            value = parts[1].strip('"')  # Remove quotes for strings
            try:
                value = int(value)  # Try converting to an integer
            except ValueError:
                pass  # Keep as string if conversion fails
            stack.push(value)
        elif opcode == "POP":
            try:
                stack.pop()
            except IndexError:
                output.append("Error: Attempted to POP from an empty stack.")
                break
        elif opcode == "ADD":
            try:
                a = stack.pop()
                b = stack.pop()
                if isinstance(a, int) and isinstance(b, int):
                    stack.push(b + a)  # Perform addition for numbers
                else:
                    stack.push(str(b) + str(a))  # Perform concatenation for strings
            except IndexError:
                output.append("Error: Attempted to ADD with insufficient values on stack.")
                break
        elif opcode == "PRINT":
            if stack.sp >= 0:  # Check if stack is not empty
                value = stack.pop()
                output.append(str(value))  # Print the string or character as is
            else:
                output.append("Error: Attempted to PRINT from an empty stack.")
                break
        elif opcode == "HALT":
            break  # Stop execution
        elif opcode == "FOR":
            try:
                count = stack.pop()  # Number of iterations
                loop_stack.append((pc, count))  # Save current position and count
            except IndexError:
                output.append("Error: Attempted to FOR with insufficient values on stack.")
                break
        elif opcode == "END_FOR":
            if not loop_stack:
                output.append("Error: Mismatched END_FOR with no corresponding FOR.")
                break
            start_pc, count = loop_stack.pop()
            count -= 1
            if count > 0:
                stack.push(count)  # Push the decremented count back to stack
                pc = start_pc  # Jump back to start of the loop
        else:
            output.append(f"Unexpected opcode: {opcode}")

    return jsonify({'output': output})

# Function to handle serverless requests (if deploying as serverless function)
def handler(event, context):
    # Check for request type
    if event['httpMethod'] == 'POST':
        return process_data()
    elif event['httpMethod'] == 'GET':
        return process_code()
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }

if __name__ == '__main__':
    app.run(debug=True)
