import 'dart:async';
import 'dart:io';

import 'package:dartz/dartz.dart';
import 'package:xml/xml.dart';

import 'entities/news_entity.dart';
import 'failures/exceptions.dart';
import 'failures/failures.dart';
import 'news_datasource.dart';
import 'translate/libre_translate_requests.dart';


class NewsRepository {
  final NewsDatasource newsDatasource;
  
  final context;

  NewsRepository({required this.newsDatasource, required this.context});


  Future<Either<Failure, List<NewsEntity>>> getRemoteNewsfeedAndTranslate({
    String locale = 'de',
  }) async {
    try {
      final newsXml = await newsDatasource.getNewsfeedAsXml();
      final astaFeed = await newsDatasource.getAStAFeedAsJson();
      final appFeed = await newsDatasource.getAppFeedAsJson();
      final newsXmlList = newsXml.findAllElements('item');

      context.log('[#] Parsing news entities. Locale: $locale');

      final List<NewsEntity> entities = [];

      for (final e in astaFeed) {
        final entity = NewsEntity.fromJSON(json: e, copyright: ['© AStA']);
        final pubDate = DateTime.parse(entity.pubDate);
        final past = DateTime.now().subtract(const Duration(days: 21));

        if (pubDate.compareTo(past) > 0) {
          entities.add(entity);
        }
      }

      for (final e in appFeed) {
        final entity = NewsEntity.fromJSON(json: e, copyright: ['© AStA']);
        final pubDate = DateTime.parse(entity.pubDate);
        final past = DateTime.now().subtract(const Duration(days: 21));

        if (pubDate.compareTo(past) > 0) {
          entities.add(entity);
        }
      }

      await Future.forEach(newsXmlList.map((news) => news), (XmlElement e) async {
        final link = e.getElement('link')!.innerText;
        final imageData = await newsDatasource.getImageDataFromNewsUrl(link);

        entities.add(NewsEntity.fromXML(e, imageData));
      });

      
      context.log('[+] Parsed news entities. Locale: $locale');

      if (locale != 'de') {
        try {
          context.log('[#] Translating news entities. Locale: $locale');
          final translatedEntitiesFutures = entities.map((e) => translateNewsEntity(e, locale)).toList();
          final translatedEntities = await Future.wait(translatedEntitiesFutures);

          context.log('[+] Translated news entities. Locale: $locale');

          return Right(translatedEntities);
        } catch (e) {
          context.error('[-] Translation failed. Error: $e');
          switch (e.runtimeType) {
            case const (HandshakeException):
              return Right(entities);
            default:
              return Left(GeneralFailure());
          }
        }
      } else {
        return Right(entities);
      }
    } catch (e) {
      switch (e.runtimeType) {
        case const (ServerException):
          return Left(ServerFailure());
        case const (HandshakeException):
          return Left(TranslationFailure());
        default:
          return Left(GeneralFailure());
      }
    }
  }


  Future<NewsEntity> translateNewsEntity(NewsEntity entity, String languageCode) async {
    // Translate title
    var translatedTitle;

    try {
      translatedTitle = await translateText(entity.title, 'auto', languageCode);
    } catch (e) {
      context.error('[-] Error while translating news entity. Error: $e');
    }

    // Translate description
    final descriptionChunks = chunk(entity.description);
    var translatedDescriptionChunks;

    try {
      translatedDescriptionChunks = await Future.wait(
        descriptionChunks.map((chunk) {
          return translateText(chunk, 'auto', languageCode);
        }),
      );
    } catch (e) {
      context.error('[-] Error while translating description chunks. Error: $e');
    }
    final translatedDescription = translatedDescriptionChunks.join();

    // Translate content
    final contentChunks = chunk(entity.content);
    var translatedContentChunks;

    try {
      translatedContentChunks = await Future.wait(
        contentChunks.map((chunk) {
          return translateText(chunk, 'auto', languageCode);
        }),
      );
    } catch (e) {
      context.error('[-] Error while translating content chunks. Error: $e');
    }
    final translatedContent = translatedContentChunks.join();

    final translatedEntity = NewsEntity(
      title: translatedTitle,
      description: translatedDescription,
      pubDate: entity.pubDate,
      imageUrl: entity.imageUrl,
      url: entity.url,
      content: translatedContent,
      author: entity.author,
      categoryIds: entity.categoryIds,
      copyright: entity.copyright,
      videoUrl: entity.videoUrl,
    );
    return translatedEntity;
  }

  List<String> chunk(String str) {
    final List<String> list = [];
    if (str.length <= 500) {
      list.add(str);
      return list;
    }
    const divisionIndex = 500;
    for (int i = 0; i < str.length; i += divisionIndex) {
      try {
        final tempString = str.substring(i, i + divisionIndex);
        list.add(tempString);
      } catch (e) {
        final tempString = str.substring(i);
        list.add(tempString);
        break;
      }
    }
    return list;
  }
}
