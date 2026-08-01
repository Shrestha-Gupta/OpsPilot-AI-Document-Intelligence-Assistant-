from collections import defaultdict


class MemoryService:
    def __init__(self):
        self.sessions = defaultdict(list)

    def get_history(self, session_id: str):
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        self.sessions[session_id].append(
            {
                "role": role,
                "content": content,
            }
        )

    def clear_history(self, session_id: str):
        self.sessions.pop(session_id, None)