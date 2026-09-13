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
TITLE = "UBERCHARGE'd!"

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
        self.debug.log_scene_info(self.scene_manager.current_scene, dt)
        self.debug.fps_counter(dt)

    def draw(self):
        screen.clear()
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

    def on_key_down(self, key):
        pass

    def on_mouse_down(self, pos):
        pass

    def on_mouse_move(self, pos):
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

    def __init__(self, master_volume = 1):
        self.master_volume = master_volume

    def play_sound(self, sound):
        audio = sounds.load(sound.sound_name)
        audio.set_volume((sound.volume * self.master_volume))
        audio.play()

    def play_random_death(self):
        audio = sounds.load("death/" + str(random.randint(1, 15)))
        audio.set_volume((0.1 * self.master_volume))
        audio.play()

    def play_random_hit(self):
        audio = sounds.load(f"hit/{str(random.randint(1, 4))}")
        audio.set_volume((0.25 * self.master_volume))
        audio.play()

    def play_track(self, sound):
        music.set_volume((sound.volume * self.master_volume))
        music.play(sound.sound_name)

# =================================================================================================================
# Start Scene
# =================================================================================================================
class StartScene(Scene):

    def __init__(self, game):
        super().__init__(game)
        self.audio_manager = AudioManager()
        self.camera = Camera()
        self.background = GameActor("background", [WIDTH / 2, HEIGHT / 2], camera=self.camera)

        self.shake_time = 0
        self.shake_strength = 0
        self.shake_duration = 0.5

        self.title = TITLE
        self.color_cycle = [
            "#000000",
            "#050505",
            "#0A0A0A",
            "#101010",
            "#161616",
            "#1C1C1C",
            "#222222",
            "#292929",
            "#303030",
            "#383838",
            "#404040",
            "#484848",
            "#505050",
            "#585858",
            "#606060",
        ]

        self.distance = 0
        self.movement_interval = 0.05
        self.movement_elapsed = 0
        self.movement_direction = True

        self.wait_time = 3
        self.current_wait_time = self.wait_time / 2

    def __str__(self):
        "START SCENE"

    def _start_shake(self, strength=2):
        self.shake_time = self.shake_duration
        self.shake_strength = strength
        self.camera.shake(2, 0.25)
        self.audio_manager.play_random_hit()

    def _animate_logo(self, dt):
        self.camera.update(dt)
                
        if self.shake_time > 0:
            self.shake_time -= dt
            if (self.shake_time < 0):
                self.current_wait_time = self.wait_time

        elif (self.current_wait_time > 0):
            self.current_wait_time -= dt

        else:
            self.movement_elapsed += dt
            if self.movement_elapsed >= self.movement_interval:
                self.movement_elapsed = 0

                if self.movement_direction:
                    self.distance += 1
                    if self.distance >= len(self.color_cycle) - 1:
                        self.movement_direction = False

                else:
                    self.distance -= 1
                    if self.distance <= 0:
                        self.movement_direction = True
                        self._start_shake()

    def update(self, dt):
            self._animate_logo(dt)

    def draw(self):
        shake_x = 0
        shake_y = 0

        if self.shake_time > 0:
            intensity = self.shake_strength * (self.shake_time / self.shake_duration)

            shake_x = random.uniform(-intensity, intensity)
            shake_y = random.uniform(-intensity, intensity)

        self.background.draw()

        screen.draw.text(
            self.title,
            center=(
                WIDTH / 2 + shake_x,
                HEIGHT / 4 + shake_y
            ),
            fontname="oleaguid",
            fontsize=96,
            color="whitesmoke",
            gcolor="gainsboro",
            shadow=(0, self.distance),
            scolor=self.color_cycle[self.distance]
        )

# =================================================================================================================
# Button
# =================================================================================================================
class Button:
    def __init__(self, center, text = ""):
        self.rect = Rect(0, 0, 250, 50)
        self.rect.center = center
        self.text = text
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self):
        color = "black" if self.hovered else "white"
        
        screen.draw.text(
            self.text,
            center=self.rect.center,
            fontname="oleaguid",
            fontsize=32,
            color=color,
            owidth=0 if self.hovered else 1,
        )

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

