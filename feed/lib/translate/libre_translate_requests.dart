import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import '../failures/exceptions.dart';

Future<String> translateText(String text, String sourceLang, String targetLang) async {
  final response = await http.post(
    Uri.parse('https://translate.app.asta-bochum.de/translate'),
    headers: {
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'q': text,
      'source': sourceLang,
      'target': targetLang,
      'format': 'text',
      'api_key': Platform.environment['TRANSLATE_API_KEY'],
    }),
  );

  if (response.statusCode == 200) {
    final jsonResponse = json.decode(utf8.decode(response.bodyBytes));
    return jsonResponse['translatedText'];
  } else {
    throw Exception('Status Code: ${response.statusCode}, Body: ${response.body}');
  }
}
