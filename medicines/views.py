from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from .forms import MedicineForm
from .models import Medicine
import qrcode
from io import BytesIO
import base64

# Translation dictionaries for offline translation
TRANSLATIONS = {
    'hi': {  # Hindi
        'about_label': 'इस दवा के बारे में',
        'batch_label': 'बैच संख्या',
        'mfg_label': 'निर्माण तिथि',
        'exp_label': 'समाप्ति तिथि',
        'mrp_label': 'अधिकतम खुदरा मूल्य (सभी करों सहित)',
        'caution_label': 'महत्वपूर्ण जानकारी',
        'expired_warning': 'चेतावनी: यह दवा समाप्त हो गई है। उपयोग न करें।',
        'footer_text': 'दवा सूचना प्रणाली',
        'need_more_info': 'अधिक जानकारी चाहिए?',
        'consult_text': 'चिकित्सा सलाह के लिए अपने स्वास्थ्य सेवा प्रदाता या फार्मासिस्ट से सलाह लें।',
        'visit_home': 'MYLE होम पर जाएं'
    },
    'bn': {  # Bengali
        'about_label': 'এই ওষুধ সম্পর্কে',
        'batch_label': 'ব্যাচ নম্বর',
        'mfg_label': 'উৎপাদনের তারিখ',
        'exp_label': 'মেয়াদ শেষের তারিখ',
        'mrp_label': 'সর্বোচ্চ খুচরা মূল্য (সমস্ত কর সহ)',
        'caution_label': 'গুরুত্বপূর্ণ তথ্য',
        'expired_warning': 'সতর্কতা: এই ওষুধের মেয়াদ শেষ হয়ে গেছে। ব্যবহার করবেন না।',
        'footer_text': 'ওষুধ তথ্য সিস্টেম',
        'need_more_info': 'আরও তথ্য প্রয়োজন?',
        'consult_text': 'চিকিৎসা পরামর্শের জন্য আপনার স্বাস্থ্যসেবা প্রদানকারী বা ফার্মাসিস্টের সাথে পরামর্শ করুন।',
        'visit_home': 'MYLE হোমে যান'
    },
    'ta': {  # Tamil
        'about_label': 'இந்த மருந்து பற்றி',
        'batch_label': 'தொகுப்பு எண்',
        'mfg_label': 'உற்பத்தி தேதி',
        'exp_label': 'காலாவதி தேதி',
        'mrp_label': 'அதிகபட்ச சில்லறை விலை (அனைத்து வரிகள் உட்பட)',
        'caution_label': 'முக்கியமான தகவல்',
        'expired_warning': 'எச்சரிக்கை: இந்த மருந்தின் காலாவதி ஆகிவிட்டது. பயன்படுத்த வேண்டாம்.',
        'footer_text': 'மருந்து தகவல் அமைப்பு',
        'need_more_info': 'மேலும் தகவல் தேவையா?',
        'consult_text': 'மருத்துவ ஆலோசனைக்கு உங்கள் சுகாதார வழங்குநர் அல்லது மருந்தாளரை அணுகவும்.',
        'visit_home': 'MYLE முகப்புக்கு செல்லுங்கள்'
    },
    'te': {  # Telugu
        'about_label': 'ఈ మందు గురించి',
        'batch_label': 'బ్యాచ్ నంబర్',
        'mfg_label': 'తయారీ తేదీ',
        'exp_label': 'గడువు తేదీ',
        'mrp_label': 'గరిష్ట రిటైల్ ధర (అన్ని పన్నులతో సహా)',
        'caution_label': 'ముఖ్యమైన సమాచారం',
        'expired_warning': 'హెచ్చరిక: ఈ మందు గడువు ముగిసింది. ఉపయోగించవద్దు.',
        'footer_text': 'మందుల సమాచార వ్యవస్థ',
        'need_more_info': 'మరింత సమాచారం కావాలా?',
        'consult_text': 'వైద్య సలహా కోసం మీ ఆరోగ్య సేవా ప్రదాత లేదా ఫార్మసిస్ట్‌ను సంప్రదించండి.',
        'visit_home': 'MYLE హోమ్‌కు వెళ్లండి'
    },
    'mr': {  # Marathi
        'about_label': 'या औषधाबद्दल',
        'batch_label': 'बॅच नंबर',
        'mfg_label': 'उत्पादन तारीख',
        'exp_label': 'कालबाह्यता तारीख',
        'mrp_label': 'कमाल किरकोळ किंमत (सर्व करांसह)',
        'caution_label': 'महत्वाची माहिती',
        'expired_warning': 'चेतावणी: या औषधाची मुदत संपली आहे. वापरू नका.',
        'footer_text': 'औषध माहिती प्रणाली',
        'need_more_info': 'अधिक माहिती हवी?',
        'consult_text': 'वैद्यकीय सल्ल्यासाठी तुमच्या आरोग्य सेवा प्रदात्याशी किंवा फार्मासिस्टशी सल्लामसलत करा.',
        'visit_home': 'MYLE मुख्यपृष्ठावर जा'
    },
    'gu': {  # Gujarati
        'about_label': 'આ દવા વિશે',
        'batch_label': 'બેચ નંબર',
        'mfg_label': 'ઉત્પાદન તારીખ',
        'exp_label': 'સમાપ્તિ તારીખ',
        'mrp_label': 'મહત્તમ છૂટક કિંમત (તમામ કર સહિત)',
        'caution_label': 'મહત્વપૂર્ણ માહિતી',
        'expired_warning': 'ચેતવણી: આ દવાની મુદત સમાપ્ત થઈ ગઈ છે. ઉપયોગ કરશો નહીં.',
        'footer_text': 'દવા માહિતી સિસ્ટમ',
        'need_more_info': 'વધુ માહિતીની જરૂર છે?',
        'consult_text': 'તબીબી સલાહ માટે તમારા આરોગ્ય સેવા પ્રદાતા અથવા ફાર્માસિસ્ટની સલાહ લો.',
        'visit_home': 'MYLE હોમ પર જાઓ'
    },
    'kn': {  # Kannada
        'about_label': 'ಈ ಔಷಧದ ಬಗ್ಗೆ',
        'batch_label': 'ಬ್ಯಾಚ್ ಸಂಖ್ಯೆ',
        'mfg_label': 'ಉತ್ಪಾದನೆ ದಿನಾಂಕ',
        'exp_label': 'ಅವಧಿ ಮೀರಿದ ದಿನಾಂಕ',
        'mrp_label': 'ಗರಿಷ್ಠ ಚಿಲ್ಲರೆ ಬೆಲೆ (ಎಲ್ಲಾ ತೆರಿಗೆಗಳೊಂದಿಗೆ)',
        'caution_label': 'ಪ್ರಮುಖ ಮಾಹಿತಿ',
        'expired_warning': 'ಎಚ್ಚರಿಕೆ: ಈ ಔಷಧದ ಅವಧಿ ಮೀರಿದೆ. ಬಳಸಬೇಡಿ.',
        'footer_text': 'ಔಷಧ ಮಾಹಿತಿ ವ್ಯವಸ್ಥೆ',
        'need_more_info': 'ಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಬೇಕೇ?',
        'consult_text': 'ವೈದ್ಯಕೀಯ ಸಲಹೆಗಾಗಿ ನಿಮ್ಮ ಆರೋಗ್ಯ ಸೇವಾ ಪೂರೈಕೆದಾರ ಅಥವಾ ಫಾರ್ಮಸಿಸ್ಟ್ ಅನ್ನು ಸಂಪರ್ಕಿಸಿ.',
        'visit_home': 'MYLE ಮುಖ್ಯಪುಟಕ್ಕೆ ಹೋಗಿ'
    },
    'ml': {  # Malayalam
        'about_label': 'ഈ മരുന്നിനെക്കുറിച്ച്',
        'batch_label': 'ബാച്ച് നമ്പർ',
        'mfg_label': 'നിർമ്മാണ തീയതി',
        'exp_label': 'കാലാവധി തീയതി',
        'mrp_label': 'പരമാവധി റീട്ടെയിൽ വില (എല്ലാ നികുതികളും ഉൾപ്പെടെ)',
        'caution_label': 'പ്രധാന വിവരങ്ങൾ',
        'expired_warning': 'മുന്നറിയിപ്പ്: ഈ മരുന്നിന്റെ കാലാവധി കഴിഞ്ഞിരിക്കുന്നു. ഉപയോഗിക്കരുത്.',
        'footer_text': 'മരുന്ന് വിവര സംവിധാനം',
        'need_more_info': 'കൂടുതൽ വിവരങ്ങൾ വേണോ?',
        'consult_text': 'വൈദ്യ ഉപദേശത്തിനായി നിങ്ങളുടെ ആരോഗ്യ പരിരക്ഷാ ദാതാവിനെയോ ഫാർമസിസ്റ്റിനെയോ സമീപിക്കുക.',
        'visit_home': 'MYLE ഹോമിലേക്ക് പോകുക'
    },
    'pa': {  # Punjabi
        'about_label': 'ਇਸ ਦਵਾਈ ਬਾਰੇ',
        'batch_label': 'ਬੈਚ ਨੰਬਰ',
        'mfg_label': 'ਨਿਰਮਾਣ ਮਿਤੀ',
        'exp_label': 'ਮਿਆਦ ਖਤਮ ਮਿਤੀ',
        'mrp_label': 'ਅਧਿਕਤਮ ਪ੍ਰਚੂਨ ਕੀਮਤ (ਸਾਰੇ ਟੈਕਸਾਂ ਸਮੇਤ)',
        'caution_label': 'ਮਹੱਤਵਪੂਰਨ ਜਾਣਕਾਰੀ',
        'expired_warning': 'ਚੇਤਾਵਨੀ: ਇਸ ਦਵਾਈ ਦੀ ਮਿਆਦ ਖਤਮ ਹੋ ਗਈ ਹੈ। ਵਰਤੋਂ ਨਾ ਕਰੋ।',
        'footer_text': 'ਦਵਾਈ ਜਾਣਕਾਰੀ ਪ੍ਰਣਾਲੀ',
        'need_more_info': 'ਹੋਰ ਜਾਣਕਾਰੀ ਚਾਹੀਦੀ ਹੈ?',
        'consult_text': 'ਡਾਕਟਰੀ ਸਲਾਹ ਲਈ ਆਪਣੇ ਸਿਹਤ ਸੇਵਾ ਪ੍ਰਦਾਤਾ ਜਾਂ ਫਾਰਮਾਸਿਸਟ ਨਾਲ ਸਲਾਹ ਕਰੋ।',
        'visit_home': 'MYLE ਘਰ ਵਿੱਚ ਜਾਓ'
    }
}

