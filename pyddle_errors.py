# Created: 2024-04-23
# Exception classes for pyddle.

# All library-related error classes must inherit from this class.
# We can casually use this class for general errors; there's not much point in very precisely classifying errors.
class GeneralError(Exception):
    pass

# Something is wrong with the arguments.
class ArgumentError(GeneralError):
    pass

# Data is not in the expected format.
class FormatError(GeneralError):
    pass

# Data is invalid/incorrect/unsuitable.
class InvalidDataError(GeneralError):
    pass

# "Dont do that now!" kind of error.
# Like trying to read from a stream that's not open.
class InvalidOperationError(GeneralError):
    pass

# Not possible yet.
# There's a high chance that it'll be implemented later.
# The name doesnt end with "Error" because it would redefine the builtin class.
class NotImplementedException(GeneralError):
    pass

# For things we probably wont implement at all.
# Sometimes, the message says something is not supported, but it's more like an argument error.
class NotSupportedError(GeneralError):
    pass

# Unable to use an instance that has been finalized/destructed.
class ObjectDisposedError(GeneralError):
    pass
