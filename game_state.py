import pygame
import math
from pygame.math import Vector2


class GameState:
    def __init__(self):
        #self.current_skin = skin_name or "default"
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
            if obj['type'] == 'circle' and not obj.get('hit') and not obj.get('missed'):
                if current_time > obj['start_time'] + self.hit_window_50:
                    self.combo = 0
                    self.hp = max(0, self.hp - 5)
                    obj['missed'] = True
                    
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


    def draw_prediction_line(self, screen):
        current_time = pygame.time.get_ticks() - self.start_time
        
        # Найти последний ВИДИМЫЙ объект (с учетом анимации исчезновения)
        prev_obj = None
        for obj in reversed(self.hit_objects):
            obj_end_time = obj['end_time'] + self.animation_duration  # Учитываем анимацию
            if obj_end_time > current_time and obj['start_time'] <= current_time:
                prev_obj = obj
                break
                
        # Найти следующий объект, который должен появиться
        next_obj = None
        for obj in self.hit_objects:
            if obj['start_time'] > current_time:
                next_obj = obj
                break

        # Рисовать только если оба объекта существуют и предыдущий еще виден
        if prev_obj and next_obj and (current_time <= prev_obj['end_time'] + self.animation_duration):
            # Рассчитать прогресс исчезновения линии
            time_since_end = current_time - prev_obj['end_time']
            fade_duration = 50  # Время исчезновения линии после ноты

            # Нормализация значений
            progress = max(0.0, min(1.0, time_since_end / fade_duration))
            alpha = 255 - int(255 * progress)

            # Параметры линии
            line_color = (255, 255, 255, alpha)
            line_width = 3
            # Отрисовка
            pygame.draw.line(
                screen,
                line_color,
                (prev_obj['x'], prev_obj['y']),
                (next_obj['x'], next_obj['y']),
                line_width
            )


    def draw(self, screen):
        screen.fill((0, 0, 0))
        
        # Отрисовка объектов
        current_time = pygame.time.get_ticks() - self.start_time
        
        self.draw_prediction_line(screen)
        
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
