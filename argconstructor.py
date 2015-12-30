from collections import OrderedDict


class ArgConstructor(object):
    def __init__(self, parameters_separator=' '):
        """Initialize an ArgConstructor object

        :param parameters_separator: a string to put between the arguments in the argument string
        :type parameters_separator: str
        """
        self._parameters_separator = str(parameters_separator)
        self._arguments_list = OrderedDict()

    def add_argument(self, name, flag,
                     mandatory=False,
                     default=None,
                     min_arguments=0,
                     max_arguments=None,
                     flag_separator=' ',
                     choices=None,
                     requires=None,
                     required_by=None,
                     conflicts_with=None,
                     args_separator=' '):
        """Add an argument to the constructor

        :param name: name of the argument. Must be unique constructor-wide
        :type name: str
        :param flag: string to be used as a flag for this argument
        :type flag: str
        :param mandatory: True if the parameter is required in the argument string
        :type mandatory: bool
        :param default: default value for the parameter
        :param min_arguments: minimum number of arguments, 0 if no restriction
        :type min_arguments: int
        :param max_arguments: maximum number of arguments, None if no restriction
        :type max_arguments: int|NoneType
        :param flag_separator: string to put between the flag and the first parameter
        :type flag_separator: str
        :param choices: if supplied - the allowed values for the argument is restricted to it
        :param requires: one or more arguments this argument depends on
        :param required_by: one or more arguments this argument is depended by
        :param conflicts_with: one or more arguments this argument must not be supplied together with
        :param args_separator: string to put between parameters of the argument
        """
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
        requires = self._convert_to_iterable(requires, str)
        required_by = self._convert_to_iterable(required_by, str)
        conflicts_with = self._convert_to_iterable(conflicts_with, str)

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
                      'conflicts_with',
                      'args_separator'):
            params[param] = locals()[param]

        self._arguments_list[name] = params

    @staticmethod
    def _check_against_choices(name, value, choices):
        """Raise an error if parameter does not match one of the choises

        :param name: name of an argument. Used only to raise meaningful exceptions
        :type name: str
        :param value: value supplied to the argument in parse_args
        :param choices: values which are allowed for an argument to take. None if no restrictions are applied
        """
        if choices is not None and value not in choices:
            raise ValueError("Parameter %s must be one of the %s, got %s instead" % (name, choices, value))

    @classmethod
    def _parse_arg(cls, name, parameters, value):
        """Construct part of the argument string for one argument

        :param name: name of an argument. Used only to raise meaningful exceptions
        :type name: str
        :param parameters: dict with argument's properties
        :type parameters: dict
        :param value: value supplied to the argument in parse_args
        :return: part of the argument string for this particular argument
        :rtype: str
        """
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

        value = cls._convert_to_iterable(value)

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
    def _append_if_not_none(container, element):
        """Append element to a container if element is not None"""
        if element is not None:
            container.append(element)

    @staticmethod
    def _convert_to_iterable(arg, cast_func=lambda x: x):
        """Converts any object to an iterable

        :param arg: any object to convert to iterable
        :param cast_func: function to apply to each element of the iterable
        :type cast_func: callable
        :return:
            - list with one element if arg is not iterable;
            - empty list if arg is None;
            - list of with the same elements as arg has is arg is itself an iterable
        :rtype: list
        """
        if arg is None:
            return []
        elif not hasattr(arg, '__iter__'):
            return [cast_func(arg)]
        else:
            return [cast_func(x) for x in arg]

    def _check_dependencies(self, kwargs):
        """Check if all dependencies are met"""
        dependants = {}
        for argument in self._arguments_list:
            if argument not in dependants:
                dependants[argument] = set()
            dependants[argument].update(self._arguments_list[argument]['requires'])
            for parameter in self._arguments_list[argument]['required_by']:
                if parameter not in dependants:
                    dependants[parameter] = set()
                dependants[parameter].add(argument)
        for argument in kwargs:
            for dep in dependants[argument]:
                if dep not in kwargs and self._arguments_list[dep]['default'] is None:
                    raise ValueError("Parameter '%s' requires '%s', but it's not supplied" % (argument, dep))
                else:
                    self._arguments_list[dep]['mandatory'] = True

    def _check_for_conflicts(self, kwargs):
        """Check if there's no conflicts in supplied arguments"""
        for argument in kwargs:
            for conflict in self._arguments_list[argument]['conflicts_with']:
                if self._arguments_list[conflict]['mandatory'] or conflict in kwargs:
                    raise ValueError("Argument %s conflicts with %s" % (argument, conflict))

    def parse_args(self, **kwargs):
        """Construct an arguments string using given values

        :param kwargs: every positional argument should be a value for previously added arguments
        :type kwargs: dict
        :return: arguments string
        :rtype: str
        """
        kwargs = {x: y for x, y in kwargs.items() if y is not None}  # Eliminate kwargs which have 'None' value

        self._check_dependencies(kwargs)
        self._check_for_conflicts(kwargs)

        result_list = []
        for argument in self._arguments_list:
            self._append_if_not_none(
                result_list,
                self._parse_arg(argument, self._arguments_list[argument], kwargs.get(argument))
            )

        return self._parameters_separator.join(result_list)
