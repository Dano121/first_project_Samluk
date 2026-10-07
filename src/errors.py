class PipelineError(Exception):
    """Base class for every error raised by this pipeline."""


class ConfigError(PipelineError):
    """Bad configuration: missing path, unknown source, wrong file format."""


class ValidationError(PipelineError):
    """A record does not meet the data contract."""


class SourceError(PipelineError):
    """The source could not deliver the data: missing directory, unreadable file."""


class DatabaseError(PipelineError):
    """The database refused to cooperate: no connection, rejected statement."""
