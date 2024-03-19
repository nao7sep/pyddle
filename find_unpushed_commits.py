# Created: 2024-03-19
# Checks repositories for actions that need to be taken.

# This app does a little more than finding unpushed commits, but that was the original purpose and I like the name's nature of being actionable.
# Although it's an option to rename it like repository_checker.py or get_status_of_repositories.py, I'll stick to the action-oriented name.

import os
import pyddle_console as console
import pyddle_debugging as debugging
import pyddle_json_based_kvs as kvs
import pyddle_path
import pyddle_string as string
import subprocess
import traceback

class RepositoryInfo:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.name = pyddle_path.basename(directory_path)
        self.__remote_branch_name = None
        self.__local_branch_name = None
        self.__untracked_files = None
        self.__conflicted_files = None
        self.__modified_files = None
        self.__staged_files = None
        self.__stashed_files = None
        self.__unpulled_commits = None
        self.__unpushed_commits = None

    def __set_remote_branch_name(self):
        os.chdir(self.directory_path)

        # https://git-scm.com/docs/git-rev-parse

        # HEAD@{upstream} refers to the upstream branch of the currently checked-out branch.
        # {upstream} refers to the default remote branch associated with the local branch the user is currently on.
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "HEAD@{upstream}"], capture_output=True)

        # If something is wrong like no upstream branch is configured, we just let the script crash.
        # Git is excessively complicated and a lot of things are one-time errors.

        self.__remote_branch_name = result.stdout.decode("utf-8").strip()

    @property
    def remote_branch_name(self):
        if self.__remote_branch_name is None:
            self.__set_remote_branch_name()

        return self.__remote_branch_name

    def __set_local_branch_name(self):
        os.chdir(self.directory_path)

        # HEAD refers to the current branch's latest commit.
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)

        self.__local_branch_name = result.stdout.decode("utf-8").strip()

    @property
    def local_branch_name(self):
        if self.__local_branch_name is None:
            self.__set_local_branch_name()

        return self.__local_branch_name

    def __set_untracked_conflicted_modified_and_staged_files(self):
        untracked_files = []
        conflicted_files = []
        modified_files = []
        staged_files = []

        os.chdir(self.directory_path)

        # https://git-scm.com/docs/git-status

        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True)

        for line in result.stdout.decode("utf-8").split("\n"):
            if not line:
                continue

            index_status_code = line[0:1]
            worktree_status_code = line[1:2]
            file_name = line[3:]

            # X           Y    Meaning
            # -------------------------------------------------
            #          [AMD]   not updated
            # M        [ MTD]  updated in index
            # T        [ MTD]  type changed in index
            # A        [ MTD]  added to index
            # D                deleted from index
            # R        [ MTD]  renamed in index
            # C        [ MTD]  copied in index
            # [MTARC]          index and work tree matches
            # [ MTARC]    M    work tree changed since index
            # [ MTARC]    T    type changed in work tree since index
            # [ MTARC]    D    deleted in work tree
            #             R    renamed in work tree
            #             C    copied in work tree
            # -------------------------------------------------
            # D           D    unmerged, both deleted
            # A           U    unmerged, added by us
            # U           D    unmerged, deleted by them
            # U           A    unmerged, added by them
            # D           U    unmerged, deleted by us
            # A           A    unmerged, both added
            # U           U    unmerged, both modified
            # -------------------------------------------------
            # ?           ?    untracked
            # !           !    ignored
            # -------------------------------------------------

            if index_status_code == "?" and worktree_status_code == "?":
                untracked_files.append(file_name)

            elif index_status_code == "U" or worktree_status_code == "U": # OR
                conflicted_files.append(file_name)

            elif index_status_code == "A" and worktree_status_code == "A":
                conflicted_files.append(file_name)

            elif index_status_code == "D" and worktree_status_code == "D":
                conflicted_files.append(file_name)

            elif worktree_status_code == "M":
                modified_files.append(file_name)

            elif index_status_code in ["M", "T", "A", "D", "R", "C" ]:
                staged_files.append(file_name)

        self.__untracked_files = untracked_files
        self.__conflicted_files = conflicted_files
        self.__modified_files = modified_files
        self.__staged_files = staged_files

    @property
    def untracked_files(self):
        if self.__untracked_files is None:
            self.__set_untracked_conflicted_modified_and_staged_files()

        return self.__untracked_files

    @property
    def conflicted_files(self):
        if self.__conflicted_files is None:
            self.__set_untracked_conflicted_modified_and_staged_files()

        return self.__conflicted_files

    @property
    def modified_files(self):
        if self.__modified_files is None:
            self.__set_untracked_conflicted_modified_and_staged_files()

        return self.__modified_files

    @property
    def staged_files(self):
        if self.__staged_files is None:
            self.__set_untracked_conflicted_modified_and_staged_files()

        return self.__staged_files

    def __set_stashed_files(self):
        stashed_files = []

        os.chdir(self.directory_path)

        # https://git-scm.com/docs/git-stash

        result = subprocess.run(["git", "stash", "list"], capture_output=True)

        for line in result.stdout.decode("utf-8").split("\n"):
            if not line:
                continue

            stashed_files.append(line)

        self.__stashed_files = stashed_files

    @property
    def stashed_files(self):
        if self.__stashed_files is None:
            self.__set_stashed_files()

        return self.__stashed_files

    def __set_unpulled_commits(self):
        unpulled_commits = []

        os.chdir(self.directory_path)

        remote_name = self.remote_branch_name.split("/")[0]

        # Fetches updates from all branches from the specified remote.
        result = subprocess.run(["git", "fetch", remote_name])

        # Getting the commits that are on the remote branch but not in HEAD, which points to the tip of the local branch.
        result = subprocess.run(["git", "log", f"HEAD..{self.remote_branch_name}", "--oneline"], capture_output=True)

        for line in result.stdout.decode("utf-8").split("\n"):
            if not line:
                continue

            unpulled_commits.append(line)

        self.__unpulled_commits = unpulled_commits

    @property
    def unpulled_commits(self):
        if self.__unpulled_commits is None:
            self.__set_unpulled_commits()

        return self.__unpulled_commits

    def __set_unpushed_commits(self):
        unpushed_commits = []

        os.chdir(self.directory_path)

        # https://git-scm.com/docs/git-log

        # Getting the commits that are in HEAD but not on the remote branch.
        result = subprocess.run(["git", "log", f"{self.remote_branch_name}..HEAD", "--oneline"], capture_output=True)

        for line in result.stdout.decode("utf-8").split("\n"):
            if not line:
                continue

            unpushed_commits.append(line)

        self.__unpushed_commits = unpushed_commits

    @property
    def unpushed_commits(self):
        if self.__unpushed_commits is None:
            self.__set_unpushed_commits()

        return self.__unpushed_commits

