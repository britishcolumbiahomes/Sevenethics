"""Run a research session. Usage: python research.py "your topic here"

Loads AGENT_ID and ENVIRONMENT_ID from the environment. Streams the
agent's progress to stdout, then downloads the generated report.
"""

import os
import sys
import time

import anthropic

client = anthropic.Anthropic()

AGENT_ID = os.environ["AGENT_ID"]
ENVIRONMENT_ID = os.environ["ENVIRONMENT_ID"]

topic = " ".join(sys.argv[1:])
if not topic:
    sys.exit('Usage: python research.py "your topic here"')

# Create a fresh session for this research task. Sessions are disposable.
session = client.beta.sessions.create(
    agent=AGENT_ID,
    environment_id=ENVIRONMENT_ID,
    title=f"Research: {topic[:60]}",
)
print(f"[session {session.id} started]\n")

# Stream-first: open the SSE stream BEFORE sending the kickoff message,
# otherwise early events arrive buffered in one batch.
with client.beta.sessions.events.stream(session_id=session.id) as stream:
    client.beta.sessions.events.send(
        session_id=session.id,
        events=[{
            "type": "user.message",
            "content": [{
                "type": "text",
                "text": (
                    f"Research this topic and produce an HTML report saved "
                    f"to /mnt/session/outputs/report.html:\n\n{topic}"
                ),
            }],
        }],
    )

    for event in stream:
        if event.type == "agent.message":
            for block in event.content:
                if block.type == "text":
                    print(block.text, end="", flush=True)
        elif event.type == "agent.tool_use":
            print(f"\n[using tool: {event.name}]", flush=True)
        elif event.type == "session.status_terminated":
            print("\n[session terminated]")
            break
        elif event.type == "session.status_idle":
            # Idle can be transient (e.g. waiting on a tool result).
            # Only break when the stop reason is terminal.
            stop = event.stop_reason
            if stop and stop.type != "requires_action":
                print(f"\n[done: {stop.type}]")
                break

# Brief lag between session-idle and outputs being indexed by the Files API.
time.sleep(2)

# Download every file the agent wrote to /mnt/session/outputs/.
files = client.beta.files.list(
    scope_id=session.id,
    betas=["managed-agents-2026-04-01"],
)
for f in files.data:
    content = client.beta.files.download(f.id)
    content.write_to_file(f.filename)
    print(f"Saved: ./{f.filename}")
