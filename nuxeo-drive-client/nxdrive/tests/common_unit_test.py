"""Common test utilities"""
import os
import unittest
import tempfile
import hashlib
import shutil
import time

from nxdrive.utils import safe_long_path
from nxdrive.client import RemoteDocumentClient
from nxdrive.client import RemoteFileSystemClient
from nxdrive.manager import Manager
from nxdrive.logging_config import configure
from PyQt4 import QtCore

def configure_logger():
    configure(
        file_level='DEBUG',
        console_level='DEBUG',
        command_name='test',
        log_filename="/tmp/nuxeo-drive-test/log.debug",
    )

# Configure test logger
configure_logger()


class UnitTestCase(unittest.TestCase):

    TEST_WORKSPACE_PATH = (
        u'/default-domain/workspaces/nuxeo-drive-test-workspace')
    FS_ITEM_ID_PREFIX = u'defaultFileSystemItemFactory#default#'

    EMPTY_DIGEST = hashlib.md5().hexdigest()
    SOME_TEXT_CONTENT = b"Some text content."
    SOME_TEXT_DIGEST = hashlib.md5(SOME_TEXT_CONTENT).hexdigest()

    # 1s time resolution as we truncate remote last modification time to the
    # seconds in RemoteFileSystemClient.file_to_info() because of the datetime
    # resolution of some databases (MySQL...)
    REMOTE_MODIFICATION_TIME_RESOLUTION = 1.0

    # 1s time resolution because of the datetime resolution of MYSQL
    AUDIT_CHANGE_FINDER_TIME_RESOLUTION = 1.0

    # 1s resolution on HFS+ on OSX
    # 2s resolution on FAT but can be ignored as no Jenkins is running the test
    # suite under windows on FAT partitions
    # ~0.01s resolution for NTFS
    # 0.001s for EXT4FS
    OS_STAT_MTIME_RESOLUTION = 1.0

    # Nuxeo max length for document name
    DOC_NAME_MAX_LENGTH = 24

    def setUp(self):
        self.app = QtCore.QCoreApplication([])
        # Check the Nuxeo server test environment
        self.nuxeo_url = os.environ.get('NXDRIVE_TEST_NUXEO_URL')
        self.admin_user = os.environ.get('NXDRIVE_TEST_USER')
        self.password = os.environ.get('NXDRIVE_TEST_PASSWORD')

        # Take default parameter if none has been set
        if self.nuxeo_url is None:
            self.nuxeo_url = "http://localhost:8080/nuxeo"
        if self.admin_user is None:
            self.admin_user = "Administrator"
        if self.password is None:
            self.password = "Administrator"

        if None in (self.nuxeo_url, self.admin_user, self.password):
            raise unittest.SkipTest(
                "No integration server configuration found in environment.")

        # Check the local filesystem test environment
        self.local_test_folder_1 = tempfile.mkdtemp(u'-nxdrive-tests-user-1')
        self.local_test_folder_2 = tempfile.mkdtemp(u'-nxdrive-tests-user-2')

        self.local_nxdrive_folder_1 = os.path.join(
            self.local_test_folder_1, u'Nuxeo Drive')
        os.mkdir(self.local_nxdrive_folder_1)
        self.local_nxdrive_folder_2 = os.path.join(
            self.local_test_folder_2, u'Nuxeo Drive')
        os.mkdir(self.local_nxdrive_folder_2)

        self.nxdrive_conf_folder_1 = os.path.join(
            self.local_test_folder_1, u'nuxeo-drive-conf')
        os.mkdir(self.nxdrive_conf_folder_1)

        # Set echo to True to enable SQL statements and transactions logging
        # and echo_pool to True to enable connection pool logging
        from mock import Mock
        options = Mock()
        self.static_drive_home = options.nxdrive_home = "/tmp/nuxeo-drive-test"
        if not os.path.exists(options.nxdrive_home):
            os.mkdir(options.nxdrive_home)
        self.manager = Manager(options)
        self.version = self.manager.get_version()
        # Long timeout for the root client that is responsible for the test
        # environment set: this client is doing the first query on the Nuxeo
        # server and might need to wait for a long time without failing for
        # Nuxeo to finish initialize the repo on the first request after
        # startup
        root_remote_client = RemoteDocumentClient(
            self.nuxeo_url, self.admin_user,
            u'nxdrive-test-administrator-device', self.version,
            password=self.password, base_folder=u'/', timeout=60)

        # Call the Nuxeo operation to setup the integration test environment
        credentials = root_remote_client.execute(
            "NuxeoDrive.SetupIntegrationTests",
            userNames="user_1, user_2", permission='ReadWrite')

        credentials = [c.strip().split(u":") for c in credentials.split(u",")]
        self.user_1, self.password_1 = credentials[0]
        self.user_2, self.password_2 = credentials[1]
        self.engine_1 = self.manager.bind_server(self.local_nxdrive_folder_1, self.nuxeo_url, self.user_1, self.password_1, start_engine=False)
        self.engine_2 = self.manager.bind_server(self.local_nxdrive_folder_2, self.nuxeo_url, self.user_2, self.password_2, start_engine=False)

        self.queue_manager_1 = self.engine_1.get_queue_manager()
        self.queue_manager_2 = self.engine_2.get_queue_manager()

        self.local_client_1 = self.engine_1.get_local_client()
        self.local_client_2 = self.engine_2.get_local_client()

        ws_info = root_remote_client.fetch(self.TEST_WORKSPACE_PATH)
        self.workspace = ws_info[u'uid']
        self.workspace_title = ws_info[u'title']

        # Document client to be used to create remote test documents
        # and folders
        self.upload_tmp_dir = tempfile.mkdtemp(u'-nxdrive-uploads')
        remote_document_client_1 = RemoteDocumentClient(
            self.nuxeo_url, self.user_1, u'nxdrive-test-device-1',
            self.version,
            password=self.password_1, base_folder=self.workspace,
            upload_tmp_dir=self.upload_tmp_dir)

        remote_document_client_2 = RemoteDocumentClient(
            self.nuxeo_url, self.user_2, u'nxdrive-test-device-2',
            self.version,
            password=self.password_2, base_folder=self.workspace,
            upload_tmp_dir=self.upload_tmp_dir)

        # File system client to be used to create remote test documents
        # and folders
        remote_file_system_client_1 = RemoteFileSystemClient(
            self.nuxeo_url, self.user_1, u'nxdrive-test-device-1',
            self.version,
            password=self.password_1, upload_tmp_dir=self.upload_tmp_dir)

        remote_file_system_client_2 = RemoteFileSystemClient(
            self.nuxeo_url, self.user_2, u'nxdrive-test-device-2',
            self.version,
            password=self.password_2, upload_tmp_dir=self.upload_tmp_dir)

        # Register root
        remote_document_client_1.register_as_root(self.workspace)

        self.root_remote_client = root_remote_client
        self.remote_document_client_1 = remote_document_client_1
        self.remote_document_client_2 = remote_document_client_2
        self.remote_file_system_client_1 = remote_file_system_client_1
        self.remote_file_system_client_2 = remote_file_system_client_2

    def tearDown(self):
        # Unbind all
        self.manager.unbind_all()
        # Don't need to revoke tokens for the file system remote clients
        # since they use the same users as the remote document clients
        self.root_remote_client.execute("NuxeoDrive.TearDownIntegrationTests")

        if os.path.exists(self.upload_tmp_dir):
            shutil.rmtree(safe_long_path(self.upload_tmp_dir))

        if os.path.exists(self.local_test_folder_1):
            try:
                shutil.rmtree(safe_long_path(self.local_test_folder_1))
            except:
                pass

        if os.path.exists(self.local_test_folder_2):
            try:
                shutil.rmtree(safe_long_path(self.local_test_folder_2))
            except:
                pass

        if os.path.exists(self.static_drive_home):
            try:
                shutil.rmtree(safe_long_path(self.static_drive_home))
            except:
                pass
        Manager._singleton = None

    def _interact(self, pause=0):
        from time import sleep
        self.app.processEvents()
        if pause > 0:
            sleep(pause)
        while (self.app.hasPendingEvents()):
            self.app.processEvents()

    def make_local_tree(self, root=None, local_client=None):
        if local_client is None:
            local_client = self.local_client_1
        if root is None:
            root = u"/" + self.workspace_title
            if not local_client.exists(root):
                local_client.make_folder(u"/", self.workspace_title)
        # create some folders on the server
        folder_1 = local_client.make_folder(root, u'Folder 1')
        folder_1_1 = local_client.make_folder(folder_1, u'Folder 1.1')
        folder_1_2 = local_client.make_folder(folder_1, u'Folder 1.2')
        folder_2 = local_client.make_folder(root, u'Folder 2')

        # create some files on the server
        local_client.make_file(folder_2, u'Duplicated File.txt',
                                content=b"Some content.")

        local_client.make_file(folder_1, u'File 1.txt', content=b"aaa")
        local_client.make_file(folder_1_1, u'File 2.txt', content=b"bbb")
        local_client.make_file(folder_1_2, u'File 3.txt', content=b"ccc")
        local_client.make_file(folder_2, u'File 4.txt', content=b"ddd")
        local_client.make_file(root, u'File 5.txt', content=b"eee")
        return (6, 5)

    def make_server_tree(self):
        remote_client = self.remote_document_client_1
        # create some folders on the server
        folder_1 = remote_client.make_folder(self.workspace, u'Folder 1')
        folder_1_1 = remote_client.make_folder(folder_1, u'Folder 1.1')
        folder_1_2 = remote_client.make_folder(folder_1, u'Folder 1.2')
        folder_2 = remote_client.make_folder(self.workspace, u'Folder 2')

        # create some files on the server
        remote_client.make_file(folder_2, u'Duplicated File.txt',
                                content=b"Some content.")
        remote_client.make_file(folder_2, u'Duplicated File.txt',
                                content=b"Other content.")

        remote_client.make_file(folder_1, u'File 1.txt', content=b"aaa")
        remote_client.make_file(folder_1_1, u'File 2.txt', content=b"bbb")
        remote_client.make_file(folder_1_2, u'File 3.txt', content=b"ccc")
        remote_client.make_file(folder_2, u'File 4.txt', content=b"ddd")
        remote_client.make_file(self.workspace, u'File 5.txt', content=b"eee")
        return (7, 4)

    def get_full_queue(self, queue, dao=None):
        if dao is None:
            dao = self.engine_1.get_dao()
        result = []
        while (len(queue) > 0):
            result.append(dao.get_state_from_id(queue.pop().id))
        return result

    def wait(self):
        self.root_remote_client.wait()

    def wait_audit_change_finder_if_needed(self):
        if not self.root_remote_client.is_event_log_id_available():
            time.sleep(self.AUDIT_CHANGE_FINDER_TIME_RESOLUTION)