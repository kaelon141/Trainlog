import json
import os

import pycountry
from googletrans import Translator

# Initialize the translator
translator = Translator()


def translate_text(text, source_lang, target_lang):
    try:
        translated = translator.translate(text, src=source_lang, dest=target_lang)
        if translated and translated.text:
            return translated.text
        else:
            raise ValueError("Invalid translation received")
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def get_flag_emoji(country_code):
    if country_code == "en":
        country_code = "GB"
    return "".join([chr(127397 + ord(char)) for char in country_code.upper()])


def get_language_from_country_code(country_code):
    try:
        language_code = pycountry.languages.get(alpha_2=country_code.lower())
        if language_code:
            return language_code.name
        else:
            return None
    except Exception as e:
        print(f"Error retrieving language for {country_code}: {e}")
        return None


def process_nested_lists(value, target_list, index, source_lang, target_lang):
    if isinstance(value[index], list):
        if len(target_list) <= index:
            target_list.append([])
        for sub_index, sub_item in enumerate(value[index]):
            process_nested_lists(
                value[index], target_list[index], sub_index, source_lang, target_lang
            )
    else:
        if len(target_list) <= index:
            translated_item = translate_text(value[index], source_lang, target_lang)
            target_list.append(translated_item)


# Load the en.json file
with open("lang/en.json", "r", encoding="utf-8") as file:
    en_content = json.load(file)

# List all language files in the lang folder
lang_files = [
    f
    for f in os.listdir("lang")
    if os.path.isfile(os.path.join("lang", f)) and f != "en.json"
]

# Add new languages to en.json after "en"
for lang_file in lang_files:
    language_code = lang_file.split(".")[0]
    if language_code not in en_content:
        language_name = get_language_from_country_code(language_code)
        if language_name:
            flag = get_flag_emoji(language_code)

            # Insert the new language entry right after "en"
            en_keys = list(en_content.keys())
            en_index = en_keys.index("en")
            en_keys.insert(en_index + 1, language_code)
            en_content = {
                key: en_content[key]
                if key != language_code
                else f"{flag} {language_name}"
                for key in en_keys
            }

for lang_file in lang_files:
    language_code = lang_file.split(".")[0]
    print(f"Processing {lang_file}...")

    with open(f"lang/{lang_file}", "r", encoding="utf-8") as file:
        lang_content = (
            json.load(file) if os.path.getsize(f"lang/{lang_file}") > 0 else {}
        )

    for key, value in en_content.items():
        if isinstance(value, list):
            if key not in lang_content:
                lang_content[key] = []
            for index, _ in enumerate(value):
                process_nested_lists(
                    value, lang_content[key], index, "en", language_code
                )
        else:
            if key not in lang_content:
                lang_content[key] = translate_text(value, "en", language_code)

    # Re-order the keys based on en_content
    lang_content = {key: lang_content.get(key, "") for key in en_content}

    # Save the updated language file
    with open(f"lang/{lang_file}", "w", encoding="utf-8") as file:
        json.dump(lang_content, file, ensure_ascii=False, indent=4)

# Save back the updated en.json file
with open("lang/en.json", "w", encoding="utf-8") as file:
    json.dump(en_content, file, ensure_ascii=False, indent=4)

print("Processing complete!")
