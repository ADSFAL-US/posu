import pygame
import math
import sys
from pygame.math import Vector2



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