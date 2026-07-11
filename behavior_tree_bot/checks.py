import logging

def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())

def threatened_planet_exists(state):
    """
    Return True if an enemy fleet is traveling toward one of our planets
    """
    my_planet_ids = {planet.ID for planet in state.my_planets()}

    threatened = any(
      fleet.destination_planet in my_planet_ids
      for fleet in state.enemy_fleets()
    )

    logging.debug("Threatened planet exists: %s", threatened)
    return threatened

def good_neutral_target_exists(state):
    """
    Return True if one of our planets can capture at least one neutral planet
    while keeping a small reserve.
    """
    for source in state.my_planets():
        available_ships = _available_ships(source)

        for target in state.neutral_planets():
            ships_required = int(target.num_ships) + 1

            if available_ships >= ships_required:
                return True

    return False


def attackable_enemy_exists(state):
    """
    Return True if one of our planets can capture an enemy planet after
    accounting for enemy growth during travel.
    """
    for source in state.my_planets():
        available_ships = _available_ships(source)

        for target in state.enemy_planets():
            distance = state.distance(source.ID, target.ID)

            projected_enemy_ships = (
                int(target.num_ships)
                + int(target.growth_rate) * distance
            )

            ships_required = projected_enemy_ships + 1

            if available_ships >= ships_required:
                return True

    return False


def _available_ships(planet):
    """
    Helper used by checks to preserve part of a planet's garrison.
    """
    ships = int(planet.num_ships)
    reserve = max(5, int(ships * 0.25))

    return max(0, ships - reserve)
