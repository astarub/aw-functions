import 'dart:convert';
import 'dart:io';

import 'package:dart_appwrite/dart_appwrite.dart';
import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';

import 'entities/news_entity.dart';
import 'failures/failures.dart';
import 'news/news_datasource.dart';
import 'news/news_repository.dart';

Future<dynamic> main(final context) async {
  // Appwrite SDK Client konfigurieren
  final client = Client()
    .setEndpoint(Platform.environment['APPWRITE_FUNCTION_API_ENDPOINT']!)
    .setProject(Platform.environment['APPWRITE_FUNCTION_PROJECT_ID']!)
    .setKey(Platform.environment['APPWRITE_FUNCTION_API_KEY']!);

  final database = Databases(client);
  final dioClient = Dio();

  final newsDatasource = NewsDatasource(client: dioClient, context: context);
  final newsRepository = NewsRepository(newsDatasource: newsDatasource, context: context);

  // Lokale Sprachen aus DB abrufen (z. B. ['de', 'en'])
  List<String> supportedLocales;
  try {
    final config = await database.getDocument(
      databaseId: 'data',
      collectionId: 'config',
      documentId: 'supportedLocales',
    );
    supportedLocales = List<String>.from(config.data['value']);
  } catch (e) {
    supportedLocales = ['de', 'en'];
    context.error('[!] Fallback auf Standardsprachen: $supportedLocales');
  }

  // Schleife durch Sprachen wie ['de', 'en', 'ar']
  for (final locale in supportedLocales) {
    context.log('[#] Starte Feed-Sync für Sprache: $locale');

    final Either<Failure, List<NewsEntity>> result =
        await newsRepository.getRemoteNewsfeedAndTranslate(locale: locale);

    final List<NewsEntity> newsList = result.getOrElse(() => []);
    if (newsList.isEmpty) {
      context.error('[-] Keine News für $locale. Überspringe.');
      continue;
    }

    // Alte Dokumente im Ziel-Locale-Feed löschen
    try {
      final oldDocs = await database.listDocuments(
        databaseId: 'feed',
        collectionId: locale,
        queries: [Query.limit(1000)],
      );

      for (final doc in oldDocs.documents) {
        await database.deleteDocument(
          databaseId: 'feed',
          collectionId: locale,
          documentId: doc.$id,
        );
      }

      context.log('[✓] Alte Dokumente gelöscht (${oldDocs.total})');
    } catch (e) {
      context.error('[-] Fehler beim Löschen alter Dokumente: $e');
      continue;
    }

    // Neue News schreiben
    int saved = 0;
    for (final n in newsList) {
      try {
        await database.createDocument(
          databaseId: 'feed',
          collectionId: locale,
          documentId: ID.unique(),
          data: {
            'json': jsonEncode(n.toInternalJson()),
          },
        );
        saved++;
      } catch (e) {
        context.error('[-] Fehler beim Speichern eines News-Objekts: ${n.url}');
      }
    }

    context.log('[+] $saved Dokument(e) geschrieben für Sprache "$locale".');
  }

  context.log('[✓✓] Alle Feeds synchronisiert.');
  return context.res.send('Feeds erfolgreich synchronisiert.');
}
