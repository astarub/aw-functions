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
  final client = Client()
    .setEndpoint(Platform.environment['APPWRITE_FUNCTION_API_ENDPOINT']!)
    .setProject(Platform.environment['APPWRITE_FUNCTION_PROJECT_ID'])
    .setKey(Platform.environment['APPWRITE_FUNCTION_API_KEY']);

  final database = Databases(client);

  final dioClient = Dio();

  final newsDatasource = NewsDatasource(client: dioClient, context: context);

  final newsRepository = NewsRepository(newsDatasource: newsDatasource, context: context);
  
  var supportedLocales;

  try {
    final temp = await database.getDocument(databaseId: 'data', collectionId: 'config', documentId: 'supportedLocales');
    supportedLocales = temp.data['value'];
  } catch (e) {
    supportedLocales = ['de', 'en'];

    context.error('[#] Unable to get supported locales document from the database. Falling back to locales: de, en');
  }

  for (final String locale in supportedLocales) {
    context.log('[#] Starting news retrieval for locale: $locale');

    Either<Failure, List<NewsEntity>> remoteFeed = await newsRepository.getRemoteNewsfeedAndTranslate(locale: locale);

    final Map<String, List<dynamic>> data = {
      'failures': <Failure>[],
      'news': <NewsEntity>[],
    };

    remoteFeed.fold(
      (failure) => data['failures']!.add(failure),
      (news) => data['news'] = news, // overwrite cached feed
    );


    if(data['news'] == null || data['news']!.length == 0) {
      context.log('[-] No news present. Number of failures: ${data['failures']!.length}. Continuing with the next locale on hand.');
      continue;
    }

    var documents;

    try {
      documents = await database.listDocuments(
        databaseId: 'feed',
        collectionId: locale,
        queries: [Query.limit(1000)],
      );
    } catch (e) {
      context.error('[-] Unable to retrieve documents in collection $locale. Error: $e');
    }
    
    int cleared = 0;
    bool error = false;

    for(final doc in documents.documents) {
      try {
        await database.deleteDocument(
          databaseId: 'feed',
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

    for(final NewsEntity n in data['news']!) {
      String encoded;
      try {
        encoded = jsonEncode(n.toInternalJson());
      } catch (e) {
        context.error('[-] Unable to convert news entity to json for news entity with URL: ${n.url}. Exception: $e');
        continue;
      }

      try {
        database.createDocument(databaseId: 'feed', collectionId: locale, documentId: ID.unique(), data: {
          'json': encoded,
        });
        wrote++;
      } catch(e) {
        context.error('[-] Error while creating news document. Error: $e');
      }
    }
    context.log('[+] Write process completed.');

    context.log('[+] Completed news retrieval for locale $locale. Documents written: $wrote');

    context.log('------------------------------------------------------------------------------------------------');
  }
  context.log('[++] All operations completed. News feed saved.');
  
  return context.res.send('Successfully got the RUB, AStA and App news feed.');
}