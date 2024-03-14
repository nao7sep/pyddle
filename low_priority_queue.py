import json
import pyddle_datetime as datetime
import pyddle_file_system as file_system
import uuid

# ------------------------------------------------------------------------------
#     Classes
# ------------------------------------------------------------------------------

class TaskInfo:
    def __init__(self, guid, creation_utc, done_utc, is_active, is_shown, content, times_per_week):
        self.guid = guid
        self.creation_utc = creation_utc
        self.done_utc = done_utc
        self.is_active = is_active
        self.is_shown = is_shown
        self.content = content
        self.times_per_week = times_per_week

def serialize_task(task):
    return {
        "guid": str(task.guid),
        "creation_utc": datetime.utc_to_roundtrip_string(task.creation_utc),
        "done_utc": datetime.utc_to_roundtrip_string(task.done_utc) if task.done_utc is not None else None,
        "is_active": task.is_active,
        "is_shown": task.is_shown,
        "content": task.content,
        "times_per_week": task.times_per_week
    }

def deserialize_task(task_data):
    return TaskInfo(
        uuid.UUID(task_data["guid"]),
        datetime.roundtrip_string_to_utc(task_data["creation_utc"]),
        datetime.roundtrip_string_to_utc(task_data["done_utc"]) if task_data["done_utc"] is not None else None,
        task_data["is_active"],
        task_data["is_shown"],
        task_data["content"],
        task_data["times_per_week"]
    )

class TaskList:
    def __init__(self, tasks_file_path):
        self.tasks_file_path = tasks_file_path
        self.tasks = []

    def load(self):
        with file_system.open_file_and_detect_utf_encoding(self.tasks_file_path) as tasks_file:
            data_from_json = json.load(tasks_file)
            self.tasks = [deserialize_task(task_data) for task_data in data_from_json]

    def save(self):
        file_system.create_parent_directory(self.tasks_file_path)

        with file_system.open_file_and_write_utf_encoding_bom(self.tasks_file_path) as tasks_file:
            json.dump(self.tasks, tasks_file, indent=4, default=serialize_task)

    def create_task(self, task):
        self.tasks.append(task)
        self.save()
        return task

    def create_task(self, content, times_per_week):
        task = TaskInfo(uuid.uuid4(), datetime.get_utc_now(), None, True, True, content, times_per_week)
        return self.create_task(task)

    def update_task(self, task):
        for index, existing_task in enumerate(self.tasks):
            if existing_task.guid == task.guid:
                self.tasks[index] = task
                self.save()
                return True

        return False

    def delete_task(self, task):
        for index, existing_task in enumerate(self.tasks):
            if existing_task.guid == task.guid:
                del self.tasks[index]
                self.save()
                return True

        return False
