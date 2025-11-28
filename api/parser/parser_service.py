import json
import re
from typing import List, Dict, Any, Optional, Set, Tuple
import xlrd


class ParserService:
    """
    Основной сервис для парсинга учебного плана
    """

    def __init__(self):
        self.chapters = ["ОП", "ПП"]
        self.cycles = ["НО", "ОО", "СО", "ОГСЭ", "ЕН", "ОПЦ", "ПЦ"]
        self.modules = ["ОУД", "ПОО", "ПМ.02", "ПМ.03", "ПМ.05", "ПМ.06", "ПМ.07"]

    def find_word(self, data: List[List], search_word: str) -> List[Dict[str, Any]]:
        """
        Поиск слова в данных
        """
        results = []
        
        for row_index, row in enumerate(data):
            for col_index, cell in enumerate(row):
                if cell and isinstance(cell, str) and search_word in cell:
                    results.append({
                        'row_index': row_index,
                        'col_index': col_index,
                        'value': cell,
                        'coordinates': [row_index, col_index]
                    })
        
        return results

    def parse_weeks_string(self, input_str: str) -> Dict[str, float]:
        """
        Парсинг строк с неделями
        """
        if not input_str or not isinstance(input_str, str):
            return {'weeks': 0, 'practice_weeks': 0}

        result = {'weeks': 0, 'practice_weeks': 0}

        # Ищем дробь в формате "число/число"
        fraction_match = re.search(r'(\d+)/(\d+)', input_str)
        if fraction_match:
            numerator = int(fraction_match.group(1))
            denominator = int(fraction_match.group(2))
            fraction_value = numerator / denominator
            result['weeks'] = fraction_value

        # Ищем значение в скобках
        bracket_match = re.search(r'\(([^)]+)\)', input_str)
        if bracket_match:
            bracket_value = bracket_match.group(1).strip()
            try:
                practice_weeks = float(re.sub(r'[^\d.]', '', bracket_value))
                result['practice_weeks'] = practice_weeks
            except ValueError:
                pass

        # Ищем основное число недель (до дроби или скобок)
        main_number_match = re.match(r'^(\d+)', input_str)
        if main_number_match:
            result['weeks'] += int(main_number_match.group(1))

        return result

    def get_next_row_data(self, json_data: List[List], indexes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Получение данных из следующей строки
        """
        results = []

        for item in indexes:
            semester_number = self.extract_semester_number(item['value'])

            if item['row_index'] + 1 < len(json_data):
                next_row = json_data[item['row_index'] + 1]
                if item['col_index'] < len(next_row):
                    next_cell_value = next_row[item['col_index']]

                    if next_cell_value is not None:
                        parsed_weeks = self.parse_weeks_string(str(next_cell_value))
                        results.append({
                            'semester': semester_number,
                            'weeks': parsed_weeks['weeks'],
                            'practice_weeks': parsed_weeks['practice_weeks']
                        })
                    else:
                        results.append({
                            'semester': semester_number,
                            'weeks': 0,
                            'practice_weeks': 0
                        })
                else:
                    results.append({
                        'semester': semester_number,
                        'weeks': 0,
                        'practice_weeks': 0
                    })
            else:
                results.append({
                    'semester': semester_number,
                    'weeks': 0,
                    'practice_weeks': 0
                })

        return results

    def extract_semester_number(self, semester_string: str) -> int:
        """
        Извлечение номера семестра из строки
        """
        match = re.search(r'(\d+)', semester_string)
        return int(match.group(1)) if match else 0

    def process_semester_data(self, json_data: List[List]) -> List[Dict[str, Any]]:
        """
        Обработка данных о семестрах
        """
        indexes = self.find_word(json_data, "Семестр")

        if not indexes:
            print('Слово "Семестр" не найдено')
            return []

        semester_data = self.get_next_row_data(json_data, indexes)
        return semester_data

    def process_structure_data(self, json_data: List[List]) -> Dict[str, Any]:
        """
        Обработка структуры учебного плана
        """
        structure = {
            'chapters': []
        }

        all_rows = []
        for i, row in enumerate(json_data):
            if len(row) >= 2:
                second_column_value = row[1]
                if second_column_value:
                    all_rows.append({
                        'row_index': i,
                        'col1': row[0] if len(row) > 0 else None,
                        'col2': row[1] if len(row) > 1 else None,
                        'col3': row[2] if len(row) > 2 else None,
                        'col4': row[3] if len(row) > 3 else None
                    })

        for row in all_rows:
            category = row['col2']

            if category in self.chapters:
                # Это раздел (chapter)
                structure['chapters'].append({
                    'code': category,
                    'name': row['col3'],  # название раздела
                    'cycles': []
                })
            elif category in self.cycles:
                # Это цикл - находим последний добавленный раздел
                if structure['chapters']:
                    parent_chapter = structure['chapters'][-1]
                    parent_chapter['cycles'].append({
                        'code': category,
                        'name': row['col3'],  # название цикла
                        'modules': [],
                        'subjects': []
                    })
            elif category in self.modules:
                # Это модуль - находим последний добавленный цикл в последнем разделе
                if structure['chapters']:
                    parent_chapter = structure['chapters'][-1]
                    if parent_chapter['cycles']:
                        parent_cycle = parent_chapter['cycles'][-1]
                        parent_cycle['modules'].append({
                            'code': category,
                            'name': row['col3'],  # название модуля
                            'subjects': []
                        })
            else:
                # Это дисциплина - проверяем, что category (col2) не нулевое и не равно "*"
                if category and category != "*":
                    # Ищем последний модуль в последнем цикле последнего раздела
                    if structure['chapters']:
                        parent_chapter = structure['chapters'][-1]
                        if parent_chapter['cycles']:
                            parent_cycle = parent_chapter['cycles'][-1]

                            if parent_cycle['modules']:
                                # Дисциплина в последнем модуле
                                parent_module = parent_cycle['modules'][-1]
                                parent_module['subjects'].append({
                                    'code': row['col2'],
                                    'name': row['col3']
                                })
                            else:
                                # Дисциплина в цикле (не в модуле)
                                parent_cycle['subjects'].append({
                                    'code': row['col2'],
                                    'name': row['col3']
                                })

        return structure

    def extract_all_subjects(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Рекурсивное извлечение всех дисциплин из структуры
        """
        subjects = []

        def traverse(obj: Any, path: List[str] = None):
            if path is None:
                path = []

            if isinstance(obj, dict):
                if 'subjects' in obj and isinstance(obj['subjects'], list):
                    for subject in obj['subjects']:
                        subjects.append({
                            **subject,
                            'path': path[:]
                        })
                if 'modules' in obj and isinstance(obj['modules'], list):
                    for i, module in enumerate(obj['modules']):
                        traverse(module, path + [f'module_{i}'])
                if 'cycles' in obj and isinstance(obj['cycles'], list):
                    for i, cycle in enumerate(obj['cycles']):
                        traverse(cycle, path + [f'cycle_{i}'])
                if 'chapters' in obj and isinstance(obj['chapters'], list):
                    for i, chapter in enumerate(obj['chapters']):
                        traverse(chapter, path + [f'chapter_{i}'])

        traverse(structure)
        return subjects

    def find_semester_columns(self, json_data: List[List]) -> List[Dict[str, Any]]:
        """
        Поиск колонок с "Семестр" и номером
        """
        semester_columns = []

        for row_index, row in enumerate(json_data):
            for col_index, cell in enumerate(row):
                if cell and isinstance(cell, str):
                    match = re.search(r'Семестр\s+(\d+)', cell, re.IGNORECASE)
                    if match:
                        semester_number = int(match.group(1))
                        semester_columns.append({
                            'semester': semester_number,
                            'col_index': col_index,
                            'row_index': row_index
                        })

        return semester_columns

    def find_second_op_volume(self, json_data: List[List], start_row_index: int = 0) -> Optional[Dict[str, Any]]:
        """
        Поиск второй строки с "Объём ОП" после указанной строки
        """
        found_count = 0

        for row_index in range(start_row_index, len(json_data)):
            row = json_data[row_index]
            for col_index, cell in enumerate(row):
                if cell and isinstance(cell, str) and "Объём ОП" in cell:
                    found_count += 1
                    if found_count == 2:
                        return {
                            'row_index': row_index,
                            'col_index': col_index
                        }

        return None

    def extract_semester_data(self, subject_row: List[Any], semester_col_index: int) -> Dict[str, Any]:
        """
        Извлечение всех данных начиная с value и ещё 10 колонок вправо
        """
        data = {
            'value': 0,
            'col1': 0,
            'col2': 0,
            'col3': 0,
            'col4': 0,
            'col5': 0,
            'col6': 0,
            'col7': 0,
            'col8': 0,
            'col9': 0,
            'col10': 0
        }

        # Значение "value" - это значение в той же колонке, где определяется номер семестра
        if semester_col_index < len(subject_row) and subject_row[semester_col_index] is not None:
            data['value'] = subject_row[semester_col_index]

        # Значения из следующих 10 колонок
        col_names = ['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10']
        for i, col_name in enumerate(col_names):
            col_index = semester_col_index + 1 + i
            if col_index < len(subject_row) and subject_row[col_index] is not None:
                data[col_name] = subject_row[col_index]
            else:
                data[col_name] = 0

        return data

    def find_subject_in_data(self, json_data: List[List], subject_code: str, subject_name: str) -> Dict[str, Any]:
        """
        Поиск предмета в данных Excel по коду и названию
        """
        for i, row in enumerate(json_data):
            if len(row) >= 3:
                code = row[1]  # предполагаем, что код в колонке 1
                name = row[2]  # предполагаем, что название в колонке 2

                if code == subject_code and name == subject_name:
                    return {
                        'found': True,
                        'row_index': i,
                        'row': row
                    }

        return {
            'found': False,
            'row_index': -1,
            'row': None
        }

    def is_practice_subject(self, subject_name: str) -> bool:
        """
        Проверка, является ли предмет практикой
        """
        return (
            "производственная практика" in subject_name.lower() or
            "учебная практика" in subject_name.lower() or
            "преддипломная практика" in subject_name.lower() 
        )

    def find_semesters_and_info_for_subject(
        self,
        json_data: List[List],
        subject_row: List[Any],
        subject_row_index: int,
        semester_columns: List[Dict[str, Any]],
        op_volume_row: Dict[str, Any],
        subject_name: str
    ) -> List[Dict[str, Any]]:
        """
        Определение семестров для предмета и получение информации по каждому семестру
        """
        semesters_info = []

        if not subject_row or not op_volume_row:
            return semesters_info

        for sem_col in semester_columns:
            semester_col_index = sem_col['col_index']

            if (
                len(subject_row) > semester_col_index and
                op_volume_row['row_index'] < len(json_data)
            ):
                op_volume_row_data = json_data[op_volume_row['row_index']]
                if len(op_volume_row_data) > semester_col_index:
                    # Извлекаем все данные начиная с value и ещё 10 колонок вправо
                    semester_data = self.extract_semester_data(subject_row, semester_col_index)

                    # Проверяем, есть ли значение в "value"
                    if (
                        semester_data['value'] != 0 and
                        semester_data['value'] is not None and
                        semester_data['value'] != ''
                    ):
                        # Проверяем, является ли это практикой
                        if self.is_practice_subject(subject_name):
                            # Для практик: умножаем 36 на значение в practical_hours (col4) и записываем в lectures_hours
                            practical_hours = semester_data['col4']
                            if (
                                practical_hours != 0 and
                                practical_hours is not None and
                                practical_hours != '' and
                                isinstance(practical_hours, (int, float))
                            ):
                                lectures_hours = 36 * practical_hours
                                semesters_info.append({
                                    'semester': sem_col['semester'],
                                    'self_study_hours': semester_data['col1'],  # через 1 колонку после value
                                    'lectures_hours': lectures_hours,  # 36 * practical_hours
                                    'practical_hours': practical_hours,  # через 4 колонки после value
                                    'laboratory_hours': semester_data['col5'],  # через 5 колонки после value
                                    'intermediate_assessment_hours': semester_data['col6'],  # через 6 колонки после value
                                    'course_project_hours': semester_data['col7'],  # через 7 колонки после value
                                    'consultation_hours': semester_data['col8'],  # через 8 колонки после value
                                    'certification_hours': semester_data['col9']  # через 9 колонки после value
                                })
                            # Если практические часы отсутствуют, запись не создаем
                        else:
                            # Для обычных предметов: стандартная обработка
                            semesters_info.append({
                                'semester': sem_col['semester'],
                                'self_study_hours': semester_data['col1'],  # через 1 колонку после value
                                'lectures_hours': semester_data['col3'],  # через 3 колонки после value
                                'practical_hours': semester_data['col4'],  # через 4 колонки после value
                                'laboratory_hours': semester_data['col5'],  # через 5 колонки после value
                                'intermediate_assessment_hours': semester_data['col6'],  # через 6 колонки после value
                                'course_project_hours': semester_data['col7'],  # через 7 колонки после value
                                'consultation_hours': semester_data['col8'],  # через 8 колонки после value
                                'certification_hours': semester_data['col9']  # через 9 колонки после value
                            })

        return semesters_info

    def process_subject_hours(self, json_data: List[List], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Обработка информации о часах для предметов
        """
        # Извлекаем все дисциплины из структурированных данных
        all_subjects = self.extract_all_subjects(structure)

        # Находим колонки с семестрами
        semester_columns = self.find_semester_columns(json_data)
        # Находим вторую строку с "Объём ОП"
        second_op_volume = self.find_second_op_volume(json_data, 0)

        # Для каждой дисциплины ищем информацию в Excel-данных
        subjects_with_info = []

        for subject in all_subjects:
            search_result = self.find_subject_in_data(
                json_data,
                subject['code'],
                subject['name']
            )

            semesters_info = []

            if search_result['found'] and second_op_volume:
                semesters_info = self.find_semesters_and_info_for_subject(
                    json_data,
                    search_result['row'],
                    search_result['row_index'],
                    semester_columns,
                    second_op_volume,
                    subject['name']
                )

            subjects_with_info.append({
                **subject,
                'found': search_result['found'],
                'hours': semesters_info,
                'excel_position': {
                    'row_index': search_result['row_index']
                } if search_result['found'] else None
            })

        return subjects_with_info

    def parse_value(self, value: Any) -> List[int]:
        """
        Разбор значения - может быть числом или диапазоном (например, "1-6")
        """
        if isinstance(value, str) and '-' in value:
            try:
                start, end = map(int, value.split('-'))
                return list(range(start, end + 1))
            except ValueError:
                pass

        # Если это просто число
        try:
            num_value = int(value)
            return [num_value]
        except (ValueError, TypeError):
            return []

    def extract_assessment_values(self, subject_row: List[Any], semester_number: int) -> Dict[str, bool]:
        """
        Извлечение значений оценок для предмета
        Берём 7 колонок после названия предмета (предполагаем, что название в колонке 2)
        В этих колонках содержится номер семестра или диапазон (например, "1-6")
        """
        assessment_fields = ['ex', 'zach', 'dif', 'proj', 'work', 'cntrl', 'other']
        values = {}

        for field in assessment_fields:
            values[field] = False  # по умолчанию false

        if not subject_row:
            return values

        name_col_index = 2  # колонка с названием предмета (индекс 2)
        assessment_start_index = name_col_index + 1  # начинаем с колонки после названия

        # Проверяем, есть ли в этих колонках указанный номер семестра
        for i, field in enumerate(assessment_fields):
            col_index = assessment_start_index + i
            if col_index < len(subject_row) and subject_row[col_index] is not None:
                cell_value = subject_row[col_index]
                # Разбираем значение (может быть числом или диапазоном)
                values_in_cell = self.parse_value(cell_value)
                # Если номер семестра присутствует в значениях ячейки, устанавливаем true
                if semester_number in values_in_cell:
                    values[field] = True

        return values

    def find_semesters_in_row(self, subject_row: List[Any]) -> List[int]:
        """
        Поиск всех уникальных номеров семестров в строке предмета
        """
        semesters = set()

        if not subject_row:
            return list(semesters)

        name_col_index = 2  # колонка с названием предмета (индекс 2)
        assessment_start_index = name_col_index + 1  # начинаем с колонки после названия
        assessment_fields = ['ex', 'zach', 'dif', 'proj', 'work', 'cntrl', 'other']

        for i in range(len(assessment_fields)):
            col_index = assessment_start_index + i
            if col_index < len(subject_row) and subject_row[col_index] is not None:
                cell_value = subject_row[col_index]
                # Разбираем значение и добавляем все семестры из него
                values_in_cell = self.parse_value(cell_value)
                semesters.update(values_in_cell)

        # Исключаем 0 и пустые значения
        return [sem for sem in semesters if sem != 0]

    def process_subject_assessments(self, json_data: List[List], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Обработка информации об оценках для предметов
        """
        # Извлекаем все дисциплины из структурированных данных
        all_subjects = self.extract_all_subjects(structure)

        # Для каждой дисциплины ищем информацию в Excel-данных
        subjects_with_assessments = []

        for subject in all_subjects:
            search_result = self.find_subject_in_data(
                json_data,
                subject['code'],
                subject['name']
            )

            semester_assessments = []

            if search_result['found']:
                # Находим все уникальные номера семестров в строке предмета
                semesters = self.find_semesters_in_row(search_result['row'])

                # Для каждого найденного номера семестра создаем запись
                for semester in semesters:
                    assessment_values = self.extract_assessment_values(
                        search_result['row'],
                        semester
                    )

                    # Проверяем, есть ли хотя бы одно true значение
                    has_assessments = any(val for val in assessment_values.values())

                    if has_assessments:
                        semester_assessments.append({
                            'semester': semester,
                            'credit': assessment_values['ex'],  # ex -> credit (exam)
                            'differentiated_credit': assessment_values['dif'],  # dif -> differentiated_credit
                            'course_project': assessment_values['proj'],  # proj -> course_project
                            'course_work': assessment_values['work'],  # work -> course_work
                            'control_work': assessment_values['cntrl'],  # cntrl -> control_work
                            'other_form': assessment_values['other']  # other -> other_form
                        })

            subjects_with_assessments.append({
                **subject,
                'found': search_result['found'],
                'certifications': semester_assessments,
                'excel_position': {
                    'row_index': search_result['row_index']
                } if search_result['found'] else None
            })

        return subjects_with_assessments

    def build_complete_structure(
        self,
        semester_data: List[Dict[str, Any]],
        structured_curriculum: Dict[str, Any],
        subjects_with_hours: List[Dict[str, Any]],
        subjects_with_assessments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сборка полной структуры
        """
        # Создаём объект для хранения оценок по предметам
        assessments_map = {}
        for subject in subjects_with_assessments:
            key = f"{subject['code']}-{subject['name']}"
            assessments_map[key] = subject['certifications']

        # Создаём структурированный JSON
        complete_structure = {
            'id': 1,  # условный ID плана
            'year': 2023,  # условный год
            'speciality_code': '09.02.07',  # условный код специальности
            'semesters': [
                {
                    'semester': semester['semester'],
                    'weeks': semester['weeks'],
                    'practice_weeks': semester['practice_weeks'],
                    'plan_id': 1  # внешний ключ на план
                }
                for semester in semester_data
            ],
            'chapters': [
                {
                    'id': chapter_idx + 1,
                    'code': chapter['code'],
                    'name': chapter['name'],
                    'plan_id': 1,  # внешний ключ на план
                    'cycles': [
                        {
                            'id': cycle_idx + 1,
                            'contains_modules': len(cycle['modules']) > 0,
                            'code': cycle['code'],
                            'name': cycle['name'],
                            'chapter_in_plan_id': chapter_idx + 1,  # внешний ключ на раздел
                            'modules': [
                                {
                                    'id': module_idx + 1,
                                    'name': module['name'],
                                    'code': module['code'],
                                    'cycle_in_chapter_id': cycle_idx + 1,  # внешний ключ на цикл
                                    'subjects': [
                                        {
                                            'id': subject_idx + 1,  # числовое ID для предмета
                                            'code': subject['code'],
                                            'title': subject['name'],
                                            'module_in_cycle_id': module_idx + 1,
                                            'cycle_in_chapter_id': cycle_idx + 1,
                                            'hours': (
                                                next((swh['hours'] for swh in subjects_with_hours 
                                                      if swh['code'] == subject['code'] and swh['name'] == subject['name']), [])
                                            ),
                                            'certifications': assessments_map.get(f"{subject['code']}-{subject['name']}", [])
                                        }
                                        for subject_idx, subject in enumerate(module['subjects'])
                                    ]
                                }
                                for module_idx, module in enumerate(cycle['modules'])
                            ],
                            'subjects': [
                                {
                                    'id': subject_idx + 1,  # числовое ID для предмета
                                    'code': subject['code'],
                                    'title': subject['name'],
                                    'module_in_cycle_id': None,
                                    'cycle_in_chapter_id': cycle_idx + 1,
                                    'hours': (
                                        next((swh['hours'] for swh in subjects_with_hours 
                                              if swh['code'] == subject['code'] and swh['name'] == subject['name']), [])
                                    ),
                                    'certifications': assessments_map.get(f"{subject['code']}-{subject['name']}", [])
                                }
                                for subject_idx, subject in enumerate(cycle['subjects'])
                            ]
                        }
                        for cycle_idx, cycle in enumerate(chapter['cycles'])
                    ]
                }
                for chapter_idx, chapter in enumerate(structured_curriculum['chapters'])
            ]
        }

        return complete_structure

    def parse_excel_file(self, file_path: str) -> Dict[str, Any]:
        """
        Основная функция парсинга Excel файла
        """
        # Открываем .xls файл
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(2)  # Третий лист (индекс 2)

        # Преобразуем в список списков (как в JavaScript)
        json_data = []
        for row_idx in range(sheet.nrows):
            row = []
            for col_idx in range(sheet.ncols):
                cell_value = sheet.cell_value(row_idx, col_idx)
                row.append(cell_value)
            json_data.append(row)

        # Запускаем все парсеры
        print("Запуск парсера недель по семестрам...")
        semester_weeks = self.process_semester_data(json_data)
        print(f'Получено {len(semester_weeks)} записей о неделях')

        print("Запуск парсера структуры учебного плана...")
        structured_curriculum = self.process_structure_data(json_data)
        print(f'Получена структура с {len(structured_curriculum["chapters"])} разделами')

        print("Запуск парсера информации по семестрам для предметов...")
        subjects_with_hours = self.process_subject_hours(json_data, structured_curriculum)
        print(f'Получено {len(subjects_with_hours)} предметов с информацией о часах')

        print("Запуск парсера оценок по семестрам...")
        subjects_with_assessments = self.process_subject_assessments(json_data, structured_curriculum)
        print(f'Получено {len(subjects_with_assessments)} предметов с информацией об оценках')

        # Собираем всё в один структурированный JSON
        print("Сборка полной структуры...")
        complete_structure = self.build_complete_structure(
            semester_weeks,
            structured_curriculum,
            subjects_with_hours,
            subjects_with_assessments
        )

        return complete_structure