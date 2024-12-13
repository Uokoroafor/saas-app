from django import forms
from django.core.validators import EmailValidator, MaxLengthValidator
from captcha.fields import CaptchaField


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        validators=[MaxLengthValidator(100)],
        widget=forms.TextInput(
            attrs={
                "class": "block p-3 w-full text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500 dark:shadow-sm-light",
                "placeholder": "First Last",
                "required": True,
            }
        ),
    )
    email = forms.EmailField(
        validators=[EmailValidator()],
        widget=forms.EmailInput(
            attrs={
                "class": "shadow-sm bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500 dark:shadow-sm-light",
                "placeholder": "name@email.com",
                "required": True,
            }
        ),
    )
    subject = forms.CharField(
        max_length=100,
        validators=[MaxLengthValidator(100)],
        widget=forms.TextInput(
            attrs={
                "class": "block p-3 w-full text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500 dark:shadow-sm-light",
                "placeholder": "Let us know how we can help you",
                "required": True,
            }
        ),
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "block p-2.5 w-full text-sm text-gray-900 bg-gray-50 rounded-lg shadow-sm border border-gray-300 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500",
                "placeholder": "Leave a comment...",
                "rows": 6,
                "required": True,
            }
        )
    )

    captcha = CaptchaField(
        label="Please enter the answer for the maths problem below. \n\nNote that multiplication is shown as '*'"
    )
