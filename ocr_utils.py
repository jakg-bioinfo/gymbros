import easyocr

reader = easyocr.Reader(['en'], gpu=False)  # Make sure GPU=False if you don't have GPU

def extract_metrics(image_path):
    results = reader.readtext(image_path, detail=0)

    extracted_data = {}
    user_name = "Unknown"  # Default if not found

    # Attempt to find User Name
    for i, text in enumerate(results):
        if 'name' in text.lower() or 'user' in text.lower() or 'profile' in text.lower():
            try:
                user_candidate = results[i+1]
                if len(user_candidate) > 2 and not any(c.isdigit() for c in user_candidate):  # Avoid numbers
                    user_name = user_candidate.strip()
            except IndexError:
                pass

    metrics_mapping = {
        'Weight': ['weight', 'wight'],
        'BMI': ['bmi'],
        'Body Fat': ['body fat', 'fat'],
        'Fat mass': ['fat mass'],
        'Fat-free Body Weight': ['fat-free', 'fat free'],
        'Muscle mass': ['muscle mass'],
        'Muscle rate': ['muscle rate'],
        'Skeletal muscle': ['skeletal muscle'],
        'Bone Mass': ['bone mass'],
        'Protein mass': ['protein mass'],
        'Protein': ['protein'],
        'Water weight': ['water weight'],
        'Body Water': ['body water'],
        'Subcutaneous fat': ['subcutaneous fat'],
        'Visceral Fat': ['visceral fat'],
        'BMR': ['bmr'],
        'Body age': ['body age'],
        'Obesity level': ['obesity level'],
        'Ideal body weight': ['ideal body weight'],
        'Body type': ['body type']
    }

    for i, text in enumerate(results):
        for key, keywords in metrics_mapping.items():
            if any(keyword.lower() in text.lower() for keyword in keywords):
                try:
                    value = results[i+1]
                    clean_value = ''.join(c for c in value if (c.isdigit() or c == '.' or c == '%'))
                    if '%' in value:
                        clean_value = clean_value.replace('%', '')
                    if clean_value:
                        extracted_data[key] = float(clean_value)
                except (IndexError, ValueError):
                    pass

    extracted_data['user'] = user_name  # Add extracted username
    return extracted_data
