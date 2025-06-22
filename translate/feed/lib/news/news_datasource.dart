import 'dart:io';
import 'dart:isolate';

import 'package:dio/dio.dart';
import 'package:html/parser.dart' as html;
import 'package:xml/xml.dart';

import '../failures/exceptions.dart';

class NewsDatasource {
  /// Dio client to perfrom network operations
  final Dio client;
  final context;

  NewsDatasource({
    required this.client,
    required this.context
  });

  /// Request news feed from news.rub.de/newsfeed.
  /// Throws a server excpetion if respond code is not 200.
  Future<XmlDocument> getNewsfeedAsXml() async {
    context.log('[#] Retrieving RUB news feed.');
    // return type is xml-v1.
    final response = await client.get(Platform.environment['RUB_NEWS_FEED_URL'] ?? 'https://news.rub.de/newsfeed');

    if (response.statusCode != 200) {
      context.error('Unable to retrieve the RUB news feed: Status code: ${response.statusCode}');

      throw ServerException();
    } else {
      context.log('[+] Retrieved RUB news feed.');
      return XmlDocument.parse(response.data);
    }
  }

  /// Request image url and copyright text from linked news
  /// Throws a server excpetion if respond code is not 200.
  Future<Map<String, dynamic>> getImageDataFromNewsUrl(String url) async {
    final Map<String, dynamic> data = {
      'copyright': <String>[],
      'imageUrls': <String>[],
    };

    final response = await client.get(url);

    if (response.statusCode != 200) {
      context.error('Unable to retrieve image: Status code: ${response.statusCode}; URL: $url');

      throw ServerException();
    } else {
      final document = html.parse(response.data);
      final htmlClass = document.getElementsByClassName('field-std-bild-artikel');

      // some news has multiple images with different HTML paths
      if (htmlClass.isEmpty) {
        // multiple image
        final images = document.getElementsByClassName('bst-bild');
        for (int i = 0; i < images.length; i++) {
          final copyright = document.getElementsByClassName('bildzeile-copyright')[i].text;

          List.castFrom(data['copyright']).add(copyright);
          List.castFrom(data['imageUrls']).add(images[i].getElementsByTagName('img')[0].attributes['src'].toString());
        }
      } else {
        final copyright = document.getElementsByClassName('bildzeile-copyright')[0].text;

        List.castFrom(data['copyright']).add(copyright);
        List.castFrom(data['imageUrls']).add(
          document
              .getElementsByClassName('field-std-bild-artikel')[0]
              .getElementsByTagName('img')[0]
              .attributes['src']
              .toString(),
        );
      }

      return data;
    }
  }

  /// Request posts from asta-bochum.de
  /// Throws a server exception if respond code is not 200.
  Future<List<dynamic>> getAStAFeedAsJson() async {
    context.log('[#] Retrieving AStA news feed.');
    final response = await client.get(Platform.environment['ASTA_FEED_URL'] ?? 'https://asta-bochum.de/wp-json/wp/v2/posts');

    if (response.statusCode != 200) {
      context.error('Unable to retrieve the asta feed: Status code: ${response.statusCode}');
      throw ServerException();
    } else {
      context.log('[+] Retrieved AStA news feed.');
      return response.data;
    }
  }

  /// Request posts from app.asta-bochum.de
  /// Throws a server exception if respond code is not 200.
  Future<List<dynamic>> getAppFeedAsJson() async {
  context.log('[#] Retrieving app news feed.');
  final response = await client.get(
    Platform.environment['APP_FEED_URL'] ?? 'https://app.asta-bochum.de/wp-json/wp/v2/posts',
  );

  if (response.statusCode != 200) {
    context.error('Unable to retrieve the app feed: Status code: ${response.statusCode}');
    throw ServerException();
  }

  final List<dynamic> data = response.data;

  // Header prüfen
  final pageHeader = response.headers.value('x-wp-totalpages');
  context.log('[DEBUG] Header x-wp-totalpages: $pageHeader');

  if (pageHeader == null) {
    context.error('[-] Missing x-wp-totalpages header. Assuming only one page.');
    return data;
  }

  final int pages = int.tryParse(pageHeader) ?? 1;

  // Falls es mehr als eine Seite gibt
  if (pages > 1) {
    final receivePort = ReceivePort();
    context.log('[#] Spawning app feed isolate for additional pages.');

    try {
      await Isolate.spawn(isolateAppFeed, [receivePort.sendPort, pages, context]);
      final List<dynamic> pageData = await receivePort.first;
      data.addAll(pageData);
    } catch (e) {
      context.error('[-] Unable to spawn isolate or fetch additional app feed pages. Error: $e');
      throw ParseException();
    }
  }

  context.log('[+] Retrieved full app news feed.');
  return data;
}

}

// Isolate function to fetch the app feed
// Isolate function to fetch additional pages of the app feed
Future<void> isolateAppFeed(List<dynamic> args) async {
  if (args.length < 3 || args[0] is! SendPort || args[1] is! int || args[2] == null) {
    print('[-] Invalid arguments passed to isolateAppFeed.');
    return;
  }

  final SendPort sendPort = args[0];
  final int pages = args[1];
  final context = args[2];

  final Dio client = Dio();
  final List<dynamic> data = [];

  context.log('[+] Spawned app feed isolate. Fetching pages 2 to $pages');

  Future<void> fetchPage(int pageNumber) async {
    final url = '${Platform.environment['APP_FEED_URL'] ?? 'https://app.asta-bochum.de/wp-json/wp/v2/posts'}?page=$pageNumber';
    try {
      context.log('[#] Fetching page $pageNumber from app feed.');
      final response = await client.get(url);

      if (response.statusCode != 200) {
        context.error('[-] Failed to fetch page $pageNumber. Status: ${response.statusCode}');
        return;
      }

      final List<dynamic> pageData = response.data;
      data.addAll(pageData);
    } catch (e) {
      context.error('[-] Exception while fetching app feed page $pageNumber: $e');
    }
  }

  final List<Future<void>> fetchTasks = [];
  for (int i = 2; i <= pages; i++) {
    fetchTasks.add(fetchPage(i));
  }

  await Future.wait(fetchTasks);

  context.log('[+] App feed isolate completed. Fetched ${data.length} additional posts.');
  sendPort.send(data);
}
