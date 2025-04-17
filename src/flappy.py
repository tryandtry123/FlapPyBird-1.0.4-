import asyncio
import sys

import pygame
from pygame.locals import K_ESCAPE, K_SPACE, K_UP, KEYDOWN, QUIT

from .entities import (
    Background,
    Floor,
    GameOver,
    Pipes,
    Player,
    PlayerMode,
    Score,
    WelcomeMessage,
)
from .entities.powerup import PowerUpManager, PowerUpType
from .utils import GameConfig, Images, Sounds, Window
from enum import Enum
import random


class GameMode(Enum):
    """游戏模式枚举"""
    CLASSIC = "经典模式"    # 经典无限模式
    TIMED = "限时挑战"      # 限时挑战模式
    REVERSE = "反向模式"    # 重力反转模式
    GHOST = "穿越模式"       # 穿越模式
    NIGHT = "夜间模式"       # 夜间模式
    SPEED = "极速模式"       # 极速模式


class Flappy:
    def __init__(self):
        """
        初始化Flappy Bird游戏
        """
        pygame.init()  # 初始化pygame
        pygame.display.set_caption("Flappy Bird")  # 设置窗口标题
        window = Window(288, 512)  # 创建窗口对象
        screen = pygame.display.set_mode((window.width, window.height))  # 设置屏幕大小
        images = Images()  # 加载图像资源

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=30,
            window=window,
            images=images,
            sounds=Sounds(),
        )
        # 记录上一帧的时间，用于计算delta_time
        self.last_frame_time = pygame.time.get_ticks()
        
        # 游戏模式相关
        self.game_mode = GameMode.CLASSIC  # 默认为经典模式
        self.time_limit = 60 * 1000  # 限时模式的时间限制（毫秒）
        self.time_remaining = self.time_limit  # 剩余时间

    async def start(self):
        """
        启动游戏循环
        """
        while True:
            self.background = Background(self.config)  # 创建背景对象
            self.floor = Floor(self.config)  # 创建地面对象
            self.player = Player(self.config)  # 创建玩家对象
            self.welcome_message = WelcomeMessage(self.config)  # 创建欢迎信息对象
            self.game_over_message = GameOver(self.config)  # 创建游戏结束信息对象
            self.pipes = Pipes(self.config)  # 创建管道对象
            self.score = Score(self.config)  # 创建得分对象
            self.powerup_manager = PowerUpManager(self.config)  # 创建道具管理器
            await self.splash()  # 显示欢迎界面
            await self.play()  # 开始游戏
            await self.game_over()  # 游戏结束

    async def splash(self):
        """
        显示欢迎界面动画
        """
        self.player.set_mode(PlayerMode.SHM)  # 设置玩家模式为SHM（静止模式）
        
        # 初始化字体 - 使用系统默认字体并设置更大的字号
        title_font = pygame.font.Font(None, 36)  # 标题字体
        mode_font = pygame.font.Font(None, 28)  # 模式选择字体
        instruction_font = pygame.font.Font(None, 22)  # 指示字体
        
        # 创建文本 - 添加标题和更美观的文本
        title_text = title_font.render("Game Mode Selection", True, (255, 255, 0))  # 黄色标题
        classic_text = mode_font.render("Classic Mode", True, (255, 255, 255))
        timed_text = mode_font.render("Timed Challenge", True, (255, 255, 255))
        reverse_text = mode_font.render("Reverse Mode", True, (255, 255, 255))  # 添加反向模式文本
        ghost_text = mode_font.render("Ghost Mode", True, (255, 255, 255))  # 添加穿越模式文本
        night_text = mode_font.render("Night Mode", True, (255, 255, 255))  # 添加夜间模式文本
        speed_text = mode_font.render("Speed Mode", True, (255, 255, 255))  # 添加极速模式文本
        instruction_text = instruction_font.render("UP/DOWN to select, SPACE to start", True, (220, 220, 220))
        
        # 为选择框准备颜色和大小
        box_color_active = (255, 255, 0)  # 活跃选择的颜色
        box_color_inactive = (100, 100, 100, 128)  # 非活跃选择的颜色
        
        # 计算文本位置 - 调整间距使界面更加平衡
        title_pos = (self.config.window.width//2 - title_text.get_width()//2, self.config.window.height//2 - 50)  # 调整标题位置
        classic_pos = (self.config.window.width//2 - classic_text.get_width()//2, 
                      self.config.window.height//2 + 20)  # 调整经典模式位置
        timed_pos = (self.config.window.width//2 - timed_text.get_width()//2, 
                    self.config.window.height//2 + 70)  # 调整限时模式位置
        reverse_pos = (self.config.window.width//2 - reverse_text.get_width()//2, 
                      self.config.window.height//2 + 120)  # 添加反向模式位置
        ghost_pos = (self.config.window.width//2 - ghost_text.get_width()//2, 
                    self.config.window.height//2 + 170)  # 添加穿越模式位置
        night_pos = (self.config.window.width//2 - night_text.get_width()//2, 
                    self.config.window.height//2 + 220)  # 添加夜间模式位置
        speed_pos = (self.config.window.width//2 - speed_text.get_width()//2, 
                    self.config.window.height//2 + 270)  # 添加极速模式位置
        instruction_pos = (self.config.window.width//2 - instruction_text.get_width()//2, 
                          self.config.window.height//2 + 320)  # 调整指示文本位置
        
        # 为按钮创建矩形
        classic_rect = pygame.Rect(classic_pos[0] - 20, classic_pos[1] - 10, 
                                 classic_text.get_width() + 40, classic_text.get_height() + 20)
        timed_rect = pygame.Rect(timed_pos[0] - 20, timed_pos[1] - 10, 
                               timed_text.get_width() + 40, timed_text.get_height() + 20)
        reverse_rect = pygame.Rect(reverse_pos[0] - 20, reverse_pos[1] - 10, 
                                 reverse_text.get_width() + 40, reverse_text.get_height() + 20)  # 添加反向模式矩形
        ghost_rect = pygame.Rect(ghost_pos[0] - 20, ghost_pos[1] - 10, 
                                ghost_text.get_width() + 40, ghost_text.get_height() + 20)  # 添加穿越模式矩形
        night_rect = pygame.Rect(night_pos[0] - 20, night_pos[1] - 10, 
                                night_text.get_width() + 40, night_text.get_height() + 20)  # 添加夜间模式矩形
        speed_rect = pygame.Rect(speed_pos[0] - 20, speed_pos[1] - 10, 
                                speed_text.get_width() + 40, speed_text.get_height() + 20)  # 添加极速模式矩形
        
        # 默认选择经典模式
        self.game_mode = GameMode.CLASSIC
        selected_index = 0  # 0表示经典模式，1表示限时模式，2表示反向模式，3表示穿越模式，4表示夜间模式，5表示极速模式

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)  # 检查退出事件
                
                # 添加调试信息
                if event.type == KEYDOWN:
                    print(f"按键按下: {event.key}, pygame.K_m = {pygame.K_m}")
                    
                # 处理模式选择
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        # 向下切换模式
                        selected_index = (selected_index + 1) % 6  # 循环切换六种模式
                        if selected_index == 0:
                            self.game_mode = GameMode.CLASSIC
                        elif selected_index == 1:
                            self.game_mode = GameMode.TIMED
                            # 重置计时器
                            self.time_remaining = self.time_limit
                        elif selected_index == 2:
                            self.game_mode = GameMode.REVERSE
                        elif selected_index == 3:
                            self.game_mode = GameMode.GHOST
                        elif selected_index == 4:
                            self.game_mode = GameMode.NIGHT
                        elif selected_index == 5:
                            self.game_mode = GameMode.SPEED
                        self.config.sounds.swoosh.play()
                    elif event.key == pygame.K_UP:
                        # 向上切换模式
                        selected_index = (selected_index - 1) % 6  # 循环切换六种模式
                        if selected_index == 0:
                            self.game_mode = GameMode.CLASSIC
                        elif selected_index == 1:
                            self.game_mode = GameMode.TIMED
                            # 重置计时器
                            self.time_remaining = self.time_limit
                        elif selected_index == 2:
                            self.game_mode = GameMode.REVERSE
                        elif selected_index == 3:
                            self.game_mode = GameMode.GHOST
                        elif selected_index == 4:
                            self.game_mode = GameMode.NIGHT
                        elif selected_index == 5:
                            self.game_mode = GameMode.SPEED
                        self.config.sounds.swoosh.play()
                
                # 空格或上箭头开始游戏
                if self.is_tap_event(event):
                    return
            
            # 绘制背景、地面和玩家
            self.background.tick()  # 更新背景
            self.floor.tick()  # 更新地面
            self.player.tick()  # 更新玩家
            self.welcome_message.tick()  # 更新欢迎信息
            
            # 绘制标题
            self.config.screen.blit(title_text, title_pos)
            
            # 绘制经典模式按钮
            if selected_index == 0:
                # 活跃按钮 - 绘制填充和边框
                pygame.draw.rect(self.config.screen, (50, 50, 50), classic_rect)  # 深色填充
                pygame.draw.rect(self.config.screen, box_color_active, classic_rect, 3, border_radius=5)  # 边框
            else:
                # 非活跃按钮 - 只绘制边框
                pygame.draw.rect(self.config.screen, (30, 30, 30), classic_rect)  # 浅色填充
                pygame.draw.rect(self.config.screen, box_color_inactive, classic_rect, 2, border_radius=5)  # 边框
            
            # 绘制限时模式按钮
            if selected_index == 1:
                # 活跃按钮
                pygame.draw.rect(self.config.screen, (50, 50, 50), timed_rect)  # 深色填充
                pygame.draw.rect(self.config.screen, box_color_active, timed_rect, 3, border_radius=5)  # 边框
            else:
                # 非活跃按钮
                pygame.draw.rect(self.config.screen, (30, 30, 30), timed_rect)  # 浅色填充
                pygame.draw.rect(self.config.screen, box_color_inactive, timed_rect, 2, border_radius=5)  # 边框
            
            # 绘制反向模式按钮
            if selected_index == 2:
                # 活跃按钮
                pygame.draw.rect(self.config.screen, (50, 50, 50), reverse_rect)  # 深色填充
                pygame.draw.rect(self.config.screen, box_color_active, reverse_rect, 3, border_radius=5)  # 边框
            else:
                # 非活跃按钮
                pygame.draw.rect(self.config.screen, (30, 30, 30), reverse_rect)  # 浅色填充
                pygame.draw.rect(self.config.screen, box_color_inactive, reverse_rect, 2, border_radius=5)  # 边框
            
            # 绘制穿越模式按钮
            if selected_index == 3:
                # 活跃按钮
                pygame.draw.rect(self.config.screen, (50, 50, 50), ghost_rect)  # 深色填充
                pygame.draw.rect(self.config.screen, box_color_active, ghost_rect, 3, border_radius=5)  # 边框
            else:
                # 非活跃按钮
                pygame.draw.rect(self.config.screen, (30, 30, 30), ghost_rect)  # 浅色填充
                pygame.draw.rect(self.config.screen, box_color_inactive, ghost_rect, 2, border_radius=5)  # 边框
            
            # 绘制夜间模式按钮
            if selected_index == 4:
                # 活跃按钮
                pygame.draw.rect(self.config.screen, (50, 50, 50), night_rect)  # 深色填充
                pygame.draw.rect(self.config.screen, box_color_active, night_rect, 3, border_radius=5)  # 边框
            else:
                # 非活跃按钮
                pygame.draw.rect(self.config.screen, (30, 30, 30), night_rect)  # 浅色填充
                pygame.draw.rect(self.config.screen, box_color_inactive, night_rect, 2, border_radius=5)  # 边框
            
            # 绘制极速模式按钮
            if selected_index == 5:
                # 活跃按钮
                pygame.draw.rect(self.config.screen, (50, 50, 50), speed_rect)  # 深色填充
                pygame.draw.rect(self.config.screen, box_color_active, speed_rect, 3, border_radius=5)  # 边框
            else:
                # 非活跃按钮
                pygame.draw.rect(self.config.screen, (30, 30, 30), speed_rect)  # 浅色填充
                pygame.draw.rect(self.config.screen, box_color_inactive, speed_rect, 2, border_radius=5)  # 边框
            
            # 绘制文本
            self.config.screen.blit(classic_text, classic_pos)
            self.config.screen.blit(timed_text, timed_pos)
            self.config.screen.blit(reverse_text, reverse_pos)
            self.config.screen.blit(ghost_text, ghost_pos)
            self.config.screen.blit(night_text, night_pos)
            self.config.screen.blit(speed_text, speed_pos)
            self.config.screen.blit(instruction_text, instruction_pos)
            
            pygame.display.update()  # 刷新显示
            await asyncio.sleep(0)  # 等待下一帧
            self.config.tick()  # 更新游戏配置

    def check_quit_event(self, event):
        """
        检查退出事件
        """
        if event.type == QUIT or (
            event.type == KEYDOWN and event.key == K_ESCAPE
        ):
            pygame.quit()  # 退出pygame
            sys.exit()  # 退出程序

    def is_tap_event(self, event):
        """
        检查点击事件
        """
        m_left, _, _ = pygame.mouse.get_pressed()  # 检查鼠标左键是否按下
        space_or_up = event.type == KEYDOWN and (
            event.key == K_SPACE or event.key == K_UP
        )  # 检查空格键或上箭头是否按下
        screen_tap = event.type == pygame.FINGERDOWN  # 检查触摸事件
        return m_left or space_or_up or screen_tap  # 返回是否有点击事件

    def calculate_delta_time(self):
        """
        计算两帧之间的时间差
        """
        current_time = pygame.time.get_ticks()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        return delta_time

    def check_powerup_collisions(self):
        """
        检查玩家与道具的碰撞
        """
        # 创建一个要删除的道具列表
        powerups_to_remove = []
        
        # 检查所有道具
        for powerup in self.powerup_manager.powerups:
            # 如果玩家碰到了道具
            if self.player.collide(powerup):
                # 应用道具效果
                self.player.apply_powerup_effect(powerup.power_type)
                # 激活道具在管理器中的效果
                self.powerup_manager.activate_effect(powerup.power_type)
                # 播放得分声音
                self.config.sounds.point.play()
                # 添加到要删除的列表
                powerups_to_remove.append(powerup)
        
        # 从管理器中删除已收集的道具
        for powerup in powerups_to_remove:
            if powerup in self.powerup_manager.powerups:
                self.powerup_manager.powerups.remove(powerup)

    def update_player_effects(self):
        """
        根据当前激活的效果更新玩家状态
        """
        # 检查每种效果是否已过期
        for power_type in list(PowerUpType):
            if self.powerup_manager.has_effect(power_type):
                # 效果仍然激活，确保效果被应用
                self.player.apply_powerup_effect(power_type)
            else:
                # 效果已过期，移除
                self.player.remove_powerup_effect(power_type)
    
    def render_active_effects(self):
        """
        在屏幕上显示当前激活的效果及其剩余时间
        """
        active_effects = []
        for power_type in PowerUpType:
            if self.powerup_manager.has_effect(power_type):
                remaining_ms = self.powerup_manager.get_remaining_time(power_type)
                if remaining_ms is not None:
                    active_effects.append((power_type, remaining_ms))
        
        # 如果有激活的效果，在屏幕上显示
        if active_effects:
            font = pygame.font.SysFont('Arial', 10)
            y_offset = 10
            
            for power_type, remaining_ms in active_effects:
                remaining_sec = remaining_ms / 1000
                
                # 根据道具类型选择显示文本和颜色
                if power_type == PowerUpType.SPEED_BOOST:
                    text = f"Speed Boost: {remaining_sec:.1f}s"
                    color = (255, 165, 0)  # 橙色
                elif power_type == PowerUpType.INVINCIBLE:
                    text = f"Invincible: {remaining_sec:.1f}s"
                    color = (255, 215, 0)  # 金色
                elif power_type == PowerUpType.SLOW_MOTION:
                    text = f"Slow Motion: {remaining_sec:.1f}s"
                    color = (0, 191, 255)  # 天蓝色
                elif power_type == PowerUpType.SMALL_SIZE:
                    text = f"Small Size: {remaining_sec:.1f}s"
                    color = (147, 112, 219)  # 紫色
                
                # 创建文本表面
                text_surface = font.render(text, True, color)
                text_rect = text_surface.get_rect()
                text_rect.topleft = (10, y_offset)
                
                # 绘制文本
                self.config.screen.blit(text_surface, text_rect)
                
                # 更新下一个文本的位置
                y_offset += 20

    def check_pipe_pass(self):
        """
        检查玩家是否通过管道并更新分数
        """
        # 为每个上管道检查是否通过
        for pipe in self.pipes.upper:
            # 管道中心点
            pipe_centerx = pipe.x + pipe.w/2
            # 检查玩家是否刚刚通过管道中心点
            if (pipe.x < self.player.x < pipe.x + pipe.w) and not hasattr(pipe, 'passed'):
                # 标记该管道已通过
                pipe.passed = True
                # 增加分数
                self.score.add()
                # 播放得分声音
                self.config.sounds.point.play()

    async def play(self):
        """
        主要游戏循环
        """
        # 当玩家开始游戏时
        # 根据游戏模式设置玩家模式
        if self.game_mode == GameMode.REVERSE:
            self.player.set_mode(PlayerMode.REVERSE)  # 设置玩家模式为REVERSE（反向模式）
        elif self.game_mode == GameMode.GHOST:
            self.player.set_mode(PlayerMode.GHOST)  # 设置玩家模式为GHOST（穿越模式）
        elif self.game_mode == GameMode.NIGHT:
            self.player.set_mode(PlayerMode.NIGHT)  # 设置玩家模式为NIGHT（夜间模式）
        elif self.game_mode == GameMode.SPEED:
            self.player.set_mode(PlayerMode.SPEED)  # 设置玩家模式为SPEED（极速模式）
            # 在极速模式下加快管道移动速度
            for pipe in self.pipes.upper + self.pipes.lower:
                pipe.vel_x = -8  # 增加管道速度
        else:
            self.player.set_mode(PlayerMode.NORMAL)  # 设置玩家模式为NORMAL（正常模式）
            
        self.powerup_manager.powerups = []  # 清空道具列表
        self.powerup_manager.active_effects = {}  # 清空活跃效果
        
        # 重置计时器（如果是限时模式）
        if self.game_mode == GameMode.TIMED:
            self.time_remaining = self.time_limit
            
        # 创建字体用于显示剩余时间 - 使用Windows默认字体
        time_font = pygame.font.SysFont('microsoftyahei', 24)  # 微软雅黑
        game_over = False

        while True:
            # 计算帧间隔时间
            current_time = pygame.time.get_ticks()
            delta_time = current_time - self.last_frame_time
            self.last_frame_time = current_time

            for event in pygame.event.get():
                self.check_quit_event(event)  # 检查退出事件
                if event.type == KEYDOWN:
                    print(f"按键按下: {event.key}, pygame.K_m = {pygame.K_m}")
                    
                if self.is_tap_event(event):
                    self.player.flap()  # 玩家点击，执行拍打动作
                elif event.type == KEYDOWN and event.key == pygame.K_m and self.game_mode == GameMode.GHOST:
                    print(f"M键被按下! 游戏模式: {self.game_mode}, 是否为穿越模式: {self.game_mode == GameMode.GHOST}")
                    # 激活穿越模式
                    self.player.activate_ghost()
                    # 检查是否成功激活穿越
                    if self.player.is_ghost_mode and not self.player.ghost_ready:
                        # 穿越：立即摧毁所有屏幕上可见的管道
                        pipes_destroyed = 0
                        for pipe in self.pipes.upper + self.pipes.lower:
                            if not pipe.destroyed and pipe.x > 0 and pipe.x < self.config.window.width:
                                pipe.destroy()
                                pipes_destroyed += 1
                        
                        # 根据摧毁的管道数量，播放对应数量的得分音效
                        if pipes_destroyed > 0:
                            self.config.sounds.point.play()
                            print(f"Ghost activated! {pipes_destroyed} pipes destroyed.")
                    # 穿越：立即摧毁所有管道
                    # for pipe in self.pipes.upper + self.pipes.lower:
                    #     if not pipe.destroyed:
                    #         pipe.destroy()
                    #         self.config.sounds.point.play()
                    # print("Ghost activated! Pipes destroyed.")

            # 限时模式时间更新
            if self.game_mode == GameMode.TIMED:
                self.time_remaining -= delta_time
                if self.time_remaining <= 0:
                    self.time_remaining = 0
                    game_over = True
            
            # 更新道具管理器
            self.powerup_manager.tick(delta_time)
            
            # 检查道具碰撞
            self.check_powerup_collisions()
            
            # 更新玩家状态效果
            self.update_player_effects()
            
            # 检查管道通过情况并更新分数
            self.check_pipe_pass()
            
            self.background.tick()  # 更新背景
            self.floor.tick()  # 更新地面
            self.pipes.tick()  # 更新管道
            self.score.tick()  # 更新得分
            self.player.tick()  # 更新玩家
            
            # 绘制道具
            for powerup in self.powerup_manager.powerups:
                powerup.tick()
                
            # 绘制活跃效果提示
            self.render_active_effects()
            
            # 如果是限时模式，显示剩余时间
            if self.game_mode == GameMode.TIMED:
                seconds_left = max(0, int(self.time_remaining / 1000))
                
                # 创建一个半透明的计时器背景
                timer_bg = pygame.Surface((100, 40), pygame.SRCALPHA)
                alpha = 180  # 透明度
                timer_bg.fill((0, 0, 0, alpha))
                self.config.screen.blit(timer_bg, (self.config.window.width - 110, 5))
                
                # 绘制计时器文本
                time_text = time_font.render(f"Time: {seconds_left}s", True, (255, 255, 255))
                time_rect = time_text.get_rect(center=(self.config.window.width - 60, 25))
                self.config.screen.blit(time_text, time_rect)
                
                # 当时间小于10秒时闪烁显示并添加红色警告效果
                if seconds_left <= 10 and self.time_remaining > 0:
                    # 闪烁效果
                    if (current_time // 500) % 2 == 0:  # 每500毫秒闪烁一次
                        # 创建警告背景
                        warning_bg = pygame.Surface((200, 40), pygame.SRCALPHA)
                        warning_bg.fill((255, 0, 0, 150))  # 半透明红色
                        warning_rect = warning_bg.get_rect(center=(self.config.window.width//2, 50))
                        self.config.screen.blit(warning_bg, warning_rect)
                        
                        # 警告文本
                        warning_text = time_font.render("Time running out!", True, (255, 255, 255))
                        warning_text_rect = warning_text.get_rect(center=(self.config.window.width//2, 50))
                        self.config.screen.blit(warning_text, warning_text_rect)
                        
            # 夜间模式特效
            if self.game_mode == GameMode.NIGHT:
                # 创建一个全屏黑色半透明图层模拟黑夜
                darkness = pygame.Surface((self.config.window.width, self.config.window.height), pygame.SRCALPHA)
                darkness.fill((0, 0, 0, 180))  # 黑色半透明
                
                # 在玩家周围创建一个视野圆圈
                vision_range = self.player.night_vision_range
                pygame.draw.circle(
                    darkness,
                    (0, 0, 0, 0),  # 完全透明
                    (int(self.player.x + self.player.w//2), int(self.player.y + self.player.h//2)),
                    vision_range
                )
                
                # 添加渐变效果到视野边缘
                for i in range(30):
                    pygame.draw.circle(
                        darkness,
                        (0, 0, 0, i * 6),  # 逐渐增加透明度
                        (int(self.player.x + self.player.w//2), int(self.player.y + self.player.h//2)),
                        vision_range + 30 - i
                    )
                
                # 应用黑暗效果
                self.config.screen.blit(darkness, (0, 0))
            
            # 极速模式特效
            if self.game_mode == GameMode.SPEED:
                # 创建速度线效果
                for i in range(10):
                    line_length = random.randint(20, 60)
                    line_y = random.randint(0, self.config.window.height)
                    line_x = random.randint(0, self.config.window.width)
                    line_color = (255, 255, 255, 100)  # 白色半透明
                    
                    pygame.draw.line(
                        self.config.screen,
                        line_color,
                        (line_x, line_y),
                        (line_x - line_length, line_y),
                        2
                    )
                
                # 显示速度提示
                speed_font = pygame.font.SysFont('microsoftyahei', 20)
                speed_text = speed_font.render("极速模式!", True, (255, 255, 0))
                speed_rect = speed_text.get_rect(topright=(self.config.window.width - 20, 20))
                
                # 创建一个闪烁效果
                if pygame.time.get_ticks() % 1000 < 500:
                    self.config.screen.blit(speed_text, speed_rect)
            
            pygame.display.update()  # 刷新显示
            await asyncio.sleep(0)  # 等待下一帧
            self.config.tick()  # 更新游戏配置
            
            # 玩家碰撞检测
            if self.player.collided(self.pipes, self.floor):
                return
            
            # 限时模式结束
            if game_over:
                return

    async def game_over(self):
        """
        玩家死亡并显示游戏结束界面
        """
        self.player.set_mode(PlayerMode.CRASH)  # 设置玩家模式为CRASH（死亡模式）
        self.pipes.stop()  # 停止管道
        self.floor.stop()  # 停止地面

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)  # 检查退出事件
                if self.is_tap_event(event):
                    if self.player.y + self.player.h >= self.floor.y - 1:
                        return  # 如果玩家落到地面，结束游戏

            self.background.tick()  # 更新背景
            self.floor.tick()  # 更新地面
            self.pipes.tick()  # 更新管道
            self.score.tick()  # 更新得分
            self.player.tick()  # 更新玩家
            self.game_over_message.tick()  # 更新游戏结束信息

            self.config.tick()  # 更新游戏配置
            pygame.display.update()  # 刷新显示
            await asyncio.sleep(0)  # 等待下一帧
