import 'dart:async';


import 'package:dartz/dartz.dart';

import '../entities/event_entity.dart';
import '../failures/exceptions.dart';
import '../failures/failures.dart';
import 'calendar_datasource.dart';

class CalendarRepository {
  final CalendarDatasource calendarDatasource;
  final dynamic context;

  CalendarRepository({required this.calendarDatasource, required this.context});

  /// Return a list of events or a failure
  Future<Either<Failure, List<Event>>> getAStAEvents() async {
    try {
      final astaEventsJson = await calendarDatasource.getAStAEventsAsJsonArray();

      final List<Event> entities = [];

      for (final Map<String, dynamic> eventJson in astaEventsJson) {
        final Event event = Event.fromExternalJson(eventJson);

        if (event.categories.map((cat) => cat.name).contains('UFO')) continue;

        entities.add(event);
      }

      return Right(entities);
    } catch (e) {
      context.error('[-] Error while fetching the asta events in the calendar repository. Exception: $e');

      switch (e.runtimeType) {
        case const (ServerException):
          return Left(ServerFailure());

        case const (JsonException):
          return Left(ServerFailure());

        case const (EmptyResponseException):
          return Left(NoDataFailure());

        default:
          return Left(GeneralFailure());
      }
    }
  }

  /// Return a list of events or a failure
  Future<Either<Failure, List<Event>>> getAppEvents() async {
    try {
      final astaEventsJson = await calendarDatasource.getAppEventsAsJsonArray();

      final List<Event> entities = [];

      for (final Map<String, dynamic> event in astaEventsJson) {
        entities.add(Event.fromExternalJson(event));
      }

      return Right(entities);
    } catch (e) {
      context.error('[-] Error while fetching the app events in the calendar repository. Exception: $e');

      switch (e.runtimeType) {
        case const (ServerException):
          return Left(ServerFailure());

        case const (JsonException):
          return Left(ServerFailure());

        case const (EmptyResponseException):
          return Left(NoDataFailure());

        default:
          return Left(GeneralFailure());
      }
    }
  }
}