# =================================================================================================================
# Game Scene
# ==================================================================================================================
class GameScene(Scene):

    def __init__(self, game):
        super().__init__(game)

        self.camera = Camera()
        self.audio_manager = AudioManager()
        self.enemy_manager = EnemyManager(self.audio_manager, None, self.camera)
        self.projectile_manager = ProjectileManager(self.enemy_manager)
        self.player = Player(self.projectile_manager, self.audio_manager, self.camera)

        self.projectile_manager.player = self.player
        self.enemy_manager.player = self.player
        self.background = GameActor("background", [WIDTH / 2, HEIGHT / 2], camera=self.camera)

        self.audio_manager.play_track(self.audio_manager.Sound.THEME)

        self.paused = False
        self.upgrade_buttons = []

    def __str__(self):
        return "GAME SCENE"

    @property
    def choosing_upgrade(self):
        return len(self.player.stats.upgrade_options) > 0

    def _create_upgrade_buttons(self):
        self.upgrade_buttons.clear()

        upgrade_count = len(self.player.stats.upgrade_options)

        for index, option in enumerate(self.player.stats.upgrade_options):
            x = WIDTH / (upgrade_count + 1) * (index + 1)
            y = HEIGHT / 10

            self.upgrade_buttons.append(
                Button((x, y), option.display_name)
            )

    def _draw_ui(self):
        screen.draw.filled_rect(self.player._get_experience_rect(), "yellow")
            
        screen.draw.text(
            f"{str(self.player.level)}", center=(WIDTH / 2, HEIGHT / 30), 
            fontname="oleaguid", fontsize=32, color="white", owidth=1
        )

        screen.draw.text(
            f"Press P to pause.", center=(WIDTH - WIDTH / 10, HEIGHT - HEIGHT / 30), 
            fontname="oleaguid", fontsize=32, color="white", owidth=1
        )

        for button in self.upgrade_buttons:
            button.draw()
    
    def update(self, dt):
        if (self.choosing_upgrade and len(self.upgrade_buttons) == 0):
            self._create_upgrade_buttons()

        if (self.paused or self.choosing_upgrade): return
        
        self.player.update(keyboard, dt)
        self.enemy_manager.update(dt)
        self.projectile_manager.update(dt)
        self.camera.update(dt)

    def on_key_down(self, key):
        if (key == key.P):
            self.paused = not self.paused
        if (key == key.O):
            self.player.stats.set_random_upgradable_stats()
            self._create_upgrade_buttons()

    def on_mouse_down(self, pos):
        if (self.choosing_upgrade):

            for index, button in enumerate(self.upgrade_buttons):
                if button.collidepoint(pos):
                    self.player.stats.increase_stat(self.player.stats.upgrade_options[index])
                    
                    self.player.stats.upgrade_options.clear()
                    self.upgrade_buttons.clear()

                    break

    def on_mouse_move(self, pos):
        for button in self.upgrade_buttons:
            button.update(pos)
        
    def draw(self):
        self.background.draw()
        self.enemy_manager.draw()
        self.player.draw()        
        self.projectile_manager.draw()
        self._draw_ui()

