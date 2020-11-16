# BFQL

The Big Friendly Query Language (BFQL - "buffquill") is a very simple way to
match objects by tag-values. BFQL is designed to be expressive and easy to
read from a human perspective. BFQL is an English query language in that its
keywords come from English natural language.

BFQL is used in three ways, to match:

1. objects where a list of specified tag-values are returned,
2. objects that require a bulk update of specific tag-values, or
3. objects from which specified tags should be deleted.

The BFQL is heavily inspired by the query language
[created for FluidInfo](https://en.wikipedia.org/wiki/Fluidinfo#Query_language).

Tags are written as a unique `namespace/tag` path.

The following kinds of queries are possible and depend on the type of the tag
used in the query.

## All Tags

The type of the tag makes no difference to these sorts of query.

* Presence: `has library/title` will return all objects that have values
  annotated by the `library/title` tag.
* Absence: `missing library/title` will return all objects that have NOT been
  annotated with the `library/title` tag. Due to the potential for huge numbers
  of results, this query can only be used in conjuntion with another via the
  `and` operator.
* Conjugation (and): `library/summary matches "whales" and library/pages < 100`
  will return all objects that have the `library/summary` and `library/pages`
  tags and whose values match `"whales"` and `less than 100` respectively.
* Disjunction (or):
  `library/summary matches "whales" or library/summary matches "dolphins"`
  will return all objects that have the `library/summary` tag and whose value
  matches either `"whales"` or `"dolphins"`.
* Grouping: `has library/title and (nicholas/rating > 5 or terry/rating > 7)`
  returns all objects where the queries within the parenthesis are evaluated
  together before being conjugated with the results of the outer query to
  produce the final result set of object_ids. 

## String Based Tags

The following queries are possible on tags that are a type of `string`
(representing arbitrary textual data) or `pointer` (representing a URL pointing
to something elsewhere on the internet).

When writing strings, enclose them within double quotes.

* Equality: `library/title is "Moby Dick"` will return all objects with the
  `library/title` tag whose value is exactly `"Moby Dick"`.
* Case insensitive equality: `library/author iis "moby dick"` will return all
  objects with the `library/title` tag whose value is a case insensitive match
  for `"moby dick"`.
* Text matching: `library/summary matches "whales"` will return all objects
  with the `library/summary` tag whose value contains a case-sensitive match
  of the word `"whales"`.
* Case insensitive text matching: `library/summary imatches "whales"` will
  return all objects with the `library/summary` tag whose value contains a
  case-INsensitive match of the word `"whales"`.

## Boolean Tags

The following queries work on tags that are `boolean`.

* Truth: `nicholas/has_met is true` will return all objects with the
  `nicholas/has_met` tag whose value is true.
* Falsity: `nicholas/has_met is false` will return all objects with the
  `nicholas/has_met` tag whose value is false.

## Scalar Tags

The following queries only work with scalar tags: `integer`, `float`,
`datetime` and `duration`.

Integer and float values can be used with each other for comparison.

Integers are written as a sequence of digits: `1234`
Floats are written as a sequence of digits with a decimal point: `1.234`
Datetimes are written precisely to the second: `2020-09-24T15:30:30`
(`YYYY-MM-DDTHH:MM:SS` with the `T` separating the date and time portions for
readability reasons) or with just the date: `2020-09-24` (`YYYY-MM-DD`).
Timezone offset may also be appended `2020-09-24T15:30:30-08:00`
(`YYYY-MM-DDTHH:MM:SS[+|-]HH:MM`). These patterns follow the recommendations
in the W3C's [Date and Time Formats Note](https://www.w3.org/TR/NOTE-datetime).
Durations are expressed as exact numbers of days (denoted by an integer
followed by `d`) or seconds (an integer followed by `s`): `12d` or
`360s`. Other durations should be constructed by multiplying days or seconds to
the right value.

* Equal: `game/score = 1000` will return all objects with the `game/score` tag
  whose value is exactly the integer `1000`.
* Not equal: `game/score != 1000` will return all objects with the `game/score`
  tag whose value is NOT equal to the integer `1000`.
* Greater than: `bookshop/delivery_weight_kg > 1.2` will return all objects
  with the `bookshop/delivery_weight_kg` tag whose value is greater than the
  float `1.2`.
* Less than: `bookshop/delivery_weight_kg < 1.5` will return all objects with
  the `bookshop/delivery_weight_kg` tag whose value is less than the float
  `1.5`.
* Greater than or equal to: `employee/dob >= 1973-08-19` will return all
  objects with the `employee/dob` tag whose value is greater than or equal to
  the date `1973-08-19` (19th August, 1973).
* Less than or equal to: `employee/probation_period <= 365d` will return all
  objects with the `employee/probation_period` tag whose value is less than or
  equal to a duration of 365 days (`365d`).

## Binary Tags

Binary tags are, by their nature opaque (they store arbitrary binary
information). However they do automatically store the value's
[MIME type](https://tools.ietf.org/html/rfc6838).

* Type of: `library/audiobook is mime:audio/mpeg` will return all objects with
  the `library/audiobook` tag whose mime type is listed as `audio/mpeg` (i.e.
  MP3). MIME type information is always treated as case insensitive and must
  start with `mime:` (to differentiate MIME values from tag paths).

The current list of valid MIME types (and what file types they represent) can
be found [on the IANA's website](https://www.iana.org/assignments/media-types/media-types.xhtml).
