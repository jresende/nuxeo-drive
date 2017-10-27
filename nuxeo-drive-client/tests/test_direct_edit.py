# coding: utf-8
import os
import unittest
from urllib2 import HTTPError

from nxdrive.client import LocalClient
from nxdrive.client.common import LOCALLY_EDITED_FOLDER_NAME
from nxdrive.engine.engine import Engine
from tests.common_unit_test import UnitTestCase


class MockUrlTestEngine(Engine):
    def __init__(self, url):
        self._url = url

    def get_binder(self):
        from nxdrive.manager import ServerBindingSettings
        return ServerBindingSettings(
            server_url=self._url,
            web_authentication=None,
            server_version=None,
            username='Administrator',
            local_folder='/',
            initialized=True,
            pwd_update_required=False)


class TestDirectEdit(UnitTestCase):

    locally_edited_path = ('/default-domain/UserWorkspaces/'
                           + 'nuxeoDriveTestUser-user-1/Collections/'
                           + LOCALLY_EDITED_FOLDER_NAME)

    def setUpApp(self):
        super(TestDirectEdit, self).setUpApp()
        self.direct_edit = self.manager_1.direct_edit
        self.direct_edit._test = True
        self.direct_edit.directEditUploadCompleted.connect(self.app.sync_completed)
        self.direct_edit.start()

        self.remote = self.remote_document_client_1
        self.local = LocalClient(os.path.join(self.nxdrive_conf_folder_1, 'edit'))

    def tearDownApp(self):
        self.direct_edit.stop()
        super(TestDirectEdit, self).tearDownApp()

    def test_url_resolver(self):
        assert self.direct_edit._get_engine(self.nuxeo_url, self.user_1)
        assert not self.direct_edit._get_engine(self.nuxeo_url, u'Administrator')
        self.manager_1._engine_types['NXDRIVETESTURL'] = MockUrlTestEngine
        # HTTP EXPLICIT
        self.manager_1._engines['0'] = MockUrlTestEngine('http://localhost:80/nuxeo')
        assert not self.direct_edit._get_engine("http://localhost:8080/nuxeo", u'Administrator')
        assert self.direct_edit._get_engine("http://localhost:80/nuxeo", u'Administrator')
        assert self.direct_edit._get_engine("http://localhost/nuxeo/", u'Administrator')
        # HTTP IMPLICIT
        self.manager_1._engines['0'] = MockUrlTestEngine('http://localhost/nuxeo')
        assert not self.direct_edit._get_engine("http://localhost:8080/nuxeo", u'Administrator')
        assert self.direct_edit._get_engine("http://localhost:80/nuxeo/", u'Administrator')
        assert self.direct_edit._get_engine("http://localhost/nuxeo", u'Administrator')
        # HTTPS EXPLICIT
        self.manager_1._engines['0'] = MockUrlTestEngine('https://localhost:443/nuxeo')
        assert not self.direct_edit._get_engine("http://localhost:8080/nuxeo", u'Administrator')
        assert self.direct_edit._get_engine("https://localhost:443/nuxeo", u'Administrator')
        assert self.direct_edit._get_engine("https://localhost/nuxeo/", u'Administrator')
        # HTTPS IMPLICIT
        self.manager_1._engines['0'] = MockUrlTestEngine('https://localhost/nuxeo')
        assert not self.direct_edit._get_engine("http://localhost:8080/nuxeo", u'Administrator')
        assert self.direct_edit._get_engine("https://localhost:443/nuxeo/", u'Administrator')
        assert self.direct_edit._get_engine("https://localhost/nuxeo", u'Administrator')

    def test_note_edit(self):
        remote_fs_client = self.remote_file_system_client_1
        toplevel_folder_info = remote_fs_client.get_filesystem_root_info()
        workspace_id = remote_fs_client.get_children_info(
            toplevel_folder_info.uid)[0].uid
        file_1_id = remote_fs_client.make_file(workspace_id, u'Mode op\xe9ratoire.txt',
                                               "Content of file 1 Avec des accents h\xe9h\xe9.").uid
        doc_id = file_1_id.split('#')[-1]
        self._direct_edit_update(doc_id, u'Mode op\xe9ratoire.txt', 'Atol de PomPom Gali')

    def test_filename_encoding(self):
        filename = u'Mode op\xe9ratoire.txt'
        doc_id = self.remote.make_file('/', filename, 'Some content.')
        self._direct_edit_update(doc_id, filename, 'Test')

    def _test_locked_file_signal(self):
        self._received = True

    def test_locked_file(self):
        self._received = False
        filename = u'Mode operatoire.txt'
        doc_id = self.remote.make_file('/', filename, 'Some content.')
        self.remote_document_client_2.lock(doc_id)
        self.direct_edit.directEditLocked.connect(self._test_locked_file_signal)
        self.direct_edit._prepare_edit(self.nuxeo_url, doc_id)
        assert self._received

    def test_self_locked_file(self):
        filename = u'Mode operatoire.txt'
        doc_id = self.remote.make_file('/', filename, 'Some content.')
        self.remote.lock(doc_id)
        self._direct_edit_update(doc_id, filename, 'Test')

    def _office_locker(self, path):
        return os.path.join(os.path.dirname(path), "~$" + os.path.basename(path)[2:])

    def _openoffice_locker(self, path):
        return os.path.join(os.path.dirname(path), ".~lock." + os.path.basename(path)[2:])

