# coding: utf-8
import os
import shutil

from tests.common_unit_test import UnitTestCase


class TestLocalMoveFolders(UnitTestCase):

    NUMBER_OF_LOCAL_IMAGE_FILES = 10
    FILE_NAME_PATTERN = 'file%03d.%s'

    def _setup(self):
        """
        1. Create folder a1 in Nuxeo Drive Test Workspace sycn root
        2. Create folder a2 in Nuxeo Drive Test Workspace sycn root
        3. Add 10 image files in a1
        4. Add 10 image files in a2
        """

        remote = self.remote_file_system_client_1

        self.engine_1.start()
        self.wait_sync(wait_for_async=True)
        self.engine_1.stop()

        # Create a1 and a2
        self.folder_path_1 = self.local_client_1.make_folder(u'/', u'a1')
        self.folder_path_2 = self.local_client_1.make_folder(u'/', u'a2')

        # Add image files to a1
        abs_folder_path_1 = self.local_client_1.abspath(self.folder_path_1)
        for file_num in range(1, self.NUMBER_OF_LOCAL_IMAGE_FILES + 1):
            file_name = self.FILE_NAME_PATTERN % (file_num, 'png')
            file_path = os.path.join(abs_folder_path_1, file_name)
            self.generate_random_png(file_path)

        # Add image files to a2
        abs_folder_path_2 = self.local_client_1.abspath(self.folder_path_2)
        for file_num in range(1, self.NUMBER_OF_LOCAL_IMAGE_FILES + 1):
            file_name = self.FILE_NAME_PATTERN % (file_num, 'png')
            file_path = os.path.join(abs_folder_path_2, file_name)
            self.generate_random_png(file_path)

        self.engine_1.start()
        self.wait_sync(timeout=60, wait_win=True)

        good = set(['file%03d.png' % file_num
                    for file_num in range(1, self.NUMBER_OF_LOCAL_IMAGE_FILES + 1)])

        # Check local files in a1
        assert self.local_client_1.exists('/a1')
        children_1 = [child.name for child in self.local_client_1.get_children_info('/a1')]
        assert len(children_1) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(children_1) == good

        # Check local files in a2
        assert self.local_client_1.exists('/a2')
        children_2 = [child.name for child in self.local_client_1.get_children_info('/a2')]
        assert len(children_2) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(children_2) == good

        # Check remote files in a1
        a1_remote_id = self.local_client_1.get_remote_id('/a1')
        assert a1_remote_id
        assert remote.exists(a1_remote_id)

        remote_children_1 = [child.name for child in remote.get_children_info(a1_remote_id)]
        assert len(remote_children_1) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(remote_children_1), good

        # Check remote files in a2
        a2_remote_id = self.local_client_1.get_remote_id('/a2')
        assert a2_remote_id
        assert remote.exists(a2_remote_id)

        remote_children_2 = [child.name for child in remote.get_children_info(a2_remote_id)]
        assert len(remote_children_2) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(remote_children_2), good

    def test_local_move_folder_with_files(self):
        self._setup()
        src = self.local_client_1.abspath(self.folder_path_1)
        dst = self.local_client_1.abspath(self.folder_path_2)
        shutil.move(src, dst)
        self.wait_sync()

        remote = self.remote_file_system_client_1

        good = set(['file%03d.png' % file_num
                    for file_num in range(1, self.NUMBER_OF_LOCAL_IMAGE_FILES + 1)])

        # Check that a1 doesn't exist anymore locally
        assert not self.local_client_1.exists('/a1')

        # Check local files in a2
        assert self.local_client_1.exists('/a2')
        children_2 = [child.name for child in self.local_client_1.get_children_info('/a2') if not child.folderish]
        assert len(children_2) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(children_2) == good

        # Check local files in a2/a1
        assert self.local_client_1.exists('/a2/a1')
        children_1 = [child.name for child in self.local_client_1.get_children_info('/a2/a1')]
        assert len(children_1) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(children_1) == good

        # Check that a1 doesn't exist anymore remotely
        assert len(self.remote_document_client_1.get_children_info(self.workspace)) == 1

        # Check remote files in a2
        a2_remote_id = self.local_client_1.get_remote_id('/a2')
        assert a2_remote_id
        assert remote.exists(a2_remote_id)

        remote_children_2 = [child.name for child in remote.get_children_info(a2_remote_id)
                             if not child.folderish]
        assert len(remote_children_2) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(remote_children_2) == good

        # Check remote files in a2/a1
        a1_remote_id = self.local_client_1.get_remote_id('/a2/a1')
        assert a1_remote_id
        assert remote.exists(a1_remote_id)

        remote_children_1 = [child.name for child in remote.get_children_info(a1_remote_id)]
        assert len(remote_children_1) == self.NUMBER_OF_LOCAL_IMAGE_FILES
        assert set(remote_children_1) == good

    def test_local_move_folder_both_sides_while_stopped(self):
        self._test_local_move_folder_both_sides(False)

    def test_local_move_folder_both_sides_while_unbinded(self):
        self._test_local_move_folder_both_sides(True)

    def _test_local_move_folder_both_sides(self, unbind):
        """ NXDRIVE-647: sync when a folder is renamed locally and remotely. """

        local = self.local_client_1
        remote = self.remote_document_client_1

        # Create initial folder and file
        folder = remote.make_folder('/', 'Folder1')
        self.engine_1.start()
        self.wait_sync(wait_for_async=True)

        # First checks, everything should be online for every one
        assert remote.exists('/Folder1')
        assert local.exists('/Folder1')
        folder_pair_state = self.engine_1.get_dao().get_state_from_local(
            '/' + self.workspace_title + '/Folder1')
        assert folder_pair_state
        folder_remote_ref = folder_pair_state.remote_ref

        # Unbind or stop engine
        if unbind:
            self.send_unbind_engine(1)
            self.wait_unbind_engine(1)
        else:
            self.engine_1.stop()

        # Make changes
        remote.update(folder, properties={'dc:title': 'Folder1_ServerName'})
        local.rename('/Folder1', 'Folder1_LocalRename')

        # Bind or start engine and wait for sync
        if unbind:
            self.send_bind_engine(1)
            self.wait_bind_engine(1)
        else:
            self.engine_1.start()
        self.wait_sync(wait_for_async=True)

        # Check that nothing has changed
        assert len(remote.get_children_info(self.workspace)) == 1
        assert remote.exists(folder)
        assert remote.get_info(folder).name == 'Folder1_ServerName'
        assert len(local.get_children_info('/')) == 1
        assert local.exists('/Folder1_LocalRename')

        # Check folder status
        folder = self.engine_1.get_dao().get_normal_state_from_remote(folder_remote_ref)
        assert folder.pair_state == 'conflicted'
