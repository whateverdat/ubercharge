# =================================================================================================================
# Imports
# =================================================================================================================
from enum import Enum
import random
import pgzrun
from pygame import Rect

# =================================================================================================================
# Window Settings
# =================================================================================================================
WIDTH = 1280
HEIGHT = 720
FULLSCREEN = False
RESIZABLE = False

# =================================================================================================================
# Game 
# =================================================================================================================
class Game:

    def __init__(self):
        self.debug = Debug(self)
        self.scene_manager = SceneManager(self)
        self.scene_manager.change_scene(GameScene(self))

    def update(self, dt):
        self.scene_manager.update(dt)
        self.debug.info(self.scene_manager.current_scene)

    def draw(self):
        self.scene_manager.draw()

# =================================================================================================================
# Base Scene
# =================================================================================================================
class Scene:

    def __init__(self, game):
        self.game = game

    def update(self, dt):
        pass

    def draw(self):
        pass

    def on_enter(self):
        pass

    def on_exit(self):
        pass

# =================================================================================================================
# Scene Manager
# =================================================================================================================
class SceneManager:

    def __init__(self, game):
        self.game = game
        self.current_scene = None

    def change_scene(self, scene):
        if self.current_scene:
            self.current_scene.on_exit()

        self.current_scene = scene
        self.current_scene.on_enter()

    def update(self, dt):
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self):
        if self.current_scene:
            self.current_scene.draw()

# =================================================================================================================
# Audio Manager
# =================================================================================================================
class AudioManager:

    class Sound(Enum):
        WEAPON = ("weapon", 0.1)
        THEME = ("osmotic_memory", 0.25)

        def __init__(self, name, volume):
            self.sound_name = name
            self.volume = volume

    def play_sound(self, sound):
        audio = sounds.load(sound.sound_name)
        audio.set_volume(sound.volume)
        audio.play()

    def play_random_death(self):
        audio = sounds.load("death/" + str(random.randint(1, 15)))
        audio.set_volume(0.1)
        audio.play()

    def play_track(self, sound):
        music.set_volume(sound.volume)
        music.play(sound.sound_name)

# =================================================================================================================
# Game Scene
# =================================================================================================================
class GameScene(Scene):

    def __init__(self, game):
        super().__init__(game)

        self.camera = Camera()
        self.audio_manager = AudioManager()
        self.enemy_manager = EnemyManager(self.audio_manager, self.camera)
        self.projectile_manager = ProjectileManager(self.enemy_manager)
        self.player = Player(self.projectile_manager, self.audio_manager, self.camera)
        self.background = GameActor("background", [WIDTH / 2, HEIGHT / 2], camera=self.camera)

        self.audio_manager.play_track(self.audio_manager.Sound.THEME)

    def __str__(self):
        return "Game Scene"
    
    def update(self, dt):
        self.player.update(keyboard, dt)
        self.enemy_manager.update(dt)
        self.projectile_manager.update(dt)
        self.camera.update(dt)

    def draw(self):
        screen.clear()

        self.background.draw()
        self.projectile_manager.draw()
        self.player.draw()        
        self.enemy_manager.draw()

# =================================================================================================================
# Enemy Manager
# =================================================================================================================
class EnemyManager():

    def __init__(self, audio_manager, camera):
        self.enemies = []
        self.kill_list = set()
        self.audio_manager = audio_manager

        self.spawn_interval = 1
        self.spawn_elapsed = 0
        self.camera = camera

        self.Y_OFFSET = 54
        self.LANE_COUNT = 10

    def _spawn_enemy(self):
        self.enemies.append(SkullMonster(self._get_random_position(), self.audio_manager, self.camera))

    def _get_random_position(self):
        x_choices = [-(Enemy.SPRITE_WIDTH), WIDTH + (Enemy.SPRITE_WIDTH)]
        x = random.choice(x_choices)
        y = (Enemy.SPRITE_HEIGHT / 2) * random.randint(0, self.LANE_COUNT - 1) + self.Y_OFFSET 
        return (x, y)

    def _add_enemy_to_killist(self, enemy):
            self.kill_list.add(enemy)

    def update(self, dt):
        self.spawn_elapsed += dt
        if (self.spawn_elapsed >= self.spawn_interval):
            self.spawn_elapsed = 0
            self._spawn_enemy()
        for enemy in self.enemies:
            enemy.update(dt)
            if (enemy.dead):
                self._add_enemy_to_killist(enemy)
        for enemy in self.kill_list:
            if (enemy in self.enemies):
                self.enemies.remove(enemy)
        self.kill_list.clear()
        

    def draw(self):
        for enemy in self.enemies:
            enemy.draw()

