# This is a sample Python script.
from pywebio.input import *
from pywebio.output import *

put_markdown("# Covid Symptoms Checker #")

symptoms = ['Fever', 'Cough', 'Headache', 'Sore Throat', 'New loss of taste or smell']

controls = [
    checkbox("Symptoms", options=symptoms, name="symptoms"),
    slider("Temperature", value=37, min_value=30, max_value=45, name="temp"),
    actions('Is this Covid?', ['Check for Covid', ], name="action")
]

result = input_group("Symptoms", controls)
temp = result['temp']
cough = 'Cough' in (result['symptoms'])
smellLoss = 'New loss of taste or smell' in (result['symptoms'])
headache = 'Headache' in (result['symptoms'])
soreThroat = 'Sore Throat' in (result['symptoms'])
fever = 'Fever' in (result['symptoms'])

print(f'{temp=}, {cough=}, {smellLoss=} {headache=}, {soreThroat=}, {fever=}')

if temp < 32:
    toast(f'Looks like you might be dead', 6)
    message = """You might be a vampire or your thermometer is broken."""
elif temp > 38 and (cough or smellLoss or headache or soreThroat or fever):
    toast(f'Looks like you have have Covid', 6)
    message = """
        Take a Covid-19 test. Stay home, isolate yourself. Notify close contacts.
        """
else:
    message = """You're fine get back to work!"""

put_markdown(message)

# I made changes to this file, I hope it's okay!
# yeah of course it's fine

#Hello ivyyy
