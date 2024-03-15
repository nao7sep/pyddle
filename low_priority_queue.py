# Created: 2024-03-14
# A simple app to manage a queue of low-priority tasks.

import copy
import datetime
import enum
import json
import os
import pyddle_console as console
import pyddle_datetime as dt
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_json_based_kvs as kvs
import pyddle_string as string
import random
import re
import traceback
import uuid

# ------------------------------------------------------------------------------
#     Classes
# ------------------------------------------------------------------------------

class TaskResult(enum.Enum):
    Done = 1,
    Postponed = 2

class TaskInfo:
    def __init__(self, guid, creation_utc, handled_utc, is_active, is_shown, content, times_per_week, result: TaskResult):
        self.guid = guid
        self.creation_utc = creation_utc
        # AI said handling_utc would be confusing as it might be interpreted as the time that the task was scheduled to be executed.
        # Then, I asked whether creation_utc too should be created_utc for consistency and it said creation_utc was more natural.
        self.handled_utc = handled_utc
        self.is_active = is_active
        self.is_shown = is_shown
        self.content = content
        self.times_per_week = times_per_week
        self.result = result

# It looks like this helper method is applied to any object that json.dump cant natively serialize.
# It would be good practice to serialize only expected types and raise an error if an unexpected type appears.
def serialize_task(task):
    if isinstance(task, TaskInfo):
        return {
            "guid": str(task.guid),
            "creation_utc": dt.utc_to_roundtrip_string(task.creation_utc),
            "handled_utc": dt.utc_to_roundtrip_string(task.handled_utc) if task.handled_utc is not None else None,
            "is_active": task.is_active,
            # is_shown is not saved.
            # It is a state that persists only during the current run of the app.
            "content": task.content,
            "times_per_week": task.times_per_week,
            # If None, None is set.
            # If not, serialize_task is called.
            "result": task.result
        }

    elif isinstance(task, TaskResult):
        return task.name

    else:
        raise RuntimeError(f"Unsupported type: {type(task)}")

