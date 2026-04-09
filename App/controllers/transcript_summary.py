from dataclasses import dataclass, field
from pypdf import PdfReader
from typing import List
from App.models.transcriptSummary import *
import json
from dataclasses import asdict
from App.database import db

@dataclass
class Course:
    subject: str = ""
    code: str = ""
    grade: str = ""
    title: str = ""

@dataclass
class Report:
    student_name: str= ""
    student_id: str =""
    courses: List[Course] =field(default_factory=list)

pdf_path= "transcript.pdf"

def parse_transcript(pdf_path):
    reader =PdfReader(pdf_path)
    report =Report()

    header= False
    in_progress =False
    buffer= ""

    def extract_student_info(line):
        if "Record of:" in line:
            return "name", line.replace("Record of:", "").strip()
        if "Student Number:" in line:
            return "id", line.replace("Student Number:", "").strip()
        return None, None

    def is_header_line(line):
        return all(k in line for k in ["Subject", "Course", "Title", "Grade", "Duration"])

    def clean_word(word):
        return word.replace("0.003.00", "")

    def clean_title(title):
        return title.replace("UGS", "")

    def extract_grade(word):
        word = clean_word(word)
        if "." in word and len(word)>4 and word[0].isdigit():
            word =word[word.find('.') +3:]
        valid_grades= ["FMP","F1","F2","F3","A+","B+","C+","A-","B-","C-","A","B","C","F","I"]
        for grade in valid_grades:
            if word.startswith(grade):
                return grade,word[len(grade):]
        return None, word

    def process_course_line(words):
        course =Course()
        for word in words:
            word= clean_word(word)
            if not course.subject and word.isalpha() and word.isupper() and len(word) == 4:
                course.subject= word
                continue
            if not course.code and word.isdigit() and len(word) == 4:
                course.code =word
                continue
            if not course.grade and not in_progress:
                grade, remaining= extract_grade(word)
                if grade:
                    course.grade= grade
                    word =remaining
            if word:
                course.title += " " +word
        course.title= clean_title(course.title)
        if in_progress and not course.grade:
            course.grade= "TBA"
        return course

    for page in reader.pages:
        text =page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            line= line
            if not line or "official transcript" in line.lower():
                continue


            key, value = extract_student_info(line)
            if key =="name":
                report.student_name =value
                continue
            if key =="id":
                report.student_id= value
                continue

            if is_header_line(line):
                header=True
                buffer=""
                continue
            if "Attempt Passed" in line:
                header= False
                buffer= ""
                continue
            if "In Progress Courses" in line:
                in_progress =True
                header= True
                buffer= ""
                continue
            if "In Progress Credits" in line:
                in_progress= False
                header=False
                buffer=""
                continue
            if header:
                buffer += " " + line
                if "UGS" in buffer:
                    words= buffer.split()
                    course= process_course_line(words)
                    report.courses.append(course)
                    buffer= ""

    return report

def create_transcript_report(student_id, application_id, parsed_report_obj):
    
    try:
        
        report_json = json.dumps(asdict(parsed_report_obj))
        
        new_summary = Transcript_summary(
            student_id=student_id,
            application_id=application_id,
            report=report_json
        )
        
        db.session.add(new_summary)
        db.session.commit()
        return new_summary
    except Exception as e:
        db.session.rollback()
        print(f"Error saving transcript: {e}")
        return None

def edit_transcript_report(transcript_id, new_data_dict):
    
    summary = Transcript_summary.query.get(transcript_id)
    if not summary:
        return None

    try:
        summary.report = json.dumps(new_data_dict)
        db.session.commit()
        return summary
    except Exception as e:
        db.session.rollback()
        return None

def delete_transcript_summary(summaryid):
    try:
        summary = get_transcript_by_id(summaryid)
        db.session.delete(summary)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("the following error occured while deleting transcipt summary")
        return None