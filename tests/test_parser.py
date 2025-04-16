# tests/test_parser.py
import unittest
import os
import shutil
from main import OsuParser, MAPS_DIR
import unittest
import os
import shutil
from main import OsuParser, MAPS_DIR

class TestParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_map_dir = os.path.join(MAPS_DIR, "unittest_map")
        os.makedirs(cls.test_map_dir, exist_ok=True)
        
        # Тестовый файл с минимально валидным форматом
        osu_content = """[General]
AudioFilename: test.mp3

[Difficulty]
ApproachRate:9.5
CircleSize:4.2

[HitObjects]
256,192,1000,1,0,0:0:0:0:"""
        
        with open(os.path.join(cls.test_map_dir, "test_map.osu"), "w", encoding="utf-8") as f:
            f.write(osu_content)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_map_dir)

    def test_circle_parsing(self):
        audio_path, hit_objects, difficulty = OsuParser.parse_map(self.test_map_dir)
        
        self.assertIsNotNone(audio_path, "Audio path is None")
        self.assertEqual(len(hit_objects), 1, 
            f"Должен быть 1 объект. Получено: {len(hit_objects)}")
        self.assertEqual(hit_objects[0]['type'], 'circle')
        self.assertEqual(hit_objects[0]['x'], 256)
        self.assertEqual(hit_objects[0]['y'], 192)
        self.assertEqual(difficulty['ar'], 9.5)
        self.assertEqual(difficulty['cs'], 4.2)

    @classmethod
    def tearDownClass(cls):
        # Удаляем тестовые данные
        shutil.rmtree(cls.test_map_dir)

    # tests/test_parser.py
    def test_circle_parsing(self):
        audio_path, hit_objects, difficulty = OsuParser.parse_map(self.test_map_dir)
        self.assertEqual(len(hit_objects), 1, 
            f"Не найдены объекты. Проверьте:\n{open(os.path.join(self.test_map_dir, 'test_map.osu')).read()}")
        self.assertEqual(hit_objects[0]['type'], 'circle')
        self.assertEqual(hit_objects[0]['x'], 256)
        self.assertEqual(hit_objects[0]['y'], 192)

if __name__ == '__main__':
    unittest.main()