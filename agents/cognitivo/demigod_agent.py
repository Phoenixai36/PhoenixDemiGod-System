# demigod-agent.py
# Lógica del DemiGod Agent

def make_decision(data):
    if data["input"] == "task1":
        return {"status": "success", "decision": "orchestrate"}
    return {"status": "failure"}

if __name__ == "__main__":
    print(make_decision({"input": "task1"}))