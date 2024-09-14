import 'package:dartz/dartz.dart';

import 'package:appwrite_function/events/calendar_repository.dart';

import '../entities/event_entity.dart';
import '../failures/failures.dart';
import '../translate/libre_translate_requests.dart';

class CalendarUsecases {
  final CalendarRepository calendarRepository;
  final dynamic context;

  CalendarUsecases({required this.calendarRepository, required this.context});

  /// Return a JSON object `data` that contains failures and events.
  ///
  /// data := { 'failures': List\<Failure>, 'events': List\<Event> }
  Future<Map<String, List<dynamic>>> getEvents(String locale) async {
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

    if (locale != 'de') {
      try {
        context.log('[#] Translating event entities.');

        final translatedEntitiesFutures = data['events']!.map((e) => translateEventEntity(e, locale)).toList();
        final translatedEntities = await Future.wait(translatedEntitiesFutures);

        context.log('[+] Translated event entities.');

        data['events'] = translatedEntities;
      } catch (e) {
        context.error('[-] Translation failed. Error: $e');
      }
    }

    List<Event>.from(data['events']!).sort((a, b) {
      return a.startDate.compareTo(b.startDate);
    });

    return data;
  }

  Future<Event> translateEventEntity(Event entity, String languageCode) async {
    var translatedTitle = "";
    var translatedDescription = "";

    // Translate title
    if(entity.title.isNotEmpty) {
      try {
        translatedTitle = await translateText(entity.title, 'auto', languageCode, context);
      } catch (e) {
        context.error('[-] Error while translating news entity. Error: $e');
      }
    }

    // Translate description / content
    if(entity.description.isNotEmpty) {
      try {
        translatedDescription = await  translateText(entity.description, 'auto', languageCode, context);
      } catch (e) {
        context.error('[-] Error while translating description. Error: $e');
      }
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
}
