from enum import Enum
from itertools import cycle

import pygame

from ..utils import GameConfig, clamp
from .entity import Entity
from .floor import Floor
from .pipe import Pipe, Pipes
from .powerup import PowerUpType


class PlayerMode(Enum):
    """玩家模式枚举"""
    NORMAL = "NORMAL"  # 正常模式
    SHM = "SHM"  # 静止模式
    CRASH = "CRASH"  # 撞击模式
    CRASHED = "CRASHED"  # 撞击模式
    REVERSE = "REVERSE"  # 反向模式
    GHOST = "GHOST"  # 穿越模式
    NIGHT = "NIGHT"  # 夜间模式
    SPEED = "SPEED"  # 极速模式


class Player(Entity):
    def __init__(self, config: GameConfig) -> None:
        image = config.images.player[0]
        x = int(config.window.width * 0.2)
        y = int((config.window.height - image.get_height()) / 2)
        super().__init__(config, image, x, y)
        self.min_y = -2 * self.h
        self.max_y = config.window.viewport_height - self.h * 0.75
        self.img_idx = 0
        self.img_gen = cycle([0, 1, 2, 1])
        self.frame = 0
        self.crashed = False
        self.crash_entity = None
        # 道具效果相关属性
        self.speed_modifier = 1.0  # 速度修改器
        self.invincible = False    # 无敌状态
        self.size_modifier = 1.0   # 大小修改器
        self.original_image = None # 保存原始图像
        self.is_reverse_mode = False  # 是否为反向模式
        # 爆炸效果相关属性
        self.explosion_active = False
        self.explosion_start_time = 0
        self.explosion_duration = 500  # 爆炸持续时间(毫秒)
        # 穿越模式相关属性
        self.is_ghost_mode = False  # 是否为穿越模式
        self.ghost_alpha = 160  # 穿越模式下的透明度
        # 夜间模式相关属性
        self.is_night_mode = False  # 是否为夜间模式
        self.night_vision_range = 120  # 夜视范围
        # 极速模式相关属性
        self.is_speed_mode = False  # 是否为极速模式
        self.speed_boost = 2.0  # 速度提升倍数
        self.set_mode(PlayerMode.SHM)
        
    def apply_powerup_effect(self, powerup_type: PowerUpType) -> None:
        """应用道具效果"""
        if powerup_type == PowerUpType.SPEED_BOOST:
            self.speed_modifier = 1.5
        elif powerup_type == PowerUpType.INVINCIBLE:
            self.invincible = True
        elif powerup_type == PowerUpType.SLOW_MOTION:
            self.speed_modifier = 0.5
        elif powerup_type == PowerUpType.SMALL_SIZE:
            # 缩小玩家
            if self.size_modifier == 1.0:
                self.original_image = self.image
                self.size_modifier = 0.6
                self._resize_player()
    
    def remove_powerup_effect(self, powerup_type: PowerUpType) -> None:
        """移除道具效果"""
        if powerup_type == PowerUpType.SPEED_BOOST or powerup_type == PowerUpType.SLOW_MOTION:
            self.speed_modifier = 1.0
        elif powerup_type == PowerUpType.INVINCIBLE:
            self.invincible = False
        elif powerup_type == PowerUpType.SMALL_SIZE:
            if self.original_image:
                self.size_modifier = 1.0
                self.image = self.original_image
                self.w = self.image.get_width()
                self.h = self.image.get_height()
                self.original_image = None
    
    def _resize_player(self) -> None:
        """根据size_modifier调整玩家大小"""
        if self.size_modifier != 1.0:
            new_width = int(self.image.get_width() * self.size_modifier)
            new_height = int(self.image.get_height() * self.size_modifier)
            self.image = pygame.transform.scale(self.image, (new_width, new_height))
            self.w = self.image.get_width()
            self.h = self.image.get_height()

    def set_mode(self, mode: PlayerMode) -> None:
        self.mode = mode
        if mode == PlayerMode.NORMAL:
            self.reset_vals_normal()
            self.config.sounds.wing.play()
        elif mode == PlayerMode.SHM:
            self.reset_vals_shm()
        elif mode == PlayerMode.REVERSE:
            self.reset_vals_reverse()
            self.config.sounds.wing.play()
        elif mode == PlayerMode.GHOST:
            self.reset_vals_ghost()
            self.config.sounds.wing.play()
        elif mode == PlayerMode.NIGHT:
            self.reset_vals_night()
            self.config.sounds.wing.play()
        elif mode == PlayerMode.SPEED:
            self.reset_vals_speed()
            self.config.sounds.wing.play()

    def reset_vals_normal(self) -> None:
        self.vel_y = -9  # player's velocity along Y axis
        self.max_vel_y = 10  # max vel along Y, max descend speed
        self.min_vel_y = -8  # min vel along Y, max ascend speed
        self.acc_y = 1  # players downward acceleration

        self.rot = 80  # player's current rotation
        self.vel_rot = -3  # player's rotation speed
        self.rot_min = -90  # player's min rotation angle
        self.rot_max = 20  # player's max rotation angle

        self.flap_acc = -9  # players speed on flapping
        self.flapped = False  # True when player flaps
        
    def reset_vals_reverse(self) -> None:
        # 反向模式下的初始化值
        self.vel_y = 9  # 反向的初始速度（向下）
        self.max_vel_y = 8  # 反向模式下的最大上升速度（实际是下降）
        self.min_vel_y = -10  # 反向模式下的最小下降速度（实际是上升）
        self.acc_y = -1  # 反向的重力加速度（向上）

        self.rot = -80  # 反向的初始旋转角度
        self.vel_rot = 3  # 反向的旋转速度
        self.rot_min = -20  # 反向的最小旋转角度
        self.rot_max = 90  # 反向的最大旋转角度

        self.flap_acc = 9  # 反向的拍打加速度
        self.flapped = False  # 拍打状态

    def reset_vals_shm(self) -> None:
        self.vel_y = 1  # player's velocity along Y axis
        self.max_vel_y = 4  # max vel along Y, max descend speed
        self.min_vel_y = -4  # min vel along Y, max ascend speed
        self.acc_y = 0.5  # players downward acceleration

        self.rot = 0  # player's current rotation
        self.vel_rot = 0  # player's rotation speed
        self.rot_min = 0  # player's min rotation angle
        self.rot_max = 0  # player's max rotation angle

        self.flap_acc = 0  # players speed on flapping
        self.flapped = False  # True when player flaps

    def reset_vals_crash(self) -> None:
        self.acc_y = 2
        self.vel_y = 7
        self.max_vel_y = 15
        self.vel_rot = -8

    def reset_vals_ghost(self) -> None:
        """重置穿越模式的值"""
        self.vel_y = -9  # 初始速度
        self.max_vel_y = 10  # 最大速度
        self.min_vel_y = -8  # 最小速度
        self.acc_y = 1  # 重力加速度

        self.rot = 80  # 初始旋转角度
        self.vel_rot = -3  # 旋转速度
        self.rot_min = -90  # 最小旋转角度
        self.rot_max = 20  # 最大旋转角度

        self.flap_acc = -9  # 拍打加速度
        self.flapped = False  # 拍打状态
        
        # 穿越模式相关
        self.is_ghost_mode = True  # 确保设置穿越模式标志

    def reset_vals_night(self) -> None:
        """重置夜间模式的值"""
        self.vel_y = -9  # 初始速度
        self.max_vel_y = 10  # 最大速度
        self.min_vel_y = -8  # 最小速度
        self.acc_y = 1  # 重力加速度

        self.rot = 80  # 初始旋转角度
        self.vel_rot = -3  # 旋转速度
        self.rot_min = -90  # 最小旋转角度
        self.rot_max = 20  # 最大旋转角度

        self.flap_acc = -9  # 拍打加速度
        self.flapped = False  # 拍打状态
        
        # 夜间模式相关
        self.is_night_mode = True  # 确保设置夜间模式标志

    def reset_vals_speed(self) -> None:
        """重置极速模式的值"""
        self.vel_y = -9  # 初始速度
        self.max_vel_y = 10  # 最大速度
        self.min_vel_y = -8  # 最小速度
        self.acc_y = 1  # 重力加速度

        self.rot = 80  # 初始旋转角度
        self.vel_rot = -3  # 旋转速度
        self.rot_min = -90  # 最小旋转角度
        self.rot_max = 20  # 最大旋转角度

        self.flap_acc = -9  # 拍打加速度
        self.flapped = False  # 拍打状态
        
        # 极速模式相关
        self.is_speed_mode = True  # 确保设置极速模式标志

    def update_image(self):
        self.frame += 1
        if self.frame % 5 == 0:
            self.img_idx = next(self.img_gen)
            orig_image = self.config.images.player[self.img_idx]
            
            # 应用大小修改
            if self.size_modifier != 1.0:
                new_width = int(orig_image.get_width() * self.size_modifier)
                new_height = int(orig_image.get_height() * self.size_modifier)
                self.image = pygame.transform.scale(orig_image, (new_width, new_height))
            else:
                self.image = orig_image
                
            self.w = self.image.get_width()
            self.h = self.image.get_height()

    def tick_shm(self) -> None:
        if self.vel_y >= self.max_vel_y or self.vel_y <= self.min_vel_y:
            self.acc_y *= -1
        self.vel_y += self.acc_y
        self.y += self.vel_y

    def tick_normal(self) -> None:
        if self.vel_y < self.max_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_modifier
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()
        
    def tick_reverse(self) -> None:
        # 反向模式的移动逻辑
        if self.vel_y > self.min_vel_y and not self.flapped:
            self.vel_y += self.acc_y  # 注意这里acc_y是负值，所以是减速
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_modifier
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()

    def tick_crash(self) -> None:
        if self.min_y <= self.y <= self.max_y:
            self.y = clamp(self.y + self.vel_y, self.min_y, self.max_y)
            # rotate only when it's a pipe crash and bird is still falling
            if self.crash_entity != "floor":
                self.rotate()

        # player velocity change
        if self.vel_y < self.max_vel_y:
            self.vel_y += self.acc_y

    def tick_ghost(self) -> None:
        """穿越模式的更新逻辑"""
        if self.vel_y < self.max_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_modifier
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()

    def tick_night(self) -> None:
        """夜间模式的更新逻辑"""
        if self.vel_y < self.max_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_modifier
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()

    def tick_speed(self) -> None:
        """极速模式的更新逻辑"""
        if self.vel_y < self.max_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_boost
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()

    def rotate(self) -> None:
        self.rot = clamp(self.rot + self.vel_rot, self.rot_min, self.rot_max)

    def draw(self, surface) -> None:
        """
        绘制玩家实体
        
        :param surface: 绘制的目标表面
        """
        self.update_image()
        if self.mode == PlayerMode.SHM:
            self.tick_shm()
        elif self.mode == PlayerMode.NORMAL:
            self.tick_normal()
        elif self.mode == PlayerMode.REVERSE:
            self.tick_reverse()
        elif self.mode == PlayerMode.GHOST:
            self.tick_ghost()
        elif self.mode == PlayerMode.NIGHT:
            self.tick_night()
        elif self.mode == PlayerMode.SPEED:
            self.tick_speed()

        self.draw_player(surface)

    def draw_player(self, surface) -> None:
        """
        绘制玩家图像
        
        :param surface: 绘制的目标表面
        """
        rotated_image = pygame.transform.rotate(self.image, self.rot)
        rotated_rect = rotated_image.get_rect(center=self.rect.center)
        
        # 爆炸效果渲染
        if self.explosion_active:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.explosion_start_time
            if elapsed < self.explosion_duration:
                # 爆炸渐变半径
                max_size = max(rotated_rect.width, rotated_rect.height)
                radius = int(max_size * (elapsed / self.explosion_duration) * 2)
                # 创建透明圆形表面
                explosion_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                alpha = max(0, 255 - int(255 * (elapsed / self.explosion_duration)))
                pygame.draw.circle(
                    explosion_surf,
                    (255, 165, 0, alpha),  # 橙色爆炸
                    (radius, radius),
                    radius
                )
                exp_rect = explosion_surf.get_rect(center=rotated_rect.center)
                surface.blit(explosion_surf, exp_rect)
            else:
                self.explosion_active = False
        
        # 无敌状态时添加闪烁效果
        if self.invincible and pygame.time.get_ticks() % 200 < 100:
            # 创建一个带有透明度的副本
            alpha_image = rotated_image.copy()
            alpha_image.set_alpha(150)
            surface.blit(alpha_image, rotated_rect)
            
            # 添加光环效果
            glow_size = max(rotated_rect.width, rotated_rect.height) + 10
            glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surface, 
                (255, 215, 0, 100),  # 金色光环
                (glow_size//2, glow_size//2), 
                glow_size//2
            )
            glow_rect = glow_surface.get_rect(center=rotated_rect.center)
            surface.blit(glow_surface, glow_rect)
            
        # 穿越模式时添加透明效果
        if self.is_ghost_mode:
            # 创建一个带有透明度的副本
            alpha_image = rotated_image.copy()
            alpha_image.set_alpha(self.ghost_alpha)
            surface.blit(alpha_image, rotated_rect)
            
        # 夜间模式时添加夜视效果
        if self.is_night_mode:
            # 创建一个带有透明度的副本
            alpha_image = rotated_image.copy()
            alpha_image.set_alpha(200)
            surface.blit(alpha_image, rotated_rect)
            
            # 添加夜视效果
            night_vision_size = max(rotated_rect.width, rotated_rect.height) + 20
            night_vision_surface = pygame.Surface((night_vision_size, night_vision_size), pygame.SRCALPHA)
            pygame.draw.circle(
                night_vision_surface, 
                (0, 0, 255, 100),  # 蓝色夜视
                (night_vision_size//2, night_vision_size//2), 
                night_vision_size//2
            )
            night_vision_rect = night_vision_surface.get_rect(center=rotated_rect.center)
            surface.blit(night_vision_surface, night_vision_rect)
            
        surface.blit(rotated_image, rotated_rect)

    def stop_wings(self) -> None:
        self.img_gen = cycle([self.img_idx])

    def flap(self) -> None:
        if self.mode == PlayerMode.REVERSE:
            # 反向模式下的拍打逻辑
            if self.y < self.max_y:
                self.vel_y = self.flap_acc  # 向下加速
                self.flapped = True
                self.rot = -80  # 反向旋转
                self.config.sounds.wing.play()
        else:
            # 正常模式下的拍打逻辑
            if self.y > self.min_y:
                self.vel_y = self.flap_acc
                self.flapped = True
                self.rot = 80
                self.config.sounds.wing.play()

    def crossed(self, pipe: Pipe) -> bool:
        return pipe.cx <= self.cx < pipe.cx - pipe.vel_x

    def collided(self, pipes: Pipes, floor: Floor) -> bool:
        """returns True if player collides with floor or pipes."""
        
        # 如果处于无敌状态，不检测碰撞
        if self.invincible:
            return False

        # 如果处于穿越模式，不检测碰撞
        if self.mode == PlayerMode.GHOST:
            return False

        # if player crashes into ground
        if self.collide(floor):
            self.crashed = True
            self.crash_entity = "floor"
            return True

        for pipe in pipes.upper:
            if self.collide(pipe):
                self.crashed = True
                self.crash_entity = "pipe"
                return True
        for pipe in pipes.lower:
            if self.collide(pipe):
                self.crashed = True
                self.crash_entity = "pipe"
                return True

        return False

    def update_bomb(self) -> None:
        """更新炮弹状态"""
        if not self.bomb_ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.bomb_start_time >= self.bomb_duration:
                self.bomb_ready = True
                print(f"Bomb deactivated! is_bomb_mode={self.is_bomb_mode}, bomb_ready={self.bomb_ready}")

    def activate_bomb(self) -> None:
        """激活炮弹模式"""
        if self.bomb_ready:
            self.bomb_ready = False
            self.is_bomb_mode = True  # 设置为炮弹模式
            self.bomb_start_time = pygame.time.get_ticks()
            # 激活爆炸效果
            self.explosion_active = True
            self.explosion_start_time = pygame.time.get_ticks()
            self.config.sounds.point.play()  # 播放炮弹音效
            print(f"Bomb activated! is_bomb_mode={self.is_bomb_mode}, bomb_ready={self.bomb_ready}")
