-- INSERT languages
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('af', 'Afrikaans', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('am', 'Amharic', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ar', 'Arabic', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('bg', 'Bulgarian', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('bn', 'Bengali', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ca', 'Catalan', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('cmn', 'Mandarin Chinese', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('cs', 'Czech', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('cy', 'Welsh', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('da', 'Danish', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('de', 'German', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('el', 'Greek', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('en', 'English', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('es', 'Spanish', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('eu', 'Basque', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('fi', 'Finnish', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('fil', 'Filipino', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('fr', 'French', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('gl', 'Galician', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('gu', 'Gujarati', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('he', 'Hebrew', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('hi', 'Hindi', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('hu', 'Hungarian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('id', 'Indonesian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('is', 'Icelandic', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('it', 'Italian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ja', 'Japanese', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('kn', 'Kannada', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ko', 'Korean', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('lt', 'Lithuanian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('lv', 'Latvian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ml', 'Malayalam', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('mr', 'Marathi', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ms', 'Malay', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('nb', 'Norwegian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('nl', 'Dutch', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('pa', 'Punjabi', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('pl', 'Polish', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('pt', 'Portuguese', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ro', 'Romanian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ru', 'Russian', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('sk', 'Slovak', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('sr', 'Serbian', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('sv', 'Swedish', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('ta', 'Tamil', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('te', 'Telugu', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('th', 'Thai', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('tr', 'Turkish', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('uk', 'Ukrainian', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('vi', 'Vietnamese', TRUE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('yue', 'Chinese (Cantonese)', FALSE);
INSERT IGNORE INTO language (language_code, language_name, supported) VALUES ('zh', 'Chinese', TRUE);


-- INSERT language_voice with AUTO_INCREMENT PK and IGNORE
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('af', 'ZA', 'Google Text-to-Speech', 'af-ZA-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('am', 'ET', 'Google Text-to-Speech', 'am-ET-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ar', 'AE', 'Amazon Polly', 'Polly.Hala-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ar', 'XA', 'Google Text-to-Speech', 'ar-XA-Chirp3-HD-Aoede');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('bg', 'BG', 'Google Text-to-Speech', 'bg-BG-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('bn', 'IN', 'Google Text-to-Speech', 'bn-IN-Standard-C');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ca', 'ES', 'Amazon Polly', 'Polly.Arlet-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('cmn', 'CN', 'Google Text-to-Speech', 'cmn-CN-Standard-C');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('cmn', 'TW', 'Google Text-to-Speech', 'cmn-TW-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('cs', 'CZ', 'Google Text-to-Speech', 'cs-CZ-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('cy', 'GB', 'Amazon Polly', 'Polly.Gwyneth');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('da', 'DK', 'Amazon Polly', 'Polly.Naja');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('de', 'AT', 'Amazon Polly', 'Polly.Hannah-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('de', 'DE', 'Amazon Polly', 'Polly.Marlene');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'US', 'Amazon Polly', 'Polly.Salli');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('el', 'GR', 'Google Text-to-Speech', 'el-GR-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'AU', 'Amazon Polly', 'Polly.Nicole');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'GB', 'Amazon Polly', 'Polly.Amy');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'GB-WLS', 'Amazon Polly', 'Polly.Geraint');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'IE', 'Amazon Polly', 'Polly.Niamh-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'IN', 'Amazon Polly', 'Polly.Aditi');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'NZ', 'Amazon Polly', 'Polly.Aria-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('en', 'ZA', 'Amazon Polly', 'Polly.Ayanda-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('es', 'ES', 'Amazon Polly', 'Polly.Conchita');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('es', 'MX', 'Amazon Polly', 'Polly.Mia');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('es', 'US', 'Amazon Polly', 'Polly.Penelope');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('eu', 'ES', 'Google Text-to-Speech', 'eu-ES-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('fi', 'FI', 'Amazon Polly', 'Polly.Suvi-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('fil', 'PH', 'Google Text-to-Speech', 'fil-PH-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('fr', 'BE', 'Amazon Polly', 'Polly.Isabelle-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('fr', 'CA', 'Amazon Polly', 'Polly.Chantal');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('fr', 'FR', 'Amazon Polly', 'Polly.Celine');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('gl', 'ES', 'Google Text-to-Speech', 'gl-ES-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('gu', 'IN', 'Google Text-to-Speech', 'gu-IN-Standard-C');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('he', 'IL', 'Google Text-to-Speech', 'he-IL-Standard-D');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('hi', 'IN', 'Amazon Polly', 'Polly.Aditi');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('hu', 'HU', 'Google Text-to-Speech', 'hu-HU-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('id', 'ID', 'Google Text-to-Speech', 'id-ID-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('is', 'IS', 'Amazon Polly', 'Polly.Dora');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('it', 'IT', 'Amazon Polly', 'Polly.Carla');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ja', 'JP', 'Amazon Polly', 'Polly.Mizuki');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('kn', 'IN', 'Google Text-to-Speech', 'kn-IN-Standard-C');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ko', 'KR', 'Amazon Polly', 'Polly.Seoyeon');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('lt', 'LT', 'Google Text-to-Speech', 'lt-LT-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('lv', 'LV', 'Google Text-to-Speech', 'lv-LV-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ml', 'IN', 'Google Text-to-Speech', 'ml-IN-Wavenet-C');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('mr', 'IN', 'Google Text-to-Speech', 'mr-IN-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ms', 'MY', 'Google Text-to-Speech', 'ms-MY-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('nb', 'NO', 'Amazon Polly', 'Polly.Liv');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('nl', 'BE', 'Amazon Polly', 'Polly.Lisa-Neural');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('nl', 'NL', 'Amazon Polly', 'Polly.Lotte');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('pa', 'IN', 'Google Text-to-Speech', 'pa-IN-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('pl', 'PL', 'Amazon Polly', 'Polly.Ewa');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('pt', 'BR', 'Amazon Polly', 'Polly.Vitoria');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('pt', 'PT', 'Amazon Polly', 'Polly.Ines');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ro', 'RO', 'Amazon Polly', 'Polly.Carmen');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ru', 'RU', 'Amazon Polly', 'Polly.Tatyana');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('sk', 'SK', 'Google Text-to-Speech', 'sk-SK-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('sr', 'RS', 'Google Text-to-Speech', 'sr-RS-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('sv', 'SE', 'Amazon Polly', 'Polly.Astrid');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('ta', 'IN', 'Google Text-to-Speech', 'ta-IN-Standard-C');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('te', 'IN', 'Google Text-to-Speech', 'te-IN-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('th', 'TH', 'Google Text-to-Speech', 'th-TH-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('tr', 'TR', 'Amazon Polly', 'Polly.Filiz');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('uk', 'UA', 'Google Text-to-Speech', 'uk-UA-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('vi', 'VN', 'Google Text-to-Speech', 'vi-VN-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('yue', 'HK', 'Google Text-to-Speech', 'yue-HK-Standard-A');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('zh', 'CN', 'Amazon Polly', 'Polly.Zhiyu');
INSERT IGNORE INTO language_voice (language_code, region_code, voice_provider, voice_name)
VALUES ('zh', 'HK', 'Amazon Polly', 'Polly.Hiujin-Neural');