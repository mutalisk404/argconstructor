from collections import OrderedDict


class ArgConstructor(object):
    def __init__(self, parameters_separator=' '):
        self._parameters_separator = str(parameters_separator)
        self._arguments_list = OrderedDict()

    def add_arguments(self, name, flag,
                      mandatory=False,
                      default=None,
                      min_arguments=0,
                      max_arguments=None,
                      flag_separator=' ',
                      choices=None,
                      requires=None,
                      required_by=None,
                      args_separator=' '):
        # Check if we already have that parameter
        if name in self._arguments_list:
            raise ValueError("parameter %s already exists" % name)

        # Basic parameters checks and type casts
        flag = str(flag)
        min_arguments = int(min_arguments) if int(min_arguments) >= 0 else 0
        max_arguments = int(max_arguments) if max_arguments is not None else None
        mandatory = bool(mandatory)
        flag_separator = str(flag_separator)
        args_separator = str(args_separator)
        requires = self._convert_to_iterable_if_not_none(requires, str)
        required_by = self._convert_to_iterable_if_not_none(required_by, str)

        # Advanced argument checks
        if choices is not None and (not hasattr(choices, '__iter__') or len(choices) == 0):
            raise ValueError("choices must be a non-zero long iterable")
        if max_arguments is not None and max_arguments < min_arguments:
            raise ValueError("'min_arguments' must be greater or equal than 'max_arguments'")

        params = {}
        for param in ('flag',
                      'mandatory',
                      'default',
                      'min_arguments',
                      'max_arguments',
                      'flag_separator',
                      'choices',
                      'requires',
                      'required_by',
                      'args_separator'):
            params[param] = locals()[param]

        self._arguments_list[name] = params

    @staticmethod
    def _check_against_choices(name, value, choices):
        if choices is not None and value not in choices:
            raise ValueError("Parameter %s must be one of the %s, got %s instead" % (name, choices, value))

    @classmethod
    def _parse_arg(cls, name, parameters, value):
        value = cls._convert_to_iterable_if_not_none(value)

        if value is None:
            if parameters['mandatory']:
                if parameters['default'] is not None:
                    # Supply default if possible
                    value = parameters['default']
                else:
                    raise ValueError("Parameter '%s' is mandatory but not supplied" % name)
            else:
                # Else make no difference
                return None

        if parameters['min_arguments'] == parameters['max_arguments'] == 0:
            return parameters['flag']
        elif len(value) < parameters['min_arguments'] or (parameters['max_arguments'] is not None and len(value) > parameters['max_arguments']):
            raise ValueError(
                    "Parameter '%s' takes from %d to %s arguments, got %d instead" % (
                        name,
                        parameters['min_arguments'],
                        parameters['max_arguments'] if parameters['max_arguments'] is not None else "infinite number of",
                        len(value)
                    )
            )

        for arg in value:
            # Check if all the values are from choices, if supplied
            cls._check_against_choices(name, arg, parameters['choices'])

        return parameters['flag_separator'].join((
                parameters['flag'],
                parameters['args_separator'].join([str(i) if i is not None else '' for i in value])
        ))

    @staticmethod
    def _append_if_not_none(container, value):
        if value is not None:
            container.append(value)

    @staticmethod
    def _convert_to_iterable_if_not_none(arg, cast_func=lambda x: x):
        if arg is None:
            return None
        elif not hasattr(arg, '__iter__'):
            return cast_func(arg),
        else:
            return [cast_func(x) for x in arg]

    def parse_args(self, **kwargs):
        kwargs = {x: y for x, y in kwargs.items() if y is not None}  # Eliminate kwargs which have 'None' value

        # Check if all the dependencies are met
        dependants = {}
        for argument in self._arguments_list:
            argument_requires = self._convert_to_iterable_if_not_none(self._arguments_list[argument]['requires'])
            argument_required_by = self._convert_to_iterable_if_not_none(self._arguments_list[argument]['required_by'])
            if argument not in dependants:
                dependants[argument] = set()
            if argument_requires is not None:
                dependants[argument].update(argument_requires)
            if argument_required_by is not None:
                for parameter in argument_required_by:
                    if parameter not in dependants:
                        dependants[parameter] = set()
                    dependants[parameter].add(argument)
        for argument in kwargs:
            for dep in dependants[argument]:
                if dep not in kwargs and self._arguments_list[dep]['default'] is None:
                    raise ValueError("Parameter '%s' requires '%s', but it's not supplied" % (argument, dep))
                else:
                    self._arguments_list[dep]['mandatory'] = True

        result_list = []
        for argument in self._arguments_list:
            self._append_if_not_none(
                result_list,
                self._parse_arg(argument, self._arguments_list[argument], kwargs.get(argument))
            )

        return self._parameters_separator.join(result_list)
