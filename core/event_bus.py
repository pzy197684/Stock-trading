# core/event_bus.py
class EventBus:
    def __init__(self):
        # 存储事件及其回调函数
        self._subscribers = {}

    def subscribe(self, event_name, callback):
        """订阅事件"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def emit(self, event_name, data):
        """发布事件"""
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                callback(data)

# 实例化 EventBus
bus = EventBus()
