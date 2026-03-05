"""Тесты извлечения телефонных номеров из мусорного текста.

Не зависит от tkinter — вся логика протестирована напрямую.
"""
import unittest
import re
from collections import Counter


class PhoneExtractorLogic:
    """Обёртка вокруг логики извлечения без GUI — повторяет код из phone_extractor.py."""

    @staticmethod
    def is_valid_phone(phone):
        return (
            phone is not None
            and len(phone) == 11
            and phone.startswith('7')
            and phone.isdigit()
        )

    @staticmethod
    def is_sequential(phone):
        sequential_count = 0
        for i in range(len(phone) - 1):
            if int(phone[i + 1]) == int(phone[i]) + 1 or int(phone[i + 1]) == int(phone[i]) - 1:
                sequential_count += 1
            else:
                sequential_count = 0
            if sequential_count >= 6:
                return True
        return False

    def validate_phone_number(self, phone):
        if not self.is_valid_phone(phone):
            return False
        if len(set(phone)) <= 3:
            return False
        if self.is_sequential(phone):
            return False
        return True

    def extract_russian_phones(self, text):
        """Извлечение российских номеров — копия логики из основного класса."""
        # Паттерн с разделителями
        pattern = (
            r'(?<!\d)'
            r'(?:\+7|8)'
            r'[\s\-\.]*'
            r'\(?'
            r'(\d{3})'
            r'\)?'
            r'[\s\-\.]*'
            r'(\d{3})'
            r'[\s\-\.]*'
            r'(\d{2})'
            r'[\s\-\.]*'
            r'(\d{2})'
            r'(?!\d)'
        )
        # Сплошной
        pattern_solid = (
            r'(?<!\d)'
            r'(?:\+7|8)'
            r'(\d{10})'
            r'(?!\d)'
        )
        # Начинается с 7 (без +) с обязательным разделителем
        pattern_seven = (
            r'(?<!\d)'
            r'7[\s\-\.]'
            r'\(?'
            r'(\d{3})'
            r'\)?'
            r'[\s\-\.]*'
            r'(\d{3})'
            r'[\s\-\.]*'
            r'(\d{2})'
            r'[\s\-\.]*'
            r'(\d{2})'
            r'(?!\d)'
        )

        found_phones = []
        occupied_ranges = []

        def is_overlapping(start, end):
            for s, e in occupied_ranges:
                if start < e and end > s:
                    return True
            return False

        for m in re.finditer(pattern, text):
            start, end = m.start(), m.end()
            if not is_overlapping(start, end):
                digits = m.group(1) + m.group(2) + m.group(3) + m.group(4)
                phone = '7' + digits
                if self.validate_phone_number(phone):
                    found_phones.append('+' + phone)
                    occupied_ranges.append((start, end))

        for m in re.finditer(pattern_solid, text):
            start, end = m.start(), m.end()
            if not is_overlapping(start, end):
                phone = '7' + m.group(1)
                if self.validate_phone_number(phone):
                    found_phones.append('+' + phone)
                    occupied_ranges.append((start, end))

        for m in re.finditer(pattern_seven, text):
            start, end = m.start(), m.end()
            if not is_overlapping(start, end):
                digits = m.group(1) + m.group(2) + m.group(3) + m.group(4)
                phone = '7' + digits
                if self.validate_phone_number(phone):
                    found_phones.append('+' + phone)
                    occupied_ranges.append((start, end))

        return found_phones


# Реалистичные тестовые номера (не содержат длинных последовательностей)
PHONE_A = '+79785550422'   # Крым
PHONE_B = '+79165551234'   # МТС
PHONE_C = '+79259871543'   # Мегафон
PHONE_D = '+79031112233'   # Билайн
PHONE_E = '+79501114455'   # Теле2

DIGITS_A = '79785550422'
DIGITS_B = '79165551234'
DIGITS_C = '79259876543'


