import pygame, random, math
import os
import faulthandler
faulthandler.enable()

# Dimension Definitions
SCREEN_WIDTH, SCREEN_HEIGHT = (1500, 1000)
PLATFORM_WIDTH, PLATFORM_HEIGHT = (2500, 2500)

# Other Definitions
NAME = "agar.io"
VERSION = "0.2"

# Declare global variables
MAIN_SURFACE = None
clock = None
font = None
big_font = None
SCOREBOARD_SURFACE = None
LEADERBOARD_SURFACE = None

RENDER_MODE = None

def initialize_pygame(render_mode):
    """Initializes Pygame if the render_mode is set to human."""
    global MAIN_SURFACE, clock, font, big_font, SCOREBOARD_SURFACE, LEADERBOARD_SURFACE

    if render_mode == "human":
        # Initialize Pygame with full display capabilities
        pygame.init()
        pygame.display.set_caption("{} - v{}".format(NAME, VERSION))
        clock = pygame.time.Clock()

        font_path = os.path.join(os.getcwd(), "Ubuntu-B.ttf")
        # Try to load the fonts, and handle the error if the file is not found
        try:
            font = pygame.font.Font(font_path, 20)
            big_font = pygame.font.Font(font_path, 24)
        except FileNotFoundError:
            print("Font file not found: Ubuntu-B.ttf, using default system font.")
            font = pygame.font.SysFont(None, 20, True)  # Use a common system font
            big_font = pygame.font.SysFont(None, 24, True)

        # Define the main display surface
        try:
            MAIN_SURFACE = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e:
            print(f"Failed to set display mode: {e}")
            return False

        # Create additional surfaces for the scoreboard and leaderboard
        SCOREBOARD_SURFACE = pygame.Surface((95, 25), pygame.SRCALPHA)
        LEADERBOARD_SURFACE = pygame.Surface((155, 278), pygame.SRCALPHA)

        # Fill the surfaces with initial colors
        SCOREBOARD_SURFACE.fill((50, 50, 50, 80))
        LEADERBOARD_SURFACE.fill((50, 50, 50, 80))

        print("Pygame initialized successfully with human render mode.")
        return MAIN_SURFACE
    else:
        # Initialize only essential components of Pygame
        font_path = os.path.join(os.getcwd(), "Ubuntu-B.ttf")
        # Try to load the fonts, and handle the error if the file is not found
        try:
            font = pygame.font.Font(font_path, 20)
            big_font = pygame.font.Font(font_path, 24)
        except FileNotFoundError:
            print("Font file not found: Ubuntu-B.ttf, using default system font.")
            font = pygame.font.SysFont(None, 20, True)  # Use a common system font
            big_font = pygame.font.SysFont(None, 24, True)

        print("Pygame initialized without display (render_mode is not 'human').")
        return True

# Auxiliary Functions
def drawText(message, pos, color=(255, 255, 255)):
    """Blits text to main (global) screen if MAIN_SURFACE is initialized and render_mode is not None."""
    if MAIN_SURFACE is not None and font is not None:
        # Draw text only if MAIN_SURFACE is initialized properly
        pos = (int(pos[0]), int(pos[1]))
        MAIN_SURFACE.blit(font.render(message, True, color), pos)
    else:
        # Skip drawing in headless mode (render_mode=None)
        print("Skipping text rendering in headless mode.")

def getDistance(a, b):
    """Calculate the distance between two points."""
    diffX = abs(a[0] - b[0])
    diffY = abs(a[1] - b[1])
    return ((diffX ** 2) + (diffY ** 2)) ** 0.5


