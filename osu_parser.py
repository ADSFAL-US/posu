import os


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