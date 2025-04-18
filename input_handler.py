import pygame
import math
import sys


class InputHandler:
    @staticmethod
    def handle_input(events, game_state, current_time):
        mouse_pos = pygame.mouse.get_pos()
        hit_detected = False
        
        # 1. Фильтруем ТОЛЬКО активные ноты в пределах хит-окна
        truly_active_objects = [
            obj for obj in game_state.active_objects
            if (obj['start_time'] - game_state.approach_time <= current_time <= obj['start_time'] + game_state.hit_window_50)
            and not obj.get('hit')
            and not obj.get('missed')
        ]

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for obj in truly_active_objects:  # 2. Используем отфильтрованный список
                    if obj['type'] == 'circle':
                        dx = obj['x'] - mouse_pos[0]
                        dy = obj['y'] - mouse_pos[1]
                        distance = math.hypot(dx, dy)
                        
                        time_diff = abs(current_time - obj['start_time'])
                        if distance <= game_state.hitcircle_radius + 15:
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
                                game_state.combo += 1
                                hit_detected = True
                            
                            if hit_detected:
                                obj['hit'] = True
                                game_state.hp = min(100, game_state.hp + 2)
                                break
                
                # 3. Наказываем ТОЛЬКО если есть активные ноты в хит-окне
                if not hit_detected and len(truly_active_objects) > 0:
                    game_state.combo = 0
                    game_state.hp = max(0, game_state.hp - 5)