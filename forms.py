from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class LanguageDetectionForm(FlaskForm):
    text = TextAreaField(
        'Enter text to detect language',
        validators=[
            DataRequired(message='Please enter some text to analyze.'),
            Length(min=1, max=10000, message='Text must be between 1 and 10,000 characters.')
        ],
        render_kw={
            'placeholder': 'Paste or type your text here...\n\nExamples:\n• Hello, how are you today?\n• Bonjour, comment allez-vous?\n• Hola, ¿cómo estás?\n• Guten Tag, wie geht es Ihnen?',
            'rows': 8,
            'class': 'form-control'
        }
    )

    languages = StringField(
        'Enter Expected Languages (comma-separated)',
        validators=[Optional()],
        render_kw={
            'placeholder': 'e.g. en, fr, de',
            'class': 'form-control'
        }
    )

    submit = SubmitField(
        'Detect Language',
        render_kw={'class': 'btn btn-primary btn-lg'}
    )
