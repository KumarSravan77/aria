class ChatOpsCommandParser:
    SUPPORTED = {"/incident", "/approve-action", "/show-evidence", "/rollback", "/slo", "/chaos"}

    def parse(self, text: str) -> dict:
        parts = text.strip().split()
        if not parts:
            return {"valid": False, "error": "empty command"}
        command = parts[0]
        if command not in self.SUPPORTED:
            return {"valid": False, "command": command, "error": "unsupported command"}
        return {"valid": True, "command": command, "args": parts[1:], "safety_note": "Commands request actions only; mutations still go through policy and approval."}
