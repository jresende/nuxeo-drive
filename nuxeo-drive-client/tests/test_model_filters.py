# coding: utf-8
from tests.common_unit_test import UnitTestCase


class TestModelFilter(UnitTestCase):

    def testSimpleFilter(self):
        dao = self.engine_1.get_dao()
        self.engine_1.add_filter("/Test/Plop")
        assert len(dao.get_filters()) == 1

        # On purpose to verify that filter not messup if starts with the
        # same value
        self.engine_1.add_filter("/Test/Plop2")
        assert len(dao.get_filters()) == 2

        self.engine_1.add_filter("/Test/Plop2/SubFolder")
        assert len(dao.get_filters()) == 2

        self.engine_1.remove_filter("/Test/Plop2/SubFor")
        assert len(dao.get_filters()) == 2

        self.engine_1.add_filter("/Test")
        assert len(dao.get_filters()) == 1

        self.engine_1.remove_filter("/Test")
        assert not dao.get_filters()

        self.engine_1.add_filter("/Test/Plop")
        self.engine_1.add_filter("/Test/Plop2")
        self.engine_1.add_filter("/Test2/Plop")
        self.engine_1.remove_filter("/Test")
        assert len(dao.get_filters()) == 1
