from flask import Flask, render_template, request,jsonify
# from flask_bootstrap import Bootstrap
import random
import spacy
from collections import Counter
# import PyPDF2
from PyPDF2 import PdfReader

# creating app
app = Flask(__name__)

# nlp = spacy.load("en_core_web_sm")
nlp=spacy.load("en_core_web_sm")

def generate_mcqs(text, num_questions=5):
    # text = clean_text(text)
    if text is None:
        return []

    # Process the text with spaCy
    doc = nlp(text)

    # Extract sentences from the text
    sentences = [sent.text for sent in doc.sents]

    # Ensure that the number of questions does not exceed the number of sentences
    num_questions = min(num_questions, len(sentences))

    # Randomly select sentences to form questions
    selected_sentences = random.sample(sentences, num_questions)

    # Initialize list to store generated MCQs
    mcqs = []

    # Generate MCQs for each selected sentence
    for sentence in selected_sentences:
        # Process the sentence with spaCy
        sent_doc = nlp(sentence)

        # Extract entities (nouns) from the sentence
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

        # Ensure there are enough nouns to generate MCQs
        if len(nouns) < 2:
            continue

        # Count the occurrence of each noun
        noun_counts = Counter(nouns)

        # Select the most common noun as the subject of the question
        if noun_counts:
            subject = noun_counts.most_common(1)[0][0]

            # Generate the question stem
            question_stem = sentence.replace(subject, "______")

            # Generate answer choices
            answer_choices = [subject]

            # Add some random words from the text as distractors
            distractors = list(set(nouns) - {subject})

            # Ensure there are at least three distractors
            while len(distractors) < 3:
                distractors.append("[Distractor]")  # Placeholder for missing distractors

            random.shuffle(distractors)
            for distractor in distractors[:3]:
                answer_choices.append(distractor)

            # Shuffle the answer choices
            random.shuffle(answer_choices)

            # Append the generated MCQ to the list
            correct_answer_index = answer_choices.index(subject)
            mcqs.append((question_stem, answer_choices, correct_answer_index))

    return mcqs

# funtion takes a file as parameter
def process_pdf(file):
    text=""
    pdf_reader=PdfReader(file)

# to check the number of pages
    for page_num in range(len(pdf_reader.pages)):
        # to extract text from pages
        page_text=pdf_reader.pages[page_num].extract_text()
        # calling function
        text+=page_text
    return text

# score
def determine_badge(score):
    if score >= 90:
        return 'Gold'
    elif score >= 70:
        return 'Silver'
    else:
        return 'Bronze'
# --

# also called flask api 
@app.route("/",methods=['POST','GET'])

def index():
    if request.method=='POST':
        text=""
        # check if files were uploaded
        if 'files[]' in request.files:
             files=request.files.getlist("files[]")
             for file in files:
                 if file.filename.endswith('.pdf'):
                    #  process pdf file
                    text += process_pdf(file)
                 else:
                    # process text file
                    text += file.read().decode('utf-8')
                     
    
        num_questions=int(request.form['num_questions'])
        mcqs=generate_mcqs(text,num_questions=num_questions) #Pass the selected number of question
        print(mcqs)

        mcqs_with_index=[(i+1,mcq)for i,mcq in enumerate(mcqs)]
        # print(mcqs_with_index)
        return render_template('mcqs.html',mcqs= mcqs_with_index)

    return render_template('index.html')
# ----
@app.route('/results', methods=['POST'])
def results():
    answers = request.json['answers']
    correct_answers = request.json['correct_answers']

    print(f'Received User Answers: {answers}')
    print(f'Received Correct Answers: {correct_answers}')
    
    # answers = [int(answer) for answer in answers if answer is not None]
    # correct_answers = [int(answer) for answer in correct_answers]

    # score = sum(1 for i in range(len(answers)) if answers[i] == correct_answers[i])

    score = sum(1 for i in range(len(answers)) if answers[i] and int(answers[i]) == int(correct_answers[i]))

    total_questions = len(correct_answers)
    percentage_score = (score / total_questions) * 100
    badge = determine_badge(percentage_score)
    print(f'Score: {score}, Total Questions: {total_questions}, Percentage: {percentage_score}, Badge: {badge}')
    return jsonify(score=score, total=total_questions, percentage=percentage_score, badge=badge)
# -----


# python main
if __name__ == '__main__':
    app.run(debug=True)