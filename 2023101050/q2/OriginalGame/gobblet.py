# pylint: disable=no-member
# pylint: disable=too-many-branches
"""
Gobblet Board Game Implementation.

A strategic board game where players place and move pieces of different sizes
on a 3x3 grid, with the goal of creating a line of their colored pieces.
"""
import sys
from enum import Enum, auto
import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
BOARD_SIZE = 3
SQUARE_SIZE = 140
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE * SQUARE_SIZE) // 2
BOARD_OFFSET_Y = (SCREEN_HEIGHT - BOARD_SIZE * SQUARE_SIZE) // 2
PIECE_SIZES = [20, 40, 60]
RESERVE_OFFSET_X = 100
RESERVE_OFFSET_Y = 150
RESERVE_SLOT_HEIGHT = 150  # Height for each piece slot
RESERVE_SLOT_WIDTH = 150 # Width for each piece slot

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
RED_TRANSPARENT = (255, 0, 0, 128)
BLUE_TRANSPARENT = (0, 0, 255, 128)
HIGHLIGHT = (255, 255, 0, 150)
BACKGROUND = (240, 240, 220)
LINE_COLOR = (50, 50, 50)
SLOT_COLOR = (230, 230, 230)
SLOT_BORDER = (180, 180, 180)

# Game States
class GameState(Enum):
    """Represents the possible states of the Gobblet game."""
    PLAYER_RED = auto()
    PLAYER_BLUE = auto()
    RED_WIN = auto()
    BLUE_WIN = auto()
    DRAW = auto()

class Piece:
    """Represents a single game piece with color and size attributes."""
    def __init__(self, color, size):
        """
        Initialize a game piece.

        Args:
            color (tuple): RGB color of the piece
            size (int): Size of the piece (0=small, 1=medium, 2=large)
        """
        self.color = color  # RED or BLUE
        self.size = size  # 0 (small), 1 (medium), 2 (large)
        self.selected = False
        self.position = None  # (x, y) on board or None if in reserve

    def is_larger_than(self, other_piece):
        """
        Check if this piece is larger than another piece.

        Args:
            other_piece (Piece): Piece to compare against

        Returns:
            bool: True if this piece is larger, False otherwise
        """
        return other_piece is None or self.size > other_piece.size

    def draw(self, screen, x, y, transparent=False):
        """
        Draw the piece on the screen at the specified position.

        Args:
            screen: Pygame screen to draw on
            x (int): X-coordinate for the center of the piece
            y (int): Y-coordinate for the center of the piece
            transparent (bool): Whether to draw the piece with transparency
        """

        color = self.color
        if transparent:
            if self.color == RED:
                color = RED_TRANSPARENT
            else:
                color = BLUE_TRANSPARENT

        pygame.draw.circle(screen, color, (x, y), PIECE_SIZES[self.size])
        pygame.draw.circle(screen, BLACK, (x, y), PIECE_SIZES[self.size], 2)

        # Draw a small black circle in the middle for visual distinction
        if self.size > 0:  # For medium and large pieces
            pygame.draw.circle(screen, BLACK, (x, y), 5)

