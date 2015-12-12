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
                      args_separator=' '):
        # Check if we already have that parameter
        if name in self._arguments_list:
            raise ValueError("parameter %s already exists" % name)

        # Advanced argument checks
        if choices is not None and (not hasattr(choices, '__iter__') or len(choices) == 0):
            raise ValueError("choices must be a non-zero long iterable")

        # Basic parameters checks and type casts
        flag = str(flag)
        takes_arguments = bool(takes_arguments)
        mandatory = bool(mandatory)
        flag_separator = str(flag_separator)
        args_separator = str(args_separator)

        params = {}
        for param in ('flag',
                      'takes_arguments',
                      'mandatory',
                      'default',
                      'flag_separator',
                      'choices',
                      'args_separator'):
            params[param] = locals()[param]

        self._arguments_list[name] = params

    @staticmethod
    def _check_against_choices(name, value, choices):
        if choices is not None and value not in choices:
            raise ValueError("Parameter %s must be one of the %s, got %s instead" %(name, choices, value))

    @classmethod
    def _parse_arg(cls, name, parameters, value):
        if parameters['takes_arguments']:
            # If no value was given
            if value is None:
                if parameters['default'] is not None:
                    # Supply default if possible
                    value = parameters['default']
                elif parameters['mandatory']:
                    # Raise if the parameter is mandatory
                    raise ValueError("Parameter '%s' is mandatory and takes argument(s)" % name)
                else:
                    # Else make no difference
                    return None

            if not hasattr(value, '__iter__'):
                # If non-iterable value is given make it a tuple with one element
                value = (value, )

            for arg in value:
                # Check if all the values are from choices, if supplied
                cls._check_against_choices(name, arg, parameters['choices'])

            return parameters['flag_separator'].join((
                    parameters['flag'],
                    parameters['args_separator'].join([str(i) if i is not None else '' for i in value])
            ))
        else:  # Param takes no arguments
            if value is not None:
                return parameters['flag']
            else:
                return None

    @staticmethod
    def _append_if_not_none(container, value):
        if value is not None:
            container.append(value)

    def parse_args(self, **kwargs):
        result_list = []
        for argument in self._arguments_list:
            self._append_if_not_none(
                result_list,
                self._parse_arg(argument, self._arguments_list[argument], kwargs.get(argument))
            )

        return self._parameters_separator.join(result_list)
