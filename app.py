from flask import Flask, render_template, request, redirect, url_for, session
from pyswip import Prolog
from googletrans import Translator

app = Flask(__name__)
app.secret_key = 'this_is_my_awesome_secret_98765'  # Needed for session (tracker)
prolog = Prolog()
translator = Translator()

# Load Prolog expert system
prolog.consult("first_aid.pl")

# Symptom severity mapping (for Emergency Assistance)
severe_symptoms = ['fever', 'sprain', 'severe bleeding', 'unconsciousness', 'chest pain']

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Handle Symptom Input


@app.route('/get_advice', methods=['POST'])
def get_advice():
    # Get user input and selected language
    user_input = request.form['symptom']
    selected_language = request.form.get('language', 'en')

    # Translate input to English if necessary
    if selected_language != 'en':
        translation = translator.translate(user_input, src=selected_language, dest='en')
        user_input = translation.text.lower()

    # Clean input (remove unnecessary words like 'have', 'feeling', 'pain', and retain core symptoms)
    cleaned_input = clean_input(user_input)
    symptoms = [word.strip() for word in cleaned_input.split() if word.strip()]

    # Debugging: print symptoms to ensure they are correctly passed
    print("Symptoms received:", symptoms)

    if not symptoms:
        return render_template('result.html', symptom=user_input, advice_list=["No valid symptoms detected."], emergency=False)

    # Prepare the list for Prolog query
    inputs_list_str = '[' + ', '.join([f"'{symptom}'" for symptom in symptoms]) + ']'
    print("Prolog query:", f"process_user_inputs({inputs_list_str}, AdviceList)")  # Print query to debug

    query = list(prolog.query(f"process_user_inputs({inputs_list_str}, AdviceList)"))
    print("Prolog query result:", query)  # Print the result from Prolog

    if query:
        advice_list = query[0]['AdviceList']
    else:
        advice_list = ["Sorry, no advice found for the given symptoms."]

    # Translate advice if necessary
    if selected_language != 'en':
        translated_advice_list = []
        for advice in advice_list:
            if "Watch:" in advice:
                text_part, link_part = advice.split("Watch:", 1)
                translated_text = translator.translate(text_part.strip(), src='en', dest=selected_language).text
                new_advice = translated_text + " Watch:" + link_part.strip()
            else:
                new_advice = translator.translate(advice, src='en', dest=selected_language).text
            translated_advice_list.append(new_advice)
        advice_list = translated_advice_list


    # Symptom Tracker (store in session)
    if 'symptom_history' not in session:
        session['symptom_history'] = []
    session['symptom_history'].append(user_input)

    # Emergency Assistance check
    emergency = any(symptom in severe_symptoms for symptom in symptoms)

    return render_template('result.html', symptom=user_input, advice_list=advice_list, emergency=emergency)

# Helper function to clean input and remove common stopwords
def clean_input(user_input):
    # Define a list of common words (stopwords) that should be removed
    stopwords = ['i', 'have', 'feeling', 'pain', 'is', 'and', 'the', 'a', 'an', 'my', 'your', 'in', 'to', 'of', '.', ',']

    # Convert input to lowercase and split into words
    words = user_input.lower().split()

    # Remove stopwords from the input
    cleaned_input = [word for word in words if word not in stopwords]

    # Join the cleaned list back into a string
    return ' '.join(cleaned_input)




# Symptom Tracker Page
@app.route('/tracker')
def tracker():
    history = session.get('symptom_history', [])
    return render_template('tracker.html', history=history)

# Dynamic Alias Expansion
@app.route('/add_alias', methods=['GET', 'POST'])
def add_alias():
    if request.method == 'POST':
        main_symptom = request.form['main_symptom'].lower()
        new_alias = request.form['new_alias'].lower()
        # Add dynamically to Prolog system
        prolog.assertz(f"symptom_alias({main_symptom}, ['{new_alias}'])")
        return redirect(url_for('index'))
    return render_template('add_alias.html')

if __name__ == "__main__":
    app.run(debug=True)
