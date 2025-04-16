import pygame
from enum import Enum
import threading
import sys
import os
import zipfile
import unittest
import shutil
from pygame.math import Vector2
import math

# Конфигурация путей
BUTTON_COLOR = (255, 255, 255)
BUTTON_HOVER_COLOR = (200, 200, 200)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, "posu", "maps")

class GameStates(Enum):
    MAIN_MENU = 0
    MAP_SELECT = 1
    PLAYING = 2

# Инициализация Pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()


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

class GameState:
    def __init__(self):
        self.WH = (1920,1080)
        self.approach_circle_surface = pygame.Surface(self.WH, pygame.SRCALPHA)
        self.font = pygame.font.Font(None, 24)  # Для счета
        self.combo_font = pygame.font.Font(None, 48)  # Для комбо
        self.slider_body_width = 15
        self.slider_border_width = 3

        #self.hit_window = 1500
        self.hit_objects = []  # Все объекты карты
        self.active_objects = []  # Объекты в процессе анимации
        self.animation_duration = 500
        self.approach_circle_color = (255, 255, 255)  # Белый цвет
        self.fade_circle_color = (255, 200, 0)        # Желтый для исчезновения
        self.slider_body_color = (100, 100, 100)      # Серый
        self.slider_border_color = (0, 255, 0) 
        self.hitcircle_color = (255, 255, 255)  # Белый цвет основного круга
        self.hitcircle_radius = 50
        self.hit_animation = {
            'circle': {
                'max_radius': 50,
                'duration': 300
            },
            'slider': {
                'tick_spacing': 50,
                'tick_radius': 5
            }
        }
        self.ar = 5.5  # Значение по умолчанию
        self.cs = 3.3  # Значение по умолчанию
        self.base_hitcircle_radius = self.cs*16  # Базовый размер для CS=4
        self.hp_drain_rate = 5.0
        self.overall_difficulty = 8.0
        self.slider_multiplier = 1.0
        self.slider_tick_rate = 1.0
        self.update_metrics()
        self.reset()
        
    def draw_main_circle(self, obj, surface):
        """Отрисовка основного круга"""
        pygame.draw.circle(
            surface,
            self.hitcircle_color,
            (obj['x'], obj['y']),
            int(self.hitcircle_radius),
            2  # Толщина обводки
        )

        
    def draw_approach_circle(self, obj, progress, surface):
        """Рисуем подходный круг с анимацией сжатия"""
        base_radius = self.hitcircle_radius
        target_radius = base_radius * 0.5  # Минимальный радиус
        current_radius = base_radius - (base_radius - target_radius) * progress
        
        # Рисуем белое кольцо
        pygame.draw.circle(
            surface,
            self.approach_circle_color,
            (obj['x'], obj['y']),
            int(current_radius),
            2  # Толщина линии
        )

    def draw_fading_circle(self, obj, alpha, surface):
        """Рисуем исчезающий круг после нажатия"""
        fade_surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(
            fade_surface,
            (*self.fade_circle_color, alpha),  # RGBA
            (100, 100),
            self.hitcircle_radius,
            2
        )
        surface.blit(fade_surface, (obj['x'] - 100, obj['y'] - 100))

    def draw_slider(self, obj, progress, surface):
        """Рисуем слайдер с анимированным ползунком"""
        # Тело слайдера
        pygame.draw.line(
            surface,
            self.slider_body_color,
            (obj['start_x'], obj['start_y']),
            (obj['end_x'], obj['end_y']),
            self.slider_body_width
        )

        # Границы
        pygame.draw.line(
            surface,
            self.slider_border_color,
            (obj['start_x'], obj['start_y']),
            (obj['end_x'], obj['end_y']),
            self.slider_border_width
        )

        # Ползунок
        t = min(1.0, max(0.0, progress))
        x = obj['start_x'] + (obj['end_x'] - obj['start_x']) * t
        y = obj['start_y'] + (obj['end_y'] - obj['start_y']) * t
        pygame.draw.circle(
            surface,
            self.slider_border_color,
            (int(x), int(y)),
            10  # Размер ползунка
        )
        
    def update_metrics(self):
        """Обновляем параметры на основе сложности"""
        # Размер круга (CS)
        self.hitcircle_radius = int(64 * (1 - 0.07 * (self.cs - 4)))
        
        # Время подхода (AR)
        if self.ar <= 5:
            self.approach_time = 1800 - self.ar * 120
        else:
            self.approach_time = 1200 - (self.ar - 5) * 150
        
        # Хит-окно (OD)

        self.hit_window_300 = 80 - 6 * self.overall_difficulty
        self.hit_window_100 = 140 - 8 * self.overall_difficulty
        self.hit_window_50 = 200 - 10 * self.overall_difficulty
        
        # Слайдеры
        self.hit_window = self.hit_window_300
        self.hit_animation['slider']['tick_spacing'] = 50 / self.slider_tick_rate
        
    def reset(self):
        self.hp = 100
        self.score = 0
        self.combo = 0
        self.hit_objects = []
        self.active_objects = []
        self.start_time = 0
        self.font = pygame.font.Font(None, 36)
        self.spinner_rotations = 0
        self.last_mouse_pos = (0, 0)

    def update(self, current_time):
        # Добавляем объекты за approach_time до их start_time
        
        self.hp = max(0, self.hp - self.hp_drain_rate * 0.01)
        
        # Проверяем пропущенные объекты
        for obj in self.active_objects:
            if obj['type'] == 'circle' and not obj.get('hit'):
                if current_time > obj['start_time'] + self.hit_window_50:
                    self.combo = 0
                    self.hp = max(0, self.hp - 5)
                    obj['hit'] = True
                    
        new_objects = [
            obj for obj in self.hit_objects
            if (obj['start_time'] - self.approach_time) <= current_time 
            and obj not in self.active_objects
        ]
        self.active_objects.extend(new_objects)
        
        # Удаление после окончания hit_window
        self.active_objects = [
            obj for obj in self.active_objects
            if current_time <= obj['start_time'] + self.hit_window
        ]

    def draw(self, screen):
        screen.fill((0, 0, 0))
        
        # Отрисовка объектов
        current_time = pygame.time.get_ticks() - self.start_time
        
        for obj in self.active_objects:
            # Общие параметры для всех объектов
            obj_time = current_time - obj['start_time']
            total_time = obj['end_time'] - obj['start_time']
            progress = obj_time / total_time if total_time > 0 else 0.0
            
            #if obj['start_time'] - self.approach_time <= current_time < obj['start_time']:
            #    self.draw_approach_circle(obj, current_time, screen)
            #
            #if current_time >= obj['start_time']:
            #    self.draw_main_circle(obj, screen)
            
            if obj.get('hit'):
                hit_progress = (current_time - obj['hit_time']) / self.hit_animation['circle']['duration']
                if hit_progress < 1:
                    radius = 30 + self.hit_animation['circle']['max_radius'] * hit_progress
                    alpha = int(255 * (1 - hit_progress))
                    pygame.draw.circle(screen, (255, 255, 0, alpha),
                                    (obj['x'], obj['y']), int(radius), 2)
            
            # Отрисовка по типам
            if obj['type'] == 'circle':
                self.draw_main_circle(obj, screen)
                if current_time < obj['end_time']:
                    self.draw_approach_circle(obj, progress, screen)
                else:
                    # Анимация исчезновения
                    fade_time = current_time - obj['end_time']
                    alpha = 255 - int(255 * fade_time / self.animation_duration)
                    if alpha > 0:
                        self.draw_fading_circle(obj, alpha, screen)

            elif obj['type'] == 'slider':
                self.draw_slider(obj, progress, screen)


            elif obj['type'] == 'spinner':
                pygame.draw.arc(screen, (0, 0, 255),
                                (obj['center_x']-100, obj['center_y']-100, 200, 200),
                                0, math.radians(self.spinner_rotations % 360), 5)
        
        # Отрисовка HUD
        self.draw_hp_bar(screen)
        self.draw_score(screen)
        self.draw_combo(screen)
        
    
    def draw_hp_bar(self, screen):
        # Параметры HP бара
        x, y = 10, 10
        max_width = 200
        height = 20
        outline_color = (255, 255, 255)
        hp_color = (76, 175, 80)  # Зеленый цвет как в osu!
        
        # Рассчитываем текущую ширину
        current_hp = max(0, min(self.hp, 100))
        fill_width = max_width * (current_hp / 100)
        
        # Рисуем обводку
        outline_points = [
            (x, y),
            (x + max_width - 9, y),
            (x + max_width, y + height),
            (x, y + height),
            (x, y)
        ]
        pygame.draw.polygon(screen, outline_color, outline_points, 2)
        
        # Рисуем заполнение
        if fill_width > 0:
            if fill_width >= 9:
                fill_points = [
                    (x, y),
                    (x + fill_width - 9, y),
                    (x + fill_width, y + height),
                    (x, y + height)
                ]
            else:
                fill_points = [
                    (x, y),
                    (x + fill_width, y),
                    (x + fill_width, y + height),
                    (x, y + height)
                ]
            pygame.draw.polygon(screen, hp_color, fill_points)

    def draw_score(self, screen):
        score_text = "{:,}".format(self.score)
        text_surface = self.font.render(score_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 35))  # Под HP баром

    def draw_combo(self, screen):
        combo_text = f"{self.combo}x"
        # Создаем шрифт для комбо
        combo_font = pygame.font.Font(None, 48)
        
        # Рендерим тень
        shadow = combo_font.render(combo_text, True, (0, 0, 0))
        shadow_rect = shadow.get_rect()
        shadow_rect.x = 20
        shadow_rect.bottom = screen.get_height() - 20
        
        # Рендерим основной текст
        text = combo_font.render(combo_text, True, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.x = shadow_rect.x + 2
        text_rect.y = shadow_rect.y + 2
        
        # Рисуем элементы
        screen.blit(shadow, shadow_rect)
        screen.blit(text, text_rect)

class MapLoader:
    @staticmethod
    def process_maps():
        """Распаковывает новые .osz архивы и удаляет оригиналы"""
        os.makedirs(MAPS_DIR, exist_ok=True)
        
        for item in os.listdir(MAPS_DIR):
            item_path = os.path.join(MAPS_DIR, item)
            
            if item.endswith(".osz"):
                map_name = os.path.splitext(item)[0]
                extract_path = os.path.join(MAPS_DIR, map_name)
                
                try:
                    with zipfile.ZipFile(item_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    os.remove(item_path)
                    print(f"Распаковано: {map_name}")
                except (zipfile.BadZipFile, PermissionError) as e:
                    print(f"Ошибка распаковки {item}: {str(e)}")

class OsuParser:
    @staticmethod
    def parse_map(map_folder):
        osu_files = [f for f in os.listdir(map_folder) if f.endswith(".osu")]
        if not osu_files:
            return None, [], {'hp':5.0, 'ar':9.0, 'cs':4.0, 'od':8.0, 'slider_multiplier':1.0, 'slider_tick_rate':1.0}

        osu_path = os.path.join(map_folder, osu_files[0])
        audio_file = None
        hit_objects = []
        difficulty = {
            'hp': 5.0,
            'ar': 9.0,
            'cs': 4.0,
            'od': 8.0,
            'slider_multiplier': 1.0,
            'slider_tick_rate': 1.0
        }
        current_section = None

        try:
            with open(osu_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith('AudioFilename:'):
                        audio_file = line.split(':')[1].strip()
                    elif line.startswith('[Difficulty]'):
                        current_section = 'difficulty'
                    elif line.startswith('[HitObjects]'):
                        current_section = 'hitobjects'
                    elif line.startswith('['):
                        current_section = None

                    if current_section == 'difficulty':
                        if line.startswith('HPDrainRate'):
                            difficulty['hp'] = float(line.split(':')[1].strip())
                        elif line.startswith('CircleSize'):
                            difficulty['cs'] = float(line.split(':')[1].strip())
                        elif line.startswith('OverallDifficulty'):
                            difficulty['od'] = float(line.split(':')[1].strip())
                        elif line.startswith('ApproachRate'):
                            difficulty['ar'] = float(line.split(':')[1].strip())
                        elif line.startswith('SliderMultiplier'):
                            difficulty['slider_multiplier'] = float(line.split(':')[1].strip())
                        elif line.startswith('SliderTickRate'):
                            difficulty['slider_tick_rate'] = float(line.split(':')[1].strip())

                    if current_section == 'hitobjects' and line:
                        parts = line.split(',')
                        if len(parts) < 4:
                            continue
                        
                        try:
                            obj_type = int(parts[3])
                            if obj_type & 1:  # Circle
                                hit_objects.append({
                                    'type': 'circle',
                                    'x': int(int(parts[0]) * 1920 / 512),
                                    'y': int(int(parts[1]) * 1080 / 384),
                                    'start_time': int(parts[2]),
                                    'end_time': int(parts[2]) + 100,
                                    'hit': False,  # Добавляем начальное состояние
                                    'hit_time': 0,
                                    'start_time': int(parts[2]),
                                    'end_time': int(parts[2]) + 100
                                })
                        except (ValueError, IndexError):
                            continue

        except Exception as e:
            print(f"Ошибка парсинга карты: {str(e)}")
            return None, [], difficulty

        audio_path = os.path.join(map_folder, audio_file) if audio_file else None
        
        if audio_file:
            # Ищем аудио файл в папке карты
            for root, dirs, files in os.walk(map_folder):
                if audio_file in files:
                    audio_path = os.path.join(root, audio_file)
                    break
            # Проверяем существование файла
            if not audio_path or not os.path.isfile(audio_path):
                audio_path = None
                
        return audio_path, hit_objects, difficulty
    
class InputHandler:
    @staticmethod
    def handle_input(game_state, current_time):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # Левая кнопка нажата
            mouse_pos = pygame.mouse.get_pos()
            hit_detected = False
            
            # Проверяем все активные объекты
            for obj in game_state.active_objects:
                if obj.get('hit'):
                    continue
                
                # Для кругов
                if obj['type'] == 'circle':
                    # Рассчитываем расстояние до центра
                    dx = obj['x'] - mouse_pos[0]
                    dy = obj['y'] - mouse_pos[1]
                    distance = math.hypot(dx, dy)
                    
                    # Проверяем попадание во временное окно
                    time_diff = abs(current_time - obj['start_time'])
                    
                    if distance <= game_state.hitcircle_radius:
                        if time_diff <= game_state.hit_window_300:
                            game_state.score += 300
                            game_state.combo += 1
                            hit_detected = True
                        elif time_diff <= game_state.hit_window_100:
                            game_state.score += 100
                            game_state.combo += 1
                            hit_detected = True
                        elif time_diff <= game_state.hit_window_50:
                            game_state.score += 50
                            hit_detected = True
                        
                        if hit_detected:
                            obj['hit'] = True
                            game_state.hp = min(100, game_state.hp + 2)
                            break
                            
            # Штраф за промах
            if not hit_detected:
                game_state.combo = 0
                game_state.hp = max(0, game_state.hp - 5)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        
        # Обработка слайдеров
        if mouse_pressed[0]:
            for obj in game_state.active_objects:
                if obj['type'] == 'slider':
                    progress = (current_time - obj['start_time']) / (obj['end_time'] - obj['start_time'])
                    current_x = obj['start_x'] + (obj['end_x'] - obj['start_x']) * progress
                    current_y = obj['start_y'] + (obj['end_y'] - obj['start_y']) * progress
                    distance = Vector2(mouse_pos).distance_to((current_x, current_y))
                    
                    if distance > 50:
                        game_state.combo = 0
                        game_state.hp = max(0, game_state.hp - 5)

class Game:
    def __init__(self):
        self.maps = []
        self.current_state = GameStates.MAIN_MENU
        self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
        self.main_menu = MainMenu(*self.screen.get_size())
        self.map_pull = MapPull(*self.screen.get_size())
        
        # Инициализация новых атрибутов
        self.current_map_index = 0
        self.game_state = None
        
        self.load_maps()
        
        # Инициализация превью и аудио
        if self.maps:
            self.map_pull.load_previews(self.maps)
            self.load_current_map_audio()
        
    def load_maps(self):
        MapLoader.process_maps()
        self.maps = [
            d for d in os.listdir(MAPS_DIR)
            if os.path.isdir(os.path.join(MAPS_DIR, d))
        ]
        # Загружаем аудио первой карты при запуске
        if self.maps:
            self.load_current_map_audio()
            
    def load_current_map_audio(self):
        """Загружаем аудио текущей выбранной карты"""

        map_folder = os.path.join(MAPS_DIR, self.maps[self.current_map_index])
        audio_path, _, _ = OsuParser.parse_map(map_folder)
        if audio_path and os.path.isfile(audio_path):
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play(-1)  # Зацикливаем воспроизведение
            except pygame.error as e:
                print(f"Ошибка загрузки аудио: {str(e)}")
                
    def start_game(self):
        """Запуск игры с полным сбросом состояния"""
        # Создаем новое состояние игры
        self.game_state = GameState()
        
        # Загружаем данные карты
        map_folder = os.path.join(MAPS_DIR, self.maps[self.current_map_index])
        audio_path, hit_objects, difficulty = OsuParser.parse_map(map_folder)
        
        # Настройка параметров сложности
        self.game_state.ar = difficulty['ar']
        self.game_state.cs = difficulty['cs']
        self.game_state.overall_difficulty = difficulty['od']
        self.game_state.update_metrics()
        
        # Сортируем объекты по времени
        self.game_state.hit_objects = sorted(
            hit_objects, 
            key=lambda x: x['start_time']
        )
        
        # Сброс таймера
        self.game_state.start_time = pygame.time.get_ticks()
        
        # Загрузка аудио
        if audio_path and os.path.exists(audio_path):
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Audio error: {e}")
        
        # Переход в игровое состояние
        self.current_state = GameStates.PLAYING
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if self.current_state == GameStates.MAIN_MENU:
                    result = self.main_menu.handle_click(pos)
                    if result == "play":
                        # Переходим в меню выбора карт
                        self.current_state = GameStates.MAP_SELECT
                    elif result == "exit":
                        pygame.quit()
                        sys.exit()
                        
                elif self.current_state == GameStates.MAP_SELECT:
                    # Запускаем игру ТОЛЬКО при клике на карту
                    selected_map = self.map_pull.get_clicked_map(pos)
                    if selected_map:
                        self.current_map_index = self.maps.index(selected_map)
                        self.start_game()
                    
    def draw_main_menu(self):
        self.screen.fill((0, 0, 0))
        self.main_menu.draw(self.screen)

    def draw_map_select(self):
        self.screen.fill((0, 0, 0))
        self.map_pull.draw(self.screen)
        
        
    def run(self, map_index=0):
        if not self.maps:
            print("Нет доступных карт в posu/maps/!")
            return
            
        map_folder = os.path.join(MAPS_DIR, self.maps[map_index])
        audio_path, hit_objects, difficulty = OsuParser.parse_map(map_folder)
        
        
        if not audio_path or not hit_objects:
            print("Ошибка загрузки карты!")
            return
        
        game_state = GameState()
        game_state.ar = difficulty['ar']
        game_state.cs = difficulty['cs']
        game_state.hp_drain_rate = difficulty['hp']
        game_state.overall_difficulty = difficulty['od']
        game_state.slider_multiplier = difficulty['slider_multiplier']
        game_state.slider_tick_rate = difficulty['slider_tick_rate']
        game_state.update_metrics()
        screen = pygame.display.set_mode(game_state.WH, pygame.FULLSCREEN)
        clock = pygame.time.Clock()
        game_state.hit_objects = hit_objects
        game_state.start_time = pygame.time.get_ticks()
        
        # Загрузка аудио
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
        except pygame.error as e:
            print(f"Ошибка загрузки аудио: {str(e)}")
            return
            
        running = True
        while running:
            dt = clock.tick(60)
            self.handle_events()
            
            if self.current_state == GameStates.MAIN_MENU:
                self.main_menu.update()
                self.draw_main_menu()
            elif self.current_state == GameStates.MAP_SELECT:
                self.draw_map_select()
            elif self.current_state == GameStates.PLAYING:
                # Обновление и отрисовка игрового процесса
                current_time = pygame.time.get_ticks() - self.game_state.start_time
                self.game_state.update(current_time)
                InputHandler.handle_input(self.game_state, current_time)
                self.game_state.draw(self.screen)
            
            pygame.display.flip()
            
if __name__ == "__main__":
    # Запуск тестов
    tests = unittest.TestLoader().discover('tests')
    test_result = unittest.TextTestRunner().run(tests)
    
    if not test_result.wasSuccessful():
        print("\nТесты не пройдены!")
        choice = input("Продолжить запуск? (y/n): ")
        if choice.lower() != 'y':
            sys.exit()
            
    # Запуск игры
    game = Game()
    if game.maps:
        game.run(0)
    else:
        print("Поместите .osz файлы в posu/maps/ и перезапустите игру!")