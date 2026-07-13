import logging
import sys

sys.path.insert(0, '../')

from planet_wars import issue_order
from behavior_tree_bot.checks import _available_ships


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

# ------------------------------------------------
# Added: Defensive behavior for threatened planets
# ------------------------------------------------

def defend_threatened_planet(state):
    """
    Reinforce one of our planets when an incoming enemy fleet appears
    strong enough to capture it.

    Return True when a reinforcement order is issued.
    Return False when no reinforcement is needed or possible
    """

    # Check every enemy fleet currently traveling across the map
    for enemy_fleet in state.enemy_fleets():

        # Find the planet that the enemy fleet is traveling toward
        threatened_planet = next(
            (
                planet
                for planet in state.my_planets()
                if planet.ID == enemy_fleet.destination_planet
            ),
            None
        )

        # Ignore enemy fleets that are not targeting one of our planets
        if threatened_planet is None:
            continue

        # Estimate how many ships the threatened planet will have
        # when the enemy fleet arrives
        projected_defenders = (
            int(threatened_planet.num_ships)
            + int(threatened_planet.growth_rate)
            * int(enemy_fleet.turns_remaining)
        )

        # -------------------------------------------------------------
        # Update: Allow function to examine other enemy fleets instead
        # of stopping completely when first planet doesn't need help
        # -------------------------------------------------------------

        # Count ships that we have already sent to reinforce
        # the threatened planet
        incoming_reinforcements = sum(
            int(fleet.num_ships)
            for fleet in state.my_fleets()
            if fleet.destination_planet == threatened_planet.ID
        )

        # Only send the additional ships that are still needed
        ships_needed = (
            int(enemy_fleet.num_ships)
            - projected_defenders
            - incoming_reinforcements
            + 1
        )

        # The planet can already survive without more help
        if ships_needed <= 0:
            continue

        # Look for one of our other planets that can send enough ships
        # and reach the threatened planet before the enemy arrives
        possible_sources = []

        for source in state.my_planets():
            if source.ID == threatened_planet.ID:
                continue

            available_ships = _available_ships(source)
            distance = state.distance(
                source.ID,
                threatened_planet.ID
            )

            if (
                available_ships >= ships_needed
                and distance <= enemy_fleet.turns_remaining
            ):
                possible_sources.append((distance, source))

        # A real threat was found, but none of our planets can respond
        # quickly enough with the required number of ships
        if not possible_sources:
            logging.debug(
                "Unable to defend planet %s: need %s reinforcement ships.",
                threatened_planet.ID,
                ships_needed
            )
            continue

        # Choose the closest planet that can provide reinforcement
        distance, source = min(
            possible_sources,
            key=lambda candidate: candidate[0]
        )

        logging.debug(
            "Defending planet %s from planet %s with %s ships; "
            "enemy arrives in %s turns.",
            threatened_planet.ID,
            source.ID,
            ships_needed,
            enemy_fleet.turns_remaining
        )

        return issue_order(
           state,
           source.ID,
           threatened_planet.ID,
           ships_needed
        )

    # No threatened planet requires a reinforcement order
    return False

# --------------------------------------------------
# Added: Attack an enemy after accounting for growth
# --------------------------------------------------

def attack_capturable_enemy(state):
    """
    Attack an enemy planet that can be captured after accounting
    for its growth during our fleet's travel time.
    """

    for source in state.my_planets():
        available_ships = _available_ships(source)

        for target in state.enemy_planets():

            # Skip targets that already have one of our fleets
            # heading toward them
            already_targeted = any(
                fleet.destination_planet == target.ID
                for fleet in state.my_fleets()
            )

            if already_targeted:
                continue

            distance = state.distance(source.ID, target.ID)

            # Estimate the enemy planet's ship count when we arrive
            projected_enemy_ships = (
                int(target.num_ships)
                + int(target.growth_rate) * distance
            )

            ships_required = projected_enemy_ships + 1

            # Attack the first enemy planet that can be safely captured
            if available_ships >= ships_required:
                logging.debug(
                    "Attacking enemy planet %s from planet %s "
                    "with %s ships.",
                    target.ID,
                    source.ID,
                    ships_required
                )

                return issue_order(
                    state,
                    source.ID,
                    target.ID,
                    ships_required
                )

    logging.debug("No capturable enemy planet was found.")
    return False
