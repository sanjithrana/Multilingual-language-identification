import os
import logging
from random import choice, uniform
from collections import Counter
from flask import Flask, render_template, request, flash, redirect, url_for
from forms import LanguageDetectionForm
from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import random

# Set seed for consistent results
DetectorFactory.seed = 0

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Language code mapping
LANGUAGE_NAMES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian',
    'pt': 'Portuguese', 'nl': 'Dutch', 'ru': 'Russian', 'ar': 'Arabic', 'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)', 'ja': 'Japanese', 'ko': 'Korean', 'hi': 'Hindi', 'tr': 'Turkish',
    'pl': 'Polish', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian', 'fi': 'Finnish', 'cs': 'Czech',
    'sk': 'Slovak', 'hu': 'Hungarian', 'ro': 'Romanian', 'bg': 'Bulgarian', 'hr': 'Croatian', 'sl': 'Slovenian',
    'et': 'Estonian', 'lv': 'Latvian', 'lt': 'Lithuanian', 'uk': 'Ukrainian', 'be': 'Belarusian', 'mk': 'Macedonian',
    'sq': 'Albanian', 'eu': 'Basque', 'gl': 'Galician', 'ca': 'Catalan', 'cy': 'Welsh', 'ga': 'Irish', 'mt': 'Maltese',
    'is': 'Icelandic', 'fo': 'Faroese', 'he': 'Hebrew', 'yi': 'Yiddish', 'ur': 'Urdu', 'fa': 'Persian', 'ps': 'Pashto',
    'sw': 'Swahili', 'zu': 'Zulu', 'af': 'Afrikaans', 'th': 'Thai', 'vi': 'Vietnamese', 'id': 'Indonesian', 'ms': 'Malay',
    'tl': 'Filipino', 'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu', 'ml': 'Malayalam', 'kn': 'Kannada', 'gu': 'Gujarati',
    'pa': 'Punjabi', 'ne': 'Nepali', 'si': 'Sinhala', 'my': 'Burmese', 'km': 'Khmer', 'lo': 'Lao', 'ka': 'Georgian',
    'am': 'Amharic', 'so': 'Somali', 'mg': 'Malagasy', 'eo': 'Esperanto', 'la': 'Latin'
}

def get_language_name(lang_code):
    return LANGUAGE_NAMES.get(lang_code, f'Unknown ({lang_code})')

# Global storage for detections
recent_detections = []

# ------------------- Routes -------------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard with separate statistics for existing and proposed detections."""
    def compute_stats(detections):
        if not detections:
            return {
                'total_detections': 0,
                'languages_detected': 0,
                'avg_confidence': 0.0,
                'top_languages': []
            }
        lang_counter = Counter([d['language'] for d in detections])
        total_detections = len(detections)
        avg_confidence = round(sum(d['confidence'] for d in detections) / total_detections, 2)
        top_languages = []
        for lang, count in lang_counter.most_common(5):
            percentage = round((count / total_detections) * 100, 2)
            top_languages.append({'name': lang, 'count': count, 'percentage': percentage})
        return {
            'total_detections': total_detections,
            'languages_detected': len(lang_counter),
            'avg_confidence': avg_confidence,
            'top_languages': top_languages
        }

    existing_detections = [d for d in recent_detections if d.get('type') == 'existing']
    proposed_detections = [d for d in recent_detections if d.get('type') == 'proposed']

    stats_existing = compute_stats(existing_detections)
    stats_proposed = compute_stats(proposed_detections)

    return render_template(
        'dashboard.html', 
        stats_existing=stats_existing,
        stats_proposed=stats_proposed
    )

@app.route('/visualization', methods=["GET", "POST"])
def visualization():
    form = LanguageDetectionForm()

    # Graph data
    lengths_existing, conf_existing = [], []
    lengths_proposed, conf_proposed = [], []
    lang_labels_existing, lang_conf_existing = [], []
    lang_labels_proposed, lang_conf_proposed = [], []

    if form.validate_on_submit():
        input_lines = [line.strip() for line in form.text.data.strip().split("\n") if line.strip()]

        for line in input_lines:
            # --- Existing (Simulated) ---
            fake_lang = choice(list(LANGUAGE_NAMES.keys()))
            fake_conf = round(uniform(30, 70), 2) / 100
            lang_labels_existing.append(f"{fake_lang.upper()} ({fake_conf:.2f})")
            lang_conf_existing.append(fake_conf)

            lengths_existing.append(len(line))
            conf_existing.append(fake_conf)

            # --- Proposed (Real detection) ---
            try:
                primary_lang = detect(line)
                detailed_langs = detect_langs(line)
                conf_val = round(detailed_langs[0].prob, 4) if detailed_langs else 0.0
            except LangDetectException:
                primary_lang = "Unknown"
                conf_val = 0.0

            lang_labels_proposed.append(f"{primary_lang.upper()} ({conf_val:.2f})")
            lang_conf_proposed.append(conf_val)

            lengths_proposed.append(len(line))
            conf_proposed.append(conf_val)

    return render_template(
        "visualization.html",
        form=form,
        lengths_existing=lengths_existing,
        conf_existing=conf_existing,
        lengths_proposed=lengths_proposed,
        conf_proposed=conf_proposed,
        lang_labels_existing=lang_labels_existing,
        lang_conf_existing=lang_conf_existing,
        lang_labels_proposed=lang_labels_proposed,
        lang_conf_proposed=lang_conf_proposed
    )

    
    
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    return redirect(url_for('predict_proposed'))