# Try to import Google Translate, but provide fallback
try:
    from googletrans import Translator
    translator = Translator()
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False


def home(request):
    """Home page view."""
    recent_medicines = Medicine.objects.all()[:5]
    return render(request, 'medicines/home.html', {'recent_medicines': recent_medicines})

def build_medicine_url(request, medicine):
    """Absolute URL for public medicine details, using the current host/scheme."""
    return request.build_absolute_uri(
        reverse('medicines:medicine_details_public', args=[medicine.batch_number])
    )


@login_required
def create_medicine_qr(request):
    """Create medicine and generate QR code."""
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save()
            messages.success(request, f'Medicine "{medicine.name}" added successfully!')
            return redirect('medicines:qr_code_display', pk=medicine.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicineForm()
    
    return render(request, 'medicines/medicine_form.html', {'form': form})


def qr_code_display(request, pk):
    """Display the QR code for a specific medicine."""
    medicine = get_object_or_404(Medicine, pk=pk)
    qr_data = build_medicine_url(request, medicine)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert image to base64 for embedding in HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'medicines/qr_code_display.html', {
        'medicine': medicine,
        'qr_code_base64': qr_code_base64
    })


@login_required
def medicine_list(request):
    """Display list of all medicines."""
    medicines = Medicine.objects.all()
    return render(request, 'medicines/medicine_list.html', {'medicines': medicines})


