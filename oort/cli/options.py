import click

from arcsecond.options import State


def verbose_option_constructor(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(State)
        state.verbose = value
        return value

    return click.option('-v',
                        '--verbose',
                        is_flag=True,
                        expose_value=False,
                        help='Increases verbosity.',
                        callback=callback)(f)


def api_option_constructor(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(State)
        state.api_name = value or 'main'
        return value

    return click.option('--api',
                        expose_value=False,
                        help='Choose API name (i.e. API server).',
                        callback=callback)(f)


def basic_options(f):
    f = verbose_option_constructor(f)
    f = api_option_constructor(f)
    return f


class MethodChoiceParamType(click.ParamType):
    name = 'method'

    def __init__(self, *args):
        super(MethodChoiceParamType, self).__init__()
        self.allowed_methods = args or ['start', 'stop', 'restart', 'status']

    def convert(self, value, param, ctx):
        if value.lower() not in self.allowed_methods:
            msg = '{} is not a valid method. '.format(value)
            msg += 'It must be one of {}.'.format(' '.join(self.allowed_methods))
            self.fail('%s is not a valid method' % value, param, ctx)
        return value.lower()