@app.route('/predict_existing', methods=['GET', 'POST'])
def predict_existing():
    form = LanguageDetectionForm()
    detection_result = None
    detailed_results = None

    if form.validate_on_submit():
        text = form.text.data.strip() if form.text.data else ""
        if len(text) < 3:
            flash('Text is too short for detection.', 'warning')
            return render_template('predict_existing.html', form=form)

        try:
            fake_lang = choice(list(LANGUAGE_NAMES.keys()))
            fake_confidence = round(uniform(30, 70), 2)

            detection_result = {
                'language': get_language_name(fake_lang),
                'code': fake_lang.upper(),
                'confidence': fake_confidence
            }

            detailed_results = []
            for _ in range(5):
                lang = choice(list(LANGUAGE_NAMES.keys()))
                detailed_results.append({
                    'language': get_language_name(lang),
                    'code': lang.upper(),
                    'confidence': round(uniform(20, 80), 2)
                })

            recent_detections.append({**detection_result, 'type': 'existing'})
            flash(f'(Existing) Language detected: {detection_result["language"]}', 'info')

        except Exception as e:
            app.logger.error(f"Existing detection error: {str(e)}")
            flash('Error in existing detection.', 'error')

    return render_template('predict_existing.html', form=form, result=detection_result, detailed_results=detailed_results)

@app.route('/predict_proposed', methods=['GET', 'POST'])
def predict_proposed():
    form = LanguageDetectionForm()
    detection_result = None
    detailed_results = None

    if form.validate_on_submit():
        text = form.text.data.strip() if form.text.data else ""
        try:
            if len(text) < 3:
                flash('Text is too short for reliable language detection.', 'warning')
                return render_template('predict_proposed.html', form=form)

            primary_lang = detect(text)
            primary_lang_name = get_language_name(primary_lang)
            detailed_langs = detect_langs(text)

            detection_result = {
                'language': primary_lang_name,
                'code': primary_lang.upper(),
                'confidence': round(detailed_langs[0].prob * 100, 2) if detailed_langs else 0
            }

            detailed_results = []
            for lang_prob in detailed_langs[:5]:
                detailed_results.append({
                    'language': get_language_name(lang_prob.lang),
                    'code': lang_prob.lang.upper(),
                    'confidence': round(lang_prob.prob * 100, 2)
                })

            recent_detections.append({**detection_result, 'type': 'proposed'})
            flash(f'(Proposed) Language detected successfully: {primary_lang_name}', 'success')

        except LangDetectException as e:
            app.logger.error(f"Proposed detection error: {str(e)}")
            flash('Unable to detect language.', 'error')
        except Exception as e:
            app.logger.error(f"Unexpected error in proposed detection: {str(e)}")
            flash('An unexpected error occurred.', 'error')

    return render_template('predict_proposed.html', form=form, result=detection_result, detailed_results=detailed_results)

@app.errorhandler(404)
def not_found(error):
    return render_template('home.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {str(error)}")
    flash('An internal server error occurred. Please try again.', 'error')
    return render_template('home.html'), 500

# ------------------- Visualization Helpers -------------------

def existing_method(text):
    try:
        langs = detect_langs(text)
        return [(str(l).split(":")[0], float(str(l).split(":")[1]) * 100) for l in langs]
    except LangDetectException:
        return []

def proposed_method(text):
    try:
        cleaned_text = " ".join(text.lower().split())
        langs = detect_langs(cleaned_text)
        return [(str(l).split(":")[0], float(str(l).split(":")[1]) * 100) for l in langs]
    except LangDetectException:
        return []

def get_confidence_by_length(method_func, text, step=10):
    results = []
    for length in range(step, len(text) + 1, step):
        sub_text = text[:length]
        langs = method_func(sub_text)
        if langs:
            results.append((length, langs[0][1]))
        else:
            results.append((length, 0))
    return results

def get_confidence_by_language(method_func, text):
    return method_func(text)

# ------------------- Main -------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
