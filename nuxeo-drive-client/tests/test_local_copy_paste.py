# coding: utf-8
import os
import shutil
import sys

from tests.common_unit_test import FILE_CONTENT, RandomBug, UnitTestCase


class TestLocalCopyPaste(UnitTestCase):
    """
    1. create folder 'Nuxeo Drive Test Workspace/A' with 100 files in it
    2. create folder 'Nuxeo Drive Test Workspace/B'
    """

    NUMBER_OF_LOCAL_TEXT_FILES = 10
    NUMBER_OF_LOCAL_IMAGE_FILES = 10
    NUMBER_OF_LOCAL_FILES_TOTAL = NUMBER_OF_LOCAL_TEXT_FILES + NUMBER_OF_LOCAL_IMAGE_FILES
    FILE_NAME_PATTERN = 'file%03d%s'
    TEST_DOC_RESOURCE = 'cat.jpg'
    FOLDER_1 = u'A'
    FOLDER_2 = u'B'
    SYNC_TIMEOUT = 100  # in seconds

    def setUp(self):
        super(TestLocalCopyPaste, self).setUp()

        local = self.local_root_client_1
        remote = self.remote_file_system_client_1

        self.engine_1.start()
        self.wait_sync(wait_for_async=True)
        self.engine_1.stop()
        assert local.exists('/Nuxeo Drive Test Workspace')

        # create  folder A
        local.make_folder("/Nuxeo Drive Test Workspace", self.FOLDER_1)
        self.folder_path_1 = os.path.join("/Nuxeo Drive Test Workspace", self.FOLDER_1)

        # create  folder B
        # NXDRIVE-477 If created after files are created inside A, creation of
        # B isn't detected wy Watchdog!
        # Reproducible with watchdemo, need to investigate.
        # That's why we are now using local scan for setUp.
        local.make_folder("/Nuxeo Drive Test Workspace", self.FOLDER_2)
        self.folder_path_2 = os.path.join("/Nuxeo Drive Test Workspace", self.FOLDER_2)

        # add text files in folder 'Nuxeo Drive Test Workspace/A'
        self.local_files_list = []
        for file_num in range(1, self.NUMBER_OF_LOCAL_TEXT_FILES + 1):
            filename = self.FILE_NAME_PATTERN % (file_num, '.txt')
            local.make_file(self.folder_path_1, filename, FILE_CONTENT)
            self.local_files_list.append(filename)

        test_resources_path = self._get_test_resources_path()
        if test_resources_path is None:
            test_resources_path = 'tests/resources'
        self.test_doc_path = os.path.join(test_resources_path, TestLocalCopyPaste.TEST_DOC_RESOURCE)

        # add image files in folder 'Nuxeo Drive Test Workspace/A'
        abs_folder_path_1 = local.abspath(self.folder_path_1)
        for file_num in range(self.NUMBER_OF_LOCAL_TEXT_FILES + 1, self.NUMBER_OF_LOCAL_FILES_TOTAL + 1):
            filename = self.FILE_NAME_PATTERN % (file_num, os.path.splitext(self.TEST_DOC_RESOURCE)[1])
            dst_path = os.path.join(abs_folder_path_1, filename)
            shutil.copyfile(self.test_doc_path, dst_path)
            self.local_files_list.append(filename)

        self.engine_1.start()
        self.wait_sync(timeout=self.SYNC_TIMEOUT)
        self.engine_1.stop()

        # get remote folders reference ids
        self.remote_ref_1 = local.get_remote_id(self.folder_path_1)
        assert self.remote_ref_1
        self.remote_ref_2 = local.get_remote_id(self.folder_path_2)
        assert self.remote_ref_2
        assert remote.exists(self.remote_ref_1)
        assert remote.exists(self.remote_ref_2)

        children = remote.get_children_info(self.remote_ref_1)
        assert len(children) == self.NUMBER_OF_LOCAL_FILES_TOTAL

    @RandomBug('NXDRIVE-815', target='mac', repeat=5)
    @RandomBug('NXDRIVE-815', target='windows', repeat=5)
    def test_local_copy_paste_files(self):
        self._local_copy_paste_files(stopped=False)

    def test_local_copy_paste_files_stopped(self):
        self._local_copy_paste_files(stopped=True)

    def _local_copy_paste_files(self, stopped=False):
        remote = self.remote_file_system_client_1

        if not stopped:
            self.engine_1.start()

        # copy all children (files) of A to B
        src = self.local_root_client_1.abspath(self.folder_path_1)
        dst = self.local_root_client_1.abspath(self.folder_path_2)
        for f in os.listdir(src):
            shutil.copy(os.path.join(src, f), dst)
        if stopped:
            self.engine_1.start()
        self.wait_sync(timeout=self.SYNC_TIMEOUT)

        # expect local 'Nuxeo Drive Test Workspace/A' to contain all the files
        abs_folder_path_1 = self.local_root_client_1.abspath(self.folder_path_1)
        assert os.path.exists(abs_folder_path_1)
        children_1 = os.listdir(abs_folder_path_1)
        assert len(children_1) == self.NUMBER_OF_LOCAL_FILES_TOTAL

        local_files_expected = set(self.local_files_list)
        local_files_actual = set(children_1)
        assert local_files_actual == local_files_expected

        # expect local 'Nuxeo Drive Test Workspace/B' to contain also
        # the same files
        abs_folder_path_2 = self.local_root_client_1.abspath(self.folder_path_2)
        assert os.path.exists(abs_folder_path_2)
        children_2 = os.listdir(abs_folder_path_2)
        assert len(children_2) == self.NUMBER_OF_LOCAL_FILES_TOTAL

        local_files_actual = set(children_2)
        assert local_files_actual == local_files_expected

        # expect remote 'Nuxeo Drive Test Workspace/A' to contain all the files
        # just compare the names
        remote_children_1 = [remote_info.name
                             for remote_info in remote.get_children_info(self.remote_ref_1)]
        assert len(remote_children_1) == self.NUMBER_OF_LOCAL_FILES_TOTAL

        remote_files_expected = set(self.local_files_list)
        remote_files_actual = set(remote_children_1)
        assert remote_files_actual == remote_files_expected

        # expect remote 'Nuxeo Drive Test Workspace/B' to contain all the files
        # just compare the names
        remote_children_2 = [remote_info.name
                             for remote_info in remote.get_children_info(self.remote_ref_2)]
        assert len(remote_children_2) == self.NUMBER_OF_LOCAL_FILES_TOTAL

        remote_files_expected = set(self.local_files_list)
        remote_files_actual = set(remote_children_2)
        assert remote_files_actual == remote_files_expected

    def _get_test_resources_path(self):
        try:
            mod_ = sys.modules[self.__module__]
            test_resources_path = os.path.join(os.path.dirname(mod_.__file__),
                                               'resources')
            return test_resources_path
        except:
            pass
