import pygame
import os
from env import *
import threading
import math


class MapPull:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.maps = []
        self.previews = {}
        self.loading_thread = None
        self.scroll_offset = 0
        self.max_scroll = 0
        
        self.target_scroll = 0
        self.current_scroll = 0
        self.animation_speed = 0.025
        self.item_spacing = 10
        self.scroll_speed = 1  # Количество карт за прокрутку
        self.selected_index = -1
        self.is_animating = False

        # Параметры отображения
        self.item_width = 400
        self.item_height = 200
        self.right_margin = 50
        self.base_scale = 0.5
        self.selected_scale = 1.0
        
    def _max_scroll(self):
        return max(0, len(self.maps)*(self.item_height + self.item_spacing) - self.screen_height)

    def load_previews(self, maps):
        self.maps = maps
        for map_folder in maps:
            map_path = os.path.join(MAPS_DIR, map_folder)
            preview_path = self.find_preview_image(map_path)
            if preview_path:
                self.load_preview_async(map_folder, preview_path)

    def find_preview_image(self, map_path):
        # Без изменений из предыдущей версии
        for f in os.listdir(map_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                return os.path.join(map_path, f)
        return None

    def load_preview_async(self, map_name, path):
        # Без изменений из предыдущей версии
        if map_name not in self.previews:
            self.previews[map_name] = None
            self.loading_thread = threading.Thread(
                target=self._load_preview_thread,
                args=(map_name, path)
            )
            self.loading_thread.start()

    def _load_preview_thread(self, map_name, path):
        # Без изменений из предыдущей версии
        try:
            image = pygame.image.load(path)
            image = pygame.transform.scale(image, (self.item_width, self.item_height))
            self.previews[map_name] = image
        except Exception as e:
            print(f"Ошибка загрузки превью: {str(e)}")

    def update(self, scroll_delta):
        scroll_step = scroll_delta * (self.item_height + self.item_spacing) * self.scroll_speed
        if not self.is_animating:
            self.target_scroll += scroll_step
            self.target_scroll = max(0, min(self.target_scroll, self._max_scroll()))
        
        # Интерполяция прокрутки
        self.current_scroll += (self.target_scroll - self.current_scroll) * self.animation_speed
        self.is_animating = abs(self.target_scroll - self.current_scroll) > 1.0
        

    def draw(self, screen):
        if not self.maps:
            return

        center_y = self.screen_height // 2
        half_height = self.screen_height // 2
        
        for i, map_folder in enumerate(self.maps):
            # Позиция с учетом анимации
            y_pos = i * (self.item_height + self.item_spacing) - self.current_scroll
            item_center_y = y_pos + self.item_height//2
            
            # Нелинейный масштаб
            distance = abs(item_center_y - center_y)
            scale = self.base_scale + (self.selected_scale - self.base_scale) * math.exp(-distance / 150)
            
            # Анимация выбора
            if i == self.selected_index:
                scale = self.selected_scale + 0.1 * math.sin(pygame.time.get_ticks() / 200)
                
            # Отрисовка карты
            self.draw_map_item(screen, map_folder, i, y_pos, scale)
            
            self.current_scroll += (self.target_scroll - self.current_scroll) * self.animation_speed
            self.is_animating = abs(self.target_scroll - self.current_scroll) > 1.0

    
    
    def ease_out_quad(self, t):
        return t*(2-t)
    
    def draw_map_item(self, screen, map_folder, index, y_pos, scale):
        x = self.screen_width - self.item_width - self.right_margin
        scaled_w = int(self.item_width * scale)
        scaled_h = int(self.item_height * scale)
        
        if self.previews.get(map_folder):
            scaled_preview = pygame.transform.scale(self.previews[map_folder], (scaled_w, scaled_h))
            rect = scaled_preview.get_rect()
            rect.x = x + (self.item_width - scaled_w) // 2
            rect.y = y_pos
            screen.blit(scaled_preview, rect)
            
            if index == self.selected_index:
                pygame.draw.rect(screen, (255, 215, 0), rect, 3)
                
                
    def get_clicked_map(self, mouse_pos):
        for i, map_folder in enumerate(self.maps):
            y_pos = i * (self.item_height + self.item_spacing) - self.current_scroll
            rect = pygame.Rect(
                self.screen_width - self.item_width - self.right_margin,
                y_pos,
                self.item_width,
                self.item_height
            )
            if rect.collidepoint(mouse_pos):
                # Анимируем к центру
                self.selected_index = i
                self.target_scroll = i * (self.item_height + self.item_spacing) - (self.screen_height//2 - self.item_height//2)
                return map_folder
        return None
