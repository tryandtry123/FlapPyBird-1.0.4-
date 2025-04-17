import math
import pygame
from ..utils import GameConfig
from .entity import Entity


class WelcomeMessage(Entity):
    """
    欢迎信息类
    """
    def __init__(self, config: GameConfig) -> None:
        """
        初始化欢迎信息
        :param config: 游戏配置
        """
        # 使用更精美的欢迎界面图片
        image = config.images.welcome_message
        
        # 添加动画效果
        self.animation_frames = 0
        self.max_animation_frames = 30
        self.original_y = int(config.window.height * 0.12)
        
        super().__init__(
            config=config,
            image=image,
            x=(config.window.width - image.get_width()) // 2,
            y=self.original_y,
        )
    
    def update(self):
        """更新欢迎信息的动画效果"""
        self.animation_frames = (self.animation_frames + 1) % self.max_animation_frames
        # 添加上下浮动的动画效果
        self.y = self.original_y + math.sin(self.animation_frames * 0.1) * 5
        
    def draw(self, surface):
        """绘制欢迎信息"""
        # 添加阴影效果
        shadow_surf = pygame.Surface((self.image.get_width()+4, self.image.get_height()+4), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        surface.blit(shadow_surf, (self.x-2, self.y-2))
        
        # 绘制主体
        super().draw(surface)
