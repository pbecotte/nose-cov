"""Coverage plugin for nose."""

from copy import copy
from optparse import Option, OptionValueError
import logging

from nose.plugins.base import Plugin

log = logging.getLogger(__name__)


def check_choice_split(option, opt, value):
    if value in option.choices:
        return value
    elif all(x.strip() in option.choices for x in value.split(',')):
        return [x.strip() for x in value.split(',')]
    elif all(x.strip() in option.choices for x in value.split()):
        return [x.strip() for x in value.split()]
    else:
        choices = ", ".join(map(repr, option.choices))
        raise OptionValueError(
            "option %s: invalid choice: %r (choose from %s)"
            % (opt, value, choices))


class ReportOption(Option):

    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["choice"] = check_choice_split

    def take_action(self, action, dest, opt, value, values, parser):
        if isinstance(value, list):
            values.ensure_value(dest, []).extend(value)
        else:
            values.ensure_value(dest, []).append(value)


class Cov(Plugin):
    """Activate cov plugin to generate coverage reports"""

    score = 200
    status = {}

    def options(self, parser, env):
        """Add options to control coverage."""

        log.debug('nose-cov options')

        Plugin.options(self, parser, env)
        parser.add_option('--cov', action='append', default=env.get('NOSE_COV', []), metavar='PATH',
                          dest='cov_source',
                          help=('Measure coverage for filesystem path '
                                '[NOSE_COV]'))
        parser.add_option(ReportOption('--cov-report', action='append', default=env.get('NOSE_COV_REPORT', []), metavar='TYPE',
                          choices=['term', 'term-missing', 'annotate', 'html', 'xml'],
                          dest='cov_report',
                          help=('Generate selected reports, available types: term, term-missing, annotate, html, xml '
                                '[NOSE_COV_REPORT]')))
        parser.add_option('--cov-config', action='store', default=env.get('NOSE_COV_CONFIG', '.coveragerc'), metavar='FILE',
                          dest='cov_config',
                          help=('Config file for coverage, default: .coveragerc '
                                '[NOSE_COV_CONFIG]'))

    def configure(self, options, config):
        """Activate coverage plugin if appropriate."""

        log.debug('nose-cov configure')

        try:
            self.status.pop('active')
        except KeyError:
            pass

        Plugin.configure(self, options, config)

        if self.enabled and not config.worker:
            self.status['active'] = True
            self.cov_source = options.cov_source or ['.']
            self.cov_report = options.cov_report or ['term']
            self.cov_config = options.cov_config
        else:
            self.enabled = False

    def begin(self):
        """Erase any previous coverage data and start coverage."""

        import cov_core

        log.debug('nose-cov begin')
        self.cov_controller = cov_core.Central(self.cov_source, self.cov_report, self.cov_config)
        self.cov_controller.start()

    def report(self, stream):
        """Produce coverage reports."""

        log.debug('nose-cov report')
        self.cov_controller.finish()
        self.cov_controller.summary(stream)
