import pygame
import os
from env import *
import threading


class MapPull:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.maps = []
        self.previews = {}
        self.loading_thread = None
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Параметры отображения
        self.item_width = 400
        self.item_height = 200
        self.right_margin = 50
        self.spacing = 5
        self.base_scale = 0.5
        self.selected_scale = 1.0
        self.scroll_speed = 40

    def load_previews(self, maps):
        self.maps = maps
        self.max_scroll = max(0, len(maps)*(self.item_height + self.spacing) - self.screen_height)
        
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

    def update(self, scroll):
        self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + scroll * self.scroll_speed))

    def draw(self, screen):
        if not self.maps:
            return

        center_y = self.screen_height // 2
        half_height = self.screen_height // 2
        
        for i, map_folder in enumerate(self.maps):
            y_pos = i * (self.item_height + self.spacing) - self.scroll_offset
            item_center_y = y_pos + self.item_height//2
            
            # Рассчитываем масштаб
            distance = abs(item_center_y - center_y)
            scale = self.base_scale + (self.selected_scale - self.base_scale) * (1 - distance / half_height)
            scale = max(self.base_scale, min(self.selected_scale, scale))
            
            # Позиция элемента
            x = self.screen_width - self.item_width - self.right_margin
            y = y_pos
            
            # Получаем превью
            preview = self.previews.get(map_folder)
            if preview:
                scaled_w = int(self.item_width * scale)
                scaled_h = int(self.item_height * scale)
                scaled_preview = pygame.transform.scale(preview, (scaled_w, scaled_h))
                
                # Позиционирование
                rect = scaled_preview.get_rect()
                rect.x = x + (self.item_width - scaled_w) // 2
                rect.y = y
                
                # Отрисовка
                screen.blit(scaled_preview, rect)
                
                # Рамка выделения
                if distance < scaled_h:
                    pygame.draw.rect(
                        screen, 
                        (255, 255, 255), 
                        rect, 
                        2
                    )

    def get_clicked_map(self, mouse_pos):
        """Возвращает карту по позиции клика"""
        for i, map_folder in enumerate(self.maps):
            y_pos = i * (self.item_height + self.spacing) - self.scroll_offset
            rect = pygame.Rect(
                self.screen_width - self.item_width - self.right_margin,
                y_pos,
                self.item_width,
                self.item_height
            )
            if rect.collidepoint(mouse_pos):
                return map_folder
        return None