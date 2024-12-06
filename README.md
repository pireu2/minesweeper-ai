# Minesweeper AI

This project implements a Minesweeper game along with an AI agent that can play the game using logical inference and external tools like Mace4.

## Project Structure

- `minesweeper.py`: Contains the implementation of the Minesweeper game and the AI agent.
- `runner.py`: Runs the game using Pygame and allows interaction with the AI.
- `requirements.txt`: Lists the Python dependencies for the project.
- `assets/`: Contains fonts and images used in the Pygame interface.
- `bin/`: Contains external tools like Mace4 and Prover9 used by the AI.
- `mace4_prompts/`: Stores input files for Mace4.
- `mace4_responses/`: Stores output files from Mace4.

## How to Run

1. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

2. Run the game:
   ```sh
   python runner.py
   ```

## Minesweeper AI

The AI agent uses logical inference to deduce safe cells and mines on the board. It interacts with external tools like Mace4 to make predictions.

### Key Classes and Methods

- `Minesweeper`: Represents the Minesweeper game.

  - `nearby_mines(cell)`: Returns the number of mines around a given cell.
  - `won()`: Checks if all mines have been flagged.

- `MinesweeperAI`: Represents the AI agent.

  - `add_knowledge(cell, count)`: Updates the AI's knowledge base with new information.
  - `make_prediction()`: Uses Mace4 to make a prediction about the board.
  - `mark_mine(cell)`: Marks a cell as a mine.
  - `mark_safe(cell)`: Marks a cell as safe.

- `Sentence`: Represents a logical statement about the game.
  - `known_mines()`: Returns the set of cells known to be mines.
  - `known_safes()`: Returns the set of cells known to be safe.

## External Tools

- **Mace4**: Used by the AI to make logical inferences about the game state.
- **Prover9**: Another tool that can be used for logical reasoning.

## License

This project is licensed under the MIT License.
