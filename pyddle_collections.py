# Created: 2024-03-26
# Collection-related things.

# For implementing sugar-coating methods.
# Sometimes, we should just not give certain arguments.

class PotentiallyFalsyArgs:
    def __init__(self):
        self.args = {}

    def must_contain(self, key, value):
        if not value:
            raise RuntimeError(f"Argument {key} must be provided.")

        self.args[key] = value

    def must_contain_enum_name(self, key, value):
        if not value:
            raise RuntimeError(f"Argument {key} must be provided.")

        self.args[key] = value.name

    def must_contain_enum_value(self, key, value):
        if not value:
            raise RuntimeError(f"Argument {key} must be provided.")

        self.args[key] = value.value

    def may_contain(self, key, value):
        if value:
            self.args[key] = value

    def may_contain_enum_name(self, key, value):
        if value:
            self.args[key] = value.name

    def may_contain_enum_value(self, key, value):
        if value:
            self.args[key] = value.value