# =================================================================================================================
# Enemy Manager
# =================================================================================================================
class EnemyManager():

    class SpawnMode(Enum):
        RANDOM_POSITION = "Spawning from random positions.",
        OPPOSITE = "Spawning from each side, in opposite patterns.",
        SYNCED = "Spawning from each side, in synced patterns."

        def __str__(self):
            return self.name

    def __init__(self, audio_manager, player, camera):
        self.enemy_classes = [SkullMonster, CuteMonster]

        self.enemies = []
        self.kill_list = set()
        self.audio_manager = audio_manager
        self.player = player

        self.spawn_mode = None
        self.spawn_mode_interval = 5
        self.spawn_mode_elapsed = 0

        self.spawn_interval = 2
        self.spawn_elapsed = 0
        self.camera = camera

        self.Y_OFFSET = 54
        self.LANE_COUNT = 10

        self.set_spawn_mode(self.SpawnMode.OPPOSITE)
        
    def _set_spawners(self, opposite):
        self.right_spawner_lane = self.LANE_COUNT / 2
        self.left_spawner_lane = self.LANE_COUNT / 2
        self.right_spawner_moving_down = True 
        self.left_spawner_moving_down = False if opposite else True

    def _spawn_enemy(self):
        match self.spawn_mode:
            case self.SpawnMode.SYNCED | self.SpawnMode.OPPOSITE:
                self.enemies.append(self._get_random_enemy_class()(self._get_lane_position(self.right_spawner_lane, True), self.audio_manager, self.player, self.camera))
                self.enemies.append(self._get_random_enemy_class()(self._get_lane_position(self.left_spawner_lane, False), self.audio_manager, self.player, self.camera))
                self._update_lane_spawners()
            case self.SpawnMode.RANDOM_POSITION:
                self.enemies.append(self._get_random_enemy_class()(self._get_random_position(), self.audio_manager, self.player, self.camera))

    def _get_random_enemy_class(self):
        return random.choice(self.enemy_classes)

    def _update_lane_spawners(self):
        if (self.left_spawner_moving_down):
            self.left_spawner_lane += 1
            if (self.left_spawner_lane >= self.LANE_COUNT - 1):
                self.left_spawner_moving_down = False
        else:
            self.left_spawner_lane -= 1
            if (self.left_spawner_lane <= 0):
                self.left_spawner_moving_down = True

        if (self.right_spawner_moving_down):
            self.right_spawner_lane += 1
            if (self.right_spawner_lane >= self.LANE_COUNT - 1):
                self.right_spawner_moving_down = False
        else:
            self.right_spawner_lane -= 1
            if (self.right_spawner_lane <= 0):
                self.right_spawner_moving_down = True

    def _get_random_position(self):
        x_choices = [-(Enemy.SPRITE_WIDTH), WIDTH + (Enemy.SPRITE_WIDTH)]
        x = random.choice(x_choices)
        y = (Enemy.SPRITE_HEIGHT / 2) * random.randint(0, self.LANE_COUNT - 1) + self.Y_OFFSET 
        return (x, y)

    def _get_lane_position(self, lane, on_right):
        x = WIDTH + (Enemy.SPRITE_WIDTH) if on_right else -(Enemy.SPRITE_WIDTH)
        y = (Enemy.SPRITE_HEIGHT / 2) * lane - 1 + self.Y_OFFSET
        return (x, y)

    def _add_enemy_to_killist(self, enemy):
            self.kill_list.add(enemy)

    def set_spawn_mode(self, to):
        if (not isinstance(to, self.SpawnMode)): return
        self.spawn_mode = to
        
        if (self.spawn_mode == self.SpawnMode.OPPOSITE):
            self._set_spawners(True)
        elif (self.spawn_mode == self.SpawnMode.SYNCED):
            self._set_spawners(False)

        Debug.log(f"Enemy spawn mode was set to: {str(to)}.")

    def update(self, dt):
        self.spawn_mode_elapsed += dt
        if (self.spawn_mode_elapsed >= self.spawn_mode_interval):
            self.set_spawn_mode(random.choice(list(self.SpawnMode)))
            self.spawn_mode_elapsed = 0
            
        self.spawn_elapsed += dt
        if (self.spawn_elapsed >= self.spawn_interval):
            self.spawn_elapsed = 0
            self._spawn_enemy()

        for enemy in self.enemies:
            enemy.update(dt)
            if (enemy.get_hitbox().colliderect(self.player.get_hitbox())):
                self.player.take_hit(enemy)
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
    active = False
    show_hitboxes = True

    # -----------------------------------------------------------------------------------------------------------------
    # Stores the prefixes for log type 
    # -----------------------------------------------------------------------------------------------------------------
    class LogType(Enum):
        INFO = "INFO",
        WARNING = "WARNING",
        ERROR = "ERROR"

        def __str__(self):
            return f"[{self.name}]"


    def __init__(self, game):
        self.game = game

        # -----------------------------------------------------------------------------------------------------------------
        # FPS counter
        # -----------------------------------------------------------------------------------------------------------------
        self.show_fps = False
        self.fps = 0
        self.frame_count = 0
        self.accumulated_time = 0
        
        # -----------------------------------------------------------------------------------------------------------------
        # Scene info settings
        # -----------------------------------------------------------------------------------------------------------------
        self.scene_info = False
        self.update_interval = 1
        self.update_elapsed = 0

        # -----------------------------------------------------------------------------------------------------------------
        # GameScene info settings
        # -----------------------------------------------------------------------------------------------------------------
        self.show_projectile_count = True
        self.show_enemy_count = True

    def fps_counter(self, dt):
        if (not self.show_fps): return

        self.accumulated_time += dt
        self.frame_count += 1
        
        if self.accumulated_time >= 0.5:
            self.fps = round(self.frame_count / self.accumulated_time)
            
            self.frame_count = 0
            self.accumulated_time = 0
            print(f"[FPS]: {self.fps}")

    def log_scene_info(self, current_scene, dt):
        if (not self.active or not self.scene_info): return

        self.update_elapsed += dt
        if (self.update_elapsed >= self.update_interval):
                self.update_elapsed = 0

                print("==================================================================================================")
                if isinstance(current_scene, GameScene):
                    print(f"[{str(current_scene)} INFO] (Updated every {self.update_interval} seconds.)")
                    if (self.show_projectile_count):
                        print(f"[{str(current_scene)}] Projectile Count: {str(len(current_scene.projectile_manager.projectiles))}")
                    if (self.show_enemy_count):
                        print(f"[{str(current_scene)}] Enemy Count: {str(len(current_scene.enemy_manager.enemies))}")
                print("==================================================================================================")

    @classmethod
    def log(cls, message, type = LogType.INFO):
        if not cls.active: return 

        print(type, message)

    @classmethod
    def render_hit_or_collision_box(cls, rect):
        if not cls.show_hitboxes or not cls.active: return
        screen.draw.rect(rect, color="red")

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
            self.shake_amount = 0
            self.offset = (0, 0)

    def shake(self, amount, duration):
        if (amount < self.shake_amount): return
        self.shake_amount = amount
        self.shake_time = duration

