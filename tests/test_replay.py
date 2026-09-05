from backend.security.replay import ReplayGuard


def test_replay_guard_rejects_duplicates():
    guard = ReplayGuard(db_path=':memory:')
    assert guard.is_duplicate('veh_1', 'msg-1', 7) is False
    guard.mark_processed('veh_1', 'msg-1', 7)
    assert guard.is_duplicate('veh_1', 'msg-1', 7) is True


def test_replay_guard_handles_new_vehicle():
    guard = ReplayGuard(db_path=':memory:')
    assert guard.is_duplicate('veh_2', 'msg-2', 2) is False