@require_POST
def delete_medicine(request, pk):
    """Delete a specific medicine."""
    medicine = get_object_or_404(Medicine, pk=pk)
    medicine_name = medicine.name
    medicine.delete()
    messages.success(request, f'Medicine "{medicine_name}" has been deleted successfully!')
    return redirect('medicines:medicine_list')


@require_POST
def delete_all_medicines(request):
    """Delete all medicines."""
    count = Medicine.objects.count()
    Medicine.objects.all().delete()
    messages.success(request, f'All {count} medicines have been deleted successfully!')
    return redirect('medicines:medicine_list')


@login_required
def download_qr_code(request, pk):
    """Download QR code as PNG file."""
    medicine = get_object_or_404(Medicine, pk=pk)
    qr_data = build_medicine_url(request, medicine)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Create HTTP response with image
    response = HttpResponse(content_type="image/png")
    response['Content-Disposition'] = f'attachment; filename="qr_code_{medicine.batch_number}.png"'
    img.save(response, "PNG")
    
    return response


def qr_scanner(request):
    """QR code scanner page."""
    return render(request, 'medicines/qr_scanner.html')


def medicine_details_public(request, batch_number):
    """Public medicine details page for QR code scanning."""
    try:
        medicine = Medicine.objects.get(batch_number=batch_number)
        context = {
            'medicine': medicine,
            'today': timezone.now().date(),
            'now': timezone.now(),
        }
        return render(request, 'medicines/medicine_details_public.html', context)
    except Medicine.DoesNotExist:
        messages.error(request, f'Medicine with batch number "{batch_number}" not found.')
        return render(request, 'medicines/medicine_not_found.html', {'batch_number': batch_number})


