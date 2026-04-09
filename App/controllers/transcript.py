from App.controllers.transcriptsummary import *
from pypdf import PdfReader

def process_course_line(line):
    
    if isinstance(line, list):
        line = " ".join(line)
        
    parts = line.strip().split()
    if len(parts) < 4:
        return None
   
    return {'subject': parts[0], 'code': parts[1], 'title': ' '.join(parts[2:-1]), 'grade': parts[-1]}

def extract_grade(grade_str):
    grade_map = {'A+': 4.3, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0,
                 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'F': 0.0}
    
    grade = grade_map.get(grade_str.strip().upper())
    return (grade, "") if grade is not None else (None, grade_str)