from itertools import combinations
import random
import shutil
import subprocess
import os
import re
from datetime import datetime as dt


MACE4_PATH = "bin/mace4"
PROVER9_PATH = "bin/prover9"
DIR_NAME = "mace4_prompts"
DIR_OUTPUT = "mace4_responses"


class Minesweeper:
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):
        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence:
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if len(self.cells) == self.count and self.count != 0:
            return self.cells
        else:
            return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if self.count == 0:
            return self.cells
        else:
            return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI:
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):
        # Set initial height and width
        self.height = height
        self.width = width

        self.step = 0

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

        for filename in os.listdir(DIR_NAME):
            file_path = os.path.join(DIR_NAME, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

        for filename in os.listdir(DIR_OUTPUT):
            file_path = os.path.join(DIR_OUTPUT, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def run_mace4_prompt(self):
        """
        Generates the input file for Mace4, including safe cells, and reflects the current step.
        """
        file_name = f"{DIR_NAME}/mace4_step_{self.step}.in"

        def generate_at_least_disjunctions(cells, count):
            if count == 0:
                # No mines, negate all cells
                return " & ".join([f"-mine({cell[0]},{cell[1]})" for cell in cells])
            disjunctions = []
            for comb in combinations(cells, count):
                clause = [f"mine({cell[0]},{cell[1]})" for cell in comb]
                disjunctions.append(f"({' & '.join(clause)})")
            return " | ".join(disjunctions)

        def generate_at_most_disjunctions(cells, count):
            if count == 0:
                # No mines, negate all cells
                return ".\n".join([f"-mine({cell[0]},{cell[1]})" for cell in cells])
            disjunctions = []
            for comb in combinations(cells, count + 1):
                clause = [f"mine({cell[0]},{cell[1]})" for cell in comb]
                disjunctions.append(f"-({' & '.join(clause)})")
            return ".\n".join(disjunctions)

        with open(file_name, "w") as f:
            f.write(f"% Mace4 input: Minesweeper problem - Step {self.step}\n")
            f.write("formulas(assumptions).\n")
            # Add known safe cells to assumptions
            f.write("% Known safe cells\n")
            for cell in self.safes:
                f.write(f"-mine({cell[0]},{cell[1]}).\n")
            # Add constraints from knowledge
            for sentence in self.knowledge:
                cells = list(sentence.cells)
                if sentence.count == 0:
                    # No mines: negate mines for all cells
                    disjunction = generate_at_least_disjunctions(cells, sentence.count)
                    if disjunction:
                        f.write(disjunction + "\n")
                elif sentence.count == len(cells):
                    # All cells are mines
                    for cell in cells:
                        f.write(f"mine({cell[0]},{cell[1]}).\n")
                else:
                    # General case: at least N mines, at most N mines
                    at_least_disjunction = generate_at_least_disjunctions(
                        cells, sentence.count
                    )
                    at_most_disjunction = generate_at_most_disjunctions(
                        cells, sentence.count
                    )
                    if at_least_disjunction:
                        f.write(f"% At least {sentence.count} mines\n")
                        f.write(at_least_disjunction + ".\n")
                    if at_most_disjunction:
                        f.write(f"% At most {sentence.count} mines\n")
                        f.write(at_most_disjunction + ".\n")

            f.write("end_of_list.\n\n")

            f.write("formulas(goals).\n")

            # Add constraints for goals
            for sentence in self.knowledge:
                cells = list(sentence.cells)
                if sentence.count == 0:
                    # No mines: negate mines for all cells
                    disjunction = generate_at_least_disjunctions(cells, sentence.count)
                    if disjunction:
                        f.write(disjunction + "\n")
                elif sentence.count == len(cells):
                    # All cells are mines
                    for cell in cells:
                        f.write(f"mine({cell[0]},{cell[1]}).\n")
                else:
                    # General case: at least N mines
                    at_least_disjunction = generate_at_least_disjunctions(
                        cells, sentence.count
                    )
                    if at_least_disjunction:
                        f.write(f"% At least {sentence.count} mines\n")
                        f.write(at_least_disjunction + ".\n")

            f.write("end_of_list.\n")

    def run_mace4(self):
        """
        Runs Mace4 on the generated input file
        """
        try:
            result = subprocess.run([MACE4_PATH], capture_output=True, text=True)
        except FileNotFoundError:
            result = subprocess.run(["mace4"], capture_output=True, text=True)


        with open(f"{DIR_OUTPUT}/output_step_{self.step}.out", "w") as f:
            f.write(result.stdout)
        return result.stdout

    def parse_mace4_output(self, output):
        """
        Parses the output from Mace4 and updates the AI's knowledge base.
        """
        for line in output.splitlines():
            if line.startswith("mine("):
                cell = tuple(map(int, line[5:-1].split(",")))
                self.mark_mine(cell)
            elif line.startswith("-mine("):
                cell = tuple(map(int, line[6:-2].split(",")))
                self.mark_safe(cell)

    def make_prediction(self):
        """
        Uses Mace4 to make a prediction about the Minesweeper board.
        """
        self.generate_mace4_input()
        output = self.run_mace4()
        self.parse_mace4_output(output)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        self.moves_made.add(cell)
        self.mark_safe(cell)
        neighbours = set()

        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                if (i, j) == cell or (i, j) in self.safes:
                    continue
                if (i, j) in self.mines:
                    count = count - 1
                    continue

                if 0 <= i < self.height and 0 <= j < self.width:
                    neighbours.add((i, j))

        self.knowledge.append(Sentence(neighbours, count))

        safes = set()
        mines = set()

        for sentence in self.knowledge:
            safes = safes.union(sentence.known_safes())
            mines = mines.union(sentence.known_mines())

        if safes:
            for safe in safes:
                self.mark_safe(safe)
        if mines:
            for mine in mines:
                self.mark_mine(mine)

        for sentence_1 in self.knowledge:
            for sentence_2 in self.knowledge:
                if sentence_1.cells == sentence_2.cells:
                    continue
                if sentence_1.cells.issubset(sentence_2.cells):
                    sentence_2.cells -= sentence_1.cells
                    sentence_2.count -= sentence_1.count

    def parse_mace4_output(self, move):

        # Generate the output Mace4 file
        output_filename = f"{DIR_OUTPUT}/output_step_{self.step}.out"
        with open(output_filename, "w") as f:
            f.write(f"interpretation( 8, [number = {self.step},seconds = {dt.now().second}], [\n")

            # Write the p function
            p_values = [1, 0, 1, 2, 3, 4, 5, 6, 7]
            f.write(f"    function(p(_), {p_values}),\n")

            # Write the s function
            s_values = [1, 2, 3, 4, 5, 6, 7, 8, 7]
            f.write(f"    function(s(_), {s_values}),\n")

            for i in range(self.height):
                for j in range(self.width):
                    if (i, j) in self.safes:
                        f.write(f"function(safe({i},{j}), 1),")
                    elif (i, j) in self.mines:
                        f.write(f"function(mine({i},{j}), 1),")
                    else:
                        f.write(f"function(mine({i},{j}), 0),")

                f.write(f"\n")

            # Write the mine function
            mine_values = []
            for i in range(self.height):
                for j in range(self.width):
                    mine_values.append(1 if (i, j) in self.mines else 0)

    def parse_interpretation_file(file_path):
        with open(file_path, "r") as file:
            content = file.read()

        # Extract the interpretation number, number, and seconds
        interpretation_match = re.search(
            r"interpretation\(\s*(\d+),\s*\[number\s*=\s*(\d+),seconds\s*=\s*(\d+)\]",
            content,
        )
        interpretation_number = int(interpretation_match.group(1))
        number = int(interpretation_match.group(2))
        seconds = int(interpretation_match.group(3))

        # Extract the functions
        functions = re.findall(r"function\(([^)]+)\),\s*(\d+)", content)

        parsed_data = {
            "interpretation_number": interpretation_number,
            "number": number,
            "seconds": seconds,
            "functions": [],
        }

        for func in functions:
            func_name, func_value = func
            parsed_data["functions"].append(
                {"name": func_name, "value": int(func_value)}
            )

        return parsed_data


    def mace4_wrapper(self):
        self.step += 1
        self.run_mace4_prompt()

        safe_moves = self.safes - self.moves_made
        if safe_moves:
            move = random.choice(list(safe_moves))
            self.parse_mace4_output(move)
            return move
        return None

    def mace4_move(self):
        i = 0
        while i < 63:
            rand = (random.randrange(self.height), random.randrange(self.width))
            if rand not in self.moves_made and rand not in self.mines:
                return rand
            i += 1
        return None
