import pygame
from enum import Enum
import sys
import os
import zipfile
import unittest


from osu_parser import *
from main_menu import *
from game_state import *
from input_handler import *
from env import *
from map_pull import *
from settings_menu import *

class GameStates(Enum):
    MAIN_MENU = 0
    MAP_SELECT = 1
    PLAYING = 2
    SETTINGS = 3

# Инициализация Pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()

class MapLoader:
    @staticmethod
    def process_maps_and_skins():
        """Обработка .osz и .osk архивов из папки import"""
        os.makedirs(IMPORT_DIR, exist_ok=True)
        os.makedirs(MAPS_DIR, exist_ok=True)
        os.makedirs(SKINS_DIR, exist_ok=True)
        
        for item in os.listdir(IMPORT_DIR):
            item_path = os.path.join(IMPORT_DIR, item)
            
            # Обработка карт
            if item.endswith(".osz"):
                map_name = os.path.splitext(item)[0]
                extract_path = os.path.join(MAPS_DIR, map_name)
                
                try:
                    with zipfile.ZipFile(item_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    os.remove(item_path)
                    print(f"Карта распакована: {map_name}")
                except (zipfile.BadZipFile, PermissionError) as e:
                    print(f"Ошибка распаковки карты {item}: {str(e)}")
            
            # Обработка скинов
            elif item.endswith(".osk"):
                skin_name = os.path.splitext(item)[0]
                extract_path = os.path.join(SKINS_DIR, skin_name)
                
                try:
                    with zipfile.ZipFile(item_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    os.remove(item_path)
                    print(f"Скин распакован: {skin_name}")
                except (zipfile.BadZipFile, PermissionError) as e:
                    print(f"Ошибка распаковки скина {item}: {str(e)}")

class Game:
    def __init__(self):
        self.maps = []
        self.current_state = GameStates.MAIN_MENU
        self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
        self.main_menu = MainMenu(*self.screen.get_size())
        self.map_pull = MapPull(*self.screen.get_size())
        self.settings_menu = SettingsMenu(*self.screen.get_size())
        
        # Инициализация новых атрибутов
        self.current_map_index = 0
        self.game_state = None
        
        self.load_maps()
        
        # Инициализация превью и аудио
        if self.maps:
            self.map_pull.load_previews(self.maps)
            self.load_current_map_audio()
        
    def load_maps(self):
        MapLoader.process_maps_and_skins()  # Переименованный метод
        self.maps = [
            d for d in os.listdir(MAPS_DIR)
            if os.path.isdir(os.path.join(MAPS_DIR, d))
        ]
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
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.current_state == GameStates.SETTINGS:
                    self.settings_menu.close_menu()
                    
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if self.current_state == GameStates.SETTINGS:
                    if pos[0] > self.settings_menu.menu_width:
                        self.settings_menu.close_menu()
                
                if self.current_state == GameStates.MAIN_MENU:
                    result = self.main_menu.handle_click(pos)
                    if result == "settings":
                        self.current_state = GameStates.SETTINGS
                        self.settings_menu.state = "opening"
                        self.settings_menu.open_menu()
                    elif result == "play":
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
        
    def draw_settings_menu(self):
        self.settings_menu.draw(self.screen)

    def draw_map_select(self):
        self.screen.fill((0, 0, 0))
        self.map_pull.draw(self.screen)
        
        
    def run(self, map_index=0):
        if not self.maps:
            print("Нет доступных карт в posu/maps/!")
            return
            
        map_folder = os.path.join(MAPS_DIR, self.maps[self.current_map_index])
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
            dt = clock.tick(120)
            current_time = 0
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
                InputHandler.handle_input(self.events, self.game_state, current_time)
                self.game_state.draw(self.screen)
            elif self.current_state == GameStates.SETTINGS:
                self.settings_menu.update()
                self.draw_settings_menu()
            if self.current_state == GameStates.SETTINGS and self.settings_menu.state == "closed":
                self.current_state = GameStates.MAIN_MENU
                
                
            
            pygame.display.flip()
            
if __name__ == "__main__":
    # Запуск тестов
    #tests = unittest.TestLoader().discover('tests')
    #test_result = unittest.TextTestRunner().run(tests)
    
    #if not test_result.wasSuccessful():
    #    print("\nТесты не пройдены!")
        #choice = input("Продолжить запуск? (y/n): ")
        #if choice.lower() != 'y':
        #    sys.exit()
            
    # Запуск игры
    game = Game()
    if game.maps:
        game.run(map_index=0)
    else:
        print("Поместите .osz файлы в posu/maps/ и перезапустите игру!")