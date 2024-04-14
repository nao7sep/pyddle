# Created: 2024-03-19
# Checks repositories for actions that need to be taken.

# This app does a little more than finding unpushed commits, but that was the original purpose and I like the name's nature of being actionable.
# Although it's an option to rename it like repository_checker.py or get_status_of_repositories.py, I'll stick to the action-oriented name.

import os
import subprocess
import traceback

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_global as pglobal
import pyddle_json_based_kvs as pkvs
import pyddle_path as ppath
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

class RepositoryInfo:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.name = ppath.basename(directory_path)
        self.__remote_branch_name = None
        self.__local_branch_name = None
        self.__untracked_files = None
        self.__conflicted_files = None
        self.__modified_files = None
        self.__deleted_files = None
        self.__staged_files = None
        self.__stashed_files = None
        self.__unpulled_commits = None
        self.__unpushed_commits = None

    def __set_remote_branch_name(self):
        os.chdir(self.directory_path)

        # https://git-scm.com/docs/git-rev-parse

        # HEAD@{upstream} refers to the upstream branch of the currently checked-out branch.
        # {upstream} refers to the default remote branch associated with the local branch the user is currently on.
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "HEAD@{upstream}"], capture_output=True, check=False)

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
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, check=False)

        self.__local_branch_name = result.stdout.decode("utf-8").strip()

    @property
    def local_branch_name(self):
        if self.__local_branch_name is None:
            self.__set_local_branch_name()

        return self.__local_branch_name

    def __set_untracked_conflicted_modified_deleted_and_staged_files(self):
        untracked_files = []
        conflicted_files = []
        modified_files = []
        deleted_files = []
        staged_files = []

        os.chdir(self.directory_path)

        # https://git-scm.com/docs/git-status

        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, check=False)

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

            # Added: 2024-03-21
            # These 4 cases CAN be considered as modifications:

            # M = modified
            # T = file type changed (regular file, symbolic link or submodule)
            # R = renamed
            # C = copied (if config option status.renames is set to "copies")

            # It appears some people prefer to see renamed files unmerged as pairs of deleted and "copied" files.
            # If the latter appear as "added" files, some may mistakenly recheck their contents although they havent been changed.

            # We generally dont need to know if "modified" files displayed by this script are actually "file type changed" or "renamed" or "copied" files
            #     as long as we get to know there's something in that repository to attend to.

            elif worktree_status_code in ["M", "T", "R", "C"]:
                modified_files.append(file_name)

            elif worktree_status_code == "D":
                deleted_files.append(file_name)

            elif index_status_code in ["M", "T", "A", "D", "R", "C"]:
                staged_files.append(file_name)

        self.__untracked_files = untracked_files
        self.__conflicted_files = conflicted_files
        self.__modified_files = modified_files
        self.__deleted_files = deleted_files
        self.__staged_files = staged_files

    @property
    def untracked_files(self):
        if self.__untracked_files is None:
            self.__set_untracked_conflicted_modified_deleted_and_staged_files()

        return self.__untracked_files

    @property
    def conflicted_files(self):
        if self.__conflicted_files is None:
            self.__set_untracked_conflicted_modified_deleted_and_staged_files()

        return self.__conflicted_files

    @property
    def modified_files(self):
        if self.__modified_files is None:
            self.__set_untracked_conflicted_modified_deleted_and_staged_files()

        return self.__modified_files

    @property
    def deleted_files(self):
        if self.__deleted_files is None:
            self.__set_untracked_conflicted_modified_deleted_and_staged_files()

        return self.__deleted_files

    @property
    def staged_files(self):
        if self.__staged_files is None:
            self.__set_untracked_conflicted_modified_deleted_and_staged_files()

        return self.__staged_files

    def __set_stashed_files(self):
        stashed_files = []

        os.chdir(self.directory_path)

        # https://git-scm.com/docs/git-stash

        result = subprocess.run(["git", "stash", "list"], capture_output=True, check=False)

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
        result = subprocess.run(["git", "fetch", remote_name], check=False)

        # Getting the commits that are on the remote branch but not in HEAD, which points to the tip of the local branch.
        result = subprocess.run(["git", "log", f"HEAD..{self.remote_branch_name}", "--oneline"], capture_output=True, check=False)

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
        result = subprocess.run(["git", "log", f"{self.remote_branch_name}..HEAD", "--oneline"], capture_output=True, check=False)

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

    return name and pstring.equals_ignore_case(name, "HEAD") is False

