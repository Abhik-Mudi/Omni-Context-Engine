import sys
import subprocess

command = sys.argv[1:]
if len(command) > 0:
    try:
        res = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        session_logs = []
        while True:
            output = res.stdout.readline()

            if output:
                session_logs.append(output)
                print(output, end="", flush=True)  # Print to console immediately

            # Check if the process has finished
            if res.poll() is not None and not output:
                break

        print(f"Return code {res.poll()}")
        full_crash_payload = ""
        if res.poll():
            full_crash_payload = "".join(session_logs)
        print(session_logs, full_crash_payload)

    except FileNotFoundError:
        print("Couldn't find the file")

else:
    print("No arg provided")