class Painter:
    """Organizes the drawing/update process using the Strategy Pattern.
    Objects are drawn in FIFO order: the first objects added are drawn first.
    """

    def __init__(self, game_state):
        self.paintings = []
        self.game_state = game_state

    def add(self, drawable):
        """Adds a drawable object to the list."""
        self.paintings.append(drawable)

    def remove(self, drawable):
        """Removes a drawable object from the list."""
        if drawable in self.paintings:
            self.paintings.remove(drawable)

    def paint(self):
        """Draws all objects in the list."""
        if MAIN_SURFACE is None:
            print("MAIN_SURFACE is None. Cannot paint.")  # Debug
            return
        
        for drawing in self.paintings:
            # Check if 'draw' method exists and is callable
            if callable(getattr(drawing, 'draw', None)):
                try:
                    drawing.draw(self.game_state.blob)  # Pass the main player 'blob'
                except TypeError:
                    drawing.draw()  # No extra argument needed


class Camera:
    """Represents the concept of POV (Point of View)."""
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.zoom = 0.5
        self.global_view = False  # Parameter for global view

    def centre(self, blobOrPos):
        """Center the view on the given object or position, considering the zoom."""
        if isinstance(blobOrPos, Player):
            x, y = blobOrPos.x, blobOrPos.y
            self.x = (x - (x * self.zoom)) - x + (SCREEN_WIDTH / 2)
            self.y = (y - (y * self.zoom)) - y + (SCREEN_HEIGHT / 2)
        elif type(blobOrPos) == tuple:
            self.x, self.y = blobOrPos

    def update(self, target):
        """Update the camera position and zoom based on the target object."""
        if self.global_view:
            # Calculate the zoom to see the entire platform width
            self.zoom = min(SCREEN_WIDTH / PLATFORM_WIDTH, SCREEN_HEIGHT / PLATFORM_HEIGHT)
            self.x, self.y = 0, 0  # Center vertically on the platform
        else:
            # Classic view: follow the player
            self.zoom = 100 / (target.mass) + 0.3
            self.centre(target)

    def toggle_global_view(self):
        """Toggle between global view and player-follow view."""
        self.global_view = not self.global_view
        print(f"Global view toggled to {self.global_view}")  # Debug





class Drawable:
    """Base class for any drawable element in the game."""
    
    def __init__(self, surface, camera):
        # Ensure that the surface is not None; otherwise, create a dummy surface.
        self.surface = surface if surface else pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.camera = camera

    def draw(self, blob=None):
        """Abstract method to draw the object on the screen."""
        pass


class Grid(Drawable):
    """Represents the background grid of the game."""
    
    def __init__(self, surface, camera):
        super().__init__(surface, camera)
        self.color = (230, 240, 240)  # Grid line color

    def draw(self):
        """Draws the grid on the game surface."""
        if self.surface is None:
            print("Cannot draw grid: Surface is None.")  # Debug
            return

        zoom = self.camera.zoom
        x, y = self.camera.x, self.camera.y

        # Draw horizontal grid lines
        for i in range(0, PLATFORM_HEIGHT, 25):
            start_pos_horiz = (x, i * zoom + y)
            end_pos_horiz = (PLATFORM_WIDTH * zoom + x, i * zoom + y)
            pygame.draw.line(self.surface, self.color, start_pos_horiz, end_pos_horiz, 3)

        # Draw vertical grid lines
        for i in range(0, PLATFORM_WIDTH, 25):
            start_pos_vert = (i * zoom + x, y)
            end_pos_vert = (i * zoom + x, PLATFORM_HEIGHT * zoom + y)
            pygame.draw.line(self.surface, self.color, start_pos_vert, end_pos_vert, 3)