class GobbletJr:
    """
    Main game class for the Gobblet Jr. board game.

    Manages game state, board, pieces, and interactions.
    """
    def __init__(self):
        """Initialize the game with default settings and UI elements."""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gobblet Jr.")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)

        # Size labels for the pieces
        self.size_labels = ["S", "M", "L"]
        self.selected_piece = None
        self.valid_moves = []
        self.last_move = None
        self.current_state = GameState.PLAYER_RED
        self.reset_game()

    def reset_game(self):
        """Reset the game to its initial state."""

        # Initialize game state
        self.current_state = GameState.PLAYER_RED

        # Initialize board (3x3 grid of stacks)
        self.board = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        # Initialize pieces: 2 of each size (0=small, 1=medium, 2=large) for each player
        # Create in order large to small for better organization
        self.red_reserve = [Piece(RED, 2), Piece(RED, 2), Piece(RED, 1),
                             Piece(RED, 1), Piece(RED, 0), Piece(RED, 0)]
        self.blue_reserve = [Piece(BLUE, 2), Piece(BLUE, 2), Piece(BLUE, 1),
                             Piece(BLUE, 1), Piece(BLUE, 0), Piece(BLUE, 0)]

        self.selected_piece = None
        self.valid_moves = []
        self.last_move = None

    def get_top_piece(self, row, col):
        """
        Get the top piece at the specified board position.

        Args:
            row (int): Row index
            col (int): Column index

        Returns:
            Piece or None: The top piece if one exists, otherwise None
        """
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col]:
            return self.board[row][col][-1]
        return None

    def select_piece(self, piece):
        """
        Select a piece and calculate its valid moves.

        Args:
            piece (Piece): The piece to select
        """
        # Deselect previously selected piece
        if self.selected_piece:
            self.selected_piece.selected = False

        # Select new piece
        piece.selected = True
        self.selected_piece = piece

        # Calculate valid moves
        self.valid_moves = self.get_valid_moves(piece)

    def get_valid_moves(self, piece):
        """
        Calculate all valid board positions for the selected piece.

        Args:
            piece (Piece): The piece to find valid moves for

        Returns:
            list: List of (row, col) tuples representing valid moves
        """
        valid_moves = []
        # current_player_color = RED if self.current_state == GameState.PLAYER_RED else BLUE

        # If the piece is in reserve, it can be placed on any valid square
        if piece.position is None:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    top_piece = self.get_top_piece(row, col)
                    # Can place on empty square or on smaller pieces
                    if top_piece is None or piece.is_larger_than(top_piece):
                        # Check if this move would reveal a winning line for the opponent
                        if not self.would_reveal_win_for_opponent(piece, None, row, col):
                            valid_moves.append((row, col))
        else:
            # If piece is on the board, it can be moved to any valid square
            current_row, current_col = piece.position

            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    # Can't move to the same position
                    if (row, col) == (current_row, current_col):
                        continue

                    top_piece = self.get_top_piece(row, col)
                    # Can place on empty square or on smaller pieces
                    if top_piece is None or piece.is_larger_than(top_piece):
                        # Check if this move would reveal a winning line for the opponent
                        if not self.would_reveal_win_for_opponent(piece, piece.position, row, col):
                            valid_moves.append((row, col))

        return valid_moves
     # pylint: disable=unused-argument
    def would_reveal_win_for_opponent(self, piece, from_pos, to_row, to_col):
        """
        Check if moving a piece would reveal a winning line for the opponent.

        Args:
            piece (Piece): The piece being moved
            from_pos (tuple): Current position (row, col) or None if from reserve
            to_row (int): Destination row (not used in current implementation)
            to_col (int): Destination column (not used in current implementation)

        Returns:
            bool: True if the move would reveal a win for the opponent
        """
        # Create a copy of the board to simulate the move
        temp_board = [[stack.copy() for stack in row] for row in self.board]
        to_col=3
        to_row=1
        # Remove the piece from its current position if it's on the board
        if from_pos:
            from_row, from_col = from_pos
            if temp_board[from_row][from_col] and temp_board[from_row][from_col][-1] == piece:
                temp_board[from_row][from_col].pop()

        # Check if removing the piece reveals a win for the opponent
        opponent_color = BLUE if piece.color == RED else RED

        # Check rows
        for row in range(BOARD_SIZE):
            count = 0
            for col in range(BOARD_SIZE):
                top_piece = None
                if temp_board[row][col]:
                    top_piece = temp_board[row][col][-1]
                if top_piece and top_piece.color == opponent_color:
                    count += 1
                else:
                    break
            if count == BOARD_SIZE:
                return True

        # Check columns
        for col in range(BOARD_SIZE):
            count = 0
            for row in range(BOARD_SIZE):
                top_piece = None
                if temp_board[row][col]:
                    top_piece = temp_board[row][col][-1]
                if top_piece and top_piece.color == opponent_color:
                    count += 1
                else:
                    break
            if count == BOARD_SIZE:
                return True

        # Check diagonals
        count = 0
        for i in range(BOARD_SIZE):
            top_piece = None
            if temp_board[i][i]:
                top_piece = temp_board[i][i][-1]
            if top_piece and top_piece.color == opponent_color:
                count += 1
            else:
                break
        if count == BOARD_SIZE:
            return True

        count = 0
        for i in range(BOARD_SIZE):
            top_piece = None
            if temp_board[i][BOARD_SIZE - 1 - i]:
                top_piece = temp_board[i][BOARD_SIZE - 1 - i][-1]
            if top_piece and top_piece.color == opponent_color:
                count += 1
            else:
                break
        if count == BOARD_SIZE:
            return True

        return False

    def make_move(self, row, col):
        """
        Make a move with the selected piece to the specified position.

        Args:
            row (int): Destination row
            col (int): Destination column

        Returns:
            bool: True if the move was successful, False otherwise
        """
        if not self.selected_piece or (row, col) not in self.valid_moves:
            return False

        # If piece is coming from the board, remove it from its current position
        if self.selected_piece.position:
            from_row, from_col = self.selected_piece.position
            self.board[from_row][from_col].pop()
        else:
            # If piece is coming from reserve, remove it from reserve
            reserves = self.red_reserve if self.selected_piece.color == RED else self.blue_reserve
            reserves.remove(self.selected_piece)

        # Add piece to the new position
        self.board[row][col].append(self.selected_piece)
        self.selected_piece.position = (row, col)

        # Record the last move
        self.last_move = (row, col)

        # Deselect the piece and clear valid moves
        self.selected_piece.selected = False
        self.selected_piece = None
        self.valid_moves = []

        # Check for win conditions
        if self.check_win(RED):
            self.current_state = GameState.RED_WIN
        elif self.check_win(BLUE):
            self.current_state = GameState.BLUE_WIN
        elif self.check_draw():
            self.current_state = GameState.DRAW
        else:
            # Switch players
            if self.current_state == GameState.PLAYER_RED :
                self.current_state = GameState.PLAYER_BLUE
            else:
                self.current_state = GameState.PLAYER_RED




        return True

    def check_win(self, color):
        """
        Check if the specified color has won the game.

        Args:
            color: The color to check for a win

        Returns:
            bool: True if the color has a winning line, False otherwise
        """
        # Check rows
        for row in range(BOARD_SIZE):
            if all(self.get_top_piece(row, col) and
                   self.get_top_piece(row, col).color == color for col in range(BOARD_SIZE)):
                return True

        # Check columns
        for col in range(BOARD_SIZE):
            if all(self.get_top_piece(row, col) and
                   self.get_top_piece(row, col).color == color for row in range(BOARD_SIZE)):
                return True

        # Check diagonals
        if all(self.get_top_piece(i, i) and
                self.get_top_piece(i, i).color == color for i in range(BOARD_SIZE)):
            return True

        if all(self.get_top_piece(i, BOARD_SIZE - 1 - i) and
               self.get_top_piece(i, BOARD_SIZE - 1 - i).color == color
               for i in range(BOARD_SIZE)):
            return True

        return False

    def check_draw(self):
        """
        Check if the game is a draw (all spaces filled).

        Returns:
            bool: True if the game is a draw, False otherwise
        """
        # Check if all spaces are filled
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if not self.get_top_piece(row, col):
                    return False
        return True

    def handle_events(self):
        """Handle pygame events (quit, key presses, mouse clicks)."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    self.handle_click(mouse_pos)

    #pylint: disable=too-many-locals
    def handle_click(self, mouse_pos):
        """
        Handle mouse click events based on current game state.

        Args:
            mouse_pos (tuple): (x, y) position of the mouse click
        """
        # If game is over, only allow reset
        if self.current_state in [GameState.RED_WIN, GameState.BLUE_WIN, GameState.DRAW]:
            return

        current_player_color = RED if self.current_state == GameState.PLAYER_RED else BLUE
        reserves = self.red_reserve if current_player_color == RED else self.blue_reserve

        # Check if a reserve piece was clicked
        reserve_clicked = False

        # Restructured the nested loops to reduce nesting levels
        # Check red reserve slots
        if current_player_color == RED:
            for i, size in enumerate([2, 1, 0]):  # Large, Medium, Small
                slot_x = RESERVE_OFFSET_X
                slot_y = RESERVE_OFFSET_Y + i * RESERVE_SLOT_HEIGHT
                slot_width = RESERVE_SLOT_WIDTH
                slot_height = RESERVE_SLOT_HEIGHT

                # Check if click is within this slot
                if (slot_x <= mouse_pos[0] <= slot_x + slot_width and
                    slot_y <= mouse_pos[1] <= slot_y + slot_height):
                    # Find if there's a piece of this size in reserve
                    for piece in reserves:
                        if piece.size == size:
                            self.select_piece(piece)
                            reserve_clicked = True
                            break
                    if reserve_clicked:
                        break

        # Check blue reserve slots
        elif current_player_color == BLUE:
            for i, size in enumerate([2, 1, 0]):  # Large, Medium, Small
                slot_x = SCREEN_WIDTH - RESERVE_OFFSET_X - RESERVE_SLOT_WIDTH
                slot_y = RESERVE_OFFSET_Y + i * RESERVE_SLOT_HEIGHT
                slot_width = RESERVE_SLOT_WIDTH
                slot_height = RESERVE_SLOT_HEIGHT

                # Check if click is within this slot
                if (slot_x <= mouse_pos[0] <= slot_x + slot_width and
                    slot_y <= mouse_pos[1] <= slot_y + slot_height):
                    # Find if there's a piece of this size in reserve
                    for piece in reserves:
                        if piece.size == size:
                            self.select_piece(piece)
                            reserve_clicked = True
                            break
                    if reserve_clicked:
                        break

        if not reserve_clicked:
            # Check if a board piece was clicked
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    # Check if the click is within this square
                    if (BOARD_OFFSET_X + col * SQUARE_SIZE <= mouse_pos[0] <=
                        BOARD_OFFSET_X + (col + 1) * SQUARE_SIZE and
                        BOARD_OFFSET_Y + row * SQUARE_SIZE <= mouse_pos[1] <=
                        BOARD_OFFSET_Y + (row + 1) * SQUARE_SIZE):

                        # If a piece is already selected, try to make a move
                        if self.selected_piece:
                            self.make_move(row, col)
                            break

                        # Otherwise, try to select a piece on the board
                        piece = self.get_top_piece(row, col)
                        if piece and piece.color == current_player_color:
                            self.select_piece(piece)
                            break

    def draw_board(self):
        """Draw the game board, pieces, and UI elements."""
        # Define text_color here to avoid potential "used before assignment" error
        text_color = BLACK

        # Fill the background
        self.screen.fill(BACKGROUND)

        # Draw the board
        pygame.draw.rect(self.screen, WHITE,
                         (BOARD_OFFSET_X, BOARD_OFFSET_Y,
                          BOARD_SIZE * SQUARE_SIZE, BOARD_SIZE * SQUARE_SIZE))

        # Draw grid lines
        for i in range(BOARD_SIZE + 1):
            # Horizontal lines
            pygame.draw.line(self.screen, LINE_COLOR,
                            (BOARD_OFFSET_X, BOARD_OFFSET_Y + i * SQUARE_SIZE),
                            (BOARD_OFFSET_X + BOARD_SIZE * SQUARE_SIZE,
                             BOARD_OFFSET_Y + i * SQUARE_SIZE),
                            2)
            # Vertical lines
            pygame.draw.line(self.screen, LINE_COLOR,
                            (BOARD_OFFSET_X + i * SQUARE_SIZE, BOARD_OFFSET_Y),
                            (BOARD_OFFSET_X + i * SQUARE_SIZE,
                             BOARD_OFFSET_Y + BOARD_SIZE * SQUARE_SIZE),
                            2)

        # Highlight the last move
        if self.last_move:
            row, col = self.last_move
            pygame.draw.rect(self.screen, GREY,
                            (BOARD_OFFSET_X + col * SQUARE_SIZE,
                             BOARD_OFFSET_Y + row * SQUARE_SIZE,
                             SQUARE_SIZE, SQUARE_SIZE))

        # Highlight valid moves for selected piece
        if self.selected_piece:
            for row, col in self.valid_moves:
                pygame.draw.rect(self.screen, HIGHLIGHT,
                                (BOARD_OFFSET_X + col * SQUARE_SIZE,
                                 BOARD_OFFSET_Y + row * SQUARE_SIZE,
                                 SQUARE_SIZE, SQUARE_SIZE))

        # Draw pieces on the board
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                square_center_x = BOARD_OFFSET_X + col * SQUARE_SIZE + SQUARE_SIZE // 2
                square_center_y = BOARD_OFFSET_Y + row * SQUARE_SIZE + SQUARE_SIZE // 2

                if self.board[row][col]:
                    self.board[row][col][-1].draw(self.screen, square_center_x, square_center_y)

        # Draw player labels for reserve areas
        red_label = self.font.render("RED PIECES", True, RED)
        blue_label = self.font.render("BLUE PIECES", True, BLUE)
        self.screen.blit(red_label, (RESERVE_OFFSET_X, RESERVE_OFFSET_Y - 50))
        self.screen.blit(blue_label, (SCREEN_WIDTH - RESERVE_OFFSET_X
                                      - blue_label.get_width(), RESERVE_OFFSET_Y - 50))

        # Draw reserve areas with vertical slots
        self._draw_reserve_area(RED)
        self._draw_reserve_area(BLUE)

        # Draw current player and game status
        status_text = ""
        if self.current_state == GameState.PLAYER_RED:
            status_text = "Red's Turn"
            text_color = RED
        elif self.current_state == GameState.PLAYER_BLUE:
            status_text = "Blue's Turn"
            text_color = BLUE
        elif self.current_state == GameState.RED_WIN:
            status_text = "Red Wins!"
            text_color = RED
        elif self.current_state == GameState.BLUE_WIN:
            status_text = "Blue Wins!"
            text_color = BLUE
        elif self.current_state == GameState.DRAW:
            status_text = "Draw!"
            text_color = BLACK

        status_surface = self.font.render(status_text, True, text_color)
        self.screen.blit(status_surface, (SCREEN_WIDTH // 2 - status_surface.get_width() // 2, 30))

        # Draw instructions
        instructions = "Click on a piece slot to select, then click on a valid square to move"
        instructions_surface = self.small_font.render(instructions, True, BLACK)
        self.screen.blit(instructions_surface,
                         (SCREEN_WIDTH // 2 - instructions_surface.get_width() // 2, 70))

        reset_text = "Press 'R' to reset the game"
        reset_surface = self.small_font.render(reset_text, True, BLACK)
        self.screen.blit(reset_surface,
                         (SCREEN_WIDTH // 2 - reset_surface.get_width() // 2, SCREEN_HEIGHT - 30))

        # Draw selected piece with mouse if one is selected
        if self.selected_piece:
            mouse_pos = pygame.mouse.get_pos()
            self.selected_piece.draw(self.screen, mouse_pos[0], mouse_pos[1], transparent=True)

    def _draw_reserve_area(self, color):
        """
        Draw reserve area for the specified color.

        Args:
            color: RED or BLUE color to draw the reserve for
        """
        reserves = self.red_reserve if color == RED else self.blue_reserve

        # Position differs based on player color
        is_red = color == RED
        if is_red:
            base_x=RESERVE_OFFSET_X
        else:
            base_x=SCREEN_WIDTH - RESERVE_OFFSET_X - RESERVE_SLOT_WIDTH

        # Draw slots for each size (L, M, S)
        for i, size in enumerate([2, 1, 0]):
            # Draw slot
            slot_x = base_x
            slot_y = RESERVE_OFFSET_Y + i * RESERVE_SLOT_HEIGHT
            pygame.draw.rect(self.screen, SLOT_COLOR,
                            (slot_x, slot_y, RESERVE_SLOT_WIDTH, RESERVE_SLOT_HEIGHT))
            pygame.draw.rect(self.screen, SLOT_BORDER,
                            (slot_x, slot_y, RESERVE_SLOT_WIDTH, RESERVE_SLOT_HEIGHT), 2)

            # Draw size label
            size_label = self.small_font.render(self.size_labels[size], True, BLACK)
            self.screen.blit(size_label, (slot_x + 10, slot_y + 5))

            # Draw counter for how many pieces of this size are in reserve
            count = sum(1 for piece in reserves if piece.size == size)
            count_label = self.small_font.render(f"x{count}", True, color)
            self.screen.blit(count_label, (slot_x + RESERVE_SLOT_WIDTH - 30, slot_y + 5))

            # Draw the pieces in this slot
            for piece in reserves:
                if piece.size == size:
                    piece_x = slot_x + RESERVE_SLOT_WIDTH // 2
                    piece_y = slot_y + RESERVE_SLOT_HEIGHT // 2
                    piece.draw(self.screen, piece_x, piece_y)
                    break  # Just draw one piece per slot as representative

    def run(self):
        """Run the main game loop."""
        while True:
            self.handle_events()
            self.draw_board()
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = GobbletJr()
    game.run()
