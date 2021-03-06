# coding: utf-8
import os
import tempfile
import unittest

from nxdrive.commandline import CliHandler
from nxdrive.options import Options
from nxdrive.osi import AbstractOSIntegration
from tests.common import clean_dir


class FakeOSIntegration(AbstractOSIntegration):
    def get_system_configuration(self):
        args = dict()
        args["log_level_console"] = "SYSTEM_TEST"
        return args


def getOSIntegration(manager):
    return FakeOSIntegration(None)


class CommandLineTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = os.path.join(os.environ.get('WORKSPACE', ''), 'tmp')
        self.addCleanup(clean_dir, self.tmpdir)
        if not os.path.isdir(self.tmpdir):
            os.makedirs(self.tmpdir)

        self.cmd = CliHandler()
        self.addCleanup(self.clean_ini)

    def create_ini(self, filename='config.ini', env='PROD'):
        with open(filename, 'w+') as inifile:
            inifile.writelines("""
[DEFAULT]
env = %s

[PROD]
log-level-console = TRACE
debug = False

[DEV]
log-level-console = ERROR
delay = 3
""" % env)

    def clean_ini(self, filename='config.ini'):
        try:
            os.remove(filename)
        except OSError:
            pass

    @Options.mock()
    def test_update_site_url(self):
        argv = ["ndrive", "console", "--update-site-url", "DEBUG_TEST"]
        options = self.cmd.parse_cli([])
        assert options.update_site_url == 'http://community.nuxeo.com/static/drive/'

        # Normal arg
        options = self.cmd.parse_cli(argv)
        assert options.update_site_url == 'DEBUG_TEST'

    @Options.mock()
    def test_system_default(self):
        self.cmd.default_home = tempfile.mkdtemp("config", dir=self.tmpdir)
        original = AbstractOSIntegration.get
        AbstractOSIntegration.get = staticmethod(getOSIntegration)
        try:
            self.clean_ini()
            argv = ["ndrive", "console", "--log-level-console", "WARNING"]
            # Default value
            options = self.cmd.parse_cli([])
            assert options.log_level_console == 'SYSTEM_TEST'

            # Normal arg
            options = self.cmd.parse_cli(argv)
            assert options.log_level_console == 'WARNING'
        finally:
            AbstractOSIntegration.get = staticmethod(original)

    @Options.mock()
    def test_default_override(self):
        self.cmd.default_home = tempfile.mkdtemp("config", dir=self.tmpdir)
        self.clean_ini()
        argv = ['ndrive', 'console', '--log-level-console=WARNING']

        # Default value
        options = self.cmd.parse_cli([])
        assert options.log_level_console == 'INFO'

        # Normal arg
        options = self.cmd.parse_cli(argv)
        assert options.log_level_console == 'WARNING'

        # config.ini override
        self.create_ini()
        options = self.cmd.parse_cli([])
        assert options.log_level_console == 'TRACE'
        self.clean_ini()

        # config.ini override, but arg specified
        options = self.cmd.parse_cli(argv)
        assert options.log_level_console == 'WARNING'

        # other usage section
        self.create_ini(env='DEV')
        options = self.cmd.parse_cli([])
        assert options.log_level_console == 'ERROR'
        self.clean_ini()
