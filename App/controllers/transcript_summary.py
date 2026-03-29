from dataclasses import dataclass
from pypdf import PdfReader

@dataclass
class Course:
    subject: str = ""
    code: str = ""
    grade: str = ""
    title: str = ""


def parse_transcript(pdf_path):
    reader = PdfReader(pdf_path)

    student_name = ""
    student_id = ""
    courses = []

    header = False
    in_progress = False
    buffer = ""

    def extract_student_info(line):
        if "Record of:" in line:
            return ("name", line.replace("Record of:", "").strip())
        if "Student Number:" in line:
            return ("id", line.replace("Student Number:", "").strip())
        return (None, None)

    def is_header_line(line):
        return all(k in line for k in ["Subject", "Course", "Title", "Grade", "Duration"])

    def clean_word(word):
        return word.replace("0.003.00", "").strip()

    def clean_title(title):
        title = title.replace("UGS", "")
        return title.strip()

    def extract_grade(word):
        word = clean_word(word)

        if "." in word and len(word) > 4 and word[0].isdigit():
            word = word[word.find('.') + 3:]

        valid_grades = ["FMP","F1","F2","F3","A+","B+","C+","A-","B-","C-","A","B","C","F","I"]

        for grade in valid_grades:
            if word.startswith(grade):
                return grade, word[len(grade):]

        return None, word

    def process_course_line(words):
        course = Course()

        for word in words:
            word = clean_word(word)

            if not course.subject and word.isalpha() and word.isupper() and len(word) == 4:
                course.subject = word
                continue

            if not course.code and word.isdigit() and len(word) == 4:
                course.code = word
                continue

            if not course.grade and not in_progress:
                grade, remaining = extract_grade(word)
                if grade:
                    course.grade = grade
                    word = remaining

            if word:
                course.title += " " + word

        return course

    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue

        for line in text.splitlines():
            line = line.strip()

            if not line or "official transcript" in line.lower():
                continue

            key, value = extract_student_info(line)
            if key == "name":
                student_name = value
                continue
            elif key == "id":
                student_id = value
                continue

            if is_header_line(line):
                header = True
                buffer = ""
                continue

            if "Attempt Passed" in line:
                header = False
                buffer = ""
                continue

            if "In Progress Courses" in line:
                in_progress = True
                header = True
                buffer = ""
                continue

            if "In Progress Credits" in line:
                in_progress = False
                header = False
                buffer = ""
                continue

            if header:
                buffer += " " + line

                if "UGS" in buffer:
                    words = buffer.split()
                    course = process_course_line(words)

                    course.title = clean_title(course.title)

                    if in_progress and not course.grade:
                        course.grade = "TBA"

                    courses.append(course)
                    buffer = ""

    return {
        "student_name": student_name,
        "student_id": student_id,
        "courses": courses
    }