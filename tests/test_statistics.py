"""Тесты правильности статистики."""
import unittest
from collections import Counter

from phone_extractor import PhoneExtractorApp


class FakeText:
    def __init__(self, content):
        self.content = content

    def get(self, _start, _end):
        return self.content


class FakeLabel:
    def __init__(self):
        self.text = None

    def config(self, **kwargs):
        self.text = kwargs.get('text')


class FakeValue:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class TestStatisticsCalculation(unittest.TestCase):
    """Тесты расчёта статистики."""

    def test_total_vs_unique(self):
        """Общее количество vs уникальные"""
        phones = ['+79781234567', '+79161234567', '+79781234567', '+79251234567']
        total = len(phones)
        unique = len(set(phones))
        duplicates = total - unique
        self.assertEqual(total, 4)
        self.assertEqual(unique, 3)
        self.assertEqual(duplicates, 1)

    def test_exclusion_counting(self):
        """Подсчёт исключённых номеров"""
        phones = ['+79781234567', '+79161234567', '+79251234567']
        exclusions = {'+79161234567'}
        after = [p for p in phones if p not in exclusions]
        removed = len(phones) - len(after)
        self.assertEqual(removed, 1)
        self.assertEqual(len(after), 2)

    def test_dedup_after_exclusion(self):
        """Дедупликация после исключения"""
        phones = ['+79781234567', '+79161234567', '+79781234567', '+79251234567']
        exclusions = {'+79161234567'}

        # Шаг 1: исключения
        after_excl = [p for p in phones if p not in exclusions]
        removed_excl = len(phones) - len(after_excl)
        self.assertEqual(removed_excl, 1)

        # Шаг 2: дедупликация с сохранением порядка
        seen = set()
        deduped = []
        for p in after_excl:
            if p not in seen:
                seen.add(p)
                deduped.append(p)
        removed_dedup = len(after_excl) - len(deduped)
        self.assertEqual(removed_dedup, 1)  # один дубликат +79781234567

        self.assertEqual(len(deduped), 2)

    def test_country_code_distribution(self):
        """Распределение по кодам стран"""
        phones = ['+79781234567', '+79161234567', '+19175551234', '+380501234567']
        codes = {}
        for phone in phones:
            if phone.startswith('+7'):
                code = '+7'
            elif phone.startswith('+1'):
                code = '+1'
            elif phone.startswith('+380'):
                code = '+380'
            else:
                code = 'other'
            codes[code] = codes.get(code, 0) + 1

        self.assertEqual(codes['+7'], 2)
        self.assertEqual(codes['+1'], 1)
        self.assertEqual(codes['+380'], 1)

    def test_duplicate_details(self):
        """Детализация дубликатов"""
        phones = [
            '+79781234567', '+79781234567', '+79781234567',
            '+79161234567', '+79161234567',
            '+79251234567',
        ]
        counter = Counter(phones)
        dups = {phone: count for phone, count in counter.items() if count > 1}
        self.assertEqual(len(dups), 2)
        self.assertEqual(dups['+79781234567'], 3)
        self.assertEqual(dups['+79161234567'], 2)

    def test_duplicate_details_normalizes_phone_formats(self):
        """Дубликаты считаются по номеру, а не по варианту записи"""
        app = object.__new__(PhoneExtractorApp)
        details = app.get_duplicate_details([
            '+79781234567',
            '89781234567',
            '+7 (978) 123-45-67',
            '+79161234567',
        ])
        dups = {phone: count for phone, count in details.items() if count > 1}
        self.assertEqual(dups, {'+79781234567': 3})

    def test_process_phones_dedups_normalized_phone_formats(self):
        """Удаление дубликатов использует тот же нормализованный ключ"""
        app = object.__new__(PhoneExtractorApp)
        app.exclusions_text = FakeText('')
        app.remove_duplicates = FakeValue(True)
        app.sort_order = FakeValue('none')
        app.phone_format = FakeValue('plus7')
        app.prefix_entry = FakeValue('')
        app.suffix_entry = FakeValue('')

        phones = ['+79781234567', '89781234567', '+79161234567']
        self.assertEqual(app.process_phones(phones), ['+79781234567', '+79161234567'])

    def test_exclusions_match_normalized_phone_formats(self):
        """Исключения применяются к тому же номеру в другом формате"""
        app = object.__new__(PhoneExtractorApp)
        app.exclusions_text = FakeText('89781234567')
        app.remove_duplicates = FakeValue(False)
        app.sort_order = FakeValue('none')
        app.phone_format = FakeValue('plus7')
        app.prefix_entry = FakeValue('')
        app.suffix_entry = FakeValue('')

        phones = ['+79781234567', '+79161234567']
        self.assertEqual(app.process_phones(phones), ['+79161234567'])

    def test_no_duplicates(self):
        """Без дубликатов"""
        phones = ['+79781234567', '+79161234567']
        total = len(phones)
        unique = len(set(phones))
        self.assertEqual(total, unique)

    def test_empty_phones(self):
        """Пустой список"""
        phones = []
        self.assertEqual(len(phones), 0)
        self.assertEqual(len(set(phones)), 0)

    def test_percentage_calculation(self):
        """Расчёт процентов"""
        phones = ['+79781234567'] * 80 + ['+79161234567'] * 20
        total = len(phones)
        counter = Counter(phones)
        for phone, count in counter.items():
            pct = count / total * 100
            if phone == '+79781234567':
                self.assertAlmostEqual(pct, 80.0)
            else:
                self.assertAlmostEqual(pct, 20.0)


class TestExclusionNormalization(unittest.TestCase):
    """Тесты нормализации номеров в списке исключений."""

    def _normalize(self, line):
        app = object.__new__(PhoneExtractorApp)
        app.exclusions_text = FakeText(line)
        return next(iter(app.get_exclusion_list()))

    def test_plus7_format(self):
        self.assertEqual(self._normalize('+79781234567'), '+79781234567')

    def test_eight_format(self):
        self.assertEqual(self._normalize('89781234567'), '+79781234567')

    def test_seven_format(self):
        self.assertEqual(self._normalize('79781234567'), '+79781234567')

    def test_ten_digits(self):
        self.assertEqual(self._normalize('9781234567'), '+79781234567')

    def test_formatted(self):
        self.assertEqual(self._normalize('+7 (978) 123-45-67'), '+79781234567')

    def test_line_with_text_and_multiple_phones(self):
        app = object.__new__(PhoneExtractorApp)
        app.exclusions_text = FakeText('VIP +7 (978) 123-45-67 and 8 916 555 12 34')
        self.assertEqual(app.get_exclusion_list(), {'+79781234567', '+79165551234'})

    def test_ignores_non_phone_numbers(self):
        app = object.__new__(PhoneExtractorApp)
        app.exclusions_text = FakeText('order 123\ncomment only')
        self.assertEqual(app.get_exclusion_list(), set())


class TestInputCounter(unittest.TestCase):
    """Тесты счётчика символов и строк."""

    def test_single_line_counts_as_one_line(self):
        app = object.__new__(PhoneExtractorApp)
        app.input_text = FakeText('abc')
        app.input_counter_label = FakeLabel()

        app._update_input_counter()

        self.assertEqual(app.input_counter_label.text, 'Символов: 3 | Строк: 1')

    def test_empty_input_counts_zero_lines(self):
        app = object.__new__(PhoneExtractorApp)
        app.input_text = FakeText('')
        app.input_counter_label = FakeLabel()

        app._update_input_counter()

        self.assertEqual(app.input_counter_label.text, 'Символов: 0 | Строк: 0')


if __name__ == '__main__':
    unittest.main()