# =================================================================================================================
# Debug Settings 
# =================================================================================================================
class Debug:

    def __init__(self, game):
        self.game = game

        self.active = False
        self.update_interval = 8
        self.update_elapsed = 0

        self.show_current_scene = False
        self.show_projectile_count = True

    def info(self, current_scene):
        if (not self.active): return
        if isinstance(current_scene, GameScene):
            self.update_elapsed += 1
            if (self.update_elapsed >= self.update_interval):
                self.update_elapsed = 0
                print()
                if (self.show_current_scene):
                    print("Current Scene: " + str(current_scene))
                if (self.show_projectile_count): 
                    print("Projectile Count: " + str(len(current_scene.projectile_manager.projectiles)))
        
# =================================================================================================================
# Camera
# =================================================================================================================
class Camera():

    def __init__(self):
        self.offset = (0, 0)
        self.shake_time = 0
        self.shake_amount = 0

    def update(self, dt):
        if self.shake_time > 0:
            self.offset = (
                random.randint(-self.shake_amount, self.shake_amount),
                random.randint(-self.shake_amount, self.shake_amount)
            )
            self.shake_time -= dt
        else:
            self.offset = (0, 0)

    def shake(self, amount, duration):
        self.shake_amount = amount
        self.shake_time = duration

# =================================================================================================================
# An actor class that is aware of the game camera. 
# =================================================================================================================
class GameActor(Actor):

    def __init__(self, sprite, position, camera = None):
        self.camera = camera
        super().__init__(sprite, position)

    def draw(self):
        original_position = self.pos

        if (self.camera):
            offset = self.camera.offset
            self.pos = (
                original_position[0] + offset[0],
                original_position[1] + offset[1]
            )

        super().draw()

        self.pos = original_position

