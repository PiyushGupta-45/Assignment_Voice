import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import Voice from '@react-native-voice/voice';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { createSong } from './songApi';
import { loadSongAudio, seekSong, toggleSongPlayback, unloadSongAudio } from './songPlayer';

// Indian Regional Languages (+ Indian English)
export const INDIAN_LANGUAGES = [
  { id: 'hindi', label: 'Hindi', nativeName: 'हिन्दी', locale: 'hi-IN', symbol: 'हि', region: 'North', vibe: 'Bollywood Pop' },
  { id: 'punjabi', label: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', locale: 'pa-IN', symbol: 'ਪੰ', region: 'North', vibe: 'Bhangra & Dhol' },
  { id: 'bhojpuri', label: 'Bhojpuri', nativeName: 'भोजपुरी', locale: 'hi-IN', symbol: 'भो', region: 'North', vibe: 'Desi Bhojpuri Beats' },
  { id: 'bengali', label: 'Bengali', nativeName: 'বাংলা', locale: 'bn-IN', symbol: 'বা', region: 'East', vibe: 'Sweet Melodic Folk' },
  { id: 'marathi', label: 'Marathi', nativeName: 'मराठी', locale: 'mr-IN', symbol: 'म', region: 'West', vibe: 'Dhol-Tasha & Lavani' },
  { id: 'gujarati', label: 'Gujarati', nativeName: 'ગુજરાતી', locale: 'gu-IN', symbol: 'ગુ', region: 'West', vibe: 'Garba & Dandiya' },
  { id: 'tamil', label: 'Tamil', nativeName: 'தமிழ்', locale: 'ta-IN', symbol: 'த', region: 'South', vibe: 'Kuthu & Melodic Beat' },
  { id: 'telugu', label: 'Telugu', nativeName: 'తెలుగు', locale: 'te-IN', symbol: 'తె', region: 'South', vibe: 'Tollywood Mass Beat' },
  { id: 'kannada', label: 'Kannada', nativeName: 'ಕನ್ನಡ', locale: 'kn-IN', symbol: 'ಕ', region: 'South', vibe: 'Sandalwood Rhythm' },
  { id: 'malayalam', label: 'Malayalam', nativeName: 'മലയാളം', locale: 'ml-IN', symbol: 'മ', region: 'South', vibe: 'Soulful Melody' },
  { id: 'haryanvi', label: 'Haryanvi', nativeName: 'हरियाणवी', locale: 'hi-IN', symbol: 'हर', region: 'North', vibe: 'Desi Raghuveer Swag' },
  { id: 'odia', label: 'Odia', nativeName: 'ଓଡ଼ିଆ', locale: 'or-IN', symbol: 'ଓ', region: 'East', vibe: 'Sweet Folk Melody' },
  { id: 'urdu', label: 'Urdu', nativeName: 'اردو', locale: 'ur-IN', symbol: 'ار', region: 'North', vibe: 'Sufi & Ghazal Vibe' },
  { id: 'english', label: 'English (India)', nativeName: 'English', locale: 'en-IN', symbol: 'IN', region: 'All-India', vibe: 'Indie Pop Rhythm' },
];

/*
const lyricLines = {
  Hindi: (name) => [
    choose([`${name}, तेरे नाम की धुन गुनगुनाए,`, `${name}, तेरी हँसी से महफ़िल मुस्काए,`, `${name}, तेरे सपनों का रंग छा जाए,`]),
    choose(['चाँद भी तेरी राह सजाए,', 'हवाएँ तेरी कहानी दोहराएँ,', 'तारे भी तेरे संग झिलमिलाएँ,']),
    choose([`${name}, दिल की हर धड़कन गाए ये गीत,`, `${name}, मन की हर गली में बजे संगीत,`, `${name}, हर पल में बसता तेरा संगीत,`]),
    choose(['तू है सबसे प्यारा मीत,', 'तेरी बातों में है जीत,', 'तू ही है इस दिल का संगीत,']),
    choose([`${name}, तेरी मुस्कान से रोशन हर प्रीत!`, `${name}, चलते रहो, ये दुनिया है तेरी!`, `${name}, खुशियों से भर जाए हर डगर तेरी!`]),
  ],
  Punjabi: (name) => [
    choose([`${name}, ਤੇਰੇ ਨਾਂ ਦੀ ਚੱਲੇ ਹਵਾ,`, `${name}, ਤੇਰੀ ਹਾਸੀ ਕਰੇ ਨਸ਼ਾ,`, `${name}, ਤੇਰੇ ਸੁਪਨਿਆਂ ਦਾ ਰੰਗ ਵੱਖਰਾ,`]),
    choose(['ਤਾਰਿਆਂ ਨੇ ਵੀ ਕੀਤਾ ਸਜਦਾ ਜਿਹਾ,', 'ਚੰਨ ਵੀ ਵੇਖੇ ਤੇਰਾ ਚਿਹਰਾ ਜਿਹਾ,', 'ਦਿਲ ਨੇ ਅੱਜ ਫਿਰ ਗੀਤ ਲਿਖਿਆ,']),
    choose([`${name}, ਦਿਲ ਦੀ ਧੜਕਣ ਗਾਵੇ ਤੇਰਾ ਗੀਤ,`, `${name}, ਹਰ ਰਾਹ ਤੇਰਾ ਬਣੇ ਸੁਹਣਾ ਮੀਤ,`, `${name}, ਢੋਲ ਦੇ ਡਗੇ ਤੇ ਨੱਚੇ ਦੁਨੀਆ ਸਾਰੀ,`]),
    choose(['ਤੂੰ ਸਾਡਾ ਸਭ ਤੋਂ ਪਿਆਰਾ ਮੀਤ,', 'ਤੇਰੀ ਰੌਣਕ ਸਭ ਤੋਂ ਜੀਤ,', 'ਤੇਰੇ ਨਾਂ ਦੀ ਚੱਲਦੀ ਰੀਤ,']),
    choose([`${name}, ਨੱਚਦੀ ਰਹੇ ਤੇਰੀ ਖੁਸ਼ੀ ਹਰ ਰੀਤ!`, `${name}, ਤੇਰੀ ਜਿੱਤ ਦਾ ਹੋਵੇ ਹਰ ਦਿਨ ਗੀਤ!`, `${name}, ਰੱਬ ਰੱਖੇ ਤੈਨੂੰ ਸਦਾ ਖੁਸ਼ ਮੀਤ!`]),
  ],
  Bhojpuri: (name) => [
    choose([`${name} जी, रउआ नाम के डंका बाजेला,`, `${name} बाबू, राउर मुस्कान दिलवा में साजेला,`, `${name}, राउर हँसी से बगिया महकेला,`]),
    choose(['माटी के खुशबू में झूम उठल मनवा,', 'पूरब के हवा गावे राउर गाना,', 'चाँद सुरूज भी करे परनामा,']),
    choose([`${name}, ढोलक के ताल प नाचे गाँव जवार,`, `${name}, राउर प्यार बा सबसे असरदार,`, `${name}, रउआ बानी सबसे शानदार,`]),
    choose(['हंसी राउर जइसे बसंत के फुहार,', 'खुशी से भरल रहे पूरा संसार,', 'जीत के आइल बा राउर बहार,']),
    choose([`${name} जी, जुग जुग जिया हमार यार!`, `${name}, चमके तारा जइसन राउर प्यार!`, `${name} बाबू, जय हो राउर हर बार!`]),
  ],
  Bengali: (name) => [
    choose([`${name}, তোমার নামের মিষ্টি সুরে মন দোলে,`, `${name}, তোমার হাসির আলোয় আকাশ খোলে,`, `${name}, তুমি তো প্রাণের প্রিয় গান,`]),
    choose(['মেঘের দেশে বাজল নতুন তান,', 'হৃদয়ে জাগে এক নতুন উড়ান,', 'নদীও গায় তোমারি জয়গান,']),
    choose([`${name}, তারারা সাজায় তোমার স্বপন মালা,`, `${name}, দূর করে দাও মনের সব জ্বালা,`, `${name}, সুরের তরীতে ভাসাও তোমার নাও,`]),
    choose(['আনন্দে ভরে উঠুক তোমার জীবন,', 'ভালোবাসায় জড়িয়ে থাকুক এই ভুবন,', 'তুমি তো সবার সেরা প্রিয়জন,']),
    choose([`${name}, চিরকাল বাজুক তোমার এই মধুর গান!`, `${name}, জয় হোক তোমার, রবে সম্মান!`, `${name}, ভালো থেকো তুমি অনন্তকাল!`]),
  ],
  Marathi: (name) => [
    choose([`${name}, तुझ्या नावाची वाजते तुतारी,`, `${name}, तुझ्या हसण्याने दुनिया झाली न्यारी,`, `${name}, तुझा थाटच आहे लई भारी,`]),
    choose(['ढोल ताशांच्या तालावर नाचू लागली ही स्वारी,', 'गुलाल उधळूया आनंदाच्या दरबारी,', 'स्वप्नांची सजली सुंदर पालखी सारी,']),
    choose([`${name}, तुझ्या पावलांनी उमटली नवी उभारी,`, `${name}, मित्रांचा राजा तू, तूच आमचा साथी,`, `${name}, सह्याद्रीच्या वाऱ्यासारखी तुझी शान,`]),
    choose(['मनामध्ये भरली सुखाची झारी,', 'कधी न कमी पडो तुझी ही भारी,', 'तुझ्या यशाचा झेंडा फडकू दे गगनावरी,']),
    choose([`${name}, तुझाच जल्लोष राहो पुढच्या पिढीवारी!`, `${name}, सदा सुखी राहा रे दोस्ता भारी!`, `${name}, जिंकत राहा दुनिया ही सारी!`]),
  ],
  Gujarati: (name) => [
    choose([`${name}, તારા નામની વાગે મીઠી શરણાઈ,`, `${name}, તારા હાસ્યથી છલકે છે ખુશાલી,`, `${name}, તારી વાતોમાં છે પ્રેમની કમાઈ,`]),
    choose(['ગરબાના તાલમાં ઝૂમે છે બધાઈ,', 'ઢોલ ઢબૂક્યો ને રમઝટ બોલાઈ,', 'આભેથી તારલાઓએ મોકલી વધાઈ,']),
    choose([`${name}, તારા સંગાથે રંગાયું આખું જીવન,`, `${name}, મોજમાં રાખે છે તારું આ મન,`, `${name}, તું જ છે અમારું વ્હાલું રતન,`]),
    choose(['સૌના હૈયે વસે તારી મીઠાશ,', 'જીવનમાં રહે સદા સુખનો ઉજાસ,', 'ખિલતો રહે તારા સપનાનો વિશ્વાસ,']),
    choose([`${name}, ગૂંજતી રહે તારી મીઠી સુવાસ!`, `${name}, સદા ખિલખિલાટ રહે તારું મુખડું!`, `${name}, તારા જીવનમાં રહે સદા આનંદનું સુખડું!`]),
  ],
  Tamil: (name) => [
    choose([`${name}, உன் பெயர் பாடும் இனிய ராகம்,`, `${name}, உன் சிரிப்பில் மலரும் அழகிய வானம்,`, `${name}, உன் வரவால் நாளும் கொண்டாட்டம்,`]),
    choose(['குத்து பாட்டுக்கு ஆடுது உள்ளம்,', 'வானத்து நிலவும் வழங்கிடும் தாளம்,', 'காற்றினில் கலக்குது உந்தன் நாதம்,']),
    choose([`${name}, வெற்றி நடை போடும் ராஜாங்கம்,`, `${name}, நெஞ்சில் நிறைந்த அன்பு தீபம்,`, `${name}, என்றும் வாழ்க உன் இனிமை கீதம்,`]),
    choose(['உன்னோடு சேர்ந்தால் மகிழ்ச்சி வெள்ளம்,', 'கனவுகள் நிஜமாகும் நல்ல காலம்,', 'எங்கும் ஒலிக்குது உன் புகழ் நாதம்,']),
    choose([`${name}, வென்று வா நீ வாழும் காலம் எல்லாம்!`, `${name}, ஒளி வீசட்டும் உந்தன் உலகம்!`, `${name}, நிலைத்து நிற்கட்டும் உன் பொன் சிரிப்பு!`]),
  ],
  Telugu: (name) => [
    choose([`${name}, నీ పేరు వింటే మోగే పల్లవి,`, `${name}, నీ నవ్వు చిందించే వెన్నెల నవ్వులు,`, `${name}, నీ రాకతో విరిసెను పూల పొదరిల్లు,`]),
    choose(['తీన్మార్ దరువుతో అదిరెను నేల,', 'గాల్లో తేలియాడెను మధుర గీతం,', 'చుక్కలు మెరిసెను నీకోసం నేడు,']),
    choose([`${name}, గుండెల్లో నిండిన స్నేహ తరంగం,`, `${name}, నీ అడుగులలో ఉరకలెత్తే ఉత్సాహం,`, `${name}, నీతో ప్రతి క్షణం ఒక పండుగలా,`]),
    choose(['విజయమే నీ చిరునామా కావాలి,', 'సంతోషం నీ ఇంట వెల్లివిరియాలి,', 'జీవితం కలకాలం రాగమై సాగాలి,']),
    choose([`${name}, కలకాలం సాగాలి నీ విజయ శంఖారావం!`, `${name}, నవ్వుతూ ఉండు ఎల్లప్పుడూ!`, `${name}, వెలుగుల దారిన సాగిపో నేస్తం!`]),
  ],
  Kannada: (name) => [
    choose([`${name}, ನಿನ್ನ ಹೆಸರೇ ಒಂದು ಮಧುರ ಗೀತೆ,`, `${name}, ನಿನ್ನ ನಗುವೇ ನಮಗೆಲ್ಲ ಹರುಷದ ಜ್ಯೋತಿ,`, `${name}, ನಿನ್ನ ಆಗಮನವೇ ಸುಂದರ ಕವಿತೆ,`]),
    choose(['ಹಾಡಿನ ಲಯದಲ್ಲಿ ತೇಲಿದೆ ಮನಸ್ಸು,', 'ಬೆಳದಿಂಗಳಂತೆ ಹೊಳೆಯಿತು ಕನಸು,', 'ಗಾಳಿಯಲಿ ತೇಲಿತು ನಿನ್ನದೇ ಸದ್ದು,']),
    choose([`${name}, ಗೆಲುವಿನ ಹಾದಿಯಲಿ ಸಾಗು ನೀ ಮುನ್ನ,`, `${name}, ಸ್ನೇಹದ ಸಿಹಿಯನು ಹಂಚಿದ ಚಿನ್ನ,`, `${name}, ಹೃದಯದ ಮಿಡಿತವು ಹಾಡಿದೆ ನಿನ್ನ,`]),
    choose(['ಪ್ರತಿ ಹೆಜ್ಜೆಯಲ್ಲೂ ಸಿಗಲಿ ನಿನಗೆ ಯಶಸ್ಸು,', 'ಸಂತಸ ತರಲಿ ಪ್ರತಿ ಹೊಸ ದಿನವು,', 'ನಿನ್ನ ನಗು ಎಂದೂ ಮಾಸದಿರಲಿ ಬದುಕು,']),
    choose([`${name}, ಸದಾ ಬೆಳಗಲಿ ನಿನ್ನ ಜೀವನದ ದೀಪ!`, `${name}, ಚಿರಕಾಲ ಉಳಿಯಲಿ ನಿನ್ನ ನಗುವಿನ ರೂಪ!`, `${name}, ನಗುನಗುತ್ತಾ ಬಾಳು ನಮ್ಮ ಪ್ರೀತಿಯ ಮಿತ್ರ!`]),
  ],
  Malayalam: (name) => [
    choose([`${name}, നിൻ പേരു ചൊല്ലുമ്പോൾ പാടും മനസ്സ്,`, `${name}, നിൻ ചിരിയിൽ വിരിയുന്നു പൂനിലാവ്,`, `${name}, നീയാണ് ഞങ്ങളുടെ പ്രിയപ്പെട്ട സ്വപ്നം,`]),
    choose(['തെന്നൽ മൂളുന്നു മധുര സംഗീതം,', 'ഓളങ്ങൾ തുള്ളുന്നു സന്തോഷ താളം,', 'മാനത്തു മിന്നുന്നു നക്ഷത്ര ദീപം,']),
    choose([`${name}, നിൻ വഴിയിൽ പൂത്തുലയട്ടെ നന്മകൾ,`, `${name}, സ്നേഹത്തിൻ തൂമഴയായ് നീ പെയ്യുമ്പോൾ,`, `${name}, നെഞ്ചിൽ ചേക്കേറുന്ന മനോഹര ഗാനം,`]),
    choose(['വിജയം തൊട്ടെഴുതും നിൻ ചരിത്രം,', 'സന്തോഷം നിറയട്ടെ നിൻ ജീവിതത്തിൽ,', 'മായാത്ത പുഞ്ചിരിയായി നീ മിന്നൂ,']),
    choose([`${name}, സന്തോഷത്തോടെ എന്നും വാഴുക നീ!`, `${name}, ഉയരങ്ങളിൽ പാറിപ്പറക്കട്ടെ നിൻ കൊടി!`, `${name}, മങ്ങാതെ നിൽക്കട്ടെ നിൻ പൊൻചിരി!`]),
  ],
  Haryanvi: (name) => [
    choose([`${name}, तेरे नाम का बजै सै डंका रै,`, `${name}, तेरी स्माइल पै मिट जा सै शंका रै,`, `${name}, तेरा टौहर पूरे गाम म्ह न्यारा सै,`]),
    choose(['डीजे पै बाज्या जब तेरा यो गाना,', 'झूम उठ्या सारा हरियाणे का ठाणा,', 'खाट पै बैठ्या भी नाचे सै ज़माना,']),
    choose([`${name}, तू सै सब तै प्यारा भाई/मित्तर,`, `${name}, चाल म्ह रुआब अर दिल म्ह सै जिगर,`, `${name}, कदे ना करिए दुनिया की फ़िकर,`]),
    choose(['हर मोड़ पै होवैगी तेरी जय-जयकार,', 'यारां की टोली म्ह तू सै सरदार,', 'खुशियां तै भर जा तेरा यो संसार,']),
    choose([`${name}, सदा भौकाल बना रहै तेरा यार!`, `${name}, जीत का परचम लहराता रहै हर बार!`, `${name}, कदे ना टूटे यो अपना प्यार!`]),
  ],
  Odia: (name) => [
    choose([`${name}, ତୁମ ନାଁ ଶୁଣିଲେ ଉଛୁଳି ଉଠେ ମନ,`, `${name}, ତୁମ ହସରେ ଝଲସେ ନୂଆ ଜୀବନ,`, `${name}, ତୁମେ ଆମ ସମସ୍ତଙ୍କ ପ୍ରିୟ ଜଣ,`]),
    choose(['ମଧୁର ତାଳରେ ବାଜେ ମିଠା ସୁର,', 'ଫୁଲର ମହକରେ ଭରିଯାଏ ଘର,', 'ଜହ୍ନ ବି ହସେ ଦେଖି ତୁମ ରୂପ ମଧୁର,']),
    choose([`${name}, ସ୍ୱପ୍ନ ସବୁ ସତ ହେଉ ତୁମ ଜୀବନେ,`, `${name}, ସଫଳତା ଆସୁ ତୁମ ପ୍ରତି ପଦକ୍ଷେପେ,`, `${name}, ସୁଖର ଲହରୀ ଖେଳୁ ପ୍ରତିଦିନେ,`]),
    choose(['ସର୍ବଦା ହସୁଥାଉ ତୁମ ମୁହଁ ସୁନ୍ଦର,', 'ଭଲପାଇବାରେ ବନ୍ଧା ରହୁ ସଂସାର,', 'ଆନନ୍ଦରେ ଭରିରହୁ ତୁମ ଅନ୍ତର,']),
    choose([`${name}, ଜୟଯୁକ୍ତ ହୁଅ ତୁମେ ସଦା ସର୍ବଦା!`, `${name}, ଖୁସିରେ ରୁହ ତୁମେ ଚିରଦିନ ସଦା!`]),
  ],
  Urdu: (name) => [
    choose([`${name}, تیرے نام کی گونجے حسیں صدا،`, `${name}, تیری مسکان سے کھلے ہر ادا،`, `${name}, تُو دل کی دھڑکن، تُو ہی دعا،`]),
    choose(['چاند بھی دیکھے تیرا راستہ سدا،', 'ہواؤں میں گھل گئی میٹھی نغمہ سرا،', 'تاروں نے بھی تجھ کو سلام کہا،']),
    choose([`${name}, تیرے سنگ چلے خوشیوں کا قافلہ،`, `${name}, تیری باتوں میں ہے پیار کی ادا،`, `${name}, تُو خوابوں کی منزل، تُو ہی رستہ،`]),
    choose(['مہکتی رہے تیری زندگی سدا،', 'کبھی نہ ہو تجھ سے غم آشنا،', 'جیت لے تُو دلوں کا یہ سلسلہ،']),
    choose([`${name}, روشن رہے تیرا نام سدا!`, `${name}, سلامت رہے تیری مسکان صدا!`, `${name}, تجھ پہ برستی رہے رب کی رضا!`]),
  ],
  English: (name) => [
    choose([`${name}, when you walk in, the music comes alive,`, `${name}, your vibrant energy helps us all thrive,`, `${name}, a superstar shining in the city sky,`]),
    choose(['The bass is pumping and the beats fly high,', 'Colors of joy dancing under open skies,', 'Every little rhythm is a sweet surprise,']),
    choose([`${name}, this catchy chorus was made for you,`, `${name}, your spirit paints the world in golden hue,`, `${name}, turn up the volume and dance on through,`]),
    choose(['Sing your melody bold and true,', 'The whole party is grooving with you,', 'Every step you take breaks right on through,']),
    choose([`${name}, you are the anthem forever brand new!`, `${name}, keep lighting up the world with your groove!`, `${name}, tonight the spotlight belongs to you!`]),
  ],
  Spanish: (name) => [
    choose([`${name}, tu nombre brilla al cantar,`, `${name}, tu risa enciende la ciudad,`, `${name}, hay magia en tu forma de soñar,`]),
    choose(['como una estrella sobre el mar,', 'como la luna en libertad,', 'y el cielo empieza a celebrar,']),
    choose([`${name}, baila libre el corazón,`, `${name}, hoy florece una ilusión,`, `${name}, eres pura inspiración,`]),
    choose(['hoy la vida tiene otro color.', 'y todo suena mucho mejor.', 'tu luz nos llena de calor.']),
    choose([`${name}, tu luz nos llena de calor!`, `${name}, contigo el mundo sabe mejor!`]),
  ],
};
*/

export default function App() {
  const [name, setName] = useState('');
  const [language, setLanguage] = useState(INDIAN_LANGUAGES[0]);
  const [listening, setListening] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [lyrics, setLyrics] = useState([]);
  const [lyricsError, setLyricsError] = useState('');
  const [song, setSong] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [positionMillis, setPositionMillis] = useState(0);
  const [durationMillis, setDurationMillis] = useState(0);
  const [seekWidth, setSeekWidth] = useState(1);
  const [downloading, setDownloading] = useState(false);

  // Quick filter & search for languages
  const [searchQuery, setSearchQuery] = useState('');
  const [regionFilter, setRegionFilter] = useState('All');

  const webRecognitionRef = useRef(null);
  const generationActiveRef = useRef(true);

  // Smart voice name formatting
  const formatSpokenName = (raw) => {
    if (!raw) return '';
    let cleaned = String(raw)
      .replace(/^(mera\s*naam|my\s*name\s*is|this\s*is|i\s*am|naam\s*hai|bol\s*raha\s*hu|bol\s*rahi\s*hu)\s*/gi, '')
      .replace(/\s*(hai|hu|h)\.?$/gi, '')
      .trim();
    if (!cleaned) cleaned = String(raw).trim();
    return cleaned.replace(/\b\w/g, (char) => char.toUpperCase());
  };

  // Live voice input handling ("jese hi user bole to type ho jaye")
  useEffect(() => {
    let mounted = true;
    try {
      Voice.onSpeechStart = () => {
        if (mounted) setListening(true);
      };

      // Real-time partial results update the input box as the user speaks!
      Voice.onSpeechPartialResults = (event) => {
        if (!mounted) return;
        const heard = formatSpokenName(event.value?.[0]);
        if (heard) setName(heard);
      };

      Voice.onSpeechResults = (event) => {
        if (!mounted) return;
        const heard = formatSpokenName(event.value?.[0]);
        if (heard) setName(heard);
        setListening(false);
      };

      Voice.onSpeechError = (e) => {
        if (!mounted) return;
        setListening(false);
        console.warn('Speech error:', e);
      };

      Voice.onSpeechEnd = () => {
        if (mounted) setListening(false);
      };
    } catch (err) {
      console.warn('Voice setup error:', err);
    }

    return () => {
      mounted = false;
      try {
        Voice.destroy().then(Voice.removeAllListeners).catch(() => {});
      } catch {}
    };
  }, []);

  useEffect(() => () => {
    generationActiveRef.current = false;
    unloadSongAudio();
  }, []);

  const listenForName = async () => {
    if (listening) {
      try {
        if (Platform.OS === 'web' && webRecognitionRef.current) {
          webRecognitionRef.current.stop();
        } else {
          await Voice.stop();
        }
      } catch {}
      setListening(false);
      return;
    }

    setListening(true);

    // Browser Web Speech API fallback
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRec) {
        try {
          const rec = new SpeechRec();
          rec.continuous = false;
          rec.interimResults = true;
          rec.lang = language.locale || 'hi-IN';

          rec.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
              transcript += event.results[i][0].transcript;
            }
            if (transcript) setName(formatSpokenName(transcript));
          };

          rec.onerror = () => setListening(false);
          rec.onend = () => setListening(false);
          webRecognitionRef.current = rec;
          rec.start();
          return;
        } catch (err) {
          console.warn('Web Speech API fallback error:', err);
        }
      }
    }

    // Native Voice start
    try {
      await Voice.start(language.locale || 'hi-IN');
    } catch {
      setListening(false);
      Alert.alert('Microphone Note', 'Could not open microphone directly. Please grant permission or type your name.');
    }
  };

  const formatTime = (millis) => {
    const seconds = Math.floor((millis || 0) / 1000);
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  };

  const loadCompletedSong = async (audioUrl) => {
    await loadSongAudio(audioUrl, (status) => {
      if (!status.isLoaded) return;
      setPositionMillis(status.positionMillis || 0);
      setDurationMillis(status.durationMillis || 0);
      setIsPlaying(Boolean(status.isPlaying));
      if (status.didJustFinish) setIsPlaying(false);
    });
  };

  const generateSong = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      Alert.alert('Tell us your name', 'Please speak or enter your name above first.');
      return;
    }

    setGenerating(true);
    setLyricsError('');
    setLyrics([]);
    setSong(null);
    setIsPlaying(false);
    setPositionMillis(0);
    setDurationMillis(0);
    await unloadSongAudio();
    try {
      // The currently bundled licensed instrumental is the birthday track.
      // Add a style picker when tracks for the other backend styles are added.
      const created = await createSong({ name: cleanName, language: language.label, style: 'birthday' });
      setLyrics(Array.isArray(created.lines) ? created.lines : []);
      await loadCompletedSong(created.audioUrl);
      setSong({ status: 'completed', audioUrl: created.audioUrl, cached: created.cached, usage: null });
    } catch (error) {
      if (Array.isArray(error?.lyrics) && error.lyrics.length) setLyrics(error.lyrics);
      else setLyrics([]);
      setLyricsError(error instanceof Error ? error.message : 'Song generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  const togglePlayback = async () => {
    try { await toggleSongPlayback(); } catch { Alert.alert('Player error', 'Could not play this temporary MP3 URL.'); }
  };

  const seekFromTap = async (event) => {
    if (!durationMillis || !seekWidth) return;
    const ratio = Math.max(0, Math.min(1, event.nativeEvent.locationX / seekWidth));
    await seekSong(durationMillis * ratio);
  };

  const downloadSong = async () => {
    if (!song?.audioUrl) return;
    setDownloading(true);
    try {
      const filename = `NameTune-${name.trim().replace(/[^a-z0-9]/gi, '-') || 'song'}-${Date.now()}.mp3`;
      const temp = await FileSystem.downloadAsync(song.audioUrl, `${FileSystem.cacheDirectory}${filename}`);
      if (Platform.OS === 'android') {
        const permission = await FileSystem.StorageAccessFramework.requestDirectoryPermissionsAsync();
        if (permission.granted) {
          const base64 = await FileSystem.readAsStringAsync(temp.uri, { encoding: FileSystem.EncodingType.Base64 });
          const destination = await FileSystem.StorageAccessFramework.createFileAsync(permission.directoryUri, filename, 'audio/mpeg');
          await FileSystem.writeAsStringAsync(destination, base64, { encoding: FileSystem.EncodingType.Base64 });
          Alert.alert('Downloaded', 'Your song was saved to the selected folder.');
          return;
        }
      }
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(temp.uri, { mimeType: 'audio/mpeg', dialogTitle: 'Save your NameTune song' });
      }
    } catch (error) {
      Alert.alert('Download failed', error instanceof Error ? error.message : 'Could not download this song.');
    } finally {
      setDownloading(false);
    }
  };

  // Filter languages based on search and region tabs
  const filteredLanguages = INDIAN_LANGUAGES.filter((item) => {
    const matchesSearch =
      item.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.nativeName.includes(searchQuery) ||
      item.vibe.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRegion =
      regionFilter === 'All' ||
      item.region.toLowerCase().includes(regionFilter.toLowerCase());
    return matchesSearch && matchesRegion;
  });
  const safeLyrics = Array.isArray(lyrics) ? lyrics : [];

  return (
    <LinearGradient colors={['#100824', '#2C104B', '#6D1951']} style={styles.page}>
      <StatusBar style="light" />
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={{ flex: 1 }}
        >
          <ScrollView
            contentContainerStyle={styles.content}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {/* Top Brand Header */}
            <View style={styles.brandRow}>
              <View style={styles.logoBadge}><Text style={styles.logo}>♪</Text></View>
              <Text style={styles.brand}>NameTune</Text>
            </View>
            <Text style={styles.title}>Your name, your song.</Text>
            <Text style={styles.subtitle}>
              Say your name, choose an Indian regional language, and create your song!
            </Text>

            {/* ========================================================================= */}
            {/* 1. VOICE REAL-TIME TYPING & MANUAL INPUT     */}
            {/* ========================================================================= */}
            <View style={styles.card}>
              <View style={styles.cardHeaderRow}>
                <Text style={styles.cardStepBadge}>1</Text>
                <Text style={styles.cardHeading}>What's your name? / आपका नाम</Text>
              </View>
              <Text style={styles.cardSub}>
                Mic dabayein aur bolein — jese hi aap bologe, turant yahan live type hoga:
              </Text>

              {/* Mic Button */}
              <Pressable
                onPress={listenForName}
                style={[styles.micBtn, listening && styles.micBtnListening]}
              >
                <Text style={styles.micIcon}>{listening ? '■' : '🎙'}</Text>
                <Text style={styles.micText}>
                  {listening ? 'Listening live... बोलिए!' : 'Tap to speak your name'}
                </Text>
              </Pressable>

              {listening && (
                <Text style={styles.liveNotice}>
                  🔴 Real-time typing active as you speak...
                </Text>
              )}

              <View style={styles.orLine}>
                <View style={styles.line} />
                <Text style={styles.or}>OR TYPE YOUR NAME</Text>
                <View style={styles.line} />
              </View>

              {/* Text Input with Clear button */}
              <View style={styles.inputBox}>
                <TextInput
                  value={name}
                  onChangeText={setName}
                  placeholder="Type your name (e.g. Rahul, Priya)..."
                  placeholderTextColor="#9F93B5"
                  style={styles.input}
                  autoCapitalize="words"
                />
                {name.length > 0 && (
                  <Pressable onPress={() => setName('')} style={styles.clearBtn}>
                    <Text style={styles.clearBtnText}>✕</Text>
                  </Pressable>
                )}
              </View>

              {name.trim().length > 0 && (
                <View style={styles.recognizedChip}>
                  <Text style={styles.chipLabel}>Name entered:</Text>
                  <Text style={styles.chipVal}>✨ {name.trim()}</Text>
                </View>
              )}
            </View>

            {/* ========================================================================= */}
            {/* 2. CHOOSE LANGUAGE (REGIONAL LANGUAGES OF INDIA)                          */}
            {/* ========================================================================= */}
            <View style={styles.card}>
              <View style={styles.cardHeaderRow}>
                <Text style={styles.cardStepBadge}>2</Text>
                <Text style={styles.cardHeading}>What is your language? / भाषा चुनें</Text>
              </View>
              <Text style={styles.cardSub}>
                Select an Indian regional language for your song:
              </Text>

              {/* Region Filter Tabs */}
              <View style={styles.regionFilterRow}>
                {['All', 'North', 'South', 'East', 'West'].map((region) => (
                  <Pressable
                    key={region}
                    onPress={() => setRegionFilter(region)}
                    style={[
                      styles.regionPill,
                      regionFilter === region && styles.regionPillActive,
                    ]}
                  >
                    <Text
                      style={[
                        styles.regionPillText,
                        regionFilter === region && styles.regionPillTextActive,
                      ]}
                    >
                      {region}
                    </Text>
                  </Pressable>
                ))}
              </View>

              {/* Fast Search Input */}
              <View style={styles.searchBox}>
                <Text style={styles.searchIcon}>🔍</Text>
                <TextInput
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                  placeholder="Search language (e.g. Punjabi, Bengali, Tamil)..."
                  placeholderTextColor="#9588A6"
                  style={styles.searchInput}
                />
                {searchQuery.length > 0 && (
                  <Pressable onPress={() => setSearchQuery('')}>
                    <Text style={styles.searchClear}>✕</Text>
                  </Pressable>
                )}
              </View>

              {/* Language Grid */}
              <View style={styles.languageGrid}>
                {filteredLanguages.map((item) => {
                  const isSelected = language.id === item.id;
                  return (
                    <Pressable
                      key={item.id}
                      onPress={() => setLanguage(item)}
                      style={[
                        styles.langCard,
                        isSelected && styles.langCardActive,
                      ]}
                    >
                      <View style={styles.langTop}>
                        <View style={[styles.langSymbol, isSelected && styles.langSymbolActive]}>
                          <Text style={styles.langSymbolText}>{item.symbol}</Text>
                        </View>
                        {isSelected && <Text style={styles.checkIcon}>✓</Text>}
                      </View>
                      <Text style={[styles.langNative, isSelected && styles.langNativeActive]}>
                        {item.nativeName}
                      </Text>
                      <Text style={[styles.langLabel, isSelected && styles.langLabelActive]}>
                        {item.label}
                      </Text>
                      <View style={styles.vibeBadge}>
                        <Text style={styles.vibeText}>{item.vibe}</Text>
                      </View>
                    </Pressable>
                  );
                })}
              </View>
            </View>

            {/* ========================================================================= */}
            {/* 3. GENERATE SONG BUTTON                                                    */}
            {/* ========================================================================= */}
            <Pressable
              disabled={generating}
              onPress={generateSong}
              style={[
                styles.generateBtn,
                generating && styles.generateBtnDisabled,
              ]}
            >
              <Text style={styles.generateBtnText}>
                {generating
                  ? `Writing lyrics and composing your ${language.label} song...`
                  : `Generate ${language.label} Song for ${name.trim() || 'You'}`}
              </Text>
            </Pressable>

            {(generating || safeLyrics.length > 0 || lyricsError) && (
              <View style={styles.songCard}>
                <Text style={styles.songPretitle}>YOUR AI-GENERATED LYRICS</Text>
                <Text style={styles.songTitle}>{name.trim() || 'Your'} · {language.label}</Text>
                {generating && (
                  <View style={styles.songStatusBox}>
                    <Text style={styles.songStatusTitle}>Creating your personalized lyrics, voice, and MP3...</Text>
                    <Text style={styles.songStatusText}>Your four lyric lines are being narrated and mixed with instrumental music.</Text>
                  </View>
                )}
                {!!lyricsError && <Text style={styles.songError}>{lyricsError}</Text>}
                {safeLyrics.length > 0 && (
                  <View style={styles.lyricsLinesWrap}>
                    {safeLyrics.map((line, index) => (
                      <View key={`${line}-${index}`} style={styles.lyricRow}>
                        <Text style={styles.lyricNum}>0{index + 1}</Text>
                        <Text style={styles.lyricText}>{line}</Text>
                      </View>
                    ))}
                  </View>
                )}
                {song?.audioUrl && (
                  <>
                    <Text style={styles.songReady}>Your MP3 song is ready for this session.</Text>
                    <View style={styles.playerRow}>
                      <Pressable onPress={togglePlayback} style={styles.playButton}>
                        <Text style={styles.playButtonText}>{isPlaying ? 'Pause' : 'Play'}</Text>
                      </Pressable>
                      <Text style={styles.timeText}>{formatTime(positionMillis)} / {formatTime(durationMillis)}</Text>
                    </View>
                    <Pressable onPress={seekFromTap} onLayout={(event) => setSeekWidth(event.nativeEvent.layout.width)} style={styles.seekTrack}>
                      <View style={[styles.seekProgress, { width: `${durationMillis ? (positionMillis / durationMillis) * 100 : 0}%` }]} />
                    </Pressable>
                    <Pressable disabled={downloading} onPress={downloadSong} style={[styles.downloadButton, downloading && styles.generateBtnDisabled]}>
                      <Text style={styles.downloadButtonText}>{downloading ? 'Preparing download...' : 'Download MP3'}</Text>
                    </Pressable>
                  </>
                )}
                {!!song?.usage?.amount_usd && <Text style={styles.priceText}>Generation cost: ${song.usage.amount_usd}</Text>}
                <Pressable disabled={generating} onPress={generateSong} style={styles.regenerateButton}>
                  <Text style={styles.regenerateText}>Generate another song</Text>
                </Pressable>
              </View>
            )}

          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1 },
  safe: { flex: 1 },
  content: { padding: 18, paddingBottom: 50 },

  // Header / Branding
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 6 },
  logoBadge: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 211, 105, 0.2)',
    borderWidth: 1,
    borderColor: '#FFD369',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: { color: '#FFD369', fontSize: 22, fontWeight: '800' },
  brand: { color: '#FFFFFF', fontSize: 22, fontWeight: '800', letterSpacing: -0.5 },
  title: { color: 'white', fontSize: 29, fontWeight: '800', letterSpacing: -0.5, marginTop: 14 },
  subtitle: { color: '#D9CEEE', fontSize: 14, lineHeight: 21, marginTop: 6, marginBottom: 20 },

  // Common Section Card
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    marginBottom: 18,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 14,
    elevation: 4,
  },
  cardHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 4 },
  cardStepBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#2C104B',
    color: '#FFD369',
    textAlign: 'center',
    lineHeight: 24,
    fontSize: 12,
    fontWeight: '800',
  },
  cardHeading: { color: '#25153E', fontWeight: '800', fontSize: 18 },
  cardSub: { color: '#726782', fontSize: 13, lineHeight: 18, marginTop: 4, marginBottom: 14 },

  // Mic & Voice
  micBtn: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: '#F5EEFD',
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderWidth: 1.5,
    borderColor: '#E2D2F9',
  },
  micBtnListening: {
    backgroundColor: '#FFEBF1',
    borderColor: '#FF7096',
  },
  micIcon: { fontSize: 22 },
  micText: { color: '#3A1869', fontWeight: '800', fontSize: 15 },
  liveNotice: {
    color: '#E61E58',
    fontWeight: '700',
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
  },

  orLine: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 9,
    marginVertical: 14,
  },
  line: { height: 1, backgroundColor: '#ECE6F2', flex: 1 },
  or: { color: '#9B90A8', fontSize: 10, fontWeight: '800', letterSpacing: 0.8 },

  inputBox: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#DED3E9',
    borderRadius: 14,
    backgroundColor: '#FAF8FC',
    paddingHorizontal: 14,
  },
  input: {
    flex: 1,
    color: '#26153D',
    height: 50,
    fontSize: 16,
    fontWeight: '600',
  },
  clearBtn: {
    padding: 6,
    borderRadius: 10,
    backgroundColor: '#E8E0F0',
  },
  clearBtnText: { color: '#564669', fontSize: 12, fontWeight: '800' },

  recognizedChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F3ECFD',
    borderRadius: 10,
    padding: 9,
    marginTop: 12,
  },
  chipLabel: { color: '#6A4D8D', fontSize: 12, fontWeight: '700' },
  chipVal: { color: '#270E4A', fontSize: 14, fontWeight: '800' },

  // Region Filters
  regionFilterRow: { flexDirection: 'row', gap: 6, marginBottom: 12, flexWrap: 'wrap' },
  regionPill: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: '#F2EDF8',
    borderWidth: 1,
    borderColor: '#E2D8ED',
  },
  regionPillActive: { backgroundColor: '#2C104B', borderColor: '#2C104B' },
  regionPillText: { color: '#5A4C6F', fontSize: 11, fontWeight: '700' },
  regionPillTextActive: { color: '#FFD369', fontWeight: '800' },

  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8F6FB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2D8EC',
    paddingHorizontal: 12,
    marginBottom: 14,
  },
  searchIcon: { fontSize: 14, marginRight: 8 },
  searchInput: { flex: 1, height: 40, color: '#26153D', fontSize: 13 },
  searchClear: { color: '#746786', fontSize: 13, padding: 6 },

  // Language Grid
  languageGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  langCard: {
    width: '48.6%',
    backgroundColor: '#F9F7FC',
    borderRadius: 14,
    padding: 11,
    borderWidth: 1.5,
    borderColor: '#E8DFEF',
  },
  langCardActive: {
    backgroundColor: '#FFF8E6',
    borderColor: '#F3B728',
  },
  langTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  langSymbol: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#EAE1F5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  langSymbolActive: { backgroundColor: '#F3B728' },
  langSymbolText: { color: '#3A1869', fontWeight: '800', fontSize: 12 },
  checkIcon: { color: '#B87E00', fontWeight: '900', fontSize: 15 },
  langNative: { color: '#26133F', fontSize: 17, fontWeight: '800', marginTop: 6 },
  langNativeActive: { color: '#8F5E00' },
  langLabel: { color: '#68597F', fontSize: 12, fontWeight: '600', marginTop: 1 },
  langLabelActive: { color: '#4D3606', fontWeight: '700' },
  vibeBadge: {
    backgroundColor: '#ECE3F6',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginTop: 6,
    alignSelf: 'flex-start',
  },
  vibeText: { color: '#54367A', fontSize: 9.5, fontWeight: '700' },

  // Generate Button
  generateBtn: {
    backgroundColor: '#FFCF6E',
    borderRadius: 16,
    paddingVertical: 17,
    alignItems: 'center',
    marginBottom: 20,
    shadowColor: '#FFCF6E',
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 4,
  },
  generateBtnDisabled: { opacity: 0.65 },
  generateBtnText: { color: '#260E43', fontSize: 16, fontWeight: '800' },

  songCard: {
    backgroundColor: 'rgba(21, 8, 45, 0.9)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.22)',
    padding: 20,
    borderRadius: 22,
    marginBottom: 25,
  },
  songPretitle: { color: '#D2C5EC', fontSize: 10, fontWeight: '800', letterSpacing: 1.2 },
  songTitle: { color: '#FFD66C', fontSize: 24, fontWeight: '900', marginTop: 4 },
  songStatusBox: { backgroundColor: 'rgba(255,255,255,.1)', borderRadius: 12, padding: 13, marginTop: 16 },
  songStatusTitle: { color: '#FFFFFF', fontWeight: '800', fontSize: 14 },
  songStatusText: { color: '#D8CEF4', fontSize: 12, lineHeight: 18, marginTop: 6 },
  songError: { color: '#FFD1D1', fontSize: 13, lineHeight: 19, marginTop: 15 },
  songReady: { color: '#BFF6D6', fontSize: 12, lineHeight: 18, marginTop: 16 },
  playerRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 16 },
  playButton: { backgroundColor: '#FFCF6E', borderRadius: 12, paddingHorizontal: 19, paddingVertical: 12 },
  playButtonText: { color: '#260E43', fontWeight: '900', fontSize: 14 },
  timeText: { color: '#F4EFFF', fontSize: 12, fontWeight: '700' },
  seekTrack: { height: 9, backgroundColor: 'rgba(255,255,255,.2)', borderRadius: 8, overflow: 'hidden', marginTop: 16 },
  seekProgress: { height: '100%', backgroundColor: '#FFCF6E', borderRadius: 8 },
  downloadButton: { backgroundColor: '#FFFFFF', alignItems: 'center', borderRadius: 12, paddingVertical: 13, marginTop: 16 },
  downloadButtonText: { color: '#31124F', fontWeight: '900', fontSize: 14 },
  priceText: { color: '#BFF6D6', fontSize: 11, marginTop: 13 },
  regenerateButton: { alignItems: 'center', borderWidth: 1, borderColor: 'rgba(255,255,255,.25)', borderRadius: 12, paddingVertical: 12, marginTop: 14 },
  regenerateText: { color: '#FFFFFF', fontSize: 13, fontWeight: '800' },

  // Lyrics Card
  lyricsCard: {
    backgroundColor: 'rgba(21, 8, 45, 0.86)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.22)',
    padding: 20,
    borderRadius: 22,
    marginBottom: 25,
  },
  lyricsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.12)',
    paddingBottom: 12,
  },
  lyricsPretitle: { color: '#D2C5EC', fontSize: 10, fontWeight: '800', letterSpacing: 1.2 },
  lyricsNameTitle: { color: '#FFD66C', fontSize: 26, fontWeight: '900', marginTop: 2 },
  lyricsLangBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.14)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  lyricsLangText: { color: '#FFFFFF', fontSize: 11, fontWeight: '700' },

  lyricsLinesWrap: { gap: 12 },
  lyricRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  lyricNum: { color: '#FFD369', fontSize: 11, fontWeight: '800', marginTop: 3, opacity: 0.75 },
  lyricText: {
    flex: 1,
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 25,
    fontWeight: '600',
    fontStyle: 'italic',
  },

  generationNote: { color: '#FFE09A', fontSize: 12, marginTop: 16, lineHeight: 17 },
  usageBox: {
    backgroundColor: 'rgba(0, 0, 0, 0.32)',
    borderRadius: 10,
    padding: 9,
    marginTop: 10,
  },
  costMeter: { color: '#BFF6D6', fontSize: 11, lineHeight: 16 },
  rawAiBox: {
    backgroundColor: 'rgba(255,255,255,.08)',
    borderRadius: 10,
    padding: 9,
    marginTop: 10,
  },
  rawAiLabel: { color: '#FFE09A', fontSize: 9.5, fontWeight: '800', letterSpacing: 1 },
  rawAiText: { color: '#F7F2FF', fontSize: 11.5, lineHeight: 16, marginTop: 4 },
  saveState: { color: '#C8BEEC', fontSize: 11.5, marginTop: 12, lineHeight: 16 },

  cardActionsRow: { flexDirection: 'row', gap: 10, marginTop: 16 },
  actionBtn: {
    backgroundColor: 'rgba(255, 255, 255, 0.14)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  actionBtnText: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },
});