#     def test_autolock_office(self):
#         self._autolock(self._office_locker)

#     def test_autolock_openoffice(self):
#      LibreOffice as well
#         self._autolock(self._openoffice_locker)

    def _autolock(self, locker):
        global called_open, lock_file
        called_open = False
        filename = u'Document.docx'
        doc_id = self.remote.make_file('/', filename, 'Some content.')

        def open_local_file(path):
            global called_open, lock_file
            called_open = True
            # Lock file
            lock_file = locker(path)
            with open(lock_file, 'w') as f:
                f.write("plop")

        self.manager_1.open_local_file = open_local_file
        self.manager_1.set_direct_edit_auto_lock(1)
        self.direct_edit._manager.open_local_file = open_local_file
        self.direct_edit.edit(self.nuxeo_url, doc_id, filename=filename, user=self.user_1)
        self.wait_sync(timeout=2, fail_if_timeout=False)
        assert called_open
        # Should be able to test lock
        assert self.remote_document_client_1.is_locked(doc_id)
        os.remove(lock_file)
        self.wait_sync(timeout=2, fail_if_timeout=False)
        # Should be unlock
        assert not self.remote_document_client_1.is_locked(doc_id)
        self.manager_1.set_direct_edit_auto_lock(0)
        with open(lock_file, 'w') as f:
            f.write("plop")
        self.wait_sync(timeout=2, fail_if_timeout=False)
        assert not self.remote_document_client_1.is_locked(doc_id)

    def _direct_edit_update(self, doc_id, filename, content, url=None):
        # Download file
        local_path = u'/%s/%s' % (doc_id, filename)

        def open_local_file(path):
            pass

        self.manager_1.open_local_file = open_local_file
        if url is None:
            self.direct_edit._prepare_edit(self.nuxeo_url, doc_id)
        else:
            self.direct_edit.handle_url(url)
        assert self.local.exists(local_path)
        self.wait_sync(timeout=2, fail_if_timeout=False)
        self.local.delete_final(local_path)

        # Update file content
        self.local.update_content(local_path, content)
        self.wait_sync()
        assert self.remote.get_blob(self.remote.get_info(doc_id)) == content

        # Update file content twice
        update_content = content + ' updated'
        self.local.update_content(local_path, update_content)
        self.wait_sync()
        assert self.remote.get_blob(self.remote.get_info(doc_id)) == update_content

    def test_direct_edit_cleanup(self):
        filename = u'Mode op\xe9ratoire.txt'
        doc_id = self.remote.make_file('/', filename, 'Some content.')
        # Download file
        local_path = u'/%s/%s' % (doc_id, filename)

        def open_local_file(_):
            pass

        self.manager_1.open_local_file = open_local_file
        self.direct_edit._prepare_edit(self.nuxeo_url, doc_id)
        assert self.local.exists(local_path)
        self.wait_sync(timeout=2, fail_if_timeout=False)
        self.direct_edit.stop()

        # Update file content
        self.local.update_content(local_path, 'Test')
        # Create empty folder (NXDRIVE-598)
        self.local.make_folder('/', 'emptyfolder')

        # Verify the cleanup dont delete document
        self.direct_edit._cleanup()
        assert self.local.exists(local_path)
        assert self.remote.get_blob(self.remote.get_info(doc_id)) != 'Test'

        # Verify it reupload it
        self.direct_edit.start()
        self.wait_sync(timeout=2, fail_if_timeout=False)
        assert self.local.exists(local_path)
        assert self.remote.get_blob(self.remote.get_info(doc_id)) == 'Test'

        # Verify it is cleanup if sync
        self.direct_edit.stop()
        self.direct_edit._cleanup()
        assert not self.local.exists(local_path)

    def test_user_name(self):
        # user_1 is drive_user_1, no more informations
        user = self.engine_1.get_user_full_name(self.user_1)
        assert user == self.user_1

        # Create a complete user
        remote = self.root_remote_client
        try:
            remote.create_user('john', firstName='John', lastName='Doe')
        except HTTPError as exc:
            if exc.code == 500:
                raise unittest.SkipTest('API not available.')
            else:
                raise exc
        user = self.engine_1.get_user_full_name('john')
        assert user == 'John Doe'

        # Unknown user
        user = self.engine_1.get_user_full_name('unknown')
        assert user == 'unknown'