def is_good_remote_branch_name(name):
    # When I set HEAD to an old commit, I got an empty string as the remote branch name.

    # ChatGPT says:

    # In a detached HEAD state, `HEAD` points directly to a commit rather than to the tip of a branch.
    # As a result, `HEAD` loses its association with any branch,
    #     leading to commands like `git rev-parse` that inquire about branch names or remote tracking branches to return empty strings or `undefined` values.
    # This is because, without a branch context, there's no upstream or remote branch information available.

    # 1. Empty string: Commands might return an empty string if no branch name is associated with `HEAD` in a detached HEAD state.
    # 2. "HEAD": Some commands return "HEAD" as the output, indicating that `HEAD` is not pointing to any branch.
    # 3. undefined/null: In certain contexts, the absence of a branch might be indicated by `undefined`, `null`, or similar non-value indicators.
    # 4. Error/warning message: There might be explicit warnings or error messages indicating that the repository is in a detached HEAD state with no branch information.
    # 5. Commit SHA: Instead of branch information, commands like `git rev-parse HEAD` may return the SHA hash of the commit that `HEAD` is currently pointing to.

    # So far, I have only received empty strings as remote branch names.
    # Plus, "HEAD" has been returned as local branch names, but not as remote branch names.
    # I'll check for these two cases (just in case) and see what happens.

    return name and string.equals_ignore_case(name, "HEAD") == False

def is_good_local_branch_name(name):
    return name and string.equals_ignore_case(name, "HEAD") == False

# ------------------------------------------------------------------------------
#     App
# ------------------------------------------------------------------------------

try:
    kvs_key_prefix = "find_unpushed_commits/"

    repositories_directory_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}repositories_directory_path")
    console.print(f"repositories_directory_path: {repositories_directory_path}")

    for entry in os.listdir(repositories_directory_path):
        repository_directory_path = os.path.join(repositories_directory_path, entry)

        if os.path.isdir(repository_directory_path):
            git_directory_path = os.path.join(repository_directory_path, ".git")

            if os.path.isdir(git_directory_path):
                repository = RepositoryInfo(repository_directory_path)

                console.print(f"Repository: {repository.name}")

                if is_good_remote_branch_name(repository.remote_branch_name):
                    console.print(f"Remote: {repository.remote_branch_name}", indents=string.leveledIndents[1])

                else:
                    console.print_important(f"Remote: {repository.remote_branch_name}", indents=string.leveledIndents[1])

                if is_good_local_branch_name(repository.local_branch_name):
                    console.print(f"Local: {repository.local_branch_name}", indents=string.leveledIndents[1])

                else:
                    console.print_important(f"Local: {repository.local_branch_name}", indents=string.leveledIndents[1])

                if repository.untracked_files:
                    console.print("Untracked files:", indents=string.leveledIndents[1])

                    for file in repository.untracked_files:
                        console.print_important(file, indents=string.leveledIndents[2])

                if repository.conflicted_files:
                    console.print("Conflicted files:", indents=string.leveledIndents[1])

                    for file in repository.conflicted_files:
                        console.print_important(file, indents=string.leveledIndents[2])

                if repository.modified_files:
                    console.print("Modified files:", indents=string.leveledIndents[1])

                    for file in repository.modified_files:
                        console.print_important(file, indents=string.leveledIndents[2])

                if repository.staged_files:
                    console.print("Staged files:", indents=string.leveledIndents[1])

                    for file in repository.staged_files:
                        console.print_important(file, indents=string.leveledIndents[2])

                if repository.stashed_files:
                    console.print("Stashed files:", indents=string.leveledIndents[1])

                    for file in repository.stashed_files:
                        console.print_important(file, indents=string.leveledIndents[2])

                if repository.unpulled_commits:
                    console.print("Unpulled commits:", indents=string.leveledIndents[1])

                    for commit in repository.unpulled_commits:
                        console.print_important(commit, indents=string.leveledIndents[2])

                if repository.unpushed_commits:
                    console.print("Unpushed commits:", indents=string.leveledIndents[1])

                    for commit in repository.unpushed_commits:
                        console.print_important(commit, indents=string.leveledIndents[2])

except Exception:
    console.print_error(traceback.format_exc())

finally:
    debugging.display_press_enter_key_to_continue_if_not_debugging()
