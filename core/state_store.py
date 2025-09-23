# core/state_store.py
import json

def load_state(state_path: str):
    """加载状态文件"""
    with open(state_path, "r") as f:
        return json.load(f)

def save_state(state_path: str, state: dict):
    """保存状态文件"""
    with open(state_path, "w") as f:
        json.dump(state, f, indent=4)
