# coding: utf-8
import sys
import urllib2
from time import sleep

import pytest

from nxdrive.client import LocalClient
from nxdrive.client.remote_filtered_file_system_client import \
    RemoteFilteredFileSystemClient
from nxdrive.engine.dao.sqlite import EngineDAO
from nxdrive.engine.engine import Engine
from nxdrive.osi import AbstractOSIntegration
from tests import RemoteTestClient
from tests.common import RemoteDocumentClientForTests, TEST_WORKSPACE_PATH
from tests.common_unit_test import RandomBug, UnitTestCase

# TODO NXDRIVE-170: refactor
LastKnownState = None


class TestLocalMoveAndRename(UnitTestCase):
    """
    Sets up the following local hierarchy:
    
    Nuxeo Drive Test Workspace
        |-- Original File 1.txt
        |-- Original File 2.txt
        |-- Original Folder 1
        |    |-- Sub-Folder 1.1
        |    |-- Sub-Folder 1.2
        |    |-- Original File 1.1.txt
        |-- Original Folder 2
        |    |-- Original File 3.txt
    """
    
    def setUp(self):
        self.engine_1.start()
        self.wait_sync(wait_for_async=True)
        self.local_client_1.make_file('/', u'Original File 1.txt',
                                      content=u'Some Content 1'.encode('utf-8'))

        self.local_client_1.make_file('/', u'Original File 2.txt',
                                      content=u'Some Content 2'.encode('utf-8'))

        self.local_client_1.make_folder(u'/', u'Original Folder 1')
        self.local_client_1.make_folder(
            u'/Original Folder 1', u'Sub-Folder 1.1')
        self.local_client_1.make_folder(
            u'/Original Folder 1', u'Sub-Folder 1.2')
        self.local_client_1.make_file(u'/Original Folder 1',
                                      u'Original File 1.1.txt',
                                      content=u'Some Content 1'.encode('utf-8'))  # Same content as OF1

        self.local_client_1.make_folder('/', 'Original Folder 2')
        self.local_client_1.make_file('/Original Folder 2',
                                      u'Original File 3.txt',
                                      content=u'Some Content 3'.encode('utf-8'))
        # Increase timeout as noticed it was sometimes insufficient in Jenkins build
        self.wait_sync(timeout=30)

    def get_local_client(self, path):
        if sys.platform == 'darwin':
            tests = ('test_local_delete_readonly_folder',
                     'test_local_rename_readonly_folder')
            if self._testMethodName in tests:
                return LocalClient(path)

            # Old mac don't handle case rename
            tests = ('test_local_rename_file_uppercase_stopped',
                     'test_local_rename_file_uppercase')
            if (AbstractOSIntegration.os_version_below('10.10')
                    and self._testMethodName in tests):
                return LocalClient(path)

        return super(TestLocalMoveAndRename, self).get_local_client(path)

    def test_local_rename_folder_while_creating(self):
        global marker
        local = self.local_client_1
        root_local_client = self.local_root_client_1
        remote = self.remote_document_client_1
        marker = False

        def update_remote_state(row, info, remote_parent_path=None, versionned=True, queue=True, force_update=False,
                                    no_digest=False):
            global marker
            EngineDAO.update_remote_state(self.engine_1._dao, row, info, remote_parent_path=remote_parent_path,
                                    versionned=versionned, queue=queue, force_update=force_update, no_digest=no_digest)
            if row.local_name == 'New Folder' and not marker:
                root_local_client.rename(row.local_path, 'Renamed Folder')
                marker = True

        self.engine_1._dao.update_remote_state = update_remote_state
        local.make_folder('/', 'New Folder')
        self.wait_sync(fail_if_timeout=False)

        assert local.exists(u'/Renamed Folder')
        assert not local.exists(u'/New Folder')
        # Path dont change on Nuxeo
        info = remote.get_info(u'/New Folder')
        assert info.name == 'Renamed Folder'
        assert len(local.get_children_info(u'/')) == 5
        assert len(remote.get_children_info(self.workspace_1)) == 5

    def test_local_rename_file_while_creating(self):
        global marker, client
        local = self.local_client_1
        root_local_client = self.local_root_client_1
        remote = self.remote_document_client_1
        marker = False
        client = None

        def set_remote_id(ref,remote_id,name='ndrive'):
            global marker, client
            LocalClient.set_remote_id(client, ref, remote_id, name)
            if 'File.txt' in ref and not marker:
                root_local_client.rename(ref, 'Renamed File.txt')
                marker = True

        def get_local_client():
            global client
            client = Engine.get_local_client(self.engine_1)
            client.set_remote_id = set_remote_id
            return client

        self.engine_1.get_local_client = get_local_client
        self.local_client_1.make_file('/', u'File.txt',
                                      content=u'Some Content 2'.encode('utf-8'))
        self.wait_sync(fail_if_timeout=False)

        assert local.exists(u'/Renamed File.txt')
        assert not local.exists(u'/File.txt')
        # Path dont change on Nuxeo
        info = remote.get_info(u'/File.txt')
        assert info.name == 'Renamed File.txt'
        assert len(local.get_children_info(u'/')) == 5
        assert len(remote.get_children_info(self.workspace_1)) == 5

    @RandomBug('NXDRIVE-811', target='windows', mode='BYPASS')
    def test_local_rename_file_while_creating_before_marker(self):
        global marker, client
        local = self.local_client_1
        root_local_client = self.local_root_client_1
        remote = self.remote_document_client_1
        marker = False
        client = None

        def set_remote_id(ref,remote_id,name='ndrive'):
            global marker, client
            if 'File.txt' in ref and not marker:
                root_local_client.rename(ref, 'Renamed File.txt')
                marker = True
            LocalClient.set_remote_id(client, ref, remote_id, name)

        def get_local_client():
            global client
            client = Engine.get_local_client(self.engine_1)
            client.set_remote_id = set_remote_id
            return client

        self.engine_1.get_local_client = get_local_client
        self.local_client_1.make_file('/', u'File.txt',
                                      content=u'Some Content 2'.encode('utf-8'))
        self.wait_sync(fail_if_timeout=False)

        assert local.exists(u'/Renamed File.txt')
        assert not local.exists(u'/File.txt')
        # Path dont change on Nuxeo
        info = remote.get_info(u'/File.txt')
        assert info.name == 'Renamed File.txt'
        assert len(local.get_children_info(u'/')) == 5
        assert len(remote.get_children_info(self.workspace_1)) == 5

    def test_local_rename_file_while_creating_after_marker(self):
        global marker
        local = self.local_client_1
        root_local_client = self.local_root_client_1
        remote = self.remote_document_client_1
        marker = False

        def update_remote_state(row, info, remote_parent_path=None, versionned=True, queue=True,
                                force_update=False, no_digest=False):
            global marker
            EngineDAO.update_remote_state(self.engine_1._dao, row, info, remote_parent_path=remote_parent_path,
                                versionned=versionned, queue=queue, force_update=force_update, no_digest=no_digest)
            if row.local_name == 'File.txt' and not marker:
                root_local_client.rename(row.local_path, 'Renamed File.txt')
                marker = True

        self.engine_1._dao.update_remote_state = update_remote_state
        self.local_client_1.make_file('/', u'File.txt',
                                      content=u'Some Content 2'.encode('utf-8'))
        self.wait_sync(fail_if_timeout=False)

        assert local.exists(u'/Renamed File.txt')
        assert not local.exists(u'/File.txt')
        # Path dont change on Nuxeo
        info = remote.get_info(u'/File.txt')
        assert info.name == 'Renamed File.txt'
        assert len(local.get_children_info(u'/')) == 5
        assert len(remote.get_children_info(self.workspace_1)) == 5

    def test_replace_file(self):
        local = self.local_client_1

        # Rename /Original File 1.txt to /Renamed File 1.txt
        original_file_1_uid = local.get_remote_id(u'/Original File 1.txt')
        local.remove_remote_id(u'/Original File 1.txt')
        local.update_content(u'/Original File 1.txt', 'plop')
        
        self.wait_sync(fail_if_timeout=False)
        uid = local.get_remote_id(u'/Original File 1.txt')
        assert uid == original_file_1_uid

    def test_local_rename_file(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Rename /Original File 1.txt to /Renamed File 1.txt
        original_file_1_uid = remote.get_info(
            u'/Original File 1.txt').uid
        local.rename(u'/Original File 1.txt', u'Renamed File 1.txt')
        assert not local.exists(u'/Original File 1.txt')
        assert local.exists(u'/Renamed File 1.txt')

        self.wait_sync()
        assert not local.exists(u'/Original File 1.txt')
        assert local.exists(u'/Renamed File 1.txt')
        original_file_1_remote_info = remote.get_info(original_file_1_uid)
        assert original_file_1_remote_info.name == u'Renamed File 1.txt'

        # Rename 'Renamed File 1.txt' to 'Renamed Again File 1.txt'
        # and 'Original File 1.1.txt' to
        # 'Renamed File 1.1.txt' at the same time as they share
        # the same digest but do not live in the same folder
        original_1_1_uid = remote.get_info(
            u'/Original Folder 1/Original File 1.1.txt').uid
        local.rename(
            u'/Original Folder 1/Original File 1.1.txt',
            u'Renamed File 1.1 \xe9.txt')
        assert not local.exists('/Original Folder 1/Original File 1.1.txt')
        assert local.exists(u'/Original Folder 1/Renamed File 1.1 \xe9.txt')
        local.rename('/Renamed File 1.txt', 'Renamed Again File 1.txt')
        assert not local.exists(u'/Renamed File 1.txt')
        assert local.exists(u'/Renamed Again File 1.txt')

        self.wait_sync()
        assert not local.exists(u'/Renamed File 1.txt')
        assert local.exists(u'/Renamed Again File 1.txt')
        assert not local.exists(u'/Original Folder 1/Original File 1.1.txt')
        assert local.exists(u'/Original Folder 1/Renamed File 1.1 \xe9.txt')

        file_1_remote_info = remote.get_info(original_file_1_uid)
        assert file_1_remote_info.name == u'Renamed Again File 1.txt'

        # User 1 does not have the rights to see the parent container
        # of the test workspace, hence set fetch_parent_uid=False
        parent_of_file_1_remote_info = remote.get_info(
            file_1_remote_info.parent_uid, fetch_parent_uid=False)
        assert parent_of_file_1_remote_info.name == self.workspace_title

        file_1_1_remote_info = remote.get_info(original_1_1_uid)
        assert file_1_1_remote_info.name == u'Renamed File 1.1 \xe9.txt'

        parent_of_file_1_1_remote_info = remote.get_info(
            file_1_1_remote_info.parent_uid)
        assert parent_of_file_1_1_remote_info.name == u'Original Folder 1'
        assert len(local.get_children_info(u'/Original Folder 1')) == 3
        assert len(remote.get_children_info(file_1_1_remote_info.parent_uid)) == 3
        assert len(local.get_children_info(u'/')) == 4
        assert len(remote.get_children_info(self.workspace_1)) == 4

    def test_local_rename_file_uppercase_stopped(self):
        local = self.local_client_1
        remote = self.remote_document_client_1
        self.engine_1.stop()

        # Rename /Original File 1.txt to /Renamed File 1.txt

        # Rename 'Renamed File 1.txt' to 'Renamed Again File 1.txt'
        # and 'Original File 1.1.txt' to
        # 'Renamed File 1.1.txt' at the same time as they share
        # the same digest but do not live in the same folder
        original_1_1_uid = remote.get_info(
            u'/Original Folder 1/Original File 1.1.txt').uid
        local.rename(
            u'/Original Folder 1/Original File 1.1.txt',
            u'original File 1.1.txt')

        self.engine_1.start()
        self.wait_sync()

        file_1_1_remote_info = remote.get_info(original_1_1_uid)
        assert file_1_1_remote_info.name == u'original File 1.1.txt'

        parent_of_file_1_1_remote_info = remote.get_info(
            file_1_1_remote_info.parent_uid)
        assert parent_of_file_1_1_remote_info.name == u'Original Folder 1'
        assert len(local.get_children_info(u'/Original Folder 1')) == 3
        assert len(remote.get_children_info(file_1_1_remote_info.parent_uid)) == 3

    def test_local_rename_file_uppercase(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Rename /Original File 1.txt to /Renamed File 1.txt

        # Rename 'Renamed File 1.txt' to 'Renamed Again File 1.txt'
        # and 'Original File 1.1.txt' to
        # 'Renamed File 1.1.txt' at the same time as they share
        # the same digest but do not live in the same folder
        original_1_1_uid = remote.get_info(
            u'/Original Folder 1/Original File 1.1.txt').uid
        local.rename(
            u'/Original Folder 1/Original File 1.1.txt',
            u'original File 1.1.txt')

        self.wait_sync()

        file_1_1_remote_info = remote.get_info(original_1_1_uid)
        assert file_1_1_remote_info.name ==  u'original File 1.1.txt'

        parent_of_file_1_1_remote_info = remote.get_info(
            file_1_1_remote_info.parent_uid)
        assert parent_of_file_1_1_remote_info.name == u'Original Folder 1'
        assert len(local.get_children_info(u'/Original Folder 1')) == 3
        assert len(remote.get_children_info(file_1_1_remote_info.parent_uid)) == 3

    def test_local_move_file(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Move /Original File 1.txt to /Original Folder 1/Original File 1.txt
        original_file_1_uid = remote.get_info(
            u'/Original File 1.txt').uid
        local.move(u'/Original File 1.txt', u'/Original Folder 1')
        assert not local.exists(u'/Original File 1.txt')
        assert local.exists(u'/Original Folder 1/Original File 1.txt')

        self.wait_sync()
        assert not local.exists(u'/Original File 1.txt')
        assert local.exists(u'/Original Folder 1/Original File 1.txt')

        file_1_remote_info = remote.get_info(original_file_1_uid)
        assert file_1_remote_info.name == u'Original File 1.txt'
        parent_of_file_1_remote_info = remote.get_info(
            file_1_remote_info.parent_uid)
        assert parent_of_file_1_remote_info.name == u'Original Folder 1'
        assert len(local.get_children_info(u'/Original Folder 1')) == 4
        assert len(remote.get_children_info(file_1_remote_info.parent_uid)) == 4
        assert len(local.get_children_info(u'/')) == 3
        assert len(remote.get_children_info(self.workspace_1)) == 3

    def test_local_move_and_rename_file(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Rename /Original File 1.txt to /Renamed File 1.txt
        original_file_1_uid = remote.get_info(
            u'/Original File 1.txt').uid

        local.move(u'/Original File 1.txt', u'/Original Folder 1',
                   name=u'Renamed File 1 \xe9.txt')
        assert not local.exists(u'/Original File 1.txt')
        assert local.exists(u'/Original Folder 1/Renamed File 1 \xe9.txt')

        self.wait_sync()
        assert not local.exists(u'/Original File 1.txt')
        assert local.exists(u'/Original Folder 1/Renamed File 1 \xe9.txt')

        file_1_remote_info = remote.get_info(original_file_1_uid)
        assert file_1_remote_info.name == u'Renamed File 1 \xe9.txt'
        parent_of_file_1_remote_info = remote.get_info(
            file_1_remote_info.parent_uid)
        assert parent_of_file_1_remote_info.name == u'Original Folder 1'
        assert len(local.get_children_info(u'/Original Folder 1')) == 4
        assert len(remote.get_children_info(file_1_remote_info.parent_uid)) == 4
        assert len(local.get_children_info(u'/')) == 3
        assert len(remote.get_children_info(self.workspace_1)) == 3

    def test_local_rename_folder(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Save the uid of some files and folders prior to renaming
        original_folder_1_uid = remote.get_info(
            u'/Original Folder 1').uid
        original_file_1_1_uid = remote.get_info(
            u'/Original Folder 1/Original File 1.1.txt').uid
        original_sub_folder_1_1_uid = remote.get_info(
            u'/Original Folder 1/Sub-Folder 1.1').uid

        # Rename a non empty folder with some content
        local.rename(u'/Original Folder 1', u'Renamed Folder 1 \xe9')
        assert not local.exists(u'/Original Folder 1')
        assert local.exists(u'/Renamed Folder 1 \xe9')

        # Synchronize: only the folder renaming is detected: all
        # the descendants are automatically realigned
        self.wait_sync()

        # The server folder has been renamed: the uid stays the same
        new_remote_name = remote.get_info(original_folder_1_uid).name
        assert new_remote_name == u'Renamed Folder 1 \xe9'

        # The content of the renamed folder is left unchanged
        file_1_1_info = remote.get_info(original_file_1_1_uid)
        assert file_1_1_info.name == u'Original File 1.1.txt'
        assert file_1_1_info.parent_uid == original_folder_1_uid

        sub_folder_1_1_info = remote.get_info(
            original_sub_folder_1_1_uid)
        assert sub_folder_1_1_info.name == u'Sub-Folder 1.1'
        assert sub_folder_1_1_info.parent_uid == original_folder_1_uid

        assert len(local.get_children_info(u'/Renamed Folder 1 \xe9')) == 3
        assert len(remote.get_children_info(file_1_1_info.parent_uid)) == 3
        assert len(local.get_children_info(u'/')) == 4
        assert len(remote.get_children_info(self.workspace_1)) == 4

    def test_local_rename_folder_while_suspended(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Save the uid of some files and folders prior to renaming
        original_folder_1_uid = remote.get_info(
            u'/Original Folder 1').uid
        original_file_1_1_uid = remote.get_info(
            u'/Original Folder 1/Original File 1.1.txt').uid
        original_sub_folder_1_1_uid = remote.get_info(
            u'/Original Folder 1/Sub-Folder 1.1').uid
        count = len(local.get_children_info(u'/Original Folder 1'))
        self.engine_1.suspend()
        # Rename a non empty folder with some content
        local.rename(u'/Original Folder 1', u'Renamed Folder 1 \xe9')
        assert not local.exists(u'/Original Folder 1')
        assert local.exists(u'/Renamed Folder 1 \xe9')

        local.rename(u'/Renamed Folder 1 \xe9/Sub-Folder 1.1', u'Sub-Folder 2.1')
        assert local.exists(u'/Renamed Folder 1 \xe9/Sub-Folder 2.1')
        local.make_file(u'/Renamed Folder 1 \xe9', u'Test.txt',
                        content=u'Some Content 1'.encode('utf-8'))  # Same content as OF1
        count += 1
        self.engine_1.resume()
        # Synchronize: only the folder renaming is detected: all
        # the descendants are automatically realigned
        self.wait_sync(wait_for_async=True)

        # The server folder has been renamed: the uid stays the same
        new_remote_name = remote.get_info(original_folder_1_uid).name
        assert new_remote_name == u'Renamed Folder 1 \xe9'

        # The content of the renamed folder is left unchanged
        file_1_1_info = remote.get_info(original_file_1_1_uid)
        assert file_1_1_info.name == u'Original File 1.1.txt'
        assert file_1_1_info.parent_uid == original_folder_1_uid

        sub_folder_1_1_info = remote.get_info(
            original_sub_folder_1_1_uid)
        assert sub_folder_1_1_info.name == u'Sub-Folder 2.1'
        assert sub_folder_1_1_info.parent_uid == original_folder_1_uid
        assert len(local.get_children_info(u'/Renamed Folder 1 \xe9')) == count
        assert len(remote.get_children_info(original_folder_1_uid)) == count
        assert len(local.get_children_info(u'/')) == 4
        assert len(remote.get_children_info(self.workspace_1)) == 4

    def test_local_rename_file_after_create(self):
        # Office 2010 and >, create a tmp file with 8 chars and move it right after
        global marker
        local = self.local_client_1
        remote = self.remote_document_client_1

        local.make_file('/', u'File.txt',
                        content=u'Some Content 2'.encode('utf-8'))
        local.rename('/File.txt', 'Renamed File.txt')
        self.wait_sync(fail_if_timeout=False)
        assert local.exists(u'/Renamed File.txt')
        assert not local.exists(u'/File.txt')
        # Path dont change on Nuxeo
        assert local.get_remote_id('/Renamed File.txt')
        assert len(local.get_children_info(u'/')) == 5
        assert len(remote.get_children_info(self.workspace_1)) == 5

    def test_local_rename_file_after_create_detected(self):
        # Office 2010 and >, create a tmp file with 8 chars and move it right after
        global marker
        local = self.local_client_1
        remote = self.remote_document_client_1
        marker = False

        def insert_local_state(info, parent_path):
            global marker
            if info.name == 'File.txt' and not marker:
                self.local_client_1.rename('/File.txt', 'Renamed File.txt')
                sleep(2)
                marker = True
            EngineDAO.insert_local_state(self.engine_1._dao, info, parent_path)

        self.engine_1._dao.insert_local_state = insert_local_state
        # Might be blacklisted once
        self.engine_1.get_queue_manager()._error_interval = 3
        self.local_client_1.make_file('/', u'File.txt',
                                      content=u'Some Content 2'.encode('utf-8'))
        sleep(10)
        self.wait_sync(fail_if_timeout=False)
        assert local.exists(u'/Renamed File.txt')
        assert not local.exists(u'/File.txt')
        # Path dont change on Nuxeo
        assert local.get_remote_id('/Renamed File.txt')
        assert len(local.get_children_info(u'/')) == 5
        assert len(remote.get_children_info(self.workspace_1)) == 5

    def test_local_move_folder(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Save the uid of some files and folders prior to move
        original_folder_1_uid = remote.get_info(
            u'/Original Folder 1').uid
        original_folder_2_uid = remote.get_info(
            u'/Original Folder 2').uid
        original_file_1_1_uid = remote.get_info(
            u'/Original Folder 1/Original File 1.1.txt').uid
        original_sub_folder_1_1_uid = remote.get_info(
            u'/Original Folder 1/Sub-Folder 1.1').uid

        # Move a non empty folder with some content
        local.move(u'/Original Folder 1', u'/Original Folder 2')
        assert not local.exists(u'/Original Folder 1')
        assert local.exists(u'/Original Folder 2/Original Folder 1')

        # Synchronize: only the folder move is detected: all
        # the descendants are automatically realigned
        self.wait_sync()
        # The server folder has been moved: the uid stays the same
        remote_folder_info = remote.get_info(original_folder_1_uid)

        # The parent folder is now folder 2
        assert remote_folder_info.parent_uid == original_folder_2_uid

        # The content of the renamed folder is left unchanged
        file_1_1_info = remote.get_info(original_file_1_1_uid)
        assert file_1_1_info.name == u'Original File 1.1.txt'
        assert file_1_1_info.parent_uid == original_folder_1_uid

        sub_folder_1_1_info = remote.get_info(
            original_sub_folder_1_1_uid)
        assert sub_folder_1_1_info.name == u'Sub-Folder 1.1'
        assert sub_folder_1_1_info.parent_uid == original_folder_1_uid

        assert len(local.get_children_info(u'/Original Folder 2/Original Folder 1')) == 3
        assert len(remote.get_children_info(original_folder_1_uid)) == 3
        assert len(local.get_children_info(u'/')) == 3
        assert len(remote.get_children_info(self.workspace_1)) == 3

    def test_concurrent_local_rename_folder(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Save the uid of some files and folders prior to renaming
        folder_1_uid = remote.get_info(u'/Original Folder 1').uid
        file_1_1_uid = remote.get_info(
            u'/Original Folder 1/Original File 1.1.txt').uid
        folder_2_uid = remote.get_info(u'/Original Folder 2').uid
        file_3_uid = remote.get_info(
            u'/Original Folder 2/Original File 3.txt').uid

        # Rename a non empty folders concurrently
        local.rename(u'/Original Folder 1', u'Renamed Folder 1')
        local.rename(u'/Original Folder 2', u'Renamed Folder 2')
        assert not local.exists(u'/Original Folder 1')
        assert local.exists(u'/Renamed Folder 1')
        assert not local.exists(u'/Original Folder 2')
        assert local.exists(u'/Renamed Folder 2')

        # Synchronize: only the folder renamings are detected: all
        # the descendants are automatically realigned
        self.wait_sync()

        # The server folders have been renamed: the uid stays the same
        folder_1_info = remote.get_info(folder_1_uid)
        assert folder_1_info.name == u'Renamed Folder 1'

        folder_2_info = remote.get_info(folder_2_uid)
        assert folder_2_info.name == u'Renamed Folder 2'

        # The content of the folder has been left unchanged
        file_1_1_info = remote.get_info(file_1_1_uid)
        assert file_1_1_info.name == u'Original File 1.1.txt'
        assert file_1_1_info.parent_uid == folder_1_uid

        file_3_info = remote.get_info(file_3_uid)
        assert file_3_info.name == u'Original File 3.txt'
        assert file_3_info.parent_uid == folder_2_uid

        assert len(local.get_children_info(u'/Renamed Folder 1')) == 3
        assert len(remote.get_children_info(folder_1_uid)) == 3
        assert len(local.get_children_info(u'/Renamed Folder 2')) == 1
        assert len(remote.get_children_info(folder_2_uid)) == 1
        assert len(local.get_children_info(u'/')) == 4
        assert len(remote.get_children_info(self.workspace_1)) == 4

    def test_local_rename_sync_root_folder(self):
        # Use the Administrator to be able to introspect the container of the
        # test workspace.
        remote = RemoteDocumentClientForTests(
            self.nuxeo_url, self.admin_user,
            'nxdrive-test-administrator-device', self.version,
            password=self.password, base_folder=self.workspace)

        folder_1_uid = remote.get_info(u'/Original Folder 1').uid

        # Create new clients to be able to introspect the test sync root
        toplevel_local_client = LocalClient(self.local_nxdrive_folder_1)

        toplevel_local_client.rename('/' + self.workspace_title,
                                     'Renamed Nuxeo Drive Test Workspace')
        self.wait_sync()

        workspace_info = remote.get_info(self.workspace)
        assert workspace_info.name == u'Renamed Nuxeo Drive Test Workspace'

        folder_1_info = remote.get_info(folder_1_uid)
        assert folder_1_info.name == u'Original Folder 1'
        assert folder_1_info.parent_uid == self.workspace
        assert len(remote.get_children_info(self.workspace_1)) == 4

    def test_local_rename_readonly_folder(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Check local folder
        assert local.exists(u'/Original Folder 1')
        uid = local.get_remote_id(u'/Original Folder 1')
        folder_1_state = self.engine_1.get_dao().get_normal_state_from_remote(uid)
        assert folder_1_state.remote_can_rename

        # Set remote folder as readonly for test user
        folder_1_path = TEST_WORKSPACE_PATH + u'/Original Folder 1'
        op_input = "doc:" + folder_1_path
        self.root_remote.execute("Document.SetACE",
                                        op_input=op_input,
                                        user=self.user_1,
                                        permission="Read")
        self.root_remote.block_inheritance(folder_1_path,
                                                  overwrite=False)
        self.wait_sync(wait_for_async=True)
        # Check can_rename flag in pair state
        folder_1_state = self.engine_1.get_dao().get_normal_state_from_remote(uid)
        assert not folder_1_state.remote_can_rename

        # Rename local folder
        local.rename(u'/Original Folder 1', u'Renamed Folder 1 \xe9')
        assert not local.exists(u'/Original Folder 1')
        assert local.exists(u'/Renamed Folder 1 \xe9')

        self.wait_sync()

        # Check remote folder has not been renamed
        folder_1_remote_info = remote.get_info(u'/Original Folder 1')
        assert folder_1_remote_info.name == u'Original Folder 1'

        # Check state of local folder and its children
        folder_1_state = self.engine_1.get_dao().get_normal_state_from_remote(uid)
        assert folder_1_state.remote_name == u'Original Folder 1'

        # The folder is re-renamed to its original name
        folder_name = u'Original Folder 1'
        assert local.exists('/' + folder_name + '/Original File 1.1.txt')
        assert local.exists('/' + folder_name + '/Sub-Folder 1.1')
        assert local.exists('/' + folder_name + '/Sub-Folder 1.2')
        assert len(local.get_children_info('/' + folder_name)) == 3
        assert len(remote.get_children_info(folder_1_remote_info.uid)) == 3
        assert len(local.get_children_info('/')) == 4
        assert len(remote.get_children_info(self.workspace_1)) == 4

    def test_local_move_with_remote_error(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Check local folder
        assert local.exists(u'/Original Folder 1')

        # Simulate server error
        self.engine_1.remote_filtered_fs_client_factory = RemoteTestClient
        self.engine_1.invalidate_client_cache()
        error = urllib2.HTTPError(None, 500, 'Mock server error', None, None)
        self.engine_1.get_remote().make_server_call_raise(error)

        local.rename(u'/Original Folder 1', u'IOErrorTest')
        self.wait_sync(timeout=5, fail_if_timeout=False)
        folder_1 = remote.get_info(u'/Original Folder 1')
        assert folder_1.name == u'Original Folder 1'
        assert local.exists(u'/IOErrorTest')

        # Remove faulty client and set engine online
        self.engine_1.get_remote().make_server_call_raise(None)
        self.engine_1.remote_filtered_fs_client_factory = RemoteFilteredFileSystemClient
        self.engine_1.invalidate_client_cache()
        self.engine_1.set_offline(value=False)

        self.wait_sync()
        folder_1 = remote.get_info(folder_1.uid)
        assert folder_1.name == u'IOErrorTest'
        assert local.exists(u'/IOErrorTest')
        assert len(local.get_children_info(u'/IOErrorTest')) == 3
        assert len(remote.get_children_info(folder_1.uid)) == 3
        assert len(local.get_children_info(u'/')) == 4
        assert len(remote.get_children_info(self.workspace_1)) == 4

    def test_local_delete_readonly_folder(self):
        local = self.local_client_1
        remote = self.remote_document_client_1

        # Check local folder
        assert local.exists(u'/Original Folder 1')
        folder_1_state = self.get_dao_state_from_engine_1(u'/Original Folder 1')
        assert folder_1_state.remote_can_delete

        # Set remote folder as readonly for test user
        folder_1_path = TEST_WORKSPACE_PATH + u'/Original Folder 1'
        op_input = "doc:" + folder_1_path
        self.root_remote.execute(
            "Document.SetACE",
            op_input=op_input,
            user=self.user_1,
            permission="Read")
        self.root_remote.block_inheritance(folder_1_path, overwrite=False)

        self.wait_sync(wait_for_async=True)

        # Check can_delete flag in pair state
        folder_1_state = self.get_dao_state_from_engine_1(u'/Original Folder 1')
        assert not folder_1_state.remote_can_delete

        # Delete local folder
        local.delete(u'/Original Folder 1')
        assert not local.exists(u'/Original Folder 1')

        self.wait_sync(wait_for_async=True)
        assert self.engine_1.get_dao().get_sync_count() == 6

        # Check remote folder and its children have not been deleted
        folder_1_remote_info = remote.get_info(u'/Original Folder 1')
        assert folder_1_remote_info.name == u'Original Folder 1'

        file_1_1_remote_info = remote.get_info(u'/Original Folder 1/Original File 1.1.txt')
        assert file_1_1_remote_info.name == u'Original File 1.1.txt'

        folder_1_1_remote_info = remote.get_info(u'/Original Folder 1/Sub-Folder 1.1')
        assert folder_1_1_remote_info.name == u'Sub-Folder 1.1'

        folder_1_2_remote_info = remote.get_info(u'/Original Folder 1/Sub-Folder 1.2')
        assert folder_1_2_remote_info.name == u'Sub-Folder 1.2'

        if sys.platform != 'win32':
            # Check filter has been created
            dao = self.engine_1.get_dao()
            assert dao.is_filter(folder_1_state.remote_parent_path + '/' + folder_1_state.remote_ref)

            # Check local folder haven't been re-created
            assert not local.exists(u'/Original Folder 1')

    @pytest.mark.skip(reason='Need expectation on this one.')
    def test_local_move_folder_to_readonly(self):
        local = self.local_client_1

        # Check local folder
        assert local.exists(u'/Original Folder 1')
        folder_1_state = self.get_dao_state_from_engine_1(u'/Original Folder 1')
        assert folder_1_state.remote_can_delete

        # Set remote folder as readonly for test user
        folder_1_path = TEST_WORKSPACE_PATH + u'/Original Folder 1'
        op_input = "doc:" + folder_1_path
        self.root_remote.execute("Document.SetACE",
                                        op_input=op_input,
                                        user=self.user_1,
                                        permission="Read")
        self.root_remote.block_inheritance(folder_1_path, overwrite=False)

        self.wait_sync(wait_for_async=True)

        # Check can_delete flag in pair state
        folder_1_state = self.get_dao_state_from_engine_1(u'/Original Folder 1')
        assert not folder_1_state.remote_can_delete

        # Delete local folder
        local.unlock_ref(u'/Original Folder 1')
        local.move(u'/Original Folder 2', u'/Original Folder 1')
        assert not local.exists(u'/Original Folder 2')

        self.wait_sync(wait_for_async=True)
        # It should have move back Original Folder 2 to its origin as
        # the target is in read only

    @pytest.mark.skip(reason='TODO: implement me once canDelete is checked'
                             ' in the synchronizer.')
    def test_local_move_sync_root_folder(self):
        pass
