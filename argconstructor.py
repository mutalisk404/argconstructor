from collections import OrderedDict


class ArgConstructor(object):
    def __init__(self, parameters_separator=' '):
        self._parameters_separator = str(parameters_separator)
        self._arguments_list = OrderedDict()

    def add_arguments(self, name, flag,
                      takes_arguments=False,
                      mandatory=False,
                      default=None,
                      flag_separator=' ',
                      choices=None,
                      action=None,
                      args_separator=' '):
        # Check if we already have that parameter
        if name in self._arguments_list:
            raise ValueError("parameter %s already exists" % name)

        # Argument checks
        if action and action not in ('append', 'repeat'):
            raise ValueError("action must be either 'append' or 'repeat'")
        if choices and (not iter(choices) or len(choices) == 0):
            raise ValueError("choices must be a non-zero long iterable")

        params = {}
        for param in ('takes_arguments',
                      'mandatory',
                      'default',
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