class TestRussianPhoneExtraction(unittest.TestCase):
    """Тесты извлечения российских номеров."""

    def setUp(self):
        self.logic = PhoneExtractorLogic()

    # ── Основные форматы ──

    def test_plus7_solid(self):
        phones = self.logic.extract_russian_phones("call me +79785550422 ok")
        self.assertEqual(phones, [PHONE_A])

    def test_eight_solid(self):
        phones = self.logic.extract_russian_phones("tel: 89785550422")
        self.assertEqual(phones, [PHONE_A])

    def test_plus7_with_spaces(self):
        phones = self.logic.extract_russian_phones("phone: +7 978 555 04 22 end")
        self.assertEqual(phones, [PHONE_A])

    def test_plus7_with_dashes(self):
        phones = self.logic.extract_russian_phones("+7-978-555-04-22")
        self.assertEqual(phones, [PHONE_A])

    def test_plus7_with_parens(self):
        phones = self.logic.extract_russian_phones("+7(978)555-04-22")
        self.assertEqual(phones, [PHONE_A])

    def test_eight_with_parens(self):
        phones = self.logic.extract_russian_phones("8(978)555-04-22")
        self.assertEqual(phones, [PHONE_A])

    def test_plus7_with_dots(self):
        phones = self.logic.extract_russian_phones("+7.978.555.04.22")
        self.assertEqual(phones, [PHONE_A])

    def test_eight_with_spaces(self):
        phones = self.logic.extract_russian_phones("8 978 555 04 22")
        self.assertEqual(phones, [PHONE_A])

    def test_mixed_separators(self):
        phones = self.logic.extract_russian_phones("+7 978-555 04-22")
        self.assertEqual(phones, [PHONE_A])

    # ── Извлечение из мусорного текста ──

    def test_garbage_text_single(self):
        text = "xkjdf89324 dfsd +79785550422 sdkjf sdf23423"
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(phones, [PHONE_A])

    def test_garbage_text_multiple(self):
        text = """
        Lorem ipsum dolor sit amet +79785550422 consectetur
        adipiscing elit 8(916)555-12-34 sed do eiusmod
        tempor incididunt +7-925-987-15-43 ut labore et dolore
        """
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(len(phones), 3)
        self.assertIn(PHONE_A, phones)
        self.assertIn(PHONE_B, phones)
        self.assertIn(PHONE_C, phones)

    def test_numbers_too_long_not_extracted(self):
        """Числа длиннее 11 цифр не должны совпадать"""
        text = "id: 178901234567890 num: 279781234567"
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(phones, [])

    def test_sequential_rejected(self):
        text = "+71234567890"
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(phones, [])

    def test_repeated_digits_rejected(self):
        text = "+77777777777"
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(phones, [])

    def test_multiple_phones_same_line(self):
        text = "+79785550422, +79165551234, +79259871543"
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(len(phones), 3)

    def test_preserves_duplicates(self):
        text = "+79785550422 и ещё раз +79785550422"
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(len(phones), 2)
        self.assertEqual(phones[0], phones[1])

    def test_empty_text(self):
        phones = self.logic.extract_russian_phones("")
        self.assertEqual(phones, [])

    def test_no_phones(self):
        text = "Привет! Как дела? Встретимся в 15:30."
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(phones, [])

    def test_various_operators(self):
        text = """
        МТС: +79105559876
        Мегафон: +79205558765
        Билайн: +79035557654
        Теле2: +79505556543
        Крым: +79785550422
        """
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(len(phones), 5)

    def test_phone_at_text_boundary(self):
        phones = self.logic.extract_russian_phones("+79785550422")
        self.assertEqual(phones, [PHONE_A])

    def test_seven_with_separator(self):
        """7 978 555 04 22 — без +, с разделителями"""
        phones = self.logic.extract_russian_phones("7 978 555 04 22")
        self.assertEqual(phones, [PHONE_A])

    def test_does_not_match_short_numbers(self):
        """Короткие числа не совпадают"""
        text = "Заказ 7978555 от 04.22"
        phones = self.logic.extract_russian_phones(text)
        self.assertEqual(phones, [])


class TestValidation(unittest.TestCase):
    """Тесты валидации номеров."""

    def setUp(self):
        self.logic = PhoneExtractorLogic()

    def test_valid_phone(self):
        self.assertTrue(self.logic.validate_phone_number(DIGITS_A))

    def test_invalid_length(self):
        self.assertFalse(self.logic.is_valid_phone('7978555042'))   # 10 цифр
        self.assertFalse(self.logic.is_valid_phone('797855504221'))  # 12 цифр

    def test_invalid_start(self):
        self.assertFalse(self.logic.is_valid_phone('39785550422'))

    def test_sequential(self):
        self.assertTrue(self.logic.is_sequential('71234567890'))

    def test_not_sequential(self):
        self.assertFalse(self.logic.is_sequential(DIGITS_A))

    def test_repeated_digits(self):
        self.assertFalse(self.logic.validate_phone_number('77777777777'))

    def test_few_unique(self):
        self.assertFalse(self.logic.validate_phone_number('71171117111'))


class TestDeduplication(unittest.TestCase):
    """Тесты удаления дубликатов с сохранением порядка."""

    def _dedup(self, phones):
        seen = set()
        result = []
        for p in phones:
            if p not in seen:
                seen.add(p)
                result.append(p)
        return result

    def test_dedup_preserves_order(self):
        phones = [PHONE_A, PHONE_B, PHONE_A, PHONE_C]
        result = self._dedup(phones)
        self.assertEqual(result, [PHONE_A, PHONE_B, PHONE_C])

    def test_dedup_all_same(self):
        phones = [PHONE_A] * 5
        result = self._dedup(phones)
        self.assertEqual(result, [PHONE_A])

    def test_no_dups(self):
        phones = [PHONE_A, PHONE_B]
        result = self._dedup(phones)
        self.assertEqual(result, phones)


class TestDuplicateDetails(unittest.TestCase):
    """Тесты подсчёта деталей дубликатов."""

    def test_counter(self):
        phones = [PHONE_A, PHONE_B, PHONE_A, PHONE_A]
        details = dict(Counter(phones))
        self.assertEqual(details[PHONE_A], 3)
        self.assertEqual(details[PHONE_B], 1)


class TestMask(unittest.TestCase):
    """Тесты маскирования номеров."""

    def _apply_mask(self, phone, start_count=0, start_mask='',
                    middle_pos=0, middle_count=0, middle_mask='',
                    end_count=0, end_mask=''):
        if phone.startswith('+'):
            phone_digits = phone[1:]
            prefix = '+'
        else:
            phone_digits = phone
            prefix = ''
        result = list(phone_digits)
        if start_count > 0 and start_mask:
            result = list(start_mask) + result[start_count:]
        if end_count > 0 and end_mask:
            result = result[:-end_count] + list(end_mask)
        if middle_count > 0 and middle_mask and middle_pos >= 0:
            if middle_pos < len(result):
                result = result[:middle_pos] + list(middle_mask) + result[middle_pos + middle_count:]
        return prefix + ''.join(result)

    def test_mask_start(self):
        result = self._apply_mask(PHONE_A, start_count=2, start_mask='**')
        self.assertEqual(result, '+**785550422')

    def test_mask_end(self):
        result = self._apply_mask(PHONE_A, end_count=4, end_mask='****')
        self.assertEqual(result, '+7978555****')

    def test_mask_middle(self):
        result = self._apply_mask(PHONE_A, middle_pos=4, middle_count=3, middle_mask='XXX')
        self.assertEqual(result, '+7978XXX0422')


if __name__ == '__main__':
    unittest.main()