# =================================================================================================================
# Player
# =================================================================================================================
class Player(GameActor):

    # -----------------------------------------------------------------------------------------------------------------
    # State to keep track of current action and retrieve animation information 
    # -----------------------------------------------------------------------------------------------------------------

    class State(Enum):
        """State stores the animation prefix in file system, and frame count."""
        IDLE = ("idle/", 8)
        WALKING = ("walking/", 8)
        STANDING_SHOOTING = ("standing_shooting/", 8)
        WALKING_SHOOTING = ("walking_shooting/", 8)

        def __init__(self, path, frame_count):
            self.path = path
            self.frame_count = frame_count

        def __str__(self):
            return self.path

    # -----------------------------------------------------------------------------------------------------------------
    # Player initialization
    # -----------------------------------------------------------------------------------------------------------------
    
    def __init__(self, projectile_manager, audio_manager, camera = None):
        self.state = Player.State.IDLE
        self.current_frame = 0
        self.facing_right = True
        self.animation_elapsed = 0
        self.shooting = False
        self.weapon_cooldown = 0
        self.projectile_manager = projectile_manager
        self.rect = Rect(0, -16, 64, 64) # This will be the hitbox, x and y are offsets from the spirte centre
        self.audio_manager = audio_manager

        self.FIRING_INTERVAL = 0.2
        self.SPRITE_BASE_LOCATION = "player/"
        self.PROJECTILE_SPRITE = "projectile/pistol_bullet"
        self.STARTING_SPRITE = self.active_frame_path
        self.STARTING_POSITION = (WIDTH / 2, HEIGHT / 2)
        self.MUZZLE_OFFSET = (16, 16)
        self.SPEED = 256
        self.ANIMATION_INTERVAL = 0.1

        super().__init__(self.STARTING_SPRITE, self.STARTING_POSITION, camera)

    # -----------------------------------------------------------------------------------------------------------------
    # Player properties
    # -----------------------------------------------------------------------------------------------------------------

    @property 
    def direction_prefix(self):
        return "" if self.facing_right else "_left"

    @property
    def active_frame_path(self):
        return self.SPRITE_BASE_LOCATION + str(self.state) + str(self.current_frame + 1) + self.direction_prefix

    # -----------------------------------------------------------------------------------------------------------------
    # Player methods
    # -----------------------------------------------------------------------------------------------------------------

    def _reset_current_frame(self):
        self.current_frame = 0
        self.animation_elapsed = self.ANIMATION_INTERVAL # This will initiate animation update on next call.

    def _update_shooting(self, keyboard):
        if (keyboard.space):
            self.shooting = True
        else: self.shooting = False

    def _check_and_update_animation(self, to, reset):
        if (self.state == to): return
        self.state = to
        if (reset): self._reset_current_frame()

    def _check_to_fire(self):
        if (self.weapon_cooldown > 0): return
        if (self.shooting):
            self.audio_manager.play_sound(self.audio_manager.Sound.WEAPON)
            self.projectile_manager.create_projectile(
                self.PROJECTILE_SPRITE, [self.x + self.MUZZLE_OFFSET[0], self.y + self.MUZZLE_OFFSET[1]], self.facing_right, self.camera
            )
            self.camera.shake(2, 0.25)
            self.weapon_cooldown = self.FIRING_INTERVAL

    def _animate(self, dt):
        self.animation_elapsed += dt
        if (self.animation_elapsed > self.ANIMATION_INTERVAL):
            self.animation_elapsed = 0

            self.current_frame += 1
            if (self.current_frame >= self.state.frame_count):
                self.current_frame = 0

            self.image = self.active_frame_path

    def _move(self, keyboard, dt):
        dx = keyboard.d - keyboard.a
        dy = keyboard.s - keyboard.w

        if dx < 0:
            self.facing_right = False
        elif dx > 0:
            self.facing_right = True

        if dx or dy:
           
            if (self.shooting):
                self._check_and_update_animation(Player.State.WALKING_SHOOTING, True)
            else:
                self._check_and_update_animation(Player.State.WALKING, True)

            length = (dx * dx + dy * dy) ** 0.5
            x = self.x + dx / length * self.SPEED * dt
            y = self.y + dy / length * self.SPEED * dt
            self.x = max(self.rect.width / 2 + self.rect.x, min(WIDTH - self.rect.width / 2 + self.rect.x, x))
            self.y = max(self.rect.height / 2 + self.rect.y, min(HEIGHT - self.rect.height / 2 + self.rect.y, y))

        else:
        
            if (self.shooting):
                self._check_and_update_animation(Player.State.STANDING_SHOOTING, True)
            else:
                self._check_and_update_animation(Player.State.IDLE, True)

    def update(self, keyboard, dt):
            if self.weapon_cooldown > 0:
                self.weapon_cooldown -= dt

            self._update_shooting(keyboard)
            self._move(keyboard, dt)
            self._animate(dt)
            self._check_to_fire()

# =================================================================================================================
# Projectile
# =================================================================================================================
class Projectile(GameActor):

    def __init__(self, starting_sprite, starting_position, facing_right = True, speed = 1024, camera = None):
            self.facing_right = facing_right
            self.speed = speed
            self.should_destroy = False
            self.rect = Rect(6, 1.5, 12, 3)
            super().__init__(starting_sprite, starting_position, camera)

    def get_hitbox(self):
        return Rect(self.x - self.rect.left, self.y - self.rect.top, self.rect.width, self.rect.height)

    def _check_if_should_destroy(self):
        if (self.x > WIDTH or self.x < 0):
            self.should_destroy = True

    def update(self, dt):
        if (self.facing_right): self.x += self.speed * dt
        else: self.x -= self.speed * dt
        self._check_if_should_destroy()


