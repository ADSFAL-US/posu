import pygame
from pygame.math import Vector2

class SettingsMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.menu_width = screen_width * 2 // 3
        self.position = Vector2(-self.menu_width, 0)
        self.animation_speed = 0.08
        self.animation_progress = 0.0
        self.state = "closed"  # closed, opening, opened, closing
        
    def open_menu(self):
        self.state = "opening"
        self.animation_progress = 0.0
        
    def close_menu(self):
        if self.state == "opened" or self.state == "opening":
            self.state = "closing"
            self.animation_progress = 1.0  # Начинаем с полного прогресса
    
    def update(self):
        if self.state == "opening":
            # Открытие: быстро → медленно (ease-out)
            self.animation_progress += self.animation_speed
            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                self.state = "opened"
            
            t = 1 - (1 - self.animation_progress) ** 2
            self.position.x = -self.menu_width + t * self.menu_width
            
        elif self.state == "closing":
            # Закрытие: медленно → быстро (ease-in)
            self.animation_progress -= self.animation_speed
            if self.animation_progress <= 0.0:
                self.animation_progress = 0.0
                self.state = "closed"
            
            t = self.animation_progress ** 2
            self.position.x = -self.menu_width + t * self.menu_width
    
    def draw(self, screen):
        if self.state == "closed":
            return
            
        # Темный фон
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        # Панель меню
        panel = pygame.Surface((self.menu_width, self.screen_height))
        panel.fill((30, 30, 30))
        screen.blit(panel, self.position)