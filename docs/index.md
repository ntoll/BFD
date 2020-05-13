# Big Friendly Datastore

Organic data collaboration, from the ground up. 🗂🚀🤔👍

This is an experiment in data storage, aggregation and discovery.

## Developer Setup

This project uses Python 3.8+.

1. Clone the repository.
2. Create and start a new virtual environment.
3. `pip install -r requirements.txt`
4. Type `make` to see a list of common developer related tasks. For instance,
   to run the full test suite and code checks type: `make check`.

## Core Concepts

* Objects represent things and have a unique unicode name. BFG doesn't impose
  any further constraints on the name, except uniqueness. However, naming
  conventions are likely to evolve and/or be specified by mutual agreement of
  users working together across domains.
* Namespaced tags annotate data on openly writeable objects. The
  combination of namespace (who) and tag (what) provide meaningful context
  for the data tagged onto the object.
* Tag values containing data about objects can be queried via predicate based
  comparison operations (`and`, `or`, `not`, `<`, `>`, `=`, `<=`, `>=`, `(`,
  `)`), or naive string matching a la SQL `like` (and case insensitive `ilike`)
  pattern matching operator on string values. Queries return specified tags on
  matching objects.
* Namespaces and tags have admins, users and readers. Admins configure
  the namespaces/tags, users may annotate objects with the namespaces/tags and
  readers can see the namespaces/tags and their associated values.
* Interrogate individual objects for readable namespaces/tags (that may match
  a pattern).
* Events are raised when specific changes happen in the datastore. These are 
  configured to call web-hooks so third parties can follow what's going on.
* Data types understood by BFD: string, boolean, integer and floats. Blobs of
  arbitrary bytes may also be stored (as a URL that referencng raw data
  identified by mime-type).

## Implementation

* Delivered via a REST API. Query results returned as either JSON or CSV.
* Admins, users and readers are expressed as a "whitelist", where an empty list
  means "everyone". For instance, if the readers are set to, `[]`, then
  everyone can see the namespace/tag. If the users are set to,
  `["nicholas", ]`, then only the user identified as "nicholas" can annotate
  with the namespace/tag. If the admins are set to, `["mary", "penelope", ]`,
  then only the users identified as "mary" and "penelope" may change the
  behaviour of the namespace/tag.
* A namespace's admins, users and readers are inherited by tags contained
  within. However, individual tags can override this inheritance.

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

## Contents
```eval_rst
.. toctree::
   :maxdepth: 2

   license.md
```