class HUD(Drawable):
    """Represents all necessary Head-Up Display information on screen."""

    def __init__(self, surface, camera):
        super().__init__(surface, camera)
        
    def draw(self, blob):
        """Draw the HUD on the game screen."""
        if self.surface is None:
            print("Cannot draw HUD: Surface is None.")  # Debug
            return

        # Draw the scoreboard and leaderboard
        w, h = font.size("Score: " + str(int(blob.mass * 2)) + " ")
        self.surface.blit(pygame.transform.scale(SCOREBOARD_SURFACE, (w, h)),
                          (8, SCREEN_HEIGHT - 30))
        self.surface.blit(LEADERBOARD_SURFACE, (SCREEN_WIDTH - 160, 15))

        # Draw the score text
        drawText("Score: " + str(int(blob.mass * 2)), (10, SCREEN_HEIGHT - 30))
        self.surface.blit(big_font.render("Leaderboard", True, (255, 255, 255)),
                          (SCREEN_WIDTH - 157, 20))

        # Draw leaderboard entries
        leaderboard_entries = [
            "1. G #1", "2. G #2", "3. ISIS", "4. ur mom", 
            "5. w = pro team", "6. jumbo", "7. [voz]plz team", 
            "8. G #3", "9. doge"
        ]

        # Draw each entry
        for i, entry in enumerate(leaderboard_entries, start=1):
            drawText(entry, (SCREEN_WIDTH - 157, 20 + 25 * i))
        
        # Draw the last entry conditionally
        if blob.mass <= 500:
            drawText("10. G #4", (SCREEN_WIDTH - 157, 20 + 25 * 10))
        else:
            drawText("10. Viliami", (SCREEN_WIDTH - 157, 20 + 25 * 10), (210, 0, 0))




class Player(Drawable):
    """Represents the concept of a player in the game."""

    COLOR_LIST = [
        (37, 7, 255), (35, 183, 253), (48, 254, 241), 
        (19, 79, 251), (255, 7, 230), (255, 7, 23), (6, 254, 13)
    ]

    FONT_COLOR = (50, 50, 50)

    def __init__(self, surface, camera, name=""):
        super().__init__(surface, camera)
        self.x = random.randint(0, PLATFORM_HEIGHT)
        self.y = random.randint(0, PLATFORM_WIDTH)
        self.speed = 0
        self.mass = 20
        self.target_mass = 20  # Target mass for smooth growth
        self.base_speed = 10  # Base speed
        self.color = col = random.choice(Player.COLOR_LIST)
        self.outlineColor = (
            int(col[0] - col[0] / 3),
            int(col[1] - col[1] / 3),
            int(col[2] - col[2] / 3))
        self.name = name if name else "Anonymous"
        self.pieces = []

    def get_speed(self):
        """Calculates the current speed of the player based on their mass."""
        # The speed decreases as the mass increases. Adjust the formula to get the desired effect.
        return self.base_speed / (self.mass ** 0.3)

    def update_size(self):
        """Updates the size of the player for smooth growth."""
        if self.mass < self.target_mass:
            self.mass += (self.target_mass - self.mass) * 0.1  # Adjust the growth rate here
        else:
            self.mass = self.target_mass

    def eat(self, other_mass):
        """Consumes another player or cell."""
        self.target_mass += other_mass / 2  # Gradually increase size

    def collisionDetection(self, edibles):
        """Detects cells and players within the current player's radius to consume."""
        for edible in edibles[:]:  # Iterate over a copy to modify the list safely
            if getDistance((edible.x, edible.y), (self.x, self.y)) <= self.mass / 2 * 0.75:  # 75% coverage needed
                self.eat(edible.mass)
                edibles.remove(edible)

    def move(self, dx=None, dy=None):
        """Updates the player's current position."""
        if MAIN_SURFACE is not None:  # Check if the display surface is initialized
            if dx is None or dy is None:
                # Calculate movement based on mouse position if no direction is provided
                dX, dY = pygame.mouse.get_pos()
                rotation = math.atan2(dY - float(SCREEN_HEIGHT) / 2, dX - float(SCREEN_WIDTH) / 2)
                rotation *= 180 / math.pi
                normalized = (90 - abs(rotation)) / 90
                self.speed = self.get_speed()
                vx = self.speed * normalized
                vy = -self.speed + abs(vx) if rotation < 0 else self.speed - abs(vx)
            else:
                # Use provided dx and dy to calculate movement
                self.speed = self.get_speed()
                vx = dx * self.speed
                vy = dy * self.speed
        else:
            # If no rendering, use a default or random movement logic
            self.speed = self.get_speed()
            vx = random.uniform(-1, 1) * self.speed
            vy = random.uniform(-1, 1) * self.speed

        # Update position with boundary checks
        self.x = max(0, min(self.x + vx, PLATFORM_WIDTH))
        self.y = max(0, min(self.y + vy, PLATFORM_HEIGHT))


    def feed(self):
        """Unsupported feature."""
        print("Feed feature is not supported.")  # Debug

    def split(self):
        """Unsupported feature."""
        print("Split feature is not supported.")  # Debug

    def draw(self, blob):
        """Draws the player as a circle with an outline."""
        if self.surface is None:
            return  # Exit early if there's no surface to draw on

        self.update_size()
        zoom = self.camera.zoom
        x, y = self.camera.x, self.camera.y
        center = (int(self.x * zoom + x), int(self.y * zoom + y))

        # Draw player with outline
        pygame.draw.circle(self.surface, self.outlineColor, center, int((self.mass / 2 + 3) * zoom))
        pygame.draw.circle(self.surface, self.color, center, int(self.mass / 2 * zoom))

        # Draw the player's name only if rendering is enabled
        if MAIN_SURFACE is not None:
            fw, fh = font.size(self.name)
            drawText(self.name, (self.x * zoom + x - int(fw / 2), self.y * zoom + y - int(fh / 2)), Player.FONT_COLOR)

    def detect_eat(self, other):
        """Determines if this player can eat another player."""
        distance = getDistance((self.x, self.y), (other.x, other.y))
        if distance < (self.mass / 2) and self.mass > other.mass:
            coverage = ((self.mass / 2) ** 2 * math.pi) / ((other.mass / 2) ** 2 * math.pi)
            if coverage >= 0.75:  # At least 75% coverage required
                return True
        return False