# =================================================================================================================
# Projectile manager
# =================================================================================================================
class ProjectileManager():

    def __init__(self, enemy_manager):
        self.projectiles = []
        self.enemy_manager = enemy_manager

    def create_projectile(self, sprite, position, facing_right, camera = None):
        projectile = Projectile(sprite, position, facing_right=facing_right, camera=camera)
        self.projectiles.append(projectile)

    def update(self, dt):
        projectiles_to_destroy = set()
        for projectile in self.projectiles:
            projectile.update(dt)
            for enemy in self.enemy_manager.enemies:
                if (enemy.marked_for_death): continue
                if projectile.get_hitbox().colliderect(enemy.get_hitbox()):
                    projectiles_to_destroy.add(projectile)
                    enemy.marked_for_death = True
                    break
            if projectile.should_destroy:
                projectiles_to_destroy.add(projectile)

        for projectile in projectiles_to_destroy:
            self.projectiles.remove(projectile)

    def draw(self):
        for projectile in self.projectiles:
            projectile.draw()

# =================================================================================================================
# Enemy
# =================================================================================================================
class Enemy(GameActor):

    SPRITE_WIDTH = 128
    SPRITE_HEIGHT = 128

    def __init__(self, sprite, position, is_facing_right, camera = None):
        self.facing_right = is_facing_right
        self.speed = 64
        self.animation_elapsed = 0

        self.marked_for_death = False
        self.dead = False

        self.ANIMATION_INTERVAL = 0.1

        self.POINTER_OFFSET = 20
        self.pointer = Actor("pointer")
        self.pointer_left = Actor("pointer_left")

        super().__init__(sprite, position, camera)

    def update(self, dt):
        if (self.facing_right):
            self.x += self.speed * dt
        else:
            self.x -= self.speed * dt

    def reset_current_frame(self):
            self.current_frame = 0
            self.animation_elapsed = self.ANIMATION_INTERVAL # This will initiate animation update on next call.

    def draw(self):
        if self.x < 0 - self.SPRITE_WIDTH / 4:
            self.pointer_left.pos = (self.POINTER_OFFSET, self.y)
            self.pointer_left.draw()

        elif self.x > WIDTH + self.SPRITE_WIDTH / 4:
            self.pointer.pos = (WIDTH - self.POINTER_OFFSET, self.y)
            self.pointer.draw()

        else:
            super().draw()

# =================================================================================================================
# Skull Monster
# =================================================================================================================
class SkullMonster(Enemy):

    class State(Enum):
        """State stores the animation prefix in file system, and frame count."""
        WALKING = ("walking/", 4)
        DEATH = ("death/", 7)

        def __init__(self, path, frame_count):
            self.path = path
            self.frame_count = frame_count

        def __str__(self):
            return self.path

    def __init__(self, position, audio_manager, camera):
        self.state = SkullMonster.State.WALKING
        self.current_frame = 0
        self.facing_right = position[0] < WIDTH / 2
        self.rect = Rect(32, 32, 64, 96)
        self.audio_manager = audio_manager

        self.SPRITE_BASE_LOCATION = "skull_monster/" 
        self.STARTING_SPRITE = self.active_frame_path

        super().__init__(self.STARTING_SPRITE, position, self.facing_right, camera)

    def get_hitbox(self):
        return Rect(self.x - self.rect.left, self.y - self.rect.top, self.rect.width, self.rect.height)

    @property 
    def direction_prefix(self):
        return "" if self.facing_right else "_left"

    @property
    def active_frame_path(self):
        return self.SPRITE_BASE_LOCATION + str(self.state) + str(self.current_frame + 1) + self.direction_prefix
    
    def _animate(self, dt):
            self.animation_elapsed += dt
            if (self.animation_elapsed > self.ANIMATION_INTERVAL):
                self.animation_elapsed = 0
    
                self.current_frame += 1
                if (self.current_frame >= self.state.frame_count):
                    if (self.state == SkullMonster.State.DEATH): self.dead = True
                    self.current_frame = 0
    
                self.image = self.active_frame_path
    
    def update(self, dt):
        self._animate(dt)
        if (self.marked_for_death):
            if (self.state != SkullMonster.State.DEATH): 
                self.state = SkullMonster.State.DEATH
                self.reset_current_frame()
                self.audio_manager.play_random_death()
                
        else: super().update(dt)

# =================================================================================================================
# Pgzero callbacks
# =================================================================================================================
game = Game()

def update(dt):
    game.update(dt)

def draw():
    game.draw()

pgzrun.go()