# =================================================================================================================
# An actor class that is aware of the game camera. 
# =================================================================================================================
class GameActor(Actor):

    def __init__(self, sprite, position, camera = None):
        self.camera = camera
        super().__init__(sprite, position)

    def _draw_collision_box(self):
        pass

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
        self._draw_collision_box()

# =================================================================================================================
# Player Stats
# =================================================================================================================
class PlayerStats:

    class Stat(Enum):
        """Stores the progression for each stat. Index 0 being start value and upgradable four times."""
        MAX_HEALTH = ((100, 200, 300, 400, 500), "Max Health")
        DAMAGE = ((1, 2, 3, 4, 5), "Damage")
        KNOCKBACK = ((0, 100, 200, 300, 400), "Knockback")
        PICK_UP_RANGE = ((50, 100, 150, 200, 250), "Pick Up Range")
        CRIT_PROBABILITY = ((0, 0.25, 0.5, 0.75, 1), "Crit Probability")
        CRIT_MULTIPLIER = ((1, 2, 3, 4, 5), "Crit Multiplier")
        FIRING_INTERVAL = ((0.2, 0.175, 0.15, 0.125, 0.1), "Firing Speed")
        SPEED = ((256, 320, 384, 448, 512), "Move Speed")
        BULLET_COUNT = ((1, 2, 4, 6, 8), "Bullet Count")

        def __init__(self, values, display_name):
            self.values = values
            self.start_value = values[0]
            self.display_name = display_name

    stat_attributes = {
        Stat.MAX_HEALTH: "max_health",
        Stat.DAMAGE: "damage",
        Stat.KNOCKBACK: "knockback",
        Stat.PICK_UP_RANGE: "pick_up_range",
        Stat.CRIT_PROBABILITY: "crit_probability",
        Stat.CRIT_MULTIPLIER: "crit_multiplier",
        Stat.FIRING_INTERVAL: "firing_interval",
        Stat.SPEED: "speed",
        Stat.BULLET_COUNT: "bullet_count",
    }

    def __init__(self):
        self.all_stats = list(self.Stat)

        self.max_health = self.Stat.MAX_HEALTH.start_value
        self.damage = self.Stat.DAMAGE.start_value
        self.knockback = self.Stat.KNOCKBACK.start_value
        self.pick_up_range = self.Stat.PICK_UP_RANGE.start_value
        self.crit_probability = self.Stat.CRIT_PROBABILITY.start_value
        self.crit_multiplier = self.Stat.CRIT_MULTIPLIER.start_value
        self.firing_interval = self.Stat.FIRING_INTERVAL.start_value
        self.speed = self.Stat.SPEED.start_value
        self.bullet_count = self.Stat.BULLET_COUNT.start_value

        self.upgrade_options = []

    def increase_stat(self, stat):
        if (not isinstance(stat, self.Stat)): return
        attribute = self.stat_attributes[stat]
        current_value = getattr(self, attribute)

        current_level = stat.values.index(current_value)
        if current_level >= len(stat.values) - 1:
            return
        
        new_value = stat.values[current_level + 1]

        setattr(self, attribute, new_value)

        Debug.log(f"{stat} was increased from {current_value} to {new_value}.")

    def set_random_upgradable_stats(self, count=3):
        upgradable_stats = [
            stat
            for stat in self.all_stats
            if getattr(self, self.stat_attributes[stat]) != stat.values[-1]
        ]

        self.upgrade_options = random.sample(upgradable_stats, min(count, len(upgradable_stats)))

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
        HURT = ("hurt/", 2)

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

        self.hurt_time = 0
        self.max_hurt_time = 0.5

        self.current_frame = 0
        self.facing_right = True
        self.animation_elapsed = 0
        self.shooting = False
        self.weapon_cooldown = 0
        self.projectile_manager = projectile_manager
        self.rect = Rect(-16, -8, 24, 48) # This will be the hitbox, x and y are offsets from the spirte centre
        self.audio_manager = audio_manager

        self.stats = PlayerStats()

        self.health = self.stats.max_health
        self.experience = 0
        self.experience_required = 15
        self.level = 1

        self.projectile_sprite = "projectile/pistol_bullet"

        self.SPRITE_BASE_LOCATION = "player/"
        self.STARTING_SPRITE = self.active_frame_path
        self.STARTING_POSITION = (WIDTH / 2, HEIGHT / 2)
        self.MUZZLE_OFFSET = (0, 16)
        self.ANIMATION_INTERVAL = 0.1
        self.SPRITE_WIDTH = 128
        self.SPRITE_HEIGHT = 128

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
    def _get_healthbar_rect(self):
            bar_width = self.SPRITE_WIDTH / 2
            bar_height = 8
            bar_x = self.x - bar_width / 2

            # Move healthbar to top, if player is close to bottom
            if (self.y > HEIGHT - self.SPRITE_HEIGHT / 2): 
                bar_y = self.y - self.SPRITE_HEIGHT / 3 + bar_height + 4
            else: 
                bar_y = self.y + self.SPRITE_HEIGHT / 2 - bar_height - 4

            if (self.camera):
                offset = self.camera.offset
                bar_x += offset[0]
                bar_y += offset[1]
    
            health_percentage = self.health / self.stats.max_health
            health_width = bar_width * health_percentage
    
            return Rect(
                bar_x,
                bar_y,
                health_width,
                bar_height
            )
    
    def _get_experience_rect(self):
        bar_width = WIDTH
        bar_height = 12
        bar_x = 0
        bar_y = 0

        experience_percentage = self.experience / self.experience_required
        health_width = bar_width * experience_percentage

        return Rect(
            bar_x,
            bar_y,
            health_width,
            bar_height
        )

    def _reset_current_frame(self):
        self.current_frame = 0
        self.animation_elapsed = self.ANIMATION_INTERVAL # This will initiate animation update on next call.

    def _update_shooting(self, keyboard):
        if (keyboard.space):
            self.shooting = True
        else: self.shooting = False

    def _check_and_update_animation(self, to, reset):
        if (self.state == to): return

        # Ensure that hurt animation is played while hurt 
        if (self.hurt_time > 0):
            return

        self.state = to
        if (reset): self._reset_current_frame()

    def _check_to_fire(self):
        if (self.weapon_cooldown > 0): return
        if (self.shooting):
            self.audio_manager.play_sound(self.audio_manager.Sound.WEAPON)
            self.projectile_manager.create_projectile(
                self.projectile_sprite, [self.x + self.MUZZLE_OFFSET[0], self.y + self.MUZZLE_OFFSET[1]], self.facing_right, self.camera, self.stats.bullet_count
            )
            self.camera.shake(2, 0.25)
            self.weapon_cooldown = self.stats.firing_interval

    def _animate(self, dt):            
        self.animation_elapsed += dt
        if (self.animation_elapsed >= self.ANIMATION_INTERVAL):
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
            x = self.x + dx / length * self.stats.speed * dt
            y = self.y + dy / length * self.stats.speed * dt
            self.x = max(self.rect.width, min(WIDTH - self.rect.width, x))
            self.y = max(self.rect.height / 3, min(HEIGHT - self.rect.height, y))

        else:
        
            if (self.shooting):
                self._check_and_update_animation(Player.State.STANDING_SHOOTING, True)
            else:
                self._check_and_update_animation(Player.State.IDLE, True)

    def _draw_collision_box(self):
        Debug.render_hit_or_collision_box(self.get_hitbox())
        Debug.render_hit_or_collision_box(self.get_pick_up_rect())

    def take_hit(self, enemy):
        damage = enemy.get_damage()
        if (damage > 0):
            self.health -= damage
            self._check_and_update_animation(self.State.HURT, True)
            self.hurt_time = self.max_hurt_time
            self.camera.shake(5, 0.25)
            self.audio_manager.play_random_hit()

    def gain_experience(self, amount = 1):
        self.experience += amount
        if (self.experience >= self.experience_required):
            self.level += 1
            overflow = self.experience - self.experience_required
            self.experience = overflow
            self.experience_required = int(5 * self.level + 0.15 * self.level ** 2)
            self.stats.set_random_upgradable_stats()

    def get_damage(self):
        return self.stats.damage if random.random() > self.stats.crit_probability else int(self.stats.damage * self.stats.crit_multiplier)

    def get_hitbox(self):
        return Rect(
            self.x + self.rect.x + (0 if self.facing_right else 8), self.y + self.rect.y,
            self.rect.width, self.rect.height,
        )
    
    def get_pick_up_rect(self):
        hitbox = self.get_hitbox()
        return Rect(
            hitbox.x - self.stats.pick_up_range, hitbox.y - self.stats.pick_up_range,
            hitbox.width + self.stats.pick_up_range * 2, hitbox.height + self.stats.pick_up_range * 2
        )

    def update(self, keyboard, dt):
            if self.weapon_cooldown > 0:
                self.weapon_cooldown -= dt

            if self.hurt_time > 0:
                self.hurt_time -= dt

            self._update_shooting(keyboard)
            self._move(keyboard, dt)
            self._animate(dt)
            self._check_to_fire()

    def draw(self):
        screen.draw.filled_rect(
        self._get_healthbar_rect(),
            "red"
        )
        super().draw()

# =================================================================================================================
# Projectile
# =================================================================================================================
class Projectile(GameActor):

    def __init__(self, starting_sprite, starting_position, facing_right = True, facing_down = None, speed = 1024, camera = None):
        self.facing_right = facing_right
        self.facing_down = facing_down
        self.speed = speed
        self.should_destroy = False
        self.rect = Rect(-6, -1.5, 12, 3)
        super().__init__(starting_sprite, starting_position, camera)

    def _check_if_should_destroy(self):
        if (self.x > WIDTH or self.x < 0) or (self.y > HEIGHT or self.y < 0):
            self.should_destroy = True

    def _draw_collision_box(self):
            Debug.render_hit_or_collision_box(self.get_hitbox())
    
    def get_hitbox(self):
        return Rect(self.x + self.rect.x, self.y + self.rect.y, self.rect.width, self.rect.height)

    def update(self, dt):
        if (self.facing_right is None):
            pass
        elif (self.facing_right): self.x += self.speed * dt
        else: self.x -= self.speed * dt

        if (self.facing_down is None):
            pass
        elif (self.facing_down): self.y += self.speed * dt
        else: self.y -= self.speed * dt
        
        self._check_if_should_destroy()

class ExperienceOrb(GameActor):

    def __init__(self, starting_position, camera):
        self.STARTING_SPRITE = "projectile/pellet"
        self.speed = 256
        self.should_destroy = False
        super().__init__(self.STARTING_SPRITE, starting_position, camera=camera)

        self.rect = Rect(-4, -4, 8, 8)

    def _check_if_should_destroy(self, player):
        if (player.get_hitbox().colliderect(self._get_collision_box())):
            self.should_destroy = True
            player.gain_experience()

    def _get_collision_box(self):
        return Rect(
            self.x + self.rect.x, self.y + self.rect.y,
            self.rect.width, self.rect.height
        )

    def _draw_collision_box(self):
        Debug.render_hit_or_collision_box(self._get_collision_box())
    
    def update(self, dt, player):
        self._check_if_should_destroy(player)
        if (self._get_collision_box().colliderect(player.get_pick_up_rect())):
            self._move(dt, player)

    def _move(self, dt, player):
        if (self.x < player.x):
            self.x += self.speed * dt
        else: self.x -= self.speed * dt

        if (self.y < player.y):
            self.y += self.speed * dt
        else: self.y -= self.speed * dt

