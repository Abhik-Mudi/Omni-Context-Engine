import sys
import subprocess
import requests
from collections import deque

# Initialize deque to store the session logs
session_payload = deque(maxlen=500)

# Get the command
command = sys.argv[1:]
command = " ".join(command)

if len(command) > 0:
    try:
        # Execute the command
        res = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True
        )

        while True:
            output = res.stdout.readline()

            # Store the logs in session_payload
            if output:
                session_payload.append(output)
                print(output, end="", flush=True)  # Print to console immediately

            # Check if the process has finished and text buffer is empty
            if res.poll() is not None and not output:
                break

        print(f"Return code {res.poll()}")

        final_payload = "".join(session_payload)

        payload = {"source":"terminal", "payload": {"command": command, "exit_code": res.poll(), "logs": final_payload}}

        try:
            # Log the event in the database
            requests.post("http://localhost:8000/api/event", json=payload)

        except requests.exceptions.RequestException:
            print("Exception request")

    except FileNotFoundError:
        print("Couldn't find the file")

else:
    print("No arg provided")
