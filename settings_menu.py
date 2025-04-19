import pygame
from pygame.math import Vector2
from env import SKINS_DIR
import os

class SettingsMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.menu_width = screen_width * 2 // 3
        self.position = Vector2(-self.menu_width, 0)
        self.animation_speed = 0.08
        self.animation_progress = 0.0
        self.state = "closed"  # closed, opening, opened, closing
        self.font = pygame.font.Font(None, 36)
        
        self.skins = []
        self.skin_dropdown_open = False
        self.selected_keys = {'key1': 'Z', 'key2': 'X', 'smoke': 'C'}
        self.rebinding_key = None
        
    def load_skins(self):
        try:
            self.skins = [d for d in os.listdir(SKINS_DIR) 
                        if os.path.isdir(os.path.join(SKINS_DIR, d))]
        except FileNotFoundError:
            os.makedirs(SKINS_DIR, exist_ok=True)
            self.skins = []
        
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
        
        # Координаты внутри меню
        x_offset = self.position.x + 20
        y_offset = 50
        
        # Заголовок Settings
        title = self.font.render("Settings", True, (255, 255, 255))
        screen.blit(title, (x_offset, y_offset))
        y_offset += 50
        
        # Поиск
        search_rect = pygame.Rect(x_offset, y_offset, self.menu_width - 40, 40)
        pygame.draw.rect(screen, (60, 60, 60), search_rect, border_radius=5)
        search_text = self.font.render("Search...", True, (150, 150, 150))
        screen.blit(search_text, (x_offset + 10, y_offset + 10))
        y_offset += 80
        
        # Скины
        skins_title = self.font.render("Skins", True, (255, 255, 255))
        screen.blit(skins_title, (x_offset, y_offset))
        y_offset += 40
        
        # Кнопка выбора скина
        skin_btn = pygame.Rect(x_offset, y_offset, 200, 40)
        pygame.draw.rect(screen, (80, 80, 80), skin_btn, border_radius=5)
        skin_text = self.font.render("Select Skin ▼", True, (255, 255, 255))
        screen.blit(skin_text, (x_offset + 10, y_offset + 10))
        y_offset += 50
        
        # Выпадающий список скинов
        if self.skin_dropdown_open:
            for i, skin in enumerate(self.skins):
                skin_rect = pygame.Rect(x_offset, y_offset + i*50, 200, 40)
                pygame.draw.rect(screen, (60, 60, 60), skin_rect, border_radius=5)
                skin_name = self.font.render(skin, True, (255, 255, 255))
                screen.blit(skin_name, (x_offset + 10, y_offset + i*50 + 10))
            y_offset += len(self.skins) * 50
            
        y_offset += 50
        
        # Настройки ввода
        input_title = self.font.render("Input", True, (255, 255, 255))
        screen.blit(input_title, (x_offset, y_offset))
        y_offset += 40
        
        # Кнопки переназначения
        keys = [
            ("Primary Key", 'key1'),
            ("Secondary Key", 'key2'),
            ("Smoke Key", 'smoke')
        ]
        
        for label, key_type in keys:
            btn_rect = pygame.Rect(x_offset, y_offset, 200, 40)
            color = (100, 100, 200) if self.rebinding_key == key_type else (80, 80, 80)
            pygame.draw.rect(screen, color, btn_rect, border_radius=5)
            key_text = self.font.render(f"{label}: {self.selected_keys[key_type]}", True, (255, 255, 255))
            screen.blit(key_text, (x_offset + 10, y_offset + 10))
            y_offset += 50

    def handle_click(self, pos):
        x_offset = self.position.x + 20
        y_offset = 140  # Позиция кнопки скинов
        
        # Клик по кнопке скинов
        skin_btn = pygame.Rect(x_offset, y_offset, 200, 40)
        if skin_btn.collidepoint(pos):
            self.skin_dropdown_open = not self.skin_dropdown_open
            
        # Клик по выпадающему списку
        if self.skin_dropdown_open:
            for i, skin in enumerate(self.skins):
                skin_rect = pygame.Rect(x_offset, y_offset + 50 + i*50, 200, 40)
                if skin_rect.collidepoint(pos):
                    print(f"Selected skin: {skin}")
                    self.skin_dropdown_open = False
                    
        # Клик по кнопкам переназначения
        y_offset = 340  # Позиция первой кнопки ввода
        for key_type in ['key1', 'key2', 'smoke']:
            btn_rect = pygame.Rect(x_offset, y_offset, 200, 40)
            if btn_rect.collidepoint(pos):
                self.rebinding_key = key_type
                return
            y_offset += 50

    def handle_key_event(self, event):
        if self.rebinding_key and event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key).upper()
            self.selected_keys[self.rebinding_key] = key_name
            self.rebinding_key = None