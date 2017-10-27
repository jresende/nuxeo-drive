# coding: utf-8
"""
NXDRIVE-842: do not sync duplicate conflicted folder content.

STEPS:
    Login DM as User02 account.
    And create another folder "citrus" and inside create a child folder "fruits" folder.
    Upload two files "Lemon.txt" and "Orange.txt"inside the "fruits" folder (/citrus/fruits/).
    Create a folder "fruits" directly under workspace in User02.
    Upload three files "mango.txt" , "cherries.txt" and "papaya.txt" inside the "fruits" folder
    Share the folder citrus/fruits to User01 with permission as Everything.
    And share the folder /fruits to User01 with permission as Everything.
    Login DM as User01.
    Enable synchronization for the folder Citrus/fruits.
    And enable synchronization for the folder /fruits.
    Login Drive as User01.
    Wait for sync completion of "fruits" and "fruits__1" folders.

Actual result:
    All plain text files are synced with only one "fruits" folder.

Expected result:
    Put the "fruits" folder and its content in conflict
"""

from tests.common_unit_test import UnitTestCase


class Test(UnitTestCase):

    def setUp(self):
        super(Test, self).setUp()
        self.engine_1.start()
        self.wait_sync(wait_for_async=True, enforce_errors=False)

    def test_nxdrive_842_rename_dupe_remotely(self):
        local = self.local_root_client_1
        remote = self.remote_document_client_1

        # Make documents in the 1st future root folder
        remote.make_folder('/', 'citrus')
        folder1 = remote.make_folder('/citrus', 'fruits')
        remote.make_file(folder1, 'lemon.txt', content='lemon')
        remote.make_file(folder1, 'orange.txt', content='orange')

        # Make documents in the 2nd future root folder
        folder2 = remote.make_folder('/', 'fruits')
        remote.make_file(folder2, 'cherries.txt', content='cherries')
        remote.make_file(folder2, 'mango.txt', content='mango')
        remote.make_file(folder2, 'papaya.txt', content='papaya')

        # Register new roots
        remote.unregister_as_root(self.workspace)
        remote.register_as_root(folder1)
        remote.register_as_root(folder2)

        # Start and wait
        self.engine_1.start()
        self.wait_sync(wait_for_async=True, enforce_errors=False)

        # Checks
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)

        # Fix the duplicate error
        new_folder = 'fruits-renamed-remotely'
        remote.update(folder1, properties={'dc:title': new_folder})
        self.wait_sync(wait_for_async=True, enforce_errors=False)
        self.assertEqual(len(local.get_children_info('/')), 2)
        self.assertEqual(len(local.get_children_info('/' + new_folder)), 2)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)

    def test_nxdrive_842_rename_remotely(self):
        local = self.local_root_client_1
        remote = self.remote_document_client_1

        # Make documents in the 1st future root folder
        remote.make_folder('/', 'citrus')
        folder1 = remote.make_folder('/citrus', 'fruits')
        remote.make_file(folder1, 'lemon.txt', content='lemon')
        remote.make_file(folder1, 'orange.txt', content='orange')

        # Make documents in the 2nd future root folder
        folder2 = remote.make_folder('/', 'fruits')
        remote.make_file(folder2, 'cherries.txt', content='cherries')
        remote.make_file(folder2, 'mango.txt', content='mango')
        remote.make_file(folder2, 'papaya.txt', content='papaya')

        # Register new roots
        remote.unregister_as_root(self.workspace)
        remote.register_as_root(folder1)
        remote.register_as_root(folder2)

        # Start and wait
        self.engine_1.start()
        self.wait_sync(wait_for_async=True)

        # Checks
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)

        # Fix the duplicate error
        new_folder = 'fruits-renamed-remotely'
        remote.update(folder2, properties={'dc:title': new_folder})
        self.wait_sync(wait_for_async=True)
        self.assertEqual(len(local.get_children_info('/')), 2)
        self.assertEqual(len(local.get_children_info('/' + new_folder)), 3)
        self.assertEqual(len(local.get_children_info('/fruits')), 2)

    def test_nxdrive_842_delete_remotely(self):
        local = self.local_root_client_1
        remote = self.remote_document_client_1

        # Make documents in the 1st future root folder
        remote.make_folder('/', 'citrus')
        folder1 = remote.make_folder('/citrus', 'fruits')
        remote.make_file(folder1, 'lemon.txt', content='lemon')
        remote.make_file(folder1, 'orange.txt', content='orange')

        # Make documents in the 2nd future root folder
        folder2 = remote.make_folder('/', 'fruits')
        remote.make_file(folder2, 'cherries.txt', content='cherries')
        remote.make_file(folder2, 'mango.txt', content='mango')
        remote.make_file(folder2, 'papaya.txt', content='papaya')

        # Register new roots
        remote.unregister_as_root(self.workspace)
        remote.register_as_root(folder1)
        remote.register_as_root(folder2)

        # Start and wait
        self.engine_1.start()
        self.wait_sync(wait_for_async=True)

        # Checks
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)

        # Fix the duplicate error
        remote.delete(folder2)
        self.wait_sync(wait_for_async=True)
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 2)

    def test_nxdrive_842_delete_dupe_remotely(self):
        local = self.local_root_client_1
        remote = self.remote_document_client_1

        # Make documents in the 1st future root folder
        remote.make_folder('/', 'citrus')
        folder1 = remote.make_folder('/citrus', 'fruits')
        remote.make_file(folder1, 'lemon.txt', content='lemon')
        remote.make_file(folder1, 'orange.txt', content='orange')

        # Make documents in the 2nd future root folder
        folder2 = remote.make_folder('/', 'fruits')
        remote.make_file(folder2, 'cherries.txt', content='cherries')
        remote.make_file(folder2, 'mango.txt', content='mango')
        remote.make_file(folder2, 'papaya.txt', content='papaya')

        # Register new roots
        remote.unregister_as_root(self.workspace)
        remote.register_as_root(folder1)
        remote.register_as_root(folder2)

        # Start and wait
        self.engine_1.start()
        self.wait_sync(wait_for_async=True)

        # Checks
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)

        # Fix the duplicate error
        remote.delete(folder1)
        self.wait_sync(wait_for_async=True)
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)
        # TODO Check error count

    def test_nxdrive_842_delete_locally(self):
        local = self.local_root_client_1
        remote = self.remote_document_client_1

        # Make documents in the 1st future root folder
        remote.make_folder('/', 'citrus')
        folder1 = remote.make_folder('/citrus', 'fruits')
        remote.make_file(folder1, 'lemon.txt', content='lemon')
        remote.make_file(folder1, 'orange.txt', content='orange')

        # Make documents in the 2nd future root folder
        folder2 = remote.make_folder('/', 'fruits')
        remote.make_file(folder2, 'cherries.txt', content='cherries')
        remote.make_file(folder2, 'mango.txt', content='mango')
        remote.make_file(folder2, 'papaya.txt', content='papaya')

        # Register new roots
        remote.unregister_as_root(self.workspace)
        remote.register_as_root(folder1)
        remote.register_as_root(folder2)

        # Start and wait
        self.engine_1.start()
        self.wait_sync(wait_for_async=True)

        # Checks
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)

        # Fix the duplicate error
        local.delete('/fruits')
        self.wait_sync(wait_for_async=True)
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertTrue(folder1 in local.get_remote_id('/fruits'))
        self.assertEqual(len(local.get_children_info('/fruits')), 2)

    def test_nxdrive_842_rename_locally(self):
        local = self.local_root_client_1
        remote = self.remote_document_client_1

        # Make documents in the 1st future root folder
        remote.make_folder('/', 'citrus')
        folder1 = remote.make_folder('/citrus', 'fruits')
        remote.make_file(folder1, 'lemon.txt', content='lemon')
        remote.make_file(folder1, 'orange.txt', content='orange')

        # Make documents in the 2nd future root folder
        folder2 = remote.make_folder('/', 'fruits')
        remote.make_file(folder2, 'cherries.txt', content='cherries')
        remote.make_file(folder2, 'mango.txt', content='mango')
        remote.make_file(folder2, 'papaya.txt', content='papaya')

        # Register new roots
        remote.unregister_as_root(self.workspace)
        remote.register_as_root(folder1)
        remote.register_as_root(folder2)

        # Start and wait
        self.engine_1.start()
        self.wait_sync(wait_for_async=True)

        # Checks
        self.assertEqual(len(local.get_children_info('/')), 1)
        self.assertEqual(len(local.get_children_info('/fruits')), 3)

        # Fix the duplicate error
        local.rename('/fruits', 'fruits-renamed')
        self.wait_sync(wait_for_async=True)
        self.assertEqual(len(local.get_children_info('/')), 2)
        self.assertEqual(len(local.get_children_info('/fruits')), 2)
        self.assertEqual(len(local.get_children_info('/fruits-renamed')), 3)