class BotPlayer(Player):
    """Represents a computer-controlled player (bot)."""

    def __init__(self, surface, camera, name="Bot"):
        super().__init__(surface, camera, name)

    def random_move(self):
        """Performs a random move for the bot."""
        dx = random.uniform(-1, 1)
        dy = random.uniform(-1, 1)
        self.speed = self.get_speed()

        # Calculate new potential positions
        tmpX = self.x + dx * self.speed
        tmpY = self.y + dy * self.speed

        # Ensure the bot stays within the screen bounds
        self.x = max(0, min(tmpX, PLATFORM_WIDTH))
        self.y = max(0, min(tmpY, PLATFORM_HEIGHT))


class Cell(Drawable):
    """Represents the fundamental entity of the game, which can be eaten by other entities."""

    CELL_COLORS = [
        (80, 252, 54), (36, 244, 255), (243, 31, 46), (4, 39, 243),
        (254, 6, 178), (255, 211, 7), (216, 6, 254), (145, 255, 7),
        (7, 255, 182), (255, 6, 86), (147, 7, 255)
    ]
    
    def __init__(self, surface, camera):
        super().__init__(surface, camera)
        self.x = random.randint(20, PLATFORM_WIDTH - 20)
        self.y = random.randint(20, PLATFORM_HEIGHT - 20)
        self.mass = 7
        self.color = random.choice(Cell.CELL_COLORS)

    def draw(self):
        """Draws a cell as a simple circle."""
        if self.surface is None:
            return

        zoom = self.camera.zoom
        x, y = self.camera.x, self.camera.y
        center = (int(self.x * zoom + x), int(self.y * zoom + y))

        pygame.draw.circle(self.surface, self.color, center, int(self.mass * zoom))