def deserialize_task(task_data):
    return TaskInfo(
        uuid.UUID(task_data["guid"]),
        dt.roundtrip_string_to_utc(task_data["creation_utc"]),
        dt.roundtrip_string_to_utc(task_data["handled_utc"]) if task_data["handled_utc"] is not None else None,
        task_data["is_active"],
        True, # is_shown is not saved.
        task_data["content"],
        task_data["times_per_week"],
        # If the value is an integer, the conversion to TaskResult will fail.
        # Enum objects should be represented as integers in databases,
        #     but in text files, I believe strings would be more user-friendly.
        TaskResult[task_data["result"]] if task_data["result"] is not None else None
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

    def create_task(self, task, no_save=False):
        self.tasks.append(task)

        if not no_save:
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

def generate_sample_data(handled_task_list, task_list):
    tasks = [
        # AI-generated trivial life-related tasks that are not valuable but must not be neglected:

        ("Check the mail", 3),
        ("Water indoor plants", 2),
        ("Take out the trash", 3),
        ("Make the bed daily", 7),
        ("Dust the living room", 1),
        ("Get a haircut", 1),
        ("Charge electronics", 4),
        ("Clean the bathroom sink", 2),
        ("Restock toiletries", 1),
        ("Vacuum the floor", 2),
        ("Check home security devices", 1),
        ("Review personal finances", 1),
        ("Wipe kitchen counters", 4),
        ("Check the refrigerator for expired items", 1),
        ("Clean the microwave", 1),
        ("Do the laundry", 2),
        ("Change the bed sheets", 1),
        ("Clean the windows", 1),
        ("Sweep the porch", 1),
        ("Water the garden", 3),
        ("Check for mail packages", 2),
        ("Clean out the car", 1),
        ("Back up digital files", 1),
        ("Update computer software", 1),
        ("Check smoke detectors", 1),
        ("Replace air filters", 1),
        ("Organize the desk", 1),
        ("Tidy living spaces", 3),
        ("Wash the dishes", 7),
        ("Restock the fridge and pantry", 1),
        ("Check for needed repairs around the home", 1),
        ("Plan weekly meals", 1),
        ("Prepare work or school bags", 5),
        ("Check pet supplies", 1),
        ("Review appointments and schedules", 3)
    ]

    for content, times_per_week in tasks:
        # As the goal of the sample data is to test the app's "stat" command,
        #     trivial attributes such as creation_utc and is_active are not randomized here.
        task_list.create_task(TaskInfo(uuid.uuid4(), dt.get_utc_now(), None, True, True, content, times_per_week, None), no_save=True)

    task_list.save()

    # As of 2024-03-15, generating handled tasks in the past 30 * 365 days on my 15 year old computer takes 2 minutes.
    # The size of handled_tasks.json is 41,771 KB.
    # Running the script in Windows Explorer takes 3 seconds until the tasks are shown.
    # Re-showing them by the Enter key causes no noticeable delay.

    # Python appears to handle arrays reasonably fast.
    # The bottleneck would be JSON serialization; deserialization is OK.
    # It's anyway unwise to recursively serialize such a large number of objects into a JSON file,
    #     but it doesnt hurt to remember incremental serialization should drastically improve performance,
    #     allowing JSON to handle relatively large data sets (if it's absolutely necessary).

    days = 365 # Just enough to test the "stat" command.
    inclusive_min_handled_tasks_per_day = 0
    inclusive_max_handled_tasks_per_day = round(len(tasks) * 7 / 10)
    done_tasks_out_of_10_handled_ones = 7

    utc_now = dt.get_utc_now()

    for day_offset in range(days - 1, -1, -1):
        # "utc" is like an adjective here.
        utc_then = utc_now - datetime.timedelta(days=day_offset)
        handled_tasks = random.randint(inclusive_min_handled_tasks_per_day, inclusive_max_handled_tasks_per_day)
        done_tasks = round(handled_tasks * done_tasks_out_of_10_handled_ones / 10)

        for index in range(handled_tasks):
            # In python, datetime objects are offset-aware OR offset-naive.
            # Maybe I'm missing something, but datetime.date() seems to return an offset-naive object,
            #     not an offset-aware representation of the moment the day has started.
            # So, date() + timedelta(seconds) resultantly causes a comparison error between offset-aware and offset-naive objects.
            # That's why the following code uses datetime's constructor to create a randomized offset-aware object.
            # https://docs.python.org/3/library/datetime.html

            total_seconds = random.randint(0, 24 * 60 * 60 - 1)
            hours = total_seconds // (60 * 60)
            minutes = (total_seconds % (60 * 60)) // 60
            seconds = total_seconds % 60

            # "utc" is a noun here.
            handled_utc = datetime.datetime(utc_then.year, utc_then.month, utc_then.day, hours, minutes, seconds, random.randint(0, 1000000 - 1), tzinfo=datetime.UTC)

            task = random.choice(task_list.tasks) # Allowing duplicates.

            handled_task = copy.copy(task)
            handled_task.handled_utc = handled_utc

            if index < done_tasks:
                handled_task.result = TaskResult.Done

            else:
                handled_task.result = TaskResult.Postponed

            handled_task_list.create_task(handled_task, no_save=True)

    handled_task_list.save()

def select_shown_tasks(handled_task_list, task_list, shows_all):
    seven_days_ago_utc = dt.get_utc_now() - datetime.timedelta(days=7)
    handled_tasks_in_last_seven_days = [task for task in handled_task_list.tasks if task.handled_utc is not None and task.handled_utc > seven_days_ago_utc]

    execution_counts = {}

    for task in handled_tasks_in_last_seven_days:
        if task.guid in execution_counts:
            execution_counts[task.guid] += 1

        else:
            execution_counts[task.guid] = 1

    shown_tasks = []

    if not shows_all:
        for task in task_list.tasks:
            if task.is_active and task.is_shown:
                if task.guid in execution_counts:
                    if execution_counts[task.guid] < task.times_per_week:
                        shown_tasks.append(task)

                else:
                    shown_tasks.append(task)

    else:
        shown_tasks = task_list.tasks

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

    handled_tasks_file_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}handled_tasks_file_path")
    console.print(f"handled_tasks_file_path: {handled_tasks_file_path}")

    task_list = TaskList(tasks_file_path)
    task_list.load()

    handled_task_list = TaskList(handled_tasks_file_path)
    handled_task_list.load()

    console.print("Type 'help' for a list of commands.")

    shows_all_next_time = False

    while True:
        try:
            shown_tasks, execution_counts = select_shown_tasks(handled_task_list, task_list, shows_all_next_time)

            if shown_tasks:
                console.print("Tasks:")

                for index, task in enumerate(shown_tasks):
                    if task.guid in execution_counts:
                        execution_count = execution_counts[task.guid]

                    else:
                        execution_count = 0

                    additional_info = ""

                    if not task.is_active:
                        additional_info += ", inactive"

                    if not task.is_shown:
                        additional_info += ", hidden"

                    if execution_count >= task.times_per_week:
                        additional_info += f", good"

                    console.print(f"{index + 1}. {task.content} ({execution_count}/{task.times_per_week}{additional_info})", indents=string.leveledIndents[1])

            shows_all_next_time = False

            console.print_important("Command", end="")
            command_str = input(": ")

            command, number, parameter = parse_command_str(command_str)

            if string.equals_ignore_case(command, "help"):
                console.print("Commands:")
                console.print("help", indents=string.leveledIndents[1])

                if debugging.is_debugging():
                    console.print("sample => Generates sample data.", indents=string.leveledIndents[1])

                console.print("create <times_per_week> <content>", indents=string.leveledIndents[1])
                console.print("all => Shows all tasks including inactive/hidden ones.", indents=string.leveledIndents[1])
                console.print("done <task_number>", indents=string.leveledIndents[1])
                console.print("later <task_number>", indents=string.leveledIndents[1])
                console.print("deactivate <task_number> => Hides the task permanently; until you activate it again.", indents=string.leveledIndents[1])
                console.print("activate <task_number>", indents=string.leveledIndents[1])
                console.print("hide <task_number> => Hides the task temporarily; until you show it again or restart the app.", indents=string.leveledIndents[1])
                console.print("show <task_number>", indents=string.leveledIndents[1])
                console.print("content <task_number> <content>", indents=string.leveledIndents[1])
                console.print("times <task_number> <times_per_week>", indents=string.leveledIndents[1])
                console.print("delete <task_number> confirm => Use deactivate instead unless you have a reason for this destructive operation.", indents=string.leveledIndents[1])
                console.print("exit", indents=string.leveledIndents[1])
                continue

            elif debugging.is_debugging() and string.equals_ignore_case(command, "sample"):
                generate_sample_data(handled_task_list, task_list)
                continue

            elif string.equals_ignore_case(command, "create"):
                if validate_times_per_week(number) and parameter:
                    task_list.create_task(TaskInfo(uuid.uuid4(), dt.get_utc_now(), None, True, True, parameter, number, None))
                    continue

            elif string.equals_ignore_case(command, "all"):
                shows_all_next_time = True
                continue

            elif string.equals_ignore_case(command, "done"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    task = shown_tasks[number - 1]
                    task.is_shown = False
                    # is_shown is not saved.

                    handled_task = copy.copy(task)
                    handled_task.handled_utc = dt.get_utc_now()
                    handled_task.result = TaskResult.Done
                    handled_task_list.create_task(handled_task)

                    continue

            elif string.equals_ignore_case(command, "later"):
                if shown_tasks and validate_shown_task_index(shown_tasks, number):
                    task = shown_tasks[number - 1]
                    task.is_shown = False
                    # is_shown is not saved.

                    handled_task = copy.copy(task)
                    handled_task.handled_utc = dt.get_utc_now()
                    handled_task.result = TaskResult.Postponed
                    handled_task_list.create_task(handled_task)

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

            # The current implementation as of 2024-03-15 doesnt support negative numbers; they are explicitly excluded by the regex.
            # This part used to check if command, rather than command_str, was truthy.
            # Back then, "done -1" was converted to a tuple of None, None, None and was treated as if the Enter key was pressed without a command string.
            # Now, without changing the regex and still disallowing negative numbers, anything other than "" must be a valid command string.

            if command_str:
               console.print_error("Invalid command string.")

        except Exception:
            console.print_error(traceback.format_exc())

except Exception:
    console.print_error(traceback.format_exc())

finally:
    debugging.display_press_enter_key_to_continue_if_not_debugging()