def qr_test_page(request):
    """Test page showing all QR codes for easy testing."""
    medicines = Medicine.objects.all()
    return render(request, 'medicines/qr_test_page.html', {'medicines': medicines})


@csrf_exempt
def translate_medicine_info(request):
    """API endpoint to translate medicine information."""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            target_language = data.get('language', 'en')
            
            if target_language == 'en':
                # Return English labels
                translations = {
                    'about_label': 'About this medicine',
                    'batch_label': 'Batch Number',
                    'mfg_label': 'Mfg Date',
                    'exp_label': 'Exp Date',
                    'mrp_label': 'Maximum Retail Price (Incl. of all taxes)',
                    'caution_label': 'Important Information',
                    'expired_warning': 'WARNING: This medicine has expired. Do not use.',
                    'footer_text': 'Medicine Information System',
                    'need_more_info': 'Need more information?',
                    'consult_text': 'Consult your healthcare provider or pharmacist for medical advice.',
                    'visit_home': 'Visit MYLE Home',
                    'description': data.get('description', ''),
                    'caution': data.get('caution', '')
                }
            elif target_language in TRANSLATIONS:
                # Use offline translations for Indian languages
                translations = TRANSLATIONS[target_language].copy()
                
                # For description and caution, try Google Translate if available, otherwise keep original
                description = data.get('description', '')
                caution = data.get('caution', '')
                
                if GOOGLE_TRANSLATE_AVAILABLE and description:
                    try:
                        translated_desc = translator.translate(description, dest=target_language)
                        translations['description'] = translated_desc.text
                    except Exception as e:
                        print(f"Google Translate failed for description: {e}")
                        translations['description'] = description
                else:
                    translations['description'] = description
                
                if GOOGLE_TRANSLATE_AVAILABLE and caution:
                    try:
                        translated_caution = translator.translate(caution, dest=target_language)
                        translations['caution'] = translated_caution.text
                    except Exception as e:
                        print(f"Google Translate failed for caution: {e}")
                        translations['caution'] = caution
                else:
                    translations['caution'] = caution
            else:
                # Unsupported language, return English
                translations = {
                    'about_label': 'About this medicine',
                    'batch_label': 'Batch Number',
                    'mfg_label': 'Mfg Date',
                    'exp_label': 'Exp Date',
                    'mrp_label': 'Maximum Retail Price (Incl. of all taxes)',
                    'caution_label': 'Important Information',
                    'expired_warning': 'WARNING: This medicine has expired. Do not use.',
                    'footer_text': 'Medicine Information System',
                    'need_more_info': 'Need more information?',
                    'consult_text': 'Consult your healthcare provider or pharmacist for medical advice.',
                    'visit_home': 'Visit MYLE Home',
                    'description': data.get('description', ''),
                    'caution': data.get('caution', '')
                }
            
            # Keep original medicine name, manufacturer, and other data
            translations.update({
                'medicine_name': data.get('medicine_name', ''),
                'manufacturer': data.get('manufacturer', ''),
                'batch_number': data.get('batch_number', ''),
                'mfg_date': data.get('mfg_date', ''),
                'exp_date': data.get('exp_date', ''),
                'mrp': data.get('mrp', '')
            })
            
            return JsonResponse({'translations': translations})
            
        except Exception as e:
            print(f"Translation error: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
