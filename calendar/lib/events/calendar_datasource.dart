import 'dart:async';
import 'dart:io';
import 'dart:isolate';

import 'package:dio/dio.dart';

import '../failures/exceptions.dart';

const String astaEvents = 'https://asta-bochum.de/wp-json/tribe/events/v1/events';
const String appEvents = 'https://app.asta-bochum.de/wp-json/tribe/events/v1/events';

class CalendarDatasource {
  /// Dio client to perfrom network operations
  final Dio client;

  CalendarDatasource({
    required this.client,
  });

  /// Request events from tribe api.
  /// Throws a server excpetion if respond code is not 200.
  Future<List<dynamic>> getAStAEventsAsJsonArray() async {
    final response = await client.get(Platform.environment['ASTA_EVENTS_URL'] ?? astaEvents);

    late final Map<String, dynamic> responseBody;

    if (response.statusCode != 200) {
      throw ServerException();
    }

    try {
      responseBody = response.data as Map<String, dynamic>;
    } catch (e) {
      throw JsonException();
    }

    final List<dynamic> events = responseBody['events'];

    // Fetch events from multiple pages, if there are more than one page
    try {
      final int pages = int.parse(response.headers.value('x-tec-totalpages')!);

      final receivePort = ReceivePort();

      await Isolate.spawn(isolateAStACalendar, [receivePort.sendPort, pages]);

      final List<dynamic> pageData = await receivePort.first;

      events.addAll(pageData);
    } catch (e) {
      throw ServerException();
    }

    return events;
  }

  /// Request events from tribe api.
  /// Throws a server excpetion if respond code is not 200.
  Future<List<dynamic>> getAppEventsAsJsonArray() async {
    final response = await client.get(Platform.environment['APP_EVENTS_URL'] ?? appEvents);

    late final Map<String, dynamic> responseBody;

    if (response.statusCode != 200) {
      throw ServerException();
    }

    try {
      responseBody = response.data as Map<String, dynamic>;
    } catch (e) {
      throw JsonException();
    }

    final List<dynamic> events = responseBody['events'];

    // Fetch events from multiple pages, if there are more than one page
    try {
      final int pages = int.parse(response.headers.value('x-tec-totalpages')!);

      final receivePort = ReceivePort();

      await Isolate.spawn(isolateAppCalendar, [receivePort.sendPort, pages]);

      final List<dynamic> pageData = await receivePort.first;

      events.addAll(pageData);
    } catch (e) {
      throw ServerException();
    }

    return events;
  }
}
/// Isolate function to fetch the AStA calendar
Future<void> isolateAStACalendar(List<dynamic> args) async {
  if (args.isEmpty || args[0] is! SendPort || args[1] is! int) return;
  final SendPort sendPort = args[0];
  final int pages = args[1];

  final client = Dio();
  final List<dynamic> events = [];

  // Fetch a specific page from the asta-bochum.de JSON API
  Future<void> getAStAEventPage(int page) async {
    final responseForPage = await client.get('$astaEvents?page=$page');

    if (responseForPage.statusCode != 200) return;

    Map<String, dynamic> responsePageBody;

    try {
      responsePageBody = responseForPage.data as Map<String, dynamic>;
    } catch (e) {
      return;
    }

    events.addAll(responsePageBody['events']);
  }

  if (pages > 1) {
    final List<Future<void>> futures = [];
    for (int i = 2; i <= pages; i++) {
      futures.add(getAStAEventPage(i));
    }

    await Future.wait(futures);
  }

  sendPort.send(events);
}

/// Isolate function to fetch the app calendar
Future<void> isolateAppCalendar(List<dynamic> args) async {
  if (args.isEmpty || args[0] is! SendPort || args[1] is! int) return;
  final SendPort sendPort = args[0];
  final int pages = args[1];

  final client = Dio();
  final List<dynamic> events = [];

  /// Fetch a specific page from the asta-bochum.de JSON API
  Future<void> getAppEventPage(int page) async {
    final responseForPage = await client.get('$appEvents?page=$page');

    if (responseForPage.statusCode != 200) return;

    Map<String, dynamic> responsePageBody;

    try {
      responsePageBody = responseForPage.data as Map<String, dynamic>;
    } catch (e) {
      return;
    }

    events.addAll(responsePageBody['events']);
  }

  if (pages > 1) {
    final List<Future<void>> futures = [];
    for (int i = 2; i <= pages; i++) {
      futures.add(getAppEventPage(i));
    }

    await Future.wait(futures);
  }

  sendPort.send(events);
}