# =================================================================================================================
# Damage text on enemy hits hnadled by projectile manager
# =================================================================================================================
class DamageText:
    def __init__(self, position, damage):
        self.random_offset = 8
        self.position = (
            position[0] + random.randint(-self.random_offset, self.random_offset), 
            position[1] + random.randint(-self.random_offset, self.random_offset)
        )
        self.time_left = 1
        self.damage = damage
        self.should_destroy = False

        self.font_size_range = (64, 128)
        self.starting_font_size = random.randint(self.font_size_range[0], self.font_size_range[1])
        self.font_size = max(1, int(self.starting_font_size * self.time_left)) 
        self.gap = (self.starting_font_size - self.font_size) / 4
        self.font_color = self._determine_color(self.damage)

    # https://pygame-zero.readthedocs.io/en/latest/colors_ref.html
    def _determine_color(self, damage):
        match damage:
            case 25:
                return "midnightblue"       
            case 24:
                return "navyblue"           
            case 23:
                return "darkblue"           
            case 22:
                return "mediumblue"         
            case 21:
                return "royalblue"          
            case 20:
                return "cornflowerblue"     
            case 19:
                return "slateblue"          
            case 18:
                return "mediumslateblue"    
            case 17:
                return "mediumpurple"       
            case 16:
                return "darkviolet"         
            case 15:
                return "blueviolet"         
            case 14:
                return "darkmagenta"        
            case 13:
                return "mediumvioletred"    
            case 12:
                return "violetred"          
            case 11:
                return "maroon"             
            case 10:
                return "darkred"            
            case 9:
                return "firebrick"          
            case 8:
                return "red"                
            case 7:
                return "orangered"          
            case 6:
                return "darkorange"         
            case 5:
                return "orange"             
            case 4:
                return "gold"               
            case 3:
                return "yellow"             
            case 2:
                return "lemonchiffon"       
            case 1:
                return "whitesmoke"         
            case _:
                return "black"
        
    def update(self, dt):
        self.time_left -= dt
        self.font_size = max(1, int(self.starting_font_size * self.time_left))
        self.gap = (self.starting_font_size - self.font_size) / 4
        if (self.time_left <= 0):
            self.should_destroy = True

    def draw(self):
        screen.draw.text(
            str(self.damage), (self.position[0] + self.gap, self.position[1] + self.gap * 2), 
            fontname="oleaguid", fontsize=self.font_size, color=self.font_color, alpha=self.time_left
        )

