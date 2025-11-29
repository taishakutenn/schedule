import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math 

@dataclass
class SemesterInfo:
    semester: int
    weeks: float
    practice_weeks: int

@dataclass
class Subject:
    code: str
    name: str

@dataclass
class Module:
    code: str
    name: str
    subjects: List[Subject]

@dataclass
class Cycle:
    code: str
    name: str
    modules: List[Module]
    subjects: List[Subject]

@dataclass
class Chapter:
    code: str
    name: str
    cycles: List[Cycle]

@dataclass
class SubjectHours:
    semester: int
    self_study_hours: float
    lectures_hours: float
    practical_hours: float
    laboratory_hours: float
    intermediate_assessment_hours: float
    course_project_hours: float
    consultation_hours: float
    certification_hours: float

@dataclass
class Certification:
    semester: int
    credit: bool
    differentiated_credit: bool
    course_project: bool
    course_work: bool
    control_work: bool
    other_form: bool

class ParserService:
    def __init__(self, chapters: List[str] = None, cycles: List[str] = None, modules: List[str] = None, sheet_name: str = "План"):
        self.chapters = chapters or ["ОП", "ПП"]
        self.cycles = cycles or ["НО", "ОО", "СО", "ОГСЭ", "ЕН", "ОПЦ", "ПЦ"]
        self.modules = modules or ["ОУД", "ПОО", "ПМ.02", "ПМ.03", "ПМ.05", "ПМ.06", "ПМ.07"]
        self.sheet_name = sheet_name 
    
    def debug_print_file_structure(self, file_path: str):
        print("=== ОТЛАДКА ФАЙЛА ===")
        
        try:
            excel_file = pd.ExcelFile(file_path)
            print(f"Доступные листы: {excel_file.sheet_names}")
            
            if self.sheet_name in excel_file.sheet_names:
                print(f"Используем лист: {self.sheet_name}")
                df = pd.read_excel(file_path, header=None, sheet_name=self.sheet_name)
            else:
                print(f"Лист '{self.sheet_name}' не найден, используем первый лист: {excel_file.sheet_names[0]}")
                df = pd.read_excel(file_path, header=None, sheet_name=excel_file.sheet_names[0])
            
            print(f"Размерность DataFrame: {df.shape}")
            print(f"Первые 10 строк:")
            print(df.head(10))
            print(f"Последние 10 строк:")
            print(df.tail(10))
            
            found_keywords = []
            for row_idx in range(min(30, len(df))):  
                for col_idx in range(min(30, len(df.columns))):  
                    cell_value = df.iloc[row_idx, col_idx]
                    if pd.notna(cell_value) and isinstance(cell_value, str):
                        cell_lower = cell_value.lower()
                        if 'семестр' in cell_lower:
                            found_keywords.append(f"Семестр в ({row_idx}, {col_idx}): {cell_value}")
                        elif 'объём оп' in cell_lower:
                            found_keywords.append(f"Объём ОП в ({row_idx}, {col_idx}): {cell_value}")
                        elif any(cat in cell_lower for cat in [ch.lower() for ch in self.chapters + self.cycles + self.modules]):
                            found_keywords.append(f"Категория в ({row_idx}, {col_idx}): {cell_value}")
            
            if found_keywords:
                print("Найденные ключевые слова:")
                for kw in found_keywords:
                    print(f"  {kw}")
            else:
                print("Ключевые слова не найдены в первых 30 строках/колонках")
                
        except Exception as e:
            print(f"Ошибка при отладке файла: {e}")
        print("=== КОНЕЦ ОТЛАДКИ ===")
    
    def parse_weeks_string(self, input_str: str) -> Tuple[float, int]:
        """Парсинг строк с неделями"""
        weeks = 0
        practice_weeks = 0
        
        if not input_str or not isinstance(input_str, str):
            return weeks, practice_weeks
        
        fraction_match = re.search(r'(\d+)\/(\d+)', input_str)
        if fraction_match:
            numerator = int(fraction_match.group(1))
            denominator = int(fraction_match.group(2))
            fraction_value = numerator / denominator
            weeks = fraction_value  
        
        bracket_match = re.search(r'\(([^)]+)\)', input_str)
        if bracket_match:
            bracket_value = bracket_match.group(1).strip()
            try:
                practice_weeks = float(re.sub(r'[^\d.]', '', bracket_value))
            except ValueError:
                practice_weeks = 0
        
        main_number_match = re.match(r'^(\d+)', input_str)
        if main_number_match:
            weeks += int(main_number_match.group(1))
        
        return weeks, practice_weeks
    
    def find_semester_rows(self, df: pd.DataFrame) -> List[Tuple[int, int, str]]:
        """Находит строки с 'Семестр'"""
        results = []
        
        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                cell_value = df.iloc[row_idx, col_idx]
                
                if pd.notna(cell_value) and isinstance(cell_value, str):
                    # Ищем различные варианты написания "Семестр"
                    if re.search(r'семестр', cell_value, re.IGNORECASE):
                        # Извлекаем номер семестра
                        match = re.search(r'(\d+)', cell_value)
                        if match:
                            semester_num = int(match.group(1))
                            results.append((row_idx, col_idx, cell_value))
        
        return results
    
    def parse_semester_weeks(self, df: pd.DataFrame) -> List[SemesterInfo]:
        """Парсинг недель по семестрам"""
        semester_rows = self.find_semester_rows(df)
        print(f"Найдено {len(semester_rows)} строк с 'Семестр': {semester_rows}")
        
        semester_info_list = []
        
        for row_idx, col_idx, value in semester_rows:
            if row_idx + 1 < len(df):  # Проверяем, есть ли следующая строка
                next_row = df.iloc[row_idx + 1]
                
                # Получаем значение в той же колонке
                cell_value = next_row.iloc[col_idx] if col_idx < len(next_row) else None
                
                if pd.notna(cell_value):
                    weeks, practice_weeks = self.parse_weeks_string(str(cell_value))
                    match = re.search(r'(\d+)', value)
                    semester_num = int(match.group(1)) if match else 0
                    
                    semester_info = SemesterInfo(
                        semester=semester_num,
                        weeks=weeks,
                        practice_weeks=practice_weeks
                    )
                    semester_info_list.append(semester_info)
                    print(f"Найдены недели для семестра {semester_num}: weeks={weeks}, practice_weeks={practice_weeks}")
                else:
                    # Если ячейка пустая, создаем с нулями
                    match = re.search(r'(\d+)', value)
                    semester_num = int(match.group(1)) if match else 0
                    semester_info = SemesterInfo(
                        semester=semester_num,
                        weeks=0,
                        practice_weeks=0
                    )
                    semester_info_list.append(semester_info)
                    print(f"Создана пустая запись для семестра {semester_num}")
        
        return semester_info_list
    
    def find_second_op_volume_row(self, df: pd.DataFrame) -> Optional[int]:
        """Находит вторую строку с 'Объём ОП'"""
        op_volume_rows = []
        
        for row_idx in range(len(df)):
            row = df.iloc[row_idx]
            for cell in row:
                if pd.notna(cell) and isinstance(cell, str):
                    if re.search(r'объём\s+оп', cell, re.IGNORECASE):
                        op_volume_rows.append(row_idx)
                        print(f"Найдена строка 'Объём ОП' на строке {row_idx}: {cell}")
                        if len(op_volume_rows) == 2:
                            return op_volume_rows[1]
        
        print(f"Найдено {len(op_volume_rows)} строк с 'Объём ОП'")
        return op_volume_rows[1] if len(op_volume_rows) >= 2 else (op_volume_rows[0] if op_volume_rows else None)
    
    def find_semester_columns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Находит колонки с 'Семестр' и номером"""
        semester_columns = []
        
        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                cell_value = df.iloc[row_idx, col_idx]
                
                if pd.notna(cell_value) and isinstance(cell_value, str):
                    match = re.search(r'семестр\s+(\d+)', cell_value, re.IGNORECASE)
                    if match:
                        semester_num = int(match.group(1))
                        semester_columns.append({
                            'semester': semester_num,
                            'col_index': col_idx,
                            'row_index': row_idx
                        })
                        print(f"Найдена колонка семестра {semester_num} на ({row_idx}, {col_idx}): {cell_value}")
        
        return semester_columns
    
    def extract_semester_data(self, subject_row: pd.Series, semester_col_index: int) -> Dict[str, float]:
        """Извлечение данных из 10 колонок после значения семестра"""
        data = {
            'value': 0,
            'col1': 0, 'col2': 0, 'col3': 0, 'col4': 0, 'col5': 0,
            'col6': 0, 'col7': 0, 'col8': 0, 'col9': 0, 'col10': 0
        }
        
        if len(subject_row) > semester_col_index:
            cell_value = subject_row.iloc[semester_col_index]
            if pd.notna(cell_value) and cell_value != "" and cell_value != 0:
                # Проверяем, является ли значение числом
                if isinstance(cell_value, (int, float)) and not math.isnan(cell_value):
                    data['value'] = float(cell_value)
                elif isinstance(cell_value, str) and cell_value.replace('.', '').replace('-', '').isdigit():
                    try:
                        data['value'] = float(cell_value)
                    except ValueError:
                        data['value'] = 0
                else:
                    data['value'] = 0
        
        col_names = ['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10']
        for i, col_name in enumerate(col_names):
            col_index = semester_col_index + 1 + i
            if len(subject_row) > col_index:
                cell_value = subject_row.iloc[col_index]
                if pd.notna(cell_value) and cell_value != "" and cell_value != 0:
                    # Проверяем, является ли значение числом
                    if isinstance(cell_value, (int, float)) and not math.isnan(cell_value):
                        data[col_name] = float(cell_value)
                    elif isinstance(cell_value, str) and cell_value.replace('.', '').replace('-', '').isdigit():
                        try:
                            data[col_name] = float(cell_value)
                        except ValueError:
                            data[col_name] = 0
                    else:
                        data[col_name] = 0
                else:
                    data[col_name] = 0
            else:
                data[col_name] = 0
        
        return data
    
    def is_practice_subject(self, subject_name: str) -> bool:
        """Проверяет, является ли предмет практикой."""
        if not subject_name:
            return False
        lower_name = subject_name.lower()
        # Расширяем проверку на все виды практик
        practice_keywords = [
            "учебная практика",
            "производственная практика",
            "преддипломная практика",
            "практика"
        ]
        return any(keyword in lower_name for keyword in practice_keywords)
    
    def find_semesters_and_info_for_subject(
        self, 
        subject_row: pd.Series, 
        semester_columns: List[Dict[str, Any]], 
        op_volume_row_idx: Optional[int],
        subject_name: str
    ) -> List[SubjectHours]:
        """Находит информацию о часах для предмета по каждому семестру."""
        semesters_info = []
        
        if op_volume_row_idx is None:
            print("Вторая строка 'Объём ОП' не найдена")
            return semesters_info
        
        print(f"Обработка предмета '{subject_name}' для {len(semester_columns)} семестров")
        
        for sem_col in semester_columns:
            semester_col_index = sem_col['col_index']
            
            if len(subject_row) > semester_col_index:
                semester_data = self.extract_semester_data(subject_row, semester_col_index)
                print("SEMESTER DATA", semester_data)
                
                # Проверяем, есть ли значение в "value"
                if (semester_data['value'] != 0 and 
                    semester_data['value'] is not None and 
                    semester_data['value'] != "") or semester_data['col4'] != 0:
                    
                    print(f"Найдены данные для семестра {sem_col['semester']}: {semester_data}")
                    print(f"{self.is_practice_subject(subject_name)} Проверка на практику")
                    
                    if self.is_practice_subject(subject_name):
                        # Для практик: умножаем 36 на значение в practical_hours (col4)
                        practical_hours = semester_data['col4']
                        print(f"practical_hours: {practical_hours}")
                        
                        if practical_hours and practical_hours != 0 and practical_hours != "":
                            lectures_hours = 36 * practical_hours
                            hour_record = SubjectHours(
                                semester=sem_col['semester'],
                                self_study_hours=semester_data['col1'],
                                lectures_hours=lectures_hours,  # 36 * practical_hours
                                practical_hours=practical_hours,
                                laboratory_hours=semester_data['col5'],
                                intermediate_assessment_hours=semester_data['col6'],
                                course_project_hours=semester_data['col7'],
                                consultation_hours=semester_data['col8'],
                                certification_hours=semester_data['col9']
                            )
                            semesters_info.append(hour_record)
                            print(f"Создана запись для практики '{subject_name}', семестр {sem_col['semester']}")
                        else:
                            print(f"Практика '{subject_name}' не имеет practical_hours или practical_hours = 0, пропускаем")
                    else:
                        # Для обычных предметов: стандартная обработка
                        hour_record = SubjectHours(
                            semester=sem_col['semester'],
                            self_study_hours=semester_data['col1'],
                            lectures_hours=semester_data['col3'],
                            practical_hours=semester_data['col4'],
                            laboratory_hours=semester_data['col5'],
                            intermediate_assessment_hours=semester_data['col6'],
                            course_project_hours=semester_data['col7'],
                            consultation_hours=semester_data['col8'],
                            certification_hours=semester_data['col9']
                        )
                        semesters_info.append(hour_record)
                        print(f"Создана запись для предмета '{subject_name}', семестр {sem_col['semester']}")
        
        return semesters_info
    
    def find_subject_in_data(self, df: pd.DataFrame, subject_code: str, subject_name: str) -> Optional[Tuple[int, pd.Series]]:
        """Поиск предмета в данных по коду и названию"""
        for row_idx in range(len(df)):
            row = df.iloc[row_idx]
            if len(row) >= 3:  # Проверяем, что строка имеет хотя бы 3 колонки
                code = row.iloc[1] if 1 < len(row) else None  # код в колонке 1
                name = row.iloc[2] if 2 < len(row) else None  # название в колонке 2
                
                if (pd.notna(code) and pd.notna(name) and 
                    str(code) == subject_code and str(name) == subject_name):
                    print(f"Найден предмет: {subject_code} - {subject_name} на строке {row_idx}")
                    return row_idx, row
        
        print(f"Предмет не найден: {subject_code} - {subject_name}")
        return None
    
    def parse_subject_hours(self, df: pd.DataFrame, structure: List[Chapter]) -> List[Dict[str, Any]]:
        """Парсинг информации о часах для предметов"""
        # Извлекаем все дисциплины из структуры
        all_subjects = self.extract_all_subjects(structure)
        print(f"Найдено {len(all_subjects)} предметов для поиска в Excel")
        
        # Находим колонки с семестрами
        semester_columns = self.find_semester_columns(df)
        print(f"Найдено {len(semester_columns)} колонок с семестрами")
        
        # Находим вторую строку с "Объём ОП"
        second_op_volume_row = self.find_second_op_volume_row(df)
        print(f"Вторая строка 'Объём ОП' найдена на строке: {second_op_volume_row}")
        
        subjects_with_info = []
        
        for subject in all_subjects:
            search_result = self.find_subject_in_data(df, subject.code, subject.name)
            
            semesters_info = []
            
            if search_result and second_op_volume_row is not None:
                row_idx, subject_row = search_result
                semesters_info = self.find_semesters_and_info_for_subject(
                    subject_row, semester_columns, second_op_volume_row, subject.name
                )
            
            subject_info = {
                'code': subject.code,
                'name': subject.name,
                'found': search_result is not None,
                'hours': [asdict(hour) for hour in semesters_info],  # Используем asdict для конвертации dataclass в словарь
                'excel_position': {'row_index': search_result[0]} if search_result else None
            }
            subjects_with_info.append(subject_info)
        
        return subjects_with_info
    
    def parse_value(self, value: Union[str, int, float]) -> List[int]:
        """Разбор значения - может быть числом или диапазоном (например, '1-6')"""
        if isinstance(value, str) and '-' in value:
            try:
                start, end = map(int, value.split('-'))
                return list(range(start, end + 1))
            except ValueError:
                pass
        
        # Если это просто число
        try:
            num_value = int(float(value))  # Поддержка float, если вдруг
            return [num_value]
        except (ValueError, TypeError):
            return []
    
    def extract_assessment_values(self, subject_row: pd.Series, semester_number: int) -> Dict[str, bool]:
        """Извлечение значений оценок для предмета"""
        assessment_fields = ['ex', 'zach', 'dif', 'proj', 'work', 'cntrl', 'other']
        values = {field: False for field in assessment_fields}
        
        if subject_row is None:
            return values
        
        name_col_index = 2  # колонка с названием предмета (индекс 2)
        assessment_start_index = name_col_index + 1  # начинаем с колонки после названия
        
        for i, field in enumerate(assessment_fields):
            col_index = assessment_start_index + i
            if len(subject_row) > col_index:
                cell_value = subject_row.iloc[col_index]
                if pd.notna(cell_value) and cell_value != "":
                    # Разбираем значение (может быть числом или диапазоном)
                    values_in_cell = self.parse_value(str(cell_value))
                    # Если номер семестра присутствует в значениях ячейки, устанавливаем True
                    if semester_number in values_in_cell:
                        values[field] = True
        
        return values
    
    def find_semesters_in_row(self, subject_row: pd.Series) -> List[int]:
        """Поиск всех уникальных номеров семестров в строке предмета"""
        semesters = set()
        
        if subject_row is None:
            return list(semesters)
        
        name_col_index = 2  # колонка с названием предмета (индекс 2)
        assessment_start_index = name_col_index + 1  # начинаем с колонки после названия
        assessment_fields = ['ex', 'zach', 'dif', 'proj', 'work', 'cntrl', 'other']
        
        for i in range(len(assessment_fields)):
            col_index = assessment_start_index + i
            if len(subject_row) > col_index:
                cell_value = subject_row.iloc[col_index]
                if pd.notna(cell_value) and cell_value != "":
                    # Разбираем значение и добавляем все семестры из него
                    values_in_cell = self.parse_value(str(cell_value))
                    for semester in values_in_cell:
                        if semester != 0:
                            semesters.add(semester)
        
        return [s for s in semesters if s != 0]  # исключаем 0
    
    def parse_subject_assessments(self, df: pd.DataFrame, structure: List[Chapter]) -> List[Dict[str, Any]]:
        """Парсинг информации об оценках для предметов"""
        # Извлекаем все дисциплины из структуры
        all_subjects = self.extract_all_subjects(structure)
        
        subjects_with_assessments = []
        
        for subject in all_subjects:
            search_result = self.find_subject_in_data(df, subject.code, subject.name)
            
            semester_assessments = []
            
            if search_result:
                row_idx, subject_row = search_result
                # Находим все уникальные номера семестров в строке предмета
                semesters = self.find_semesters_in_row(subject_row)
                
                # Для каждого найденного номера семестра создаем запись
                for semester in semesters:
                    assessment_values = self.extract_assessment_values(subject_row, semester)
                    
                    # Проверяем, есть ли хотя бы одно True значение
                    has_assessments = any(assessment_values.values())
                    
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
            
            subject_info = {
                'code': subject.code,
                'name': subject.name,
                'found': search_result is not None,
                'certifications': semester_assessments,
                'excel_position': {'row_index': search_result[0]} if search_result else None
            }
            subjects_with_assessments.append(subject_info)
        
        return subjects_with_assessments
    
    def extract_all_subjects(self, structure: List[Chapter]) -> List[Subject]:
        """Рекурсивное извлечение всех дисциплин из структуры"""
        subjects = []
        
        def traverse(obj):
            if hasattr(obj, 'subjects') and obj.subjects:
                for subject in obj.subjects:
                    subjects.append(Subject(code=subject.code, name=subject.name))
            
            if hasattr(obj, 'modules') and obj.modules:
                for module in obj.modules:
                    traverse(module)
            
            if hasattr(obj, 'cycles') and obj.cycles:
                for cycle in obj.cycles:
                    traverse(cycle)
        
        for chapter in structure:
            traverse(chapter)
        
        return subjects
    
    def parse_structure(self, df: pd.DataFrame) -> List[Chapter]:
        """Парсинг структуры учебного плана"""
        structure = []
        
        # Собираем все строки с категориями
        all_rows = []
        for i in range(len(df)):
            row = df.iloc[i]
            if len(row) >= 2:
                second_column_value = row.iloc[1] if 1 < len(row) else None
                if pd.notna(second_column_value):
                    all_rows.append({
                        'row_index': i,
                        'col1': row.iloc[0] if 0 < len(row) else None,
                        'col2': row.iloc[1] if 1 < len(row) else None,
                        'col3': row.iloc[2] if 2 < len(row) else None,
                        'col4': row.iloc[3] if 3 < len(row) else None,
                    })
        
        print(f"Найдено {len(all_rows)} строк для анализа структуры")
        
        # Идентифицируем типы строк
        for row_data in all_rows:
            category = row_data['col2']
            
            if category in self.chapters:
                # Это раздел (chapter)
                print(f"Найден раздел: {category} - {row_data['col3']}")
                structure.append(Chapter(
                    code=category,
                    name=row_data['col3'],  # название раздела
                    cycles=[]
                ))
            elif category in self.cycles:
                # Это цикл - находим последний добавленный раздел
                if structure:
                    parent_chapter = structure[-1]
                    print(f"Найден цикл: {category} - {row_data['col3']} в разделе {parent_chapter.code}")
                    parent_chapter.cycles.append(Cycle(
                        code=category,
                        name=row_data['col3'],  # название цикла
                        modules=[],
                        subjects=[]
                    ))
            elif category in self.modules:
                # Это модуль - находим последний добавленный цикл в последнем разделе
                if structure and structure[-1].cycles:
                    parent_chapter = structure[-1]
                    parent_cycle = parent_chapter.cycles[-1]
                    print(f"Найден модуль: {category} - {row_data['col3']} в цикле {parent_cycle.code}")
                    parent_cycle.modules.append(Module(
                        code=category,
                        name=row_data['col3'],  # название модуля
                        subjects=[]
                    ))
            else:
                # Это дисциплина - проверяем, что category не нулевое и не равно "*"
                if category and str(category) != "*":
                    # Ищем последний модуль в последнем цикле последнего раздела
                    if (structure and structure[-1].cycles and 
                        structure[-1].cycles[-1].modules):
                        # Дисциплина в последнем модуле
                        parent_chapter = structure[-1]
                        parent_cycle = parent_chapter.cycles[-1]
                        parent_module = parent_cycle.modules[-1]
                        print(f"Найден предмет в модуле: {category} - {row_data['col3']} в модуле {parent_module.code}")
                        parent_module.subjects.append(Subject(
                            code=category,
                            name=row_data['col3']
                        ))
                    elif structure and structure[-1].cycles:
                        # Дисциплина в цикле (не в модуле)
                        parent_chapter = structure[-1]
                        parent_cycle = parent_chapter.cycles[-1]
                        print(f"Найден предмет в цикле: {category} - {row_data['col3']} в цикле {parent_cycle.code}")
                        parent_cycle.subjects.append(Subject(
                            code=category,
                            name=row_data['col3']
                        ))
        
        print(f"Построена структура: {len(structure)} разделов")
        return structure
    
    def clean_nan_values(self, obj):
        """Рекурсивно заменяет NaN значения на None для сериализации в JSON"""
        if isinstance(obj, dict):
            return {key: self.clean_nan_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_nan_values(item) for item in obj]
        elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        elif isinstance(obj, (int, float)) and obj != obj:  # проверка на NaN (obj != obj верно только для NaN)
            return None
        else:
            return obj
    
    def parse_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Парсинг Excel файла"""
        # Отладочная печать структуры файла
        self.debug_print_file_structure(file_path)
        
        try:
            # Загружаем Excel файл с указанным листом
            excel_file = pd.ExcelFile(file_path)
            if self.sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, header=None, sheet_name=self.sheet_name)
                print(f"Используем лист: {self.sheet_name}")
            else:
                print(f"Лист '{self.sheet_name}' не найден, используем первый лист: {excel_file.sheet_names[0]}")
                df = pd.read_excel(file_path, header=None, sheet_name=excel_file.sheet_names[0])
        except Exception as e:
            print(f"Ошибка при загрузке Excel-файла: {e}")
            # Пробуем с другим движком
            try:
                df = pd.read_excel(file_path, header=None, sheet_name=self.sheet_name, engine='openpyxl')
                print(f"Успешно загружен с движком openpyxl, лист: {self.sheet_name}")
            except:
                df = pd.read_excel(file_path, header=None, engine='xlrd')
                print(f"Успешно загружен с движком xlrd, первый лист")
        
        print(f"Файл загружен, размер: {df.shape}")
        
        print("Запуск парсера недель по семестрам...")
        semester_weeks = self.parse_semester_weeks(df)
        print(f"Получено {len(semester_weeks)} записей о неделях")
        
        print("Запуск парсера структуры учебного плана...")
        structured_curriculum = self.parse_structure(df)
        print(f"Получена структура с {len(structured_curriculum)} разделами")
        
        print("Запуск парсера информации по семестрам для предметов...")
        subjects_with_hours = self.parse_subject_hours(df, structured_curriculum)
        print(f"Получено {len(subjects_with_hours)} предметов с информацией о часах")
        
        print("Запуск парсера оценок по семестрам...")
        subjects_with_assessments = self.parse_subject_assessments(df, structured_curriculum)
        print(f"Получено {len(subjects_with_assessments)} предметов с информацией об оценках")
        
        # Собираем всё в одну структуру
        complete_structure = {
            'id': 1,  # условный ID плана
            'year': 2023,  # условный год
            'speciality_code': "09.02.07",  # условный код специальности
            'semesters': [
                {
                    'semester': semester.semester,
                    'weeks': semester.weeks,
                    'practice_weeks': semester.practice_weeks,
                    'plan_id': 1  # внешний ключ на план
                }
                for semester in semester_weeks
            ],
            'chapters': [
                {
                    'id': chapter_idx + 1,
                    'code': chapter.code,
                    'name': chapter.name,
                    'plan_id': 1,  # внешний ключ на план
                    'cycles': [
                        {
                            'id': cycle_idx + 1,
                            'contains_modules': len(cycle.modules) > 0,
                            'code': cycle.code,
                            'name': cycle.name,
                            'chapter_in_plan_id': chapter_idx + 1,  # внешний ключ на раздел
                            'modules': [
                                {
                                    'id': module_idx + 1,
                                    'name': module.name,
                                    'code': module.code,
                                    'cycle_in_chapter_id': cycle_idx + 1,  # внешний ключ на цикл
                                    'subjects': [
                                        {
                                            'id': subject_idx + 1,  # числовое ID для предмета
                                            'code': subject.code,  # используем атрибут объекта
                                            'title': subject.name,  # используем атрибут объекта
                                            'module_in_cycle_id': module_idx + 1,
                                            'cycle_in_chapter_id': cycle_idx + 1,
                                            'hours': self._get_subject_hours(subject.code, subject.name, subjects_with_hours),
                                            'certifications': self._get_subject_certifications(subject.code, subject.name, subjects_with_assessments)
                                        }
                                        for subject_idx, subject in enumerate(module.subjects)
                                    ]
                                }
                                for module_idx, module in enumerate(cycle.modules)
                            ],
                            'subjects': [
                                {
                                    'id': subject_idx + 1,  # числовое ID для предмета
                                    'code': subject.code,  # используем атрибут объекта
                                    'title': subject.name,  # используем атрибут объекта
                                    'module_in_cycle_id': None,
                                    'cycle_in_chapter_id': cycle_idx + 1,
                                    'hours': self._get_subject_hours(subject.code, subject.name, subjects_with_hours),
                                    'certifications': self._get_subject_certifications(subject.code, subject.name, subjects_with_assessments)
                                }
                                for subject_idx, subject in enumerate(cycle.subjects)
                            ]
                        }
                        for cycle_idx, cycle in enumerate(chapter.cycles)
                    ]
                }
                for chapter_idx, chapter in enumerate(structured_curriculum)
            ]
        }
        
        print(f"Полная структура построена: {len(complete_structure['chapters'])} разделов, {len(complete_structure['semesters'])} семестров")
        
        # Очищаем структуру от NaN значений перед возвратом
        cleaned_structure = self.clean_nan_values(complete_structure)
        
        return cleaned_structure
    
    def _get_subject_hours(self, code: str, name: str, subjects_with_hours: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Получение часов для конкретного предмета"""
        for subject in subjects_with_hours:
            if subject['code'] == code and subject['name'] == name:
                return subject.get('hours', [])
        return []
    
    def _get_subject_certifications(self, code: str, name: str, subjects_with_assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Получение оценок для конкретного предмета"""
        for subject in subjects_with_assessments:
            if subject['code'] == code and subject['name'] == name:
                return subject.get('certifications', [])
        return []