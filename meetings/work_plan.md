# P3 Work Plan: Behavior Trees for Planet Wars

## Assignment Goal

Build a behavior tree bot for Planet Wars that can beat the five
provided test bots while staying within the 1-second-per-turn
time limit.

## Main Files

- `behavior_tree_bot/bt_bot.py`
  - Defines the overall behavior tree strategy.

- `behavior_tree_bot/behaviors.py`
  - Contains action functions that issue orders.

- `behavior_tree_bot/checks.py`
  - Contains condition checks used by the behavior tree.

- `behavior_tree_bot/bt_nodes.py`
  - Contains the behavior tree node classes.

## Required Submission

- `behavior_tree_bot/` folder
- Text file containing the output of `root.tree_to_string()`
- Final ZIP named `Lastname1-Lastname2-P3.zip`

## Proposed Work Split

### Louie
- Review and organize the overall behavior tree in `bt_bot.py`.
- Test the bot against the provided opponent bots.
- Keep meeting notes and document what strategies work.

### Brandon
- Implement helper actions in `behaviors.py`.
- Implement helper checks in `checks.py`.
- Help improve the bot based on failed tests.

## Shared Responsibilities

- Review each other's changes before merging.
- Test against all five bots.
- Make sure the bot stays under 1 second per turn.
- Generate the final behavior tree text file.
- Package the final submission.

## First Meeting Itinerary

1. Confirm that we can access the GitHub repository.
2. Confirm that we can run the starter project.
3. Review the assignment requirements.
4. Decide who will work on which files first.
5. Agree on a Git workflow for commits, pushes, and pull requests.
