from django import forms

class TestForm(forms.Form):
    text = forms.CharField(widget=forms.widgets.Textarea())
    mood = forms.ChoiceField(choices=[
                                      ('positive', 'Positive'),
                                      ('negative', 'Negative')
                                      ],
                             widget=forms.RadioSelect(),
                             label="Positive?"
                             )

class PlayLabsmbForm(forms.Form):
    mood = forms.ChoiceField(choices=[
                                      ('positive', 'Positive'),
                                      ('negative', 'Negative')
                                      ],
                             initial='positive',
                             widget=forms.RadioSelect(),
                             label="Positive?"
                             )
