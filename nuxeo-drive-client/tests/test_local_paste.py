# coding: utf-8
import os
import shutil
import tempfile

from common_unit_test import UnitTestCase
from tests.common import clean_dir
from tests.common_unit_test import FILE_CONTENT

TEST_TIMEOUT = 60


class TestLocalPaste(UnitTestCase):
    """
    1. create folder 'temp/a1' with more than 20 files in it
    2. create folder 'temp/a2', empty
    3. copy 'a1' and 'a2', in this order to the test sync root
    4. repeat step 3, but copy 'a2' and 'a1', in this order (to the test sync root)
    5. Verify that both folders and their content is sync to DM, in both steps 3 and 4
    """

    NUMBER_OF_LOCAL_FILES = 25
    TEMP_FOLDER = u'temp_folder'
    FOLDER_A1 = u'a1'
    FOLDER_A2 = u'a2'
    FILENAME_PATTERN = u'file%03d.txt'

    def setUp(self):
        super(TestLocalPaste, self).setUp()

        self.engine_1.start()
        self.wait_sync(wait_for_async=True)
        assert self.local_client_1.exists('/')
        self.workspace_abspath = self.local_client_1.abspath('/')

        # create  folder a1 and a2 under a temp folder
        self.local_temp = tempfile.mkdtemp(self.TEMP_FOLDER)
        self.addCleanup(clean_dir, self.local_temp)

        self.folder1 = os.path.join(self.local_temp, self.FOLDER_A1)
        os.makedirs(self.folder1)
        self.folder2 = os.path.join(self.local_temp, self.FOLDER_A2)
        os.makedirs(self.folder2)

        # add files in folder 'temp/a1'
        for file_num in range(1, self.NUMBER_OF_LOCAL_FILES + 1):
            filename = self.FILENAME_PATTERN % file_num
            with open(os.path.join(self.folder1, filename), 'w') as f:
                f.write(FILE_CONTENT)

    def test_copy_paste_empty_folder_first(self):
        """
        Copy 'a2' to 'Nuxeo Drive Test Workspace',
        then 'a1'to 'Nuxeo Drive Test Workspace'.
        """
        
        # copy 'temp/a2' under 'Nuxeo Drive Test Workspace'
        shutil.copytree(self.folder2, os.path.join(self.workspace_abspath, self.FOLDER_A2))

        # copy 'temp/a1' under 'Nuxeo Drive Test Workspace'
        shutil.copytree(self.folder1, os.path.join(self.workspace_abspath, self.FOLDER_A1))
        self.wait_sync(timeout=TEST_TIMEOUT)

        # check that '/Nuxeo Drive Test Workspace/a1' does exist
        assert self.local_client_1.exists(os.path.join('/', self.FOLDER_A1))

        # check that '/Nuxeo Drive Test Workspace/a2' does exist
        assert self.local_client_1.exists(os.path.join('/', self.FOLDER_A2))

        # check that '/Nuxeo Drive Test Workspace/a1/ has all the files
        children = os.listdir(os.path.join(self.workspace_abspath, self.FOLDER_A1))
        assert len(children) == self.NUMBER_OF_LOCAL_FILES

        # check that remote (DM) 'Nuxeo Drive Test Workspace/a1' exists
        remote_ref_1 = self.local_client_1.get_remote_id(os.path.join('/', self.FOLDER_A1))
        assert self.remote_file_system_client_1.exists(remote_ref_1)

        # check that remote (DM) 'Nuxeo Drive Test Workspace/a2' exists
        remote_ref_2 = self.local_client_1.get_remote_id(os.path.join('/', self.FOLDER_A2))
        assert self.remote_file_system_client_1.exists(remote_ref_2)

        # check that remote (DM) 'Nuxeo Drive Test Workspace/a1' has all the files
        remote_children = [remote_info.name
                           for remote_info in self.remote_file_system_client_1.get_children_info(remote_ref_1)]
        assert len(remote_children) == self.NUMBER_OF_LOCAL_FILES

    def test_copy_paste_empty_folder_last(self):
        """
        Copy 'a1' to 'Nuxeo Drive Test Workspace',
        then 'a2' to 'Nuxeo Drive Test Workspace'.
        """
        
        workspace_abspath = self.local_client_1.abspath('/')
        # copy 'temp/a1' under 'Nuxeo Drive Test Workspace'
        shutil.copytree(self.folder1, os.path.join(workspace_abspath, self.FOLDER_A1))

        # copy 'temp/a2' under 'Nuxeo Drive Test Workspace'
        shutil.copytree(self.folder2, os.path.join(workspace_abspath, self.FOLDER_A2))
        self.wait_sync(timeout=TEST_TIMEOUT)

        # check that '/Nuxeo Drive Test Workspace/a1' does exist
        assert self.local_client_1.exists(os.path.join('/', self.FOLDER_A1))

        # check that '/Nuxeo Drive Test Workspace/a2' does exist
        assert self.local_client_1.exists(os.path.join('/', self.FOLDER_A2))

        # check that '/Nuxeo Drive Test Workspace/a1/ has all the files
        children = os.listdir(os.path.join(self.workspace_abspath, self.FOLDER_A1))
        assert len(children) == self.NUMBER_OF_LOCAL_FILES

        # check that remote (DM) 'Nuxeo Drive Test Workspace/a1' exists
        remote_ref_1 = self.local_client_1.get_remote_id(os.path.join('/', self.FOLDER_A1))
        assert self.remote_file_system_client_1.exists(remote_ref_1)

        # check that remote (DM) 'Nuxeo Drive Test Workspace/a2' exists
        remote_ref_2 = self.local_client_1.get_remote_id(os.path.join('/', self.FOLDER_A2))
        assert self.remote_file_system_client_1.exists(remote_ref_2)

        # check that remote (DM) 'Nuxeo Drive Test Workspace/a1' has all the files
        remote_children = [remote_info.name
                           for remote_info in self.remote_file_system_client_1.get_children_info(remote_ref_1)]
        assert len(remote_children) == self.NUMBER_OF_LOCAL_FILES

    def test_copy_paste_same_file(self):
        """
        Copy 'a1' to 'Nuxeo Drive Test Workspace',
        then 'a2' to 'Nuxeo Drive Test Workspace'.
        """

        name = self.FILENAME_PATTERN % 1
        workspace_abspath = self.local_client_1.abspath('/')
        path = os.path.join('/', self.FOLDER_A1, name)
        copypath = os.path.join('/', self.FOLDER_A1, name + 'copy')

        # copy 'temp/a1' under 'Nuxeo Drive Test Workspace'
        os.mkdir(os.path.join(workspace_abspath, self.FOLDER_A1))
        shutil.copy2(os.path.join(self.folder1, name), os.path.join(workspace_abspath, self.FOLDER_A1, name))
        self.wait_sync(timeout=TEST_TIMEOUT)

        # check that '/Nuxeo Drive Test Workspace/a1' does exist
        assert self.local_client_1.exists(os.path.join('/', self.FOLDER_A1))

        # check that '/Nuxeo Drive Test Workspace/a1/ has all the files
        children = os.listdir(os.path.join(self.workspace_abspath, self.FOLDER_A1))
        assert len(children) == 1

        # check that remote (DM) 'Nuxeo Drive Test Workspace/a1' exists
        remote_ref_1 = self.local_client_1.get_remote_id(os.path.join('/', self.FOLDER_A1))
        assert self.remote_file_system_client_1.exists(remote_ref_1)
        remote_children = [remote_info.name
                           for remote_info in self.remote_file_system_client_1.get_children_info(remote_ref_1)]
        assert len(remote_children) == 1
        remote_id = self.local_client_1.get_remote_id(path)

        shutil.copy2(self.local_client_1.abspath(path), self.local_client_1.abspath(copypath))
        self.local_client_1.set_remote_id(copypath, remote_id)
        self.wait_sync(timeout=TEST_TIMEOUT)
        remote_children = [remote_info.name
                           for remote_info in self.remote_file_system_client_1.get_children_info(remote_ref_1)]
        assert len(remote_children) == 2
        children = os.listdir(os.path.join(self.workspace_abspath, self.FOLDER_A1))
        assert len(children) == 2
