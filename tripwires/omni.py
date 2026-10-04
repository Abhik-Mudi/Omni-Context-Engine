import sys
import subprocess
import requests
from collections import deque

session_payload = deque(maxlen=500)

command = sys.argv[1:]
if len(command) > 0:
    try:
        res = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        while True:
            output = res.stdout.readline()

            if output:
                session_payload.append(output)
                print(output, end="", flush=True)  # Print to console immediately

            # Check if the process has finished
            if res.poll() is not None and not output:
                break

        print(f"Return code {res.poll()}")

        final_payload = "".join(session_payload)

        payload = {"source":"terminal", "payload": {"command": command, "exit_code": res.poll(), "logs": final_payload}}

        try:
            requests.post("http://localhost:8000/api/event", json=payload)

        except requests.exceptions.RequestException:
            print("Exception request")

    except FileNotFoundError:
        print("Couldn't find the file")

else:
    print("No arg provided")
