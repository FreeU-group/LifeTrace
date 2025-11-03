from lifetrace_backend.storage import DatabaseManager
import os

db = DatabaseManager()
screenshots = db.get_event_screenshots(1)
print('事件1的截图:')
for s in screenshots[:3]:
    print(f'ID: {s["id"]}, 路径: {s["file_path"]}, 存在: {os.path.exists(s["file_path"])}')
