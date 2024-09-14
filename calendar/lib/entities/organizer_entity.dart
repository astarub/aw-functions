class Organizer {
  /// The unique id of the event
  final int id;

  /// The url to REST API of specific news
  final String url;

  /// The organizers name
  final String name;

  /// The url identifier after base url:
  /// https://asta-bochum.de/veranstalter/${slug}
  final String slug;

  /// The organizers website phone number
  final String? phone;

  /// The organizers website
  final String? website;

  /// The organizers email
  final String? email;

  const Organizer({
    required this.id,
    required this.url,
    required this.name,
    required this.slug,
    this.phone,
    this.website,
    this.email,
  });

  factory Organizer.fromJson(Map<String, dynamic> json) {
    final phone = json.containsKey('phone') ? json['phone'] : null;
    final website = json.containsKey('website') ? json['website'] : null;
    final email = json.containsKey('email') ? json['email'] : null;

    return Organizer(
      id: json['id'],
      name: json['organizer'],
      url: json['url'],
      slug: json['slug'],
      phone: phone,
      website: website,
      email: email,
    );
  }

  Map<String, dynamic> toInternalJson() {
    return {
      'id': id,
      'url': name,
      'slug': slug,
      'phone': phone,
      'website': website,
      'email': email,
    };
  }

  @override
  String toString() => name;
}
