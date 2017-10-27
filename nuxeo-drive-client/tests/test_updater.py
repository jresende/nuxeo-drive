# coding: utf-8
import unittest
from os.path import dirname

import esky.finder
import pytest
from esky import Esky
from mock import Mock

from nxdrive.updater import AppUpdater, MissingCompatibleVersion, \
    MissingUpdateSiteInfo, UPDATE_STATUS_DOWNGRADE_NEEDED, \
    UPDATE_STATUS_MISSING_INFO, UPDATE_STATUS_MISSING_VERSION, \
    UPDATE_STATUS_UPDATE_AVAILABLE, UPDATE_STATUS_UPGRADE_NEEDED, \
    UPDATE_STATUS_UP_TO_DATE
from nxdrive.utils import version_compare, version_compare_client


class MockManager(Mock):
    _engines = dict()
    _client = None

    def clean_engines(self):
        MockManager._engines = dict()

    def set_version(self, version):
        MockManager._client = version

    def get_version(self):
        return MockManager._client

    def add_engine(self, version):
        obj = Mock()
        obj.get_server_version = lambda: version
        MockManager._engines[version] = obj

    def get_engines(self):
        return MockManager._engines


class MockEsky(Esky):
    """Mock Esky subclass using a LocalVersionFinder."""

    def __init__(self, appdir_or_exe, version_finder=None):
        super(MockEsky, self).__init__(appdir_or_exe,
                                       version_finder=version_finder)
        self.set_local_version_finder(version_finder)

    def set_local_version_finder(self, version_finder):
        if isinstance(version_finder, basestring):
            kwds = {"download_url": version_finder}
            version_finder = esky.finder.LocalVersionFinder(**kwds)
        self.version_finder = version_finder


