import secrets
from flask import Flask, render_template, request, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField, validators
from services import EmailService

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) 

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d')
    end_date = DateField('End Date', format='%Y-%m-%d')
    submit = SubmitField('Generate CSV')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        print("Raw start date:", form.start_date.data)
        print("Raw end date:", form.end_date.data)
        email_service = EmailService(form.email.data, form.password.data)
        csv_path = email_service.fetch_emails(form.start_date.data, form.end_date.data)
        if csv_path:
            return send_file(csv_path, as_attachment=True)
    return render_template('index.html', form=form)

if __name__ == "__main__":
    app.run(debug=True)
