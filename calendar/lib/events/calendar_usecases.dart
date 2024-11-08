import 'dart:isolate';

import 'package:collection/collection.dart';
import 'package:dartz/dartz.dart';

import 'package:appwrite_function/events/calendar_repository.dart';

import '../entities/event_entity.dart';
import '../failures/failures.dart';
import '../translate/libre_translate_requests.dart';

final int MAX_THREADS = 4;

class CalendarUsecases {
  final CalendarRepository calendarRepository;
  final dynamic context;

  CalendarUsecases({required this.calendarRepository, required this.context});

  /// Return a JSON object `data` that contains failures and events.
  ///
  /// data := { 'failures': List\<Failure>, 'events': List\<Event> }
  Future<Map<String, List<dynamic>>> getEvents() async {
    // return data
    final Map<String, List<dynamic>> data = {
      'failures': <Failure>[],
      'events': <Event>[],
    };

    context.log('[#] Loading events.');

    // get events from AStA API and cached events
    final Either<Failure, List<Event>> remoteEvents = await calendarRepository.getAStAEvents();
    final Either<Failure, List<Event>> remoteAppEvents = await calendarRepository.getAppEvents();

    // fold remoteEvents
    remoteEvents.fold(
      (failure) => data['failures']!.add(failure),
      (events) => data['events'] = events, // overwrite cached feed
    );
    remoteAppEvents.fold(
      (failure) => data['failures']!.add(failure),
      (events) => data['events'] = List<Event>.from(data['events']!) + List<Event>.from(events),
    );

    context.log('[#] Loaded events and failures.');

    List<Event>.from(data['events']!).sort((a, b) {
      return a.startDate.compareTo(b.startDate);
    });

    return data;
  }

  Future<List<Event>> translateEvents(List<Event> events, String locale) async {
    context.log('[#] Starting translation of ${events.length} event(s).');

    final List<List<Event>> slicedEvents = events.slices(MAX_THREADS).toList();

    final List<Event> translatedEvents = [];

    final ReceivePort receivePort = ReceivePort();

    context.log('[#] Spawning translation isolates...');

    for(int i = 0; i < slicedEvents.length; i++) {
      await Isolate.spawn(translateIsolate, [receivePort.sendPort, slicedEvents[i], locale, i+1 == slicedEvents.length ? true : false]);
    }

    context.log('[#] Listening for translated events...');

    receivePort.listen((data) {
      Map<String, dynamic> result = data; 
      List<Event> events = List<Event>.from(result['events']).toList();

      translatedEvents.addAll(events);

      if(result['last']){
        receivePort.close();
      }
    });

    List<Event>.from(translatedEvents).sort((a, b) {
      return a.startDate.compareTo(b.startDate);
    });

    context.log('[#] Translated ${translatedEvents.length} event(s)...');

    return translatedEvents;
  }
}

Future<void> translateIsolate(List<dynamic> args) async {
  Future<Event> translateEventEntity(Event entity, String languageCode) async {
    var translatedTitle = "";
    var translatedDescription = "";

    // Translate title
    if(entity.title.isNotEmpty) {
      try {
        translatedTitle = await translateText(entity.title, 'auto', languageCode);
      } catch (e) {
      }
    }

    // Translate description / content
    if(entity.description.isNotEmpty) {
      try {
        translatedDescription = await translateText(entity.description, 'auto', languageCode);
      } catch (e) {}
    }

    return Event(
      id: entity.id,
      url: entity.url,
      title: translatedTitle,
      description: translatedDescription,
      slug: entity.slug,
      hasImage: entity.hasImage,
      imageUrl: entity.imageUrl,
      startDate: entity.startDate,
      endDate: entity.endDate,
      allDay: entity.allDay,
      cost: entity.cost,
      website: entity.website,
      categories: entity.categories,
      venue: entity.venue,
      organizers: entity.organizers,
      author: entity.author,
    );
  }

  if (args.isEmpty || args[0] is! SendPort || args[1] is! int) return;
  final SendPort sendPort = args[0];
  final List<Event> events = args[1];
  final String languageCode = args[2];
  final bool last = args[3];

  final List<Future<Event>> eventFutures = events.map((e) => translateEventEntity(e, languageCode)).toList();

  List<Event> translatedEvents = [];

  try {
    translatedEvents = await Future.wait(eventFutures);
  } catch(e) {}

  for(Event event in translatedEvents) {
    if(event.title.isEmpty) {
      translatedEvents.remove(event);
    }
  }

  Map<String, dynamic> result =  {
    'events': translatedEvents,
    'last': last
  };

  sendPort.send(result);
}