class TestUpdater(unittest.TestCase):

    def setUp(self):
        location = dirname(__file__)
        appdir = location + '/resources/esky_app'
        version_finder = location + '/resources/esky_versions'
        self.esky_app = MockEsky(appdir, version_finder=version_finder)
        self.manager = MockManager()
        self.updater = AppUpdater(self.manager, esky_app=self.esky_app,
                                  local_update_site=True)

    def test_version_compare(self):
        # Compare server versions
        # Releases
        assert not version_compare('5.9.3', '5.9.3')
        assert version_compare('5.9.3', '5.9.2') == 1
        assert version_compare('5.9.2', '5.9.3') == -1
        assert version_compare('5.9.3', '5.8') == 1
        assert version_compare('5.8', '5.6.0') == 1
        assert version_compare('5.9.1', '5.9.0.1') == 1
        assert version_compare('6.0', '5.9.3') == 1
        assert version_compare('5.10', '5.1.2') == 1

        # Date-based
        assert not version_compare('5.9.4-I20140415_0120', '5.9.4-I20140415_0120')
        assert version_compare('5.9.4-I20140415_0120', '5.9.4-I20140410_0120') == 1
        assert version_compare('5.9.4-I20140515_0120', '5.9.4-I20140415_0120') == 1
        assert version_compare('5.9.4-I20150102_0120', '5.9.4-I20143112_0120') == 1
        assert version_compare('5.9.4-I20140415_0120', '5.9.3-I20140415_0120') == 1

        # Releases and date-based
        assert version_compare('5.9.4-I20140415_0120', '5.9.3') == 1
        assert version_compare('5.9.4-I20140415_0120', '5.9.4') == -1
        assert version_compare('5.9.4-I20140415_0120', '5.9.5') == -1

        assert version_compare('5.9.3', '5.9.4-I20140415_0120') == -1
        assert version_compare('5.9.4', '5.9.4-I20140415_0120') == 1
        assert version_compare('5.9.5', '5.9.4-I20140415_0120') == 1

        # Snapshots
        assert not version_compare('5.9.4-SNAPSHOT', '5.9.4-SNAPSHOT')
        assert version_compare('5.9.4-SNAPSHOT', '5.9.3-SNAPSHOT') == 1
        assert version_compare('5.9.4-SNAPSHOT', '5.8-SNAPSHOT') == 1
        assert version_compare('5.9.3-SNAPSHOT', '5.9.4-SNAPSHOT') == -1
        assert version_compare('5.8-SNAPSHOT', '5.9.4-SNAPSHOT') == -1

        # Releases and snapshots
        assert version_compare('5.9.4-SNAPSHOT', '5.9.3') == 1
        assert version_compare('5.9.4-SNAPSHOT', '5.9.4') == -1
        assert version_compare('5.9.4-SNAPSHOT', '5.9.5') == -1

        assert version_compare('5.9.3', '5.9.4-SNAPSHOT') == -1
        assert version_compare('5.9.4', '5.9.4-SNAPSHOT') == 1
        assert version_compare('5.9.5', '5.9.4-SNAPSHOT') == 1

        # Date-based and snapshots
        assert version_compare('5.9.4-I20140415_0120', '5.9.3-SNAPSHOT') == 1
        assert version_compare('5.9.4-I20140415_0120', '5.9.5-SNAPSHOT') == -1
        assert version_compare('5.9.3-SNAPSHOT', '5.9.4-I20140415_0120') == -1
        assert version_compare('5.9.5-SNAPSHOT', '5.9.4-I20140415_0120') == 1
        
        # Can't decide, consider as equal
        assert not version_compare('5.9.4-I20140415_0120', '5.9.4-SNAPSHOT')
        assert not version_compare('5.9.4-SNAPSHOT', '5.9.4-I20140415_0120')

        # Hotfixes
        assert not version_compare('5.8.0-HF14', '5.8.0-HF14')
        assert version_compare('5.8.0-HF14', '5.8.0-HF13') == 1
        assert version_compare('5.8.0-HF14', '5.8.0-HF15') == -1
        assert version_compare('5.8.0-HF14', '5.6.0-HF35') == 1
        assert version_compare('5.6.0-H35', '5.8.0-HF14') == -1

        # Releases and hotfixes
        assert version_compare('5.8.0-HF14', '5.6') == 1
        assert version_compare('5.8.0-HF14', '5.8') == 1
        assert version_compare('5.8.0-HF14', '5.9.1') == -1

        assert version_compare('5.6', '5.8.0-HF14') == -1
        assert version_compare('5.8', '5.8.0-HF14') == -1
        assert version_compare('5.9.1', '5.8.0-HF14') == 1

        # Date-based and hotfixes
        assert version_compare('5.9.4-I20140415_0120', '5.8.0-HF14') == 1
        assert version_compare('5.8.1-I20140415_0120', '5.8.0-HF14') == 1
        assert version_compare('5.8.0-I20140415_0120', '5.8.0-HF14') == -1
        assert version_compare('5.8-I20140415_0120', '5.8.0-HF14') == -1
        assert version_compare('5.9.4-I20140415_0120', '5.10.0-HF01') == -1

        assert version_compare('5.8.0-HF14', '5.9.4-I20140415_0120') == -1
        assert version_compare('5.8.0-HF14', '5.8.1-I20140415_0120') == -1
        assert version_compare('5.8.0-HF14', '5.8.0-I20140415_0120') == 1
        assert version_compare('5.8.0-HF14', '5.8-I20140415_0120') == 1
        assert version_compare('5.10.0-HF01', '5.9.4-I20140415_0120') == 1

        # Snaphsots and hotfixes
        assert version_compare('5.8.0-HF14', '5.7.1-SNAPSHOT') == 1
        assert version_compare('5.8.0-HF14', '5.8.0-SNAPSHOT') == 1
        assert version_compare('5.8.0-HF14', '5.8-SNAPSHOT') == 1
        assert version_compare('5.8.0-HF14', '5.9.1-SNAPSHOT') == -1

        assert version_compare('5.7.1-SNAPSHOT', '5.8.0-HF14') == -1
        assert version_compare('5.8.0-SNAPSHOT', '5.8.0-HF14') == -1
        assert version_compare('5.8-SNAPSHOT', '5.8.0-HF14') == -1
        assert version_compare('5.9.1-SNAPSHOT', '5.8.0-HF14') == 1

        # Snapshot hotfixes
        assert not version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-HF14-SNAPSHOT')
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-HF13-SNAPSHOT') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-HF15-SNAPSHOT') == -1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.6.0-HF35-SNAPSHOT') == 1
        assert version_compare('5.6.0-H35-SNAPSHOT', '5.8.0-HF14-SNAPSHOT') == -1

        # Releases and snapshot hotfixes
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.6') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.9.1') == -1

        assert version_compare('5.6', '5.8.0-HF14-SNAPSHOT') == -1
        assert version_compare('5.8', '5.8.0-HF14-SNAPSHOT') == -1
        assert version_compare('5.9.1', '5.8.0-HF14-SNAPSHOT') == 1

        # Date-based and snapshot hotfixes
        assert version_compare('5.9.4-I20140415_0120', '5.8.0-HF14-SNAPSHOT') == 1
        assert version_compare('5.8.0-I20140415_0120', '5.8.0-HF14-SNAPSHOT') == -1
        assert version_compare('5.9.4-I20140415_0120', '5.10.0-HF01-SNAPSHOT') == -1

        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.9.4-I20140415_0120') == -1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-I20140415_0120') == 1
        assert version_compare('5.10.0-HF01-SNAPSHOT', '5.9.4-I20140415_0120') == 1

        # Snaphsots and snapshot hotfixes
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.7.1-SNAPSHOT') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8-SNAPSHOT') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-SNAPSHOT') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.9.1-SNAPSHOT') == -1

        assert version_compare('5.7.1-SNAPSHOT', '5.8.0-HF14-SNAPSHOT') == -1
        assert version_compare('5.8-SNAPSHOT', '5.8.0-HF14-SNAPSHOT') == -1
        assert version_compare('5.8.0-SNAPSHOT', '5.8.0-HF14-SNAPSHOT') == -1
        assert version_compare('5.9.1-SNAPSHOT', '5.8.0-HF14-SNAPSHOT') == 1

        # Hotfixes and snapshot hotfixes
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.6.0-HF35') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-HF13') == 1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-HF14') == -1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.8.0-HF15') == -1
        assert version_compare('5.8.0-HF14-SNAPSHOT', '5.10.0-HF01') == -1

        # Compare client versions
        assert version_compare_client('0.1', '1.0') == -1
        assert not version_compare_client('1.0', '1.0')
        assert not version_compare_client('1.3.0424', '1.3.0424')
        assert version_compare_client('1.3.0524', '1.3.0424') == 1
        assert version_compare_client('1.4', '1.3.0524') == 1
        assert version_compare_client('1.4.0622', '1.3.0524') == 1
        assert version_compare_client('1.10', '1.1.2') == 1
        assert version_compare_client('2.1.0528', '1.10') == 1
        assert version_compare_client('2.0.0626', '2.0.806') == -1
        assert version_compare_client('2.0.0805', '2.0.806') == -1
        assert version_compare_client('2.0.0905', '2.0.806') == 1
        assert version_compare_client('2.0.805', '2.0.1206') == -1

        # Compare client versions using semantic versioning
        assert version_compare_client('2.0.805', '2.4.0') == -1
        assert version_compare_client('2.1.1130', '2.4.0b1') == -1
        assert version_compare_client('2.4.0b1', '2.4.0b2') == -1
        assert version_compare_client('2.4.0b10', '2.4.0b1') == 1
        assert not version_compare_client('2.4.0b1', '2.4.0b1')
        assert version_compare_client('2.4.2b1', '2.4.2') == -1

        # Compare to None
        assert version_compare('8.10-HF37', None) == 1
        assert version_compare(None, '8.10-HF37') == -1
        assert not version_compare(None, None)
        assert version_compare_client('2.0.805', None) == 1
        assert version_compare_client(None, '2.0.805') == -1
        assert not version_compare_client(None, None)

    def test_get_active_version(self):
        # Active version is None because Esky instance is built from a
        # directory, see Esky._init_from_appdir
        assert not self.updater.get_active_version()

    def test_get_current_latest_version(self):
        assert self.updater.get_current_latest_version() == '1.3.0424'

    def test_find_versions(self):
        versions = self.updater.find_versions()
        good = ['1.3.0424', '1.3.0524', '1.4.0622', '2.4.2b1', '2.4.2', '2.5.0b1', '2.5.0b2']
        assert versions == good

    def test_get_server_min_version(self):
        # Unexisting version
        with pytest.raises(MissingUpdateSiteInfo):
            self.updater.get_server_min_version('4.6.2012')
        assert self.updater.get_server_min_version('1.3.0424') == '5.8'
        assert self.updater.get_server_min_version('1.3.0524') == '5.9.1'
        assert self.updater.get_server_min_version('1.4.0622') =='5.9.2'
        assert self.updater.get_server_min_version('2.4.2b1') == '9.1'
        assert self.updater.get_server_min_version('2.5.0b1') == '9.2'

    def test_get_client_min_version(self):
        # Unexisting version
        with pytest.raises(MissingUpdateSiteInfo):
            self.updater._get_client_min_version('5.6')
        assert self.updater._get_client_min_version('5.8') == '1.2.0110'
        assert self.updater._get_client_min_version('5.9.1') == '1.3.0424'
        assert self.updater._get_client_min_version('5.9.2') == '1.3.0424'
        assert self.updater._get_client_min_version('5.9.3') == '1.4.0622'
        assert self.updater._get_client_min_version('5.9.4') == '1.5.0715'
        assert self.updater._get_client_min_version('9.1') == '2.4.2b1'
        assert self.updater._get_client_min_version('9.2') == '2.5.0b1'

    def _get_latest_compatible_version(self, version):
        self.manager.clean_engines()
        self.manager.add_engine(version)
        return self.updater.get_latest_compatible_version()

    def test_get_latest_compatible_version(self):
        # No update info available for server version
        with pytest.raises(MissingUpdateSiteInfo):
            self._get_latest_compatible_version('5.6')
        # No compatible client version with server version
        with pytest.raises(MissingCompatibleVersion):
            self._get_latest_compatible_version('5.9.4')
        # Compatible versions
        assert self._get_latest_compatible_version('5.9.3') == '1.4.0622'
        assert self._get_latest_compatible_version('5.9.2') == '1.4.0622'
        assert self._get_latest_compatible_version('5.9.1') == '1.3.0524'
        assert self._get_latest_compatible_version('5.8') == '1.3.0424'
        assert self._get_latest_compatible_version('9.1') == '2.4.2'

    def _get_update_status(self, client_version, server_version, add_version=None):
        self.manager.set_version(client_version)
        self.manager.clean_engines()
        self.manager.add_engine(server_version)
        if add_version is not None:
            self.manager.add_engine(add_version)
        return self.updater._get_update_status()

    def test_get_update_status(self):
        # No update info available (missing client version info)
        status = self._get_update_status('1.2.0207', '5.9.3')
        assert status == (UPDATE_STATUS_MISSING_INFO, None)

        # No update info available (missing server version info)
        status = self._get_update_status('1.3.0424', '5.6')
        assert status == (UPDATE_STATUS_MISSING_INFO, None)

        # No compatible client version with server version
        status = self._get_update_status('1.4.0622', '5.9.4')
        assert status == (UPDATE_STATUS_MISSING_VERSION, None)

        # Upgraded needed
        status = self._get_update_status('1.3.0424', '5.9.3')
        assert status == (UPDATE_STATUS_UPGRADE_NEEDED, '1.4.0622')
        status = self._get_update_status('1.3.0524', '5.9.3')
        assert status == (UPDATE_STATUS_UPGRADE_NEEDED, '1.4.0622')

        # Downgrade needed
        status = self._get_update_status('1.3.0524', '5.8')
        assert status == (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0424')
        status = self._get_update_status('1.4.0622', '5.8')
        assert status == (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0424')
        status = self._get_update_status('1.4.0622', '5.9.1')
        assert status == (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0524')

        # Upgrade available
        status = self._get_update_status('1.3.0424', '5.9.1')
        assert status == (UPDATE_STATUS_UPDATE_AVAILABLE, '1.3.0524')
        status = self._get_update_status('1.3.0424', '5.9.2')
        assert status == (UPDATE_STATUS_UPDATE_AVAILABLE, '1.4.0622')
        status = self._get_update_status('1.3.0524', '5.9.2')
        assert status == (UPDATE_STATUS_UPDATE_AVAILABLE, '1.4.0622')
        status = self._get_update_status('2.4.2b1', '9.1')
        assert status == (UPDATE_STATUS_UPDATE_AVAILABLE, '2.4.2')
        status = self._get_update_status('2.5.0b1', '9.2')
        assert status == (UPDATE_STATUS_UPDATE_AVAILABLE, '2.5.0b2')

        # Up-to-date
        status = self._get_update_status('1.3.0424', '5.8')
        assert status == (UPDATE_STATUS_UP_TO_DATE, None)
        status = self._get_update_status('1.3.0524', '5.9.1')
        assert status == (UPDATE_STATUS_UP_TO_DATE, None)
        status = self._get_update_status('1.4.0622', '5.9.2')
        assert status == (UPDATE_STATUS_UP_TO_DATE, None)
        status = self._get_update_status('1.4.0622', '5.9.3')
        assert status == (UPDATE_STATUS_UP_TO_DATE, None)
        status = self._get_update_status('2.4.2', '9.1')
        assert status == (UPDATE_STATUS_UP_TO_DATE, None)

        # Test multi server
        status = self._get_update_status('1.3.0524', '5.9.2', '5.9.1')
        assert status == (UPDATE_STATUS_UP_TO_DATE, None)
        # Force upgrade for the 5.9.3 server
        status = self._get_update_status('1.3.0524', '5.9.2', '5.9.3')
        assert status == (UPDATE_STATUS_UPGRADE_NEEDED, '1.4.0622')
        # No compatible version with 5.9.1 and 5.9.3
        status = self._get_update_status('1.3.0524', '5.9.1', '5.9.3')
        assert status == (UPDATE_STATUS_MISSING_VERSION, None)
        # Need to downgrade for 5.8 server
        status = self._get_update_status('1.3.0524', '5.8', '5.9.1')
        assert status == (UPDATE_STATUS_DOWNGRADE_NEEDED, '1.3.0424')
        # Up to date once downgrade
        status = self._get_update_status('1.3.0424', '5.8', '5.9.1')
        assert status == (UPDATE_STATUS_UP_TO_DATE, None)
        # Limit the range of upgrade because of 5.9.1 server
        status = self._get_update_status('1.3.0424', '5.9.2', '5.9.1')
        assert status == (UPDATE_STATUS_UPDATE_AVAILABLE, '1.3.0524')
