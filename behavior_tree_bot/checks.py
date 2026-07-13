import logging

def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())

# --------------------------------------------------------
# Update: Check whether an incoming fleet is a real threat
# --------------------------------------------------------
def threatened_planet_exists(state):
    """
    Return True if an enemy fleet is likely to capture one
    of our planets
    """

    # Store our planets by ID so we can quickly find the target
    # of each enemy fleet
    my_planets = {
        planet.ID: planet
        for planet in state.my_planets()
    }

    for enemy_fleet in state.enemy_fleets():
        target = my_planets.get(enemy_fleet.destination_planet)

        # Ignore fleets that are not heading toward one of our planets
        if target is None:
            continue

        # Estimate how many ships the planet will have when the
        # enemy fleet arrives
        projected_defenders = (
            int(target.num_ships)
            + int(target.growth_rate)
            * int(enemy_fleet.turns_remaining)
        )

        # Count any reinforcement ships that we already have
        # traveling toward this planet
        incoming_reinforcements = sum(
            int(fleet.num_ships)
            for fleet in state.my_fleets()
            if fleet.destination_planet == target.ID
        )


        total_defenders = (
            projected_defenders + incoming_reinforcements
        )

        # Only treat the planet as threatened if the enemy fleet
        # is stronger than the projected defense
        if int(enemy_fleet.num_ships) > total_defenders:
            logging.debug(
                "Planet %s is threatened: enemy=%s defenders=%s",
                target.ID,
                enemy_fleet.num_ships,
                total_defenders
            )
            return True

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
