class ArgConstructor(object):
    def __init__(self):
        self._arguments_list = {}

    def add_arguments(self, name, flag,
                      takes_arguments=False,
                      mandatory=False,
                      default=None,
                      argument_type=None,
                      flag_separator=' ',
                      choices=None,
                      action=None,
                      args_separator=' '):

        # Argument checks
        if action and action not in ('append', 'repeat'):
            raise ValueError("action must be either 'append' or 'repeat'")
        if choices and (not iter(choices) or len(choices) == 0):
            raise ValueError("choices must be a non-zero long iterable")
        if argument_type and not isinstance(argument_type, type):
            raise ValueError("argument_type must be a type")

        params = {}
        for param in ('takes_arguments',
                      'mandatory',
                      'default',
                      'argument_type',
                      'flag_separator',
                      'choices',
                      'action',
                      'args_separator'):
            params[param] = locals()[param]

        self._arguments_list[name] = params

    def parse_args(self, **kwargs):
        pass

if __name__ == '__main__':
    a = ArgConstructor()
    a.add_arguments('file', '-f', True, argument_type=5)
