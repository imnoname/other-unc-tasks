from ant_colony import AntColony, route_length, validate_route


def test_cycle_and_open_path_use_all_cities():
    distances = [[0, 1, 4], [1, 0, 2], [4, 2, 0]]
    colony = AntColony(distances, ants=8, iterations=5, seed=4)
    cycle = colony.run(closed=True)
    path = colony.run(closed=False)
    assert validate_route(cycle.route, 3)
    assert validate_route(path.route, 3)
    assert cycle.closed and not path.closed
    assert cycle.length > path.length


def test_route_validation_rejects_duplicate_city():
    assert not validate_route([0, 1, 1], 3)


def test_open_route_length_does_not_add_return_edge():
    distances = [[0, 3], [3, 0]]
    assert route_length([0, 1], distances, closed=False) == 3
    assert route_length([0, 1], distances, closed=True) == 6
