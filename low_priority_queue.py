# Created: 2024-03-14
# A simple app to manage a queue of low-priority tasks.

import copy
import json
import os
import pyddle_console as console
import pyddle_datetime as datetime
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_json_based_kvs as kvs
import pyddle_string as string
import re
import traceback
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
        # is_shown is not saved.
        "content": task.content,
        "times_per_week": task.times_per_week
    }

def deserialize_task(task_data):
    return TaskInfo(
        uuid.UUID(task_data["guid"]),
        datetime.roundtrip_string_to_utc(task_data["creation_utc"]),
        datetime.roundtrip_string_to_utc(task_data["done_utc"]) if task_data["done_utc"] is not None else None,
        task_data["is_active"],
        True, # is_shown is not saved.
        task_data["content"],
        task_data["times_per_week"]
    )

class TaskList:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tasks = []

    def load(self):
        if os.path.isfile(self.file_path):
            with file_system.open_file_and_detect_utf_encoding(self.file_path) as tasks_file:
                data_from_json = json.load(tasks_file)
                self.tasks = [deserialize_task(task_data) for task_data in data_from_json]

    def save(self):
        file_system.create_parent_directory(self.file_path)

        with file_system.open_file_and_write_utf_encoding_bom(self.file_path) as tasks_file:
            json.dump(self.tasks, tasks_file, indent=4, default=serialize_task)

    def create_task(self, task):
        self.tasks.append(task)
        self.save()
        return task

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

# ------------------------------------------------------------------------------
#     Helpers
# ------------------------------------------------------------------------------

def select_shown_tasks(done_task_list, task_list, shows_all):
    seven_days_ago_utc = datetime.get_utc_now() - datetime.datetime.timedelta(days=7)
    done_tasks_in_last_seven_days = [task for task in done_task_list.tasks if task.done_utc is not None and task.done_utc > seven_days_ago_utc]

    execution_counts = {}

    for task in done_tasks_in_last_seven_days:
        if task.guid in execution_counts:
            execution_counts[task.guid] += 1

        else:
            execution_counts[task.guid] = 1

    shown_tasks = []

    for task in task_list.tasks:
        if task.is_active and task.is_shown:
            if task.guid in execution_counts:
                if execution_counts[task.guid] < task.times_per_week:
                    shown_tasks.append(task)

            else:
                shown_tasks.append(task)

    # Not great coding, but I dont want to change shown_tasks to an array of tuples.
    return shown_tasks, execution_counts

def parse_command_str(command_str):
    match = re.match(r"^(?P<command>[a-z]+)(\s+(?P<number>[0-9]+)(\s+(?P<parameter>.+))?)?$", command_str, re.IGNORECASE)

    if match:
        number_str = match.group("number")

        if number_str:
            try:
                # May fail if the number is too big.
                number = int(number_str)

                parameter_str = match.group("parameter")

                if parameter_str:
                    parameter_str = parameter_str.strip()

                return match.group("command"), number, parameter_str

            except Exception:
                pass

        else:
            return match.group("command"), number_str, match.group("parameter")

    return None, None, None

def validate_shown_task_index(shown_tasks, number):
    return number is not None and number > 0 and number <= len(shown_tasks)

def validate_times_per_week(number):
    return number is not None and number > 0

# ------------------------------------------------------------------------------
#     Application
# ------------------------------------------------------------------------------

try:
    kvs_key_prefix = "low_priority_queue/"

    tasks_file_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}tasks_file_path")
    console.print(f"tasks_file_path: {tasks_file_path}")

    done_tasks_file_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}done_tasks_file_path")
    console.print(f"done_tasks_file_path: {done_tasks_file_path}")

    task_list = TaskList(tasks_file_path)
    task_list.load()

    done_task_list = TaskList(done_tasks_file_path)
    done_task_list.load()

    shows_all_next_time = False

    while True:
        try:
            shown_tasks, execution_counts = select_shown_tasks(done_task_list, task_list, shows_all_next_time)

            if shown_tasks:
                console.print("Tasks:")

                for index, task in enumerate(shown_tasks):
                    if task.guid in execution_counts:
                        execution_count = execution_counts[task.guid]

                    else:
                        execution_count = 0

                    console.print(f"{index + 1}. {task.content} ({execution_count}/{task.times_per_week})", indents=string.leveledIndents[1])

            shows_all_next_time = False

            console.print_important("Commands", end="")
            command_str = input(": ")

            command, number, parameter = parse_command_str(command_str)

            if string.equals_ignore_case(command, "create"):
                if validate_times_per_week(number) and parameter:
                    task_list.create_task(TaskInfo(uuid.uuid4(), datetime.get_utc_now(), None, True, True, parameter, number))
                    continue

            elif string.equals_ignore_case(command, "all"):
                shows_all_next_time = True
                continue

            elif string.equals_ignore_case(command, "done"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    task = shown_tasks[number - 1]
                    task.is_shown = False
                    # is_shown is not saved.

                    done_task = copy.copy(task)
                    done_task.done_utc = datetime.get_utc_now()
                    done_task_list.create_task(done_task)

                    continue

            elif string.equals_ignore_case(command, "deactivate"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    task = shown_tasks[number - 1]
                    task.is_active = False
                    task_list.update_task(task)
                    continue

            elif string.equals_ignore_case(command, "activate"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    task = shown_tasks[number - 1]
                    task.is_active = True
                    task_list.update_task(task)
                    continue

            elif string.equals_ignore_case(command, "hide"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    task = shown_tasks[number - 1]
                    task.is_shown = False
                    task_list.update_task(task)
                    continue

            elif string.equals_ignore_case(command, "show"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    task = shown_tasks[number - 1]
                    task.is_shown = True
                    task_list.update_task(task)
                    continue

            elif string.equals_ignore_case(command, "content"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number) and parameter:
                    task = shown_tasks[number - 1]
                    task.content = parameter
                    task_list.update_task(task)
                    continue

            elif string.equals_ignore_case(command, "times"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number) and parameter:
                    try:
                        task = shown_tasks[number - 1]
                        task.times_per_week = int(parameter)
                        task_list.update_task(task)
                        continue

                    except Exception:
                        pass

            elif string.equals_ignore_case(command, "delete"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    if  string.equals_ignore_case(parameter, "confirm"):
                        task = shown_tasks[number - 1]
                        task_list.delete_task(task)

                    else:
                        console.print_warning("Destructive operation.")
                        console.print_warning("Consider deactivating the task instead or confirm deletion by adding 'confirm' to the command string.")

                    continue

            elif string.equals_ignore_case(command, "exit"):
                break

            if command:
               console.print_error("Invalid command string.")

        except Exception:
            console.print_error(traceback.format_exc())

except Exception:
    console.print_error(traceback.format_exc())

finally:
    debugging.display_press_enter_key_to_continue_if_not_debugging()