def is_good_local_branch_name(name):
    return name and pstring.equals_ignore_case(name, "HEAD") is False

# ------------------------------------------------------------------------------
#     App
# ------------------------------------------------------------------------------

try:
    KVS_KEY_PREFIX = "find_unpushed_commits/"

    repositories_directory_path = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}repositories_directory_path")
    pconsole.print(f"repositories_directory_path: {repositories_directory_path}")

    for entry in os.listdir(repositories_directory_path):
        repository_directory_path = os.path.join(repositories_directory_path, entry)

        if os.path.isdir(repository_directory_path):
            git_directory_path = os.path.join(repository_directory_path, ".git")

            if os.path.isdir(git_directory_path):
                repository = RepositoryInfo(repository_directory_path)

                pconsole.print(f"Repository: {repository.name}")

                if is_good_remote_branch_name(repository.remote_branch_name):
                    pconsole.print(f"Remote: {repository.remote_branch_name}", indents=pstring.LEVELED_INDENTS[1])

                else:
                    pconsole.print(f"Remote: {repository.remote_branch_name}", indents=pstring.LEVELED_INDENTS[1], colors = pconsole.IMPORTANT_COLORS)

                if is_good_local_branch_name(repository.local_branch_name):
                    pconsole.print(f"Local: {repository.local_branch_name}", indents=pstring.LEVELED_INDENTS[1])

                else:
                    pconsole.print(f"Local: {repository.local_branch_name}", indents=pstring.LEVELED_INDENTS[1], colors = pconsole.IMPORTANT_COLORS)

                if repository.untracked_files:
                    pconsole.print("Untracked files:", indents=pstring.LEVELED_INDENTS[1])

                    for file in repository.untracked_files:
                        pconsole.print(file, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

                if repository.conflicted_files:
                    pconsole.print("Conflicted files:", indents=pstring.LEVELED_INDENTS[1])

                    for file in repository.conflicted_files:
                        pconsole.print(file, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

                if repository.modified_files:
                    pconsole.print("Modified files:", indents=pstring.LEVELED_INDENTS[1])

                    for file in repository.modified_files:
                        pconsole.print(file, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

                if repository.deleted_files:
                    pconsole.print("Deleted files:", indents=pstring.LEVELED_INDENTS[1])

                    for file in repository.deleted_files:
                        pconsole.print(file, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

                if repository.staged_files:
                    pconsole.print("Staged files:", indents=pstring.LEVELED_INDENTS[1])

                    for file in repository.staged_files:
                        pconsole.print(file, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

                if repository.stashed_files:
                    pconsole.print("Stashed files:", indents=pstring.LEVELED_INDENTS[1])

                    for file in repository.stashed_files:
                        pconsole.print(file, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

                if repository.unpulled_commits:
                    pconsole.print("Unpulled commits:", indents=pstring.LEVELED_INDENTS[1])

                    for commit in repository.unpulled_commits:
                        pconsole.print(commit, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

                if repository.unpushed_commits:
                    pconsole.print("Unpushed commits:", indents=pstring.LEVELED_INDENTS[1])

                    for commit in repository.unpushed_commits:
                        pconsole.print(commit, indents=pstring.LEVELED_INDENTS[2], colors = pconsole.IMPORTANT_COLORS)

except Exception: # pylint: disable=broad-except
    pconsole.print(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

finally:
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
