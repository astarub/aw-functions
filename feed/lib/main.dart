import 'dart:convert';
import 'dart:io';

import 'package:dart_appwrite/dart_appwrite.dart';
import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';

import 'entities/news_entity.dart';
import 'failures/failures.dart';
import 'news_datasource.dart';
import 'news_repository.dart';

Future<dynamic> main(final context) async {
  final client = Client()
    .setEndpoint(Platform.environment['APPWRITE_FUNCTION_API_ENDPOINT']!)
    .setProject(Platform.environment['APPWRITE_FUNCTION_PROJECT_ID'])
    .setKey(Platform.environment['APPWRITE_FUNCTION_API_KEY']);

  final database = Databases(client);

  final dioClient = Dio();

  final newsDatasource = NewsDatasource(client: dioClient, context: context);

  final newsRepository = NewsRepository(newsDatasource: newsDatasource, context: context);
  
  final supportedLocalesDoc = await database.getDocument(databaseId: 'data', collectionId: 'config', documentId: 'supportedLocales');

  for (final String locale in supportedLocalesDoc.data['value']) {
    Either<Failure, List<NewsEntity>> remoteFeed = await newsRepository.getRemoteNewsfeedAndTranslate(locale: locale);

    final Map<String, List<dynamic>> data = {
      'failures': <Failure>[],
      'news': <NewsEntity>[],
    };

    remoteFeed.fold(
      (failure) => data['failures']!.add(failure),
      (news) => data['news'] = news, // overwrite cached feed
    );


    if(data['news'] == null || data['news']!.length == 0) continue;

    var documents;

    try {
      documents = await database.listDocuments(
        databaseId: 'feed',
        collectionId: locale,
      );
    } catch (e) {
      context.error("[-] Unable to retrieve documents in collection $locale. Error: $e");
    }

    for(const doc in documents) {
      try {
        await database.deleteDocument(
          databaseId: 'feed',
          collectionId: locale,
          documentId: doc.$id,
        );
      } catch (e) {
        context.error("[-] Unable to delete document ${doc.$id}. Error: $e");
      }
    }

    for(final NewsEntity n in data['news']!) {
      String encoded;
      try {
        encoded = jsonEncode(n.toInternalJson());
      } catch (e) {
        context.error('Unable to convert news entity to json for news entity with URL: ${n.url}');
        continue;
      }

      database.createDocument(databaseId: 'feed', collectionId: locale, documentId: ID.unique(), data: {
        'json': encoded,
      });
    }
  }
  return context.res.send('Successfully got the RUB, AStA and App news feed.');
}