# =================================================================================================================
# Projectile manager
# =================================================================================================================
class ProjectileManager():

    def __init__(self, enemy_manager, player = None):
        self.projectiles = []
        self.damage_texts = []
        self.experience_orbs = []

        self.enemy_manager = enemy_manager
        self.player = player

    def create_projectile(self, sprite, position, facing_right, camera = None, bullet_count = 1):
        for bullet in range(bullet_count):
            projectile = None
            match bullet:
                case 0:
                    projectile = Projectile(sprite, position, facing_right=facing_right, camera=camera)
                case 1:
                    projectile = Projectile(sprite, position, facing_right=not facing_right, camera=camera)
                case 2:
                    projectile = Projectile(sprite, position, facing_right=None, facing_down=False, camera=camera)
                case 3:
                    projectile = Projectile(sprite, position, facing_right=None, facing_down=True, camera=camera)
                case 4:
                    projectile = Projectile(sprite, position, facing_right=False, facing_down=False, camera=camera)
                case 5:
                    projectile = Projectile(sprite, position, facing_right=True, facing_down=True, camera=camera)
                case 6:
                    projectile = Projectile(sprite, position, facing_right=False, facing_down=True, camera=camera)
                case 7:
                    projectile = Projectile(sprite, position, facing_right=True, facing_down=False, camera=camera)
                case _:
                    pass
            if (projectile): self.projectiles.append(projectile)

    def update(self, dt):
        self._update_projectiles(dt)
        self._update_damage_texts(dt)
        self._update_experience_orbs(dt)    

    def _update_projectiles(self, dt):
        projectiles_to_destroy = set()
        for projectile in self.projectiles:
            projectile.update(dt)
            for enemy in self.enemy_manager.enemies:
                if (enemy.marked_for_death): continue
                if projectile.get_hitbox().colliderect(enemy.get_hitbox()):
                    projectiles_to_destroy.add(projectile)
                    damage = self.player.get_damage()
                    if (enemy.take_hit(damage, self.player.stats.knockback)):
                        self.experience_orbs.append(ExperienceOrb((projectile.x, projectile.y), self.player.camera))
                    damage_text = DamageText([enemy.x, enemy.y], damage)
                    self.damage_texts.append(damage_text)
                    break
            if projectile.should_destroy:
                projectiles_to_destroy.add(projectile)

        for projectile in projectiles_to_destroy:
            self.projectiles.remove(projectile)

    def _update_damage_texts(self, dt):
        texts_to_destroy = set()
        for text in self.damage_texts:
            text.update(dt)

            if text.should_destroy:
                texts_to_destroy.add(text)

        for text in texts_to_destroy:
            self.damage_texts.remove(text)

    def _update_experience_orbs(self, dt):
        orbs_to_destroy = set()
        for orb in self.experience_orbs:
            orb.update(dt, self.player)
            if (orb.should_destroy): orbs_to_destroy.add(orb)

        for orb in orbs_to_destroy:
            self.experience_orbs.remove(orb)

    def draw(self):
        for projectile in self.projectiles:
            projectile.draw()

        for text in self.damage_texts:
            text.draw()

        for orb in self.experience_orbs:
            orb.draw()

