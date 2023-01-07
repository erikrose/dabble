class Environment:
    """A mapping of variables to values. Basically, a scope. They can point to
    parent scopes."""

    def __init__(self, vars=None, parent=None):
        """
        :arg vars: A dict of variable names pointing to their values
        :arg parent Environment: The surrounding scope, if any
        """
        self.vars = vars or {}
        self.parent = parent

    def define(self, name, value):
        """Create a var with the given name and value."""
        self.vars[name] = value
        return value

    def look_up(self, name):
        """Return the value of a var in this scope or the nearest parent one
        where it's defined."""
        return self._env_where_bound(name).vars[name]

    def assign(self, name, value):
        """Set an existing var to a value."""
        env = self._env_where_bound(name)
        env.vars[name] = value

    def _env_where_bound(self, name):
        """Return the innermost environment from the scope chain (starting at
        myself) where var `name` is bound."""
        if name in self.vars:
            return self
        elif self.parent is None:
            raise Exception(f'Variable "{name}" is not defined.')
        else:
            return self.parent._env_where_bound(name)

    def __str__(self):
        return f'<Environment ({self.vars})>'
