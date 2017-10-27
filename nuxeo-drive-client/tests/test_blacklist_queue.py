# coding: utf-8
import time

from nxdrive.engine.blacklist_queue import BlacklistQueue


def test_delay():
    sleep_time = 3
    # Push two items with a delay of 1s
    queue = BlacklistQueue(delay=1)
    queue.push(1, 'Item1')
    queue.push(2, 'Item2')

    # Verify no item is returned back before 1s
    assert not queue.get()
    time.sleep(sleep_time)

    # Verfiy we get the two items now
    item = queue.get()
    assert item is not None
    assert item.get() == 'Item1'
    assert item.get_id() == 1

    item = queue.get()
    assert item is not None
    assert item.get() == 'Item2'
    assert item.get_id() == 2
    assert item._count == 1

    # Repush item without increasing delay
    queue.repush(item, increase_wait=False)
    assert not queue.get()
    time.sleep(sleep_time)

    # We should get the repushed item after 1s wait
    item = queue.get()
    assert item is not None
    assert item.get() == 'Item2'
    assert item.get_id() == 2
    assert item._count == 2

    # Repush item with increase
    queue.repush(item, increase_wait=True)
    time.sleep(sleep_time)
    assert not queue.get()
    time.sleep(sleep_time)

    item = queue.get()
    assert item is not None
    assert item.get() == 'Item2'
    assert item.get_id() == 2
    assert item._count == 3

    assert not queue.get()
