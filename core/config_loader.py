# core/config_loader.py
import json
from typing import Dict

def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, "r") as f:
        return json.load(f)

def save_config(config_path: str, config: Dict):
    """保存配置文件"""
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