class CellList(Drawable):
    """Used to group and organize cells. Also keeps track of living/dead cells."""

    def __init__(self, surface, camera, numOfCells):
        super().__init__(surface, camera)
        self.count = numOfCells
        self.list = [Cell(self.surface, self.camera) for _ in range(self.count)]

    def draw(self):
        """Draws all the cells in the list."""
        if self.surface is None:
            return

        for cell in self.list:
            cell.draw()

class GameState:
    """Class to represent the game state."""

    def __init__(self, surface=None):
        # Initialize game entities
        self.surface = surface  # Store the surface being used
        self.cam = Camera()
        self.grid = Grid(surface, self.cam)
        self.cells = CellList(surface, self.cam, 1000)
        self.blob = Player(surface, self.cam, "GeoVas")

        # Create several bots
        self.bots = [BotPlayer(surface, self.cam, f"Bot {i+1}") for i in range(15)]

        # Initialize the painter
        self.painter = Painter(self)
        self.painter.add(self.grid)
        self.painter.add(self.cells)
        self.painter.add(self.blob)
        for bot in self.bots:
            self.painter.add(bot)

    def update(self):
        """Updates the game state."""
        # Update the main player
        self.blob.move()
        self.blob.collisionDetection(self.cells.list)
        self.blob.update_size()

        # Update bots
        for bot in self.bots[:]:  # Iterate over a copy to modify the list safely
            bot.random_move()
            bot.collisionDetection(self.cells.list)
            bot.update_size()
            if self.blob.detect_eat(bot):
                self.blob.eat(bot.mass)
                self.painter.remove(bot)
                self.bots.remove(bot)

        # Update camera
        self.cam.update(self.blob)

    def render(self):
        """Renders the current game state."""
        if self.surface is not None:
            self.surface.fill((242, 251, 255))  # Clear the screen with a background color
            self.painter.paint()
            pygame.display.flip()  # Update the display
        else:
            print("Rendering is disabled (no surface available).")  # Debug

    def render_to_surface(self, surface):
        """Render the game state to the provided surface."""
        if surface is None:
            raise ValueError("A valid surface must be provided for rendering.")

        # Remplir la surface avec une couleur de fond
        surface.fill((242, 251, 255))

        # Centrer la caméra sur le joueur principal (blob)
        player = self.blob
        zoom = 100 / (player.mass) + 0.3
        x_offset = (SCREEN_WIDTH / 2) - player.x * zoom
        y_offset = (SCREEN_HEIGHT / 2) - player.y * zoom

        # Dessiner chaque élément du jeu sur la surface fictive
        for drawing in self.painter.paintings:
            try:
                if isinstance(drawing, Grid):
                    # Dessin de la grille
                    color = (230, 240, 240)  # Couleur de la grille

                    # Lignes horizontales
                    for i in range(0, PLATFORM_HEIGHT, 25):
                        start_pos = (x_offset, i * zoom + y_offset)
                        end_pos = (PLATFORM_WIDTH * zoom + x_offset, i * zoom + y_offset)
                        pygame.draw.line(surface, color, start_pos, end_pos, 3)

                    # Lignes verticales
                    for i in range(0, PLATFORM_WIDTH, 25):
                        start_pos = (i * zoom + x_offset, y_offset)
                        end_pos = (i * zoom + x_offset, PLATFORM_HEIGHT * zoom + y_offset)
                        pygame.draw.line(surface, color, start_pos, end_pos, 3)

                elif isinstance(drawing, CellList):
                    # Dessiner chaque cellule dans la liste
                    for cell in drawing.list:
                        cell_center = (int(cell.x * zoom + x_offset), int(cell.y * zoom + y_offset))
                        pygame.draw.circle(surface, cell.color, cell_center, max(int(cell.mass * zoom), 1))

                elif isinstance(drawing, (Player, BotPlayer)):
                    # Dessin des joueurs et des bots
                    center = (int(drawing.x * zoom + x_offset), int(drawing.y * zoom + y_offset))

                    # Dessiner le contour et le cercle du joueur/bot
                    pygame.draw.circle(surface, drawing.outlineColor, center, max(int((drawing.mass / 2 + 3) * zoom), 1))
                    pygame.draw.circle(surface, drawing.color, center, max(int(drawing.mass / 2 * zoom), 1))

                    # Dessiner le nom du joueur/bot
                    if font:
                        fw, fh = font.size(drawing.name)
                        font_surface = font.render(drawing.name, True, Player.FONT_COLOR)
                        surface.blit(font_surface, (center[0] - int(fw / 2), center[1] - int(fh / 2)))
            except pygame.error as e:
                print(f"Pygame error occurred while rendering: {e}")
            except Exception as e:
                print(f"General error occurred while rendering: {e}")


    def check_player_collisions(self):
        """Checks collisions between the main player and bots, and between bots themselves."""
        all_players = [self.blob] + self.bots  # Create a list of all players

        for i, player1 in enumerate(all_players):
            for player2 in all_players[i + 1:]:
                if self.is_collision(player1, player2):
                    self.resolve_collision(player1, player2)

    def is_collision(self, player1, player2):
        """Determines if two players are in collision."""
        distance = getDistance((player1.x, player1.y), (player2.x, player2.y))
        min_distance = (player1.mass + player2.mass) / 2
        collision = distance < min_distance

    def resolve_collision(self, player1, player2):
        """Resolves the collision between two players: the larger one eats the smaller one if there is enough overlap."""
        distance = getDistance((player1.x, player1.y), (player2.x, player2.y))
        radius1 = player1.mass / 2
        radius2 = player2.mass / 2
        min_overlap = 0.75 * radius2  # 75% coverage required

        if distance < (radius1 - min_overlap):
            if player1.mass > player2.mass:
                player1.eat(player2.mass)
                self.painter.remove(player2)
                if player2 in self.bots:
                    self.bots.remove(player2)
                print(f"{player1.name} has eaten {player2.name}.")  # Debug
            else:
                player2.eat(player1.mass)
                if player1 == self.blob:
                    print("The main player has been eaten!")  # Debug
                    # Handle game over or other logic here
                else:
                    self.painter.remove(player1)
                    if player1 in self.bots:
                        self.bots.remove(player1)


