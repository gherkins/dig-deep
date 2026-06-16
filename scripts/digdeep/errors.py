"""Shared exception types."""


class MissingTool(RuntimeError):
    """A required external CLI (ddgs, yt-dlp, ...) is not on PATH."""

    def __init__(self, tool, hint=""):
        msg = "required tool '%s' not found on PATH." % tool
        if hint:
            msg += " " + hint
        super().__init__(msg)
        self.tool = tool
        self.hint = hint
