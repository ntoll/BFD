# Big Friendly Datastore

Organic data collaboration, from the ground up.

This is an experiment in APIs, data storage, aggregation and discovery.

## Developer Setup

This project uses Python 3.8+.

1. Clone the repository.
2. Create and start a new virtual environment.
3. `pip install -r requirements.txt`
4. Type `make` to see a list of common developer related tasks. For instance,
   to run the full test suite and code checks type: `make check`.

Developer documentation is in the `docs` sub-directory.

## Core Concepts

* Objects represent things and have a unique unicode name. BFD doesn't impose
  any further constraints on the name, except uniqueness. However, naming
  conventions are likely to evolve and/or be specified by mutual agreement of
  users working together across domains.
* Namespaced tags annotate data on openly writeable objects. The
  combination of namespace (who) and tag (what) provide meaningful context
  for the data tagged onto the object. Namespaces and tags also have
  associated descriptions to provide more schema detail.
* Tag values containing data about objects are typed and can be queried via
  predicate based comparison operations (`and`, `or`, `missing`, `<`, `>`, `=`,
  `<=`, `>=`, `(`, `)`, `has`), or naive string matching a la SQL `like`
  (and case insensitive `ilike`) pattern matching operator on string values.
  Queries either return specified tags on matching objects, update given values
  for matching objects, or delete specified tags from matching objects.
* Namespaces have admins and tags have users and readers. Admins configure
  the namespaces and tags belonging to their namespaces, users may annotate
  objects with the namespaces/tags and readers can see the namespaces/tags and
  their associated values.
* Interrogate individual objects for readable namespaces/tags (that may match
  a pattern).
* Events are raised when specific changes happen in the datastore. These are 
  configured to call web-hooks so third parties can follow what's going on. The
  event log can be used observe how the object and associated values changed
  through time (i.e. versioning).
* Data types understood by BFD: string, boolean, integer, floats, datetime,
  duration and pointer (URL). Geospatial types may also be added soon. Blobs of
  arbitrary bytes may also be stored (as raw data identified by mime-type).
  There is no such thing as "null". If a value isn't known, the tag is removed
  (but its historic presence is retained in the event log).

## Implementation

* Delivered via a REST API. Query results returned as either JSON or CSV.
* Admins, users and readers are expressed as a "whitelist", when the `private`
  flag is set to `True`. For instance, if the readers are set to,
  `private=False`, then everyone can see the namespace/tag. If the users are
  set to, `["nicholas", ]` and the flag `private=True`, then only the user
  identified as "nicholas" can annotate with the namespace/tag. If the admins
  are set to, `["mary", "penelope", ]`, then only the users identified as
  "mary" and "penelope" may change the behaviour of the namespace and the tags
  contained therein.

# Acknowledgements

Many of the ideas found herein have evolved from those used in FluidDB by
[Fluidinfo](https://fluidinfo.com/), a defunct startup project I was involved
with between 2009-2012 (when it folded). Special mention to
[Terry Jones](https://github.com/terrycojones) for much of the original thought
behind this, and to [Nick Radcliffe](https://github.com/njr0) for subsequent
stimulating exploration of the concepts involved.

Why this? Why now?

I find myself in need of such a data store, and since FluidDB is no more, I
need to reheat the ocean with my own plastic kettle. 🤨