# =================================================================================================================
# Enemy
# =================================================================================================================
class Enemy(GameActor):

    SPRITE_WIDTH = 128
    SPRITE_HEIGHT = 128

    def __init__(self, sprite, position, is_facing_right, player, camera = None):
        self.facing_right = is_facing_right
        self.speed = 64
        self.animation_elapsed = 0
        self.player = player

        self.knockback_velocity = 0
        self.knockback_resistance = 100

        self.max_health = int(player.level * 1.25)
        self.health = self.max_health

        self.marked_for_death = False
        self.dead = False
        self.rect = Rect(0, 0, 0, 0)

        self.pointer = Actor("pointer")
        self.pointer_left = Actor("pointer_left")
        self.POINTER_OFFSET = 20

        self.ANIMATION_INTERVAL = 0.1

        self.DAMAGE_INTERVAL = 1
        self.damage = 1
        self.damage_elapsed = 0

        super().__init__(sprite, position, camera)

    @property 
    def direction_prefix(self):
        return "" if self.facing_right else "_left"
    
    @property
    def active_frame_path(self):
        return self.SPRITE_BASE_LOCATION + str(self.state) + str(self.current_frame + 1) + self.direction_prefix

    def _knockback(self, amount):
        self.knockback_velocity += amount if self.x > self.player.x else -amount

    def _draw_collision_box(self):
        Debug.render_hit_or_collision_box(self.get_hitbox())

    def _get_healthbar_rect(self):
        bar_width = self.rect.width / 2
        bar_height = 6
        bar_x = self.x + self.rect.x / 2
        bar_y = self.y + self.rect.y

        health_percentage = self.health / self.max_health
        health_width = bar_width * health_percentage

        return Rect(
            bar_x,
            bar_y,
            health_width,
            bar_height
        )

    def _animate(self, dt):
        self.animation_elapsed += dt
        if (self.animation_elapsed > self.ANIMATION_INTERVAL):
            self.animation_elapsed = 0

            self.current_frame += 1
            if (self.current_frame >= self.state.frame_count):
                if (self.state == self.State.DEATH): self.dead = True
                self.current_frame = 0

            self.image = self.active_frame_path

    def _check_if_left_screen(self):
        # Checks if enemy is pushed out of boundary by the player with knockback
        if (self.knockback_velocity != 0) and (self.x > WIDTH + self.SPRITE_WIDTH / 2 or self.x < -self.SPRITE_WIDTH / 2):
            self.marked_for_death = True
            # Immediately award player the experience, since experience orbs will not spawn out of bounds
            self.player.gain_experience() 

        # Checks if enemy got out of bounds on its own and just despawn
        elif ((self.x > WIDTH and self.facing_right) or (self.x < 0 and not self.facing_right)):
            self.dead = True

    def _move(self, dt):
        if (self.facing_right):
            self.x += self.speed * dt
        else:
            self.x -= self.speed * dt

    def _apply_knockback(self, dt):
        if (self.knockback_velocity == 0): return

        self.x += self.knockback_velocity * dt
        if (self.knockback_velocity > 0):
            self.knockback_velocity -= self.knockback_resistance * dt
            if (self.knockback_velocity < 0):
                self.knockback_velocity = 0
        else:
            self.knockback_velocity += self.knockback_resistance * dt
            if (self.knockback_velocity > 0):
                self.knockback_velocity = 0

    def get_damage(self):
        if (self.damage_elapsed > 0 or self.marked_for_death or self.dead):
            return 0
        else:
            self.damage_elapsed = self.DAMAGE_INTERVAL 
            return self.damage

    def take_hit(self, damage, knockback = 0):
        """Returns True if enemy dies, False otherwise"""
        self.health -= damage
        if (self.health <= 0):
            self.marked_for_death = True
            return True
        self._knockback(knockback)
        return False

    def get_hitbox(self):
            return Rect(self.x + self.rect.x, self.y + self.rect.y, self.rect.width, self.rect.height)

    def reset_current_frame(self):
            self.current_frame = 0
            self.animation_elapsed = self.ANIMATION_INTERVAL # This will initiate animation update on next call.

    def update(self, dt):
        if (self.damage_elapsed > 0):
            self.damage_elapsed -= dt
            if (self.damage_elapsed < 0):
                self.damage_elapsed = 0

        self._animate(dt)
        if (self.marked_for_death):
            if (self.state != self.State.DEATH): 
                self.state = self.State.DEATH
                self.reset_current_frame()
                self.audio_manager.play_random_death()
                
        else: 
            self._move(dt)
            self._apply_knockback(dt)
            self._check_if_left_screen()

    def draw(self):
        if self.x < 0 - self.SPRITE_WIDTH / 4:
            self.pointer_left.pos = (self.POINTER_OFFSET, self.y)
            self.pointer_left.draw()

        elif self.x > WIDTH + self.SPRITE_WIDTH / 4:
            self.pointer.pos = (WIDTH - self.POINTER_OFFSET, self.y)
            self.pointer.draw()

        else:
            screen.draw.filled_rect(
                self._get_healthbar_rect(),
                "red"
            )
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

    def __init__(self, position, audio_manager, player, camera):
        self.state = SkullMonster.State.WALKING
        self.current_frame = 0
        self.facing_right = position[0] < WIDTH / 2
        self.audio_manager = audio_manager

        self.SPRITE_BASE_LOCATION = "skull_monster/" 
        self.STARTING_SPRITE = self.active_frame_path
        super().__init__(self.STARTING_SPRITE, position, self.facing_right, player, camera)
        self.rect = Rect(-32, -32, 64, 96)

# =================================================================================================================
# Cute Monster
# =================================================================================================================
class CuteMonster(Enemy):

    class State(Enum):
        """State stores the animation prefix in file system, and frame count."""
        WALKING = ("walking/", 5)
        DEATH = ("death/", 7)

        def __init__(self, path, frame_count):
            self.path = path
            self.frame_count = frame_count

        def __str__(self):
            return self.path

    def __init__(self, position, audio_manager, player, camera):
        self.state = CuteMonster.State.WALKING
        self.current_frame = 0
        self.facing_right = position[0] < WIDTH / 2
        self.audio_manager = audio_manager

        self.SPRITE_BASE_LOCATION = "cute_monster/" 
        self.STARTING_SPRITE = self.active_frame_path
        super().__init__(self.STARTING_SPRITE, position, self.facing_right, player, camera)
        self.rect = Rect(-32, -16, 64, 64)
        self.speed = 96

# =================================================================================================================
# Pgzero callbacks
# =================================================================================================================
game = Game()

def update(dt):
    game.update(dt)

def draw():
    game.draw()

def on_key_down(key):
    game.scene_manager.current_scene.on_key_down(key)

def on_mouse_down(pos):
    game.scene_manager.current_scene.on_mouse_down(pos)

def on_mouse_move(pos):
    game.scene_manager.current_scene.on_mouse_move(pos)

pgzrun.go()