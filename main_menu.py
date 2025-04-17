import pygame
from env import *

class MainMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.buttons = []
        self.animation_progress = 0  # 0-1
        self.animation_speed = 0.1
        self.state = "closed"  # или "opened"
        
        # Главная круглая кнопка
        self.main_button = {
            'rect': pygame.Rect(0, 0, 200, 200),
            'color': BUTTON_COLOR,
            'target_pos': (screen_width//2, screen_height//2)
        }
        self.main_button['rect'].center = self.main_button['target_pos']
        
        # Второстепенные кнопки
        self.sub_buttons = [
            {'text': "Играть", 'pos': (0, 0), 'visible': False},
            {'text': "Настройки", 'pos': (0, 0), 'visible': False},
            {'text': "Выйти", 'pos': (0, 0), 'visible': False}
        ]

    def update(self):
        if self.state == "opening":
            self.animation_progress = min(1, self.animation_progress + self.animation_speed)
            if self.animation_progress == 1:
                self.state = "opened"
        elif self.state == "closing":
            self.animation_progress = max(0, self.animation_progress - self.animation_speed)
            if self.animation_progress == 0:
                self.state = "closed"

        # Анимация главной кнопки
        start_pos = (self.screen_width//2, self.screen_height//2)
        target_pos = (self.screen_width//4, self.screen_height//2)
        current_x = start_pos[0] + (target_pos[0] - start_pos[0]) * self.animation_progress
        current_y = start_pos[1] + (target_pos[1] - start_pos[1]) * self.animation_progress
        self.main_button['rect'].center = (current_x, current_y)

        # Позиции второстепенных кнопок
        for i, btn in enumerate(self.sub_buttons):
            start_x = self.screen_width + 100
            target_x = self.screen_width - 200
            current_x = start_x + (target_x - start_x) * self.animation_progress
            btn['pos'] = (current_x, self.screen_height//2 - 100 + i*100)
            btn['visible'] = self.animation_progress > 0

    def draw(self, screen):
        # Рисуем главную кнопку
        pygame.draw.circle(screen, 
                         self.main_button['color'], 
                         self.main_button['rect'].center, 
                         self.main_button['rect'].width//2,
                         2)

        # Рисуем второстепенные кнопки
        font = pygame.font.Font(None, 36)
        for btn in self.sub_buttons:
            if btn['visible']:
                text = font.render(btn['text'], True, BUTTON_COLOR)
                text_rect = text.get_rect(center=btn['pos'])
                screen.blit(text, text_rect)

    def handle_click(self, pos):
        font = pygame.font.Font(None, 36)
        if self.state == "closed":
            if self.main_button['rect'].collidepoint(pos):
                self.state = "opening"
                return "open_menu"
        elif self.state == "opened":
            for i, btn in enumerate(self.sub_buttons):
                text = font.render(btn['text'], True, BUTTON_COLOR)
                text_rect = text.get_rect(center=btn['pos'])
                if text_rect.collidepoint(pos):
                    return ["play", "settings", "exit"][i]
        return None