from public import public


@public
class Target(object):
    """A target."""

    def connect(self):
        """Connect to the target device."""
        raise NotImplementedError

    def disconnect(self):
        """Disconnect from the target device."""
        raise NotImplementedError