def initialize_game(render_mode="human"):
    """Initialize the game state."""
    # Initialize Pygame conditionally
    if render_mode == "human":
        if not initialize_pygame(render_mode):
            print("Failed to initialize Pygame. Exiting...")
            exit()

    # Create the game state with the initialized surface
    surface = MAIN_SURFACE if render_mode == "human" else None
    game_state = GameState(surface=surface)
    print(f"Game initialized successfully with render mode: {render_mode}.")  # Debug
    return game_state

if __name__ == "__main__":
    # Set render mode to "human" for visual rendering or None for no rendering
    render_mode = "human"  # Change this to "human" or None based on your needs

    # Initialize the game
    initialize_pygame(render_mode=render_mode)  # Initialize Pygame based on the render mode
    game_state = GameState(surface=MAIN_SURFACE if render_mode == "human" else None)

    running = True
    while running:
        # Handle events only if render_mode is "human"
        if render_mode == "human" and MAIN_SURFACE:
            clock.tick(70)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:  # Close the window
                    pygame.quit()
                    quit()
                elif e.type == pygame.KEYDOWN:  # Key pressed
                    if e.key == pygame.K_ESCAPE:
                        running = False
                    elif e.key == pygame.K_g:  # Toggle global view
                        game_state.cam.toggle_global_view()
                elif e.type == pygame.MOUSEBUTTONDOWN:  # Mouse click
                    pass  # No action for now, just to prevent crash
                elif e.type == pygame.ACTIVEEVENT:  # Handle activity events
                    pass

        # Update the game state
        game_state.update()
        
        # Render the game only if render_mode is "human"
        if render_mode == "human":
            game_state.render()

    if render_mode == "human" and MAIN_SURFACE:
        pygame.quit()




