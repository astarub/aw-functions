import 'dart:convert';
import 'dart:io';

import 'package:appwrite_function/events/calendar_usecases.dart';
import 'package:dart_appwrite/dart_appwrite.dart';
import 'package:dio/dio.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'events/calendar_datasource.dart';
import 'events/calendar_repository.dart';
import 'entities/event_entity.dart';

Future<dynamic> main(final context) async {
  final client = Client()
    .setEndpoint(Platform.environment['APPWRITE_FUNCTION_API_ENDPOINT']!)
    .setProject(Platform.environment['APPWRITE_FUNCTION_PROJECT_ID'])
    .setKey(Platform.environment['APPWRITE_FUNCTION_API_KEY']);

  final database = Databases(client);

  final dioClient = Dio();

  final calendarDatasource = CalendarDatasource(client: dioClient, context: context);
  final calendarRepository = CalendarRepository(calendarDatasource: calendarDatasource, context: context);
  final calendarUsecases = CalendarUsecases(calendarRepository: calendarRepository, context: context);

  initializeDateFormatting();
  
  var supportedLocales;

  try {
    final temp = await database.getDocument(databaseId: 'data', collectionId: 'config', documentId: 'supportedLocales');
    supportedLocales = temp.data['value'];
  } catch (e) {
    supportedLocales = ['de', 'en'];

    context.error('[#] Unable to get supported locales document from the database. Falling back to locales: de, en');
  }

  for (final String locale in supportedLocales) {
    context.log('[#] Starting events retrieval for locale: $locale');

    final Map<String, List<dynamic>> data = await calendarUsecases.getEvents(locale);

    if(data['events'] == null || data['events']!.length == 0) {
      context.log('[-] No events present. Number of failures: ${data['failures']!.length}. Continuing with the next locale.');
      continue;
    }

    var documents;

    try {
      documents = await database.listDocuments(
        databaseId: 'calendar',
        collectionId: locale,
      );
    } catch (e) {
      context.error('[-] Unable to retrieve documents in collection $locale. Error: $e');
    }
    
    int cleared = 0;
    bool error = false;

    for(final doc in documents.documents) {
      try {
        await database.deleteDocument(
          databaseId: 'calendar',
          collectionId: locale,
          documentId: doc.$id,
        );
        cleared++;
      } catch (e) {
        context.error('[-] Unable to delete document ${doc.$id}. Error: $e');
        error = true;
        break;
      }
    }

    if(!error) context.log('[+] Cleared $cleared documents in collection $locale.');

    context.log('[#] Commencing write process.');

    int wrote = 0;

    for(final Event event in data['events']!) {
      String encoded;
      try {
        encoded = jsonEncode(event.toInternalJson());
      } catch (e) {
        context.error('[-] Unable to convert event entity to json for news entity with URL: ${event.url}');
        continue;
      }

      try {
        database.createDocument(databaseId: 'calendar', collectionId: locale, documentId: ID.unique(), data: {
          'json': encoded,
        });
        wrote++;
      } catch(e) {
        context.error('[-] Error while creating event document. Error: $e');
      }
    }
    context.log('[+] Write process completed.');

    context.log('[+] Completed events retrieval for locale $locale. Documents written: $wrote');

    context.log('------------------------------------------------------------------------------------------------');
  }
  context.log('[++] All operations completed.');
  
  return context.res.send('Successfully saved the latest calendar entities.');
}