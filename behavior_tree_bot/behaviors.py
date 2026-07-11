import sys
sys.path.insert(0, '../')
from planet_wars import issue_order

MINIMUM_GARRISION = 5
SAFETY_MARGIN = 2


def attack_weakest_enemy_planet(state):
    # (1) If we currently have a fleet in flight, abort plan.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)

    # (3) Find the weakest enemy planet.
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)

def spread_to_weakest_neutral_planet(state):
    # (1) If we currently have a fleet in flight, just do nothing.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    # (3) Find the weakest neutral planet.
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)

def _incoming_enemy_ships(state, planet_id):
    """
    Return the total number of enemy ships currently traveling
    toward the given planet.
    """
    return sum(
        fleet.num_ships
        for fleet in state.enemy_fleets()
        if fleet.destination_planet == planet_id
    )

def _incoming_friendly_ships(state, planet_id):
    """
    Return the total number of friendly ships currently traveling
    toward the given planet.
    """
    return sum(
        fleet.num_ships
        for fleet in state.my_fleets()
        if fleet.destination_planet == planet_id
    )

def defend_threatened_planet(state):
    """
    Reinforce the friendly planet with the greatest projected ship deficit.

    Returns True if an order is issued, otherwise False.
    """
    most_threatened = None
    greatest_deficit = 0

    for planet in state.my_planets():
        enemy_incoming = _incoming_enemy_ships(state, planet.ID)

        if enemy_incoming == 0:
            continue

        friendly_incoming = _incoming_friendly_ships(state, planet.ID)

        projected_ships = (
            planet.num_ships
            + friendly_incoming
            - enemy_incoming
        )

        if projected_ships < greatest_deficit:
            greatest_deficit = projected_ships
            most_threatened = planet

    if most_threatened is None:
        return False

    ships_needed = abs(greatest_deficit) + 1

    possible_sources = [
        planet
        for planet in state.my_planets()
        if planet.ID != most_threatened.ID
        and planet.num_ships > ships_needed
    ]

    if not possible_sources:
        return False

    source = min(
        possible_sources,
        key=lambda planet: state.distance(
            planet.ID,
            most_threatened.ID,
        ),
    )

    return issue_order(
        state,
        source.ID,
        most_threatened.ID,
        int(ships_needed),
    )

def capture_best_neutral_planet(state):
    """
    Capture the best available neutral planet.

    Prefers planets with high growth, low ship cost, and short travel distance.
    Returns True if an order is issued, otherwise False.
    """
    best_source = None
    best_target = None
    best_score = None
    ships_to_send = 0

    for source in state.my_planets():
        # Keep at least five ships on the source planet.
        available_ships = int(source.num_ships) - 5

        if available_ships <= 0:
            continue

        for target in state.neutral_planets():
            friendly_incoming = _incoming_friendly_ships(
                state,
                target.ID,
            )

            # Avoid repeatedly targeting a planet that already has
            # enough friendly ships traveling toward it.
            required_ships = (
                int(target.num_ships)
                - int(friendly_incoming)
                + 1
            )

            if required_ships <= 0:
                continue

            if available_ships < required_ships:
                continue

            distance = state.distance(
                source.ID,
                target.ID,
            )

            score = (
                int(target.growth_rate) * 5
                - required_ships
                - distance
            )

            if best_score is None or score > best_score:
                best_score = score
                best_source = source
                best_target = target
                ships_to_send = required_ships

    if best_source is None or best_target is None:
        return False

    return issue_order(
        state,
        best_source.ID,
        best_target.ID,
        int(ships_to_send),
    )

def attack_best_enemy_planet(state):
    """
    Attack the most valuable enemy planet we can capture safely.

    Prefers high-growth, nearby, low-cost enemy planets.
    Returns True if an order is issued, otherwise False.
    """
    best_source = None
    best_target = None
    best_score = None
    ships_to_send = 0

    for source in state.my_planets():
        # Preserve a small defensive garrison.
        available_ships = int(source.num_ships) - 5

        if available_ships <= 0:
            continue

        for target in state.enemy_planets():
            distance = state.distance(source.ID, target.ID)

            friendly_incoming = _incoming_friendly_ships(
                state,
                target.ID,
            )

            enemy_incoming = _incoming_enemy_ships(
                state,
                target.ID,
            )

            projected_strength = (
                int(target.num_ships)
                + int(target.growth_rate) * distance
                + int(enemy_incoming)
                - int(friendly_incoming)
            )

            required_ships = projected_strength + 1

            if required_ships <= 0:
                continue

            if available_ships < required_ships:
                continue

            score = (
                int(target.growth_rate) * 8
                - required_ships
                - distance
            )

            if best_score is None or score > best_score:
                best_score = score
                best_source = source
                best_target = target
                ships_to_send = required_ships

    if best_source is None or best_target is None:
        return False

    return issue_order(
        state,
        best_source.ID,
        best_target.ID,
        int(ships_to_send),
    )

def finish_weak_enemy(state):
    """
    Aggressively finish a weakened opponent.

    Used as a late fallback when the normal attack behavior finds no
    sufficiently valuable target.
    """
    strongest_source = max(
        state.my_planets(),
        key=lambda planet: planet.num_ships,
        default=None,
    )

    weakest_target = min(
        state.enemy_planets(),
        key=lambda planet: planet.num_ships,
        default=None,
    )

    if strongest_source is None or weakest_target is None:
        return False

    available_ships = int(strongest_source.num_ships) - 5

    if available_ships <= 0:
        return False

    distance = state.distance(
        strongest_source.ID,
        weakest_target.ID,
    )

    required_ships = (
        int(weakest_target.num_ships)
        + int(weakest_target.growth_rate) * distance
        + 1
    )

    if available_ships < required_ships:
        return False

    return issue_order(
        state,
        strongest_source.ID,
        weakest_target.ID,
        int(required_ships),
    )
