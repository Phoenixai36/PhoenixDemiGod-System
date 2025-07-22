# thanatos-agent.py
# Lógica del Thanatos Agent

import subprocess

def respawn_agent(agent_name):
    """
    Invokes the thanatos-agent.sh script to respawn a given agent.
    """
    script_path = "autogen/scripts/thanatos-agent.sh"
    try:
        print(f"Respawning agent: {agent_name}...")
        subprocess.run([script_path, agent_name], check=True)
        print(f"Agent {agent_name} respawned successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error respawning agent {agent_name}: {e}")
    except FileNotFoundError:
        print(f"Error: Script not found at {script_path}")

if __name__ == "__main__":
    # Example usage: respawn the 'demigod' agent
    respawn_agent("demigod")