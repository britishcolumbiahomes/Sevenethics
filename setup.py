"""One-time setup: create the environment and agent. Run this ONCE.

After running, save the printed AGENT_ID and ENVIRONMENT_ID into a .env
file or your shell config. Every subsequent research run reuses them.
"""

import anthropic

client = anthropic.Anthropic()

# 1. Create the environment (the sandbox template).
#    Networking is unrestricted so the agent can reach search engines.
env = client.beta.environments.create(
    name="research-env",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)

# 2. Create the agent (model + system prompt + tool set).
#    This is a versioned, persisted object. Sessions reference it by ID.
agent = client.beta.agents.create(
    name="Research Assistant",
    model="claude-opus-4-7",
    system="""You are a research assistant. Given a topic, you:

1. Use web_search to gather current, authoritative information from
   multiple sources. Prefer primary sources, peer-reviewed work, and
   recent reporting from established outlets.
2. Synthesize findings into a clear report with: an executive summary,
   3-5 key findings, supporting detail, and a sources section.
3. Generate a single self-contained HTML file (inline CSS, no external
   assets) and save it to /mnt/session/outputs/report.html using bash.
4. Cite every factual claim with the source URL inline.

When done, briefly tell the user the report is ready.""",
    tools=[
        {"type": "agent_toolset_20260401", "default_config": {"enabled": True}},
    ],
)

print(f"ENVIRONMENT_ID={env.id}")
print(f"AGENT_ID={agent.id}")
print()
print("Save these two lines to your .env file (or export them).")
