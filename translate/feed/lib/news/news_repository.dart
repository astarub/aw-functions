import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:dartz/dartz.dart';
import 'package:http/http.dart' as http;
import 'package:xml/xml.dart';

import '../entities/news_entity.dart';
import '../failures/exceptions.dart';
import '../failures/failures.dart';
import 'news_datasource.dart';

class NewsRepository {
  final NewsDatasource newsDatasource;
  final context;

  NewsRepository({required this.newsDatasource, required this.context});

  Future<Either<Failure, List<NewsEntity>>> getRemoteNewsfeedAndTranslate({
    String locale = 'de',
  }) async {
    try {
      final newsXml = await newsDatasource.getNewsfeedAsXml();
      context.log('[DEBUG] RUB Feed raw XML loaded');
      final astaFeed = await newsDatasource.getAStAFeedAsJson();
      context.log('[DEBUG] AStA Feed raw: $astaFeed');
      final appFeed = await newsDatasource.getAppFeedAsJson();
      context.log('[DEBUG] AStA Feed count: ${astaFeed.length}');
      context.log('[DEBUG] App Feed count: ${appFeed.length}');
      context.log('[DEBUG] App Feed raw: $appFeed');
      context.log(
          '[DEBUG] RUB Feed count: ${newsXml.findAllElements('item').length}');
      if (astaFeed == null || astaFeed.isEmpty) {
        context.error('[-] AStA Feed is empty or null');
      }

      if (appFeed == null || appFeed.isEmpty) {
        context.error('[-] App Feed is empty or null');
      }


      final newsXmlList = newsXml.findAllElements('item');

      context.log('[#] Parsing news entities.');

      final List<NewsEntity> entities = [];

      for (final e in astaFeed) {
        final entity = NewsEntity.fromJSON(json: e, copyright: ['© AStA']);
        final pubDate = DateTime.parse(entity.pubDate);
        if (pubDate
            .isAfter(DateTime.now().subtract(const Duration(days: 21)))) {
          entities.add(entity);
        }
      }
      context
          .log('[DEBUG] Gesamtzahl News vor Übersetzung: ${entities.length}');

      for (final e in appFeed) {
        final entity = NewsEntity.fromJSON(json: e, copyright: ['© AStA']);
        final pubDate = DateTime.parse(entity.pubDate);
        if (pubDate
            .isAfter(DateTime.now().subtract(const Duration(days: 365)))) {
          entities.add(entity);
        }
      }

      await Future.forEach(newsXmlList.map((e) => e), (XmlElement e) async {
        final link = e.getElement('link')!.innerText;
        final imageData = await newsDatasource.getImageDataFromNewsUrl(link);
        entities.add(NewsEntity.fromXML(e, imageData));
      });

      context.log('[+] Parsed news entities.');

      if (locale != 'de') {
        try {
          context.log('[#] Translating news entities');
          final translatedEntitiesFutures =
              entities.map((e) => translateNewsEntity(e, locale)).toList();
          final translatedEntities =
              await Future.wait(translatedEntitiesFutures);
          context.log('[+] Translated news entities');
          return Right(translatedEntities);
        } catch (e) {
          context.error('[-] Translation failed. Error: $e');
          return Left(GeneralFailure());
        }
      } else {
        return Right(entities);
      }
    } catch (e) {
      if (e is ServerException) {
        return Left(ServerFailure());
      } else {
        return Left(GeneralFailure());
      }
    }
  }

  Future<NewsEntity> translateNewsEntity(
      NewsEntity entity, String languageCode) async {
    final endpoint = Platform.environment['APPWRITE_TRANSLATE_FUNCTION_URL'] ??
        'https://cloud.appwrite.io/v1/functions/translate/executions';

    try {
      context.log(
          '[DEBUG] Translating news: ${entity.title} (${entity.url}) → $languageCode');
      final response = await http.post(
        Uri.parse(endpoint),
        headers: {
          'Content-Type': 'application/json',
          'X-Appwrite-Project':
              Platform.environment['APPWRITE_FUNCTION_PROJECT_ID']!,
          'X-Appwrite-Key': Platform.environment['APPWRITE_FUNCTION_API_KEY']!,
        },
        body: jsonEncode({
          'newsId': entity.url,
          'title': entity.title,
          'description': entity.description,
          'text': entity.content,
          'targetLang': languageCode,
          'sourceLang': 'de',
        }),
      );

      if (response.statusCode != 200 && response.statusCode != 201) {
        throw Exception('Translation request failed: ${response.body}');
      }

      final data = jsonDecode(response.body);
      final translated = data['translated'];

      return NewsEntity(
        title: translated['title'],
        description: translated['description'],
        content: translated['content'],
        pubDate: entity.pubDate,
        imageUrl: entity.imageUrl,
        url: entity.url,
        author: entity.author,
        categoryIds: entity.categoryIds,
        copyright: entity.copyright,
        videoUrl: entity.videoUrl,
      );
    } catch (e) {
      context.error('[-] Error during translation: $e');
      // Return the original entity if translation fails
      return entity;
    }
  }
